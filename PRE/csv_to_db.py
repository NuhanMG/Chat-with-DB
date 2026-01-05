"""
Standalone CSV to SQLite Database Creator with LLM Analysis

This script:
1. Loads a CSV file (supports large files via chunked processing)
2. Uses Ollama LLM to analyze metadata and column types
3. Creates a SQLite database with proper schema
4. Inserts the data in batches for memory efficiency

Usage:
    python csv_to_db.py <csv_file> [--db database.db] [--model qwen2.5:7b] [--chunksize 50000]
    
Example:
    python csv_to_db.py sales.csv --db analysis.db --model qwen2.5:7b
    python csv_to_db.py large_file.csv --db analysis.db --chunksize 100000
"""

import os
import re
import sqlite3
import logging
import argparse
import json
import gc
from typing import Dict, List, Any, Iterator

import pandas as pd
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MetadataResponse(BaseModel):
    """Metadata response model"""
    table_name: str = Field(description="Suggested table name in snake_case")
    description: str = Field(description="Detailed description of the table content")
    suggested_primary_key: str | None = Field(default=None, description="Suggested primary key")
    category: str = Field(default="unknown", description="Business category")
    business_context: str = Field(description="Business context")
    data_quality_notes: List[str] = Field(default_factory=list, description="Data quality observations")


class DataTypeResponse(BaseModel):
    """Data type response model"""
    sql_type: str = Field(description="SQL data type (TEXT, INTEGER, REAL, DATE, BOOLEAN)")
    python_type: str = Field(description="Python data type")
    description: str = Field(description="Column description")
    business_meaning: str = Field(description="Business meaning")
    constraints: List[str] = Field(default_factory=list, description="SQL constraints")
    is_nullable: bool = Field(default=True, description="Can contain NULL")
    suggested_index: bool = Field(default=False, description="Should be indexed")


class CSVtoDatabaseConverter:
    """Convert CSV to SQLite with LLM-powered analysis (supports large files)"""
    
    # Default chunk size for processing large files
    DEFAULT_CHUNK_SIZE = 50000  # 50k rows per chunk
    SAMPLE_SIZE = 5000  # Rows to sample for LLM analysis
    
    def __init__(self, model: str = "qwen2.5:7b", db_path: str = "marks.db", chunksize: int = None):
        self.model = model
        self.db_path = db_path
        self.chunksize = chunksize or self.DEFAULT_CHUNK_SIZE
        
        # Initialize LLM
        logger.info(f"Initializing Ollama with model: {model}")
        self.llm = ChatOllama(
            model=model,
            base_url="http://localhost:11434",
            temperature=0.0
        )
        
        # Initialize parsers
        self.metadata_parser = PydanticOutputParser(pydantic_object=MetadataResponse)
        self.datatype_parser = PydanticOutputParser(pydantic_object=DataTypeResponse)
        
        self._setup_prompts()
    
    def _setup_prompts(self):
        """Setup LLM prompts"""
        self.metadata_prompt = PromptTemplate(
            input_variables=["sheet_name", "columns", "sample_data"],
            partial_variables={"format_instructions": self.metadata_parser.get_format_instructions()},
            template="""Analyze this dataset and provide metadata:
            
Sheet/Table Name: {sheet_name}
Columns: {columns}
Sample Data (first 5 rows):
{sample_data}

Determine:
1. Appropriate table name (snake_case, database-friendly)
2. Business description and purpose
3. Suggested primary key column (if any)
4. Data category (sales, financial, educational, healthcare, etc.)
5. Business context
6. Any data quality observations

{format_instructions}"""
        )
        
        self.datatype_prompt = PromptTemplate(
            input_variables=["column_name", "sample_values", "unique_count", "null_count", "total_rows"],
            partial_variables={"format_instructions": self.datatype_parser.get_format_instructions()},
            template="""Analyze this column and determine its data type:

Column Name: {column_name}
Sample Values: {sample_values}
Unique Values: {unique_count} out of {total_rows} rows
Null Count: {null_count}

Determine the optimal:
1. SQL data type (TEXT, INTEGER, REAL, DATE, BOOLEAN)
2. Python type equivalent
3. Description of what this column contains
4. Business meaning
5. Constraints (UNIQUE, NOT NULL, etc.)
6. Whether it should be indexed

{format_instructions}"""
        )
    
    def _parse_with_fallback(self, response_text: str, parser, fallback_data: dict):
        """Parse LLM response with fallback"""
        try:
            return parser.parse(response_text)
        except Exception as e:
            logger.warning(f"Parsing failed: {e}. Using fallback.")
            
            # Try to extract JSON
            try:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0).replace("'", '"')
                    json_str = re.sub(r',\s*}', '}', json_str)
                    parsed_data = json.loads(json_str)
                    return parsed_data
            except:
                pass
            
            return fallback_data
    
    def analyze_metadata(self, df: pd.DataFrame, filename: str) -> Dict:
        """Analyze CSV metadata using LLM"""
        logger.info("Analyzing file metadata...")
        
        sheet_name = os.path.basename(filename).replace('.csv', '')
        sample_data = df.head(5).to_string()
        columns = ", ".join(df.columns)
        
        chain = self.metadata_prompt | self.llm | StrOutputParser()
        response_text = chain.invoke({
            "sheet_name": sheet_name,
            "columns": columns,
            "sample_data": sample_data
        })
        
        fallback = {
            "table_name": re.sub(r'[^a-zA-Z0-9_]', '_', sheet_name.lower()),
            "description": f"Data from {sheet_name}",
            "suggested_primary_key": None,
            "category": "unknown",
            "business_context": "General data",
            "data_quality_notes": []
        }
        
        result = self._parse_with_fallback(response_text, self.metadata_parser, fallback)
        metadata = result.model_dump() if hasattr(result, 'model_dump') else result
        
        logger.info(f"✓ Table name: {metadata['table_name']}")
        logger.info(f"✓ Description: {metadata['description']}")
        logger.info(f"✓ Category: {metadata['category']}")
        
        return metadata
    
    def analyze_column(self, column_name: str, column_data: pd.Series) -> Dict:
        """Analyze single column using LLM"""
        sample_values = column_data.dropna().head(10).tolist()
        unique_count = column_data.nunique()
        null_count = column_data.isna().sum()
        total_rows = len(column_data)
        
        chain = self.datatype_prompt | self.llm | StrOutputParser()
        response_text = chain.invoke({
            "column_name": column_name,
            "sample_values": str(sample_values),
            "unique_count": unique_count,
            "null_count": null_count,
            "total_rows": total_rows
        })
        
        fallback = self._auto_detect_type(column_data)
        result = self._parse_with_fallback(response_text, self.datatype_parser, fallback)
        return result.model_dump() if hasattr(result, 'model_dump') else result
    
    def _auto_detect_type(self, column_data: pd.Series) -> Dict:
        """Auto-detect column type as fallback"""
        if pd.api.types.is_integer_dtype(column_data):
            sql_type, python_type = "INTEGER", "int"
        elif pd.api.types.is_float_dtype(column_data):
            sql_type, python_type = "REAL", "float"
        elif pd.api.types.is_datetime64_any_dtype(column_data):
            sql_type, python_type = "DATE", "datetime"
        elif pd.api.types.is_bool_dtype(column_data):
            sql_type, python_type = "BOOLEAN", "bool"
        else:
            sql_type, python_type = "TEXT", "str"
        
        return {
            "sql_type": sql_type,
            "python_type": python_type,
            "description": "Auto-detected column",
            "business_meaning": "Data column",
            "constraints": [],
            "is_nullable": column_data.isna().any(),
            "suggested_index": False
        }
    
    def create_database(self, df_sample: pd.DataFrame, metadata: Dict, column_analysis: Dict[str, Dict], csv_file: str):
        """Create SQLite database with analyzed schema and insert data in chunks"""
        logger.info(f"Creating database: {self.db_path}")
        
        table_name = metadata['table_name']
        
        # Clean column names - create mapping
        original_columns = df_sample.columns.tolist()
        clean_columns = []
        column_mapping = {}
        for col in original_columns:
            clean_col = re.sub(r'[^a-zA-Z0-9_]', '_', col.lower())
            clean_columns.append(clean_col)
            column_mapping[col] = clean_col
        
        # Build CREATE TABLE statement
        ddl_parts = [f"CREATE TABLE IF NOT EXISTS {table_name} ("]
        
        for orig_col, clean_col in zip(original_columns, clean_columns):
            col_info = column_analysis.get(orig_col, {})
            sql_type = col_info.get('sql_type', 'TEXT')
            constraints = col_info.get('constraints', [])
            
            # Avoid strict constraints based on partial samples
            constraints = [c for c in constraints if c.upper() not in ['NOT NULL', 'UNIQUE']]
            
            constraint_str = " ".join(constraints) if constraints else ""
            ddl_parts.append(f"    {clean_col} {sql_type} {constraint_str},")
        
        ddl_parts[-1] = ddl_parts[-1].rstrip(',')
        ddl_parts.append(")")
        ddl = "\n".join(ddl_parts)
        
        logger.info(f"Schema:\n{ddl}")
        
        # Create connection and table
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enable optimizations for bulk insert
        cursor.execute("PRAGMA journal_mode = OFF")
        cursor.execute("PRAGMA synchronous = OFF")
        cursor.execute("PRAGMA cache_size = 1000000")  # ~1GB cache
        cursor.execute("PRAGMA temp_store = MEMORY")
        
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.execute(ddl)
        conn.commit()
        
        # Insert data in chunks
        logger.info(f"Inserting data in chunks of {self.chunksize} rows...")
        total_rows = 0
        chunk_num = 0
        
        # Build type conversion info once
        type_conversions = {}
        for orig_col in original_columns:
            col_info = column_analysis.get(orig_col, {})
            type_conversions[orig_col] = col_info.get('sql_type', 'TEXT')
        
        # Read and insert in chunks
        for chunk in pd.read_csv(csv_file, chunksize=self.chunksize, low_memory=True):
            chunk_num += 1
            
            # Rename columns
            chunk.columns = clean_columns
            
            # Apply type conversions
            for orig_col, clean_col in zip(original_columns, clean_columns):
                sql_type = type_conversions.get(orig_col, 'TEXT')
                
                if sql_type == 'DATE':
                    chunk[clean_col] = pd.to_datetime(chunk[clean_col], errors='coerce')
                elif sql_type == 'INTEGER':
                    chunk[clean_col] = pd.to_numeric(chunk[clean_col], errors='coerce', downcast='integer')
                elif sql_type == 'REAL':
                    chunk[clean_col] = pd.to_numeric(chunk[clean_col], errors='coerce')
            
            # Insert chunk
            chunk.to_sql(table_name, conn, if_exists='append', index=False)
            total_rows += len(chunk)
            
            if chunk_num % 10 == 0:
                logger.info(f"  Processed chunk {chunk_num}: {total_rows:,} rows inserted so far...")
                gc.collect()  # Free memory
        
        conn.commit()
        
        # Re-enable normal mode and verify
        cursor.execute("PRAGMA journal_mode = DELETE")
        cursor.execute("PRAGMA synchronous = FULL")
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        logger.info(f"✅ Created table '{table_name}' with {count:,} rows")
        
        conn.close()
        return table_name, count
    
    def _get_file_info(self, csv_file: str) -> Dict:
        """Get basic file info without loading entire file"""
        file_size = os.path.getsize(csv_file)
        file_size_mb = file_size / (1024 * 1024)
        file_size_gb = file_size / (1024 * 1024 * 1024)
        
        # Count rows efficiently (without loading into memory)
        logger.info("Counting rows (this may take a moment for large files)...")
        row_count = 0
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            for _ in f:
                row_count += 1
        row_count -= 1  # Subtract header row
        
        return {
            'file_size_bytes': file_size,
            'file_size_mb': file_size_mb,
            'file_size_gb': file_size_gb,
            'row_count': row_count
        }
    
    def _load_sample(self, csv_file: str) -> pd.DataFrame:
        """Load only a sample of the CSV for analysis"""
        logger.info(f"Loading sample of {self.SAMPLE_SIZE} rows for analysis...")
        return pd.read_csv(csv_file, nrows=self.SAMPLE_SIZE, low_memory=True)
    
    def convert(self, csv_file: str) -> str:
        """Main conversion workflow with chunked processing for large files"""
        logger.info(f"Starting conversion: {csv_file} → {self.db_path}")
        
        # Get file info
        file_info = self._get_file_info(csv_file)
        logger.info(f"✓ File size: {file_info['file_size_mb']:.2f} MB ({file_info['file_size_gb']:.2f} GB)")
        logger.info(f"✓ Total rows: {file_info['row_count']:,}")
        
        # Load only a sample for LLM analysis (not entire file)
        df_sample = self._load_sample(csv_file)
        logger.info(f"✓ Loaded sample: {len(df_sample)} rows, {len(df_sample.columns)} columns")
        
        # Analyze metadata using sample
        metadata = self.analyze_metadata(df_sample, csv_file)
        
        # Analyze each column using sample data
        logger.info("Analyzing columns using sample data...")
        column_analysis = {}
        for col in df_sample.columns:
            logger.info(f"  Analyzing column: {col}")
            col_info = self.analyze_column(col, df_sample[col])
            column_analysis[col] = col_info
            logger.info(f"    → Type: {col_info['sql_type']}, Nullable: {col_info['is_nullable']}")
        
        # Free sample memory before bulk insert
        del df_sample
        gc.collect()
        
        # Create database and insert data in chunks
        table_name, total_rows = self.create_database(
            self._load_sample(csv_file),  # Reload sample for column names
            metadata, 
            column_analysis, 
            csv_file
        )
        
        logger.info(f"\n{'='*60}")
        logger.info("✅ CONVERSION COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Database: {self.db_path}")
        logger.info(f"Table: {table_name}")
        logger.info(f"Description: {metadata['description']}")
        logger.info(f"Category: {metadata['category']}")
        logger.info(f"Rows: {total_rows:,}")
        logger.info(f"Original file size: {file_info['file_size_mb']:.2f} MB")
        logger.info(f"{'='*60}\n")
        
        return table_name


def main():
    parser = argparse.ArgumentParser(
        description='Convert CSV to SQLite database with LLM-powered analysis (supports large files)'
    )
    parser.add_argument('csv_file', help='Path to CSV file')
    parser.add_argument('--db', default='analysis.db', help='Output database path (default: analysis.db)')
    parser.add_argument('--model', default='qwen2.5:7b', help='Ollama model to use (default: qwen2.5:7b)')
    parser.add_argument('--chunksize', type=int, default=50000, 
                        help='Number of rows to process at a time (default: 50000). Increase for faster processing, decrease if running out of memory.')
    
    args = parser.parse_args()
    
    # Validate CSV file
    if not os.path.exists(args.csv_file):
        logger.error(f"CSV file not found: {args.csv_file}")
        return 1
    
    try:
        # Create converter and run
        converter = CSVtoDatabaseConverter(
            model=args.model, 
            db_path=args.db,
            chunksize=args.chunksize
        )
        converter.convert(args.csv_file)
        return 0
    except Exception as e:
        logger.error(f"Conversion failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())
