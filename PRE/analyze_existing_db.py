#!/usr/bin/env python3
"""
One-time database analyzer script
Analyzes existing SQLite database tables and saves metadata to a vector database
"""
import sqlite3
import logging
from typing import Dict, List, Any
import pandas as pd
import argparse
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field
import json
import os
import chromadb
from chromadb.config import Settings
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# analysis of a single database table.

class MetadataResponse(BaseModel):
    """Metadata response model"""
    table_name: str = Field(description="Table name")    # confirms which table the AI is currently analyzing
    description: str = Field(description="Detailed description of the table content") 
    suggested_primary_key: str | None = Field(default=None, description="Suggested primary key")  
    category: str = Field(default="unknown", description="Business category") # sementic grouping like sales, financial, educational, healthcare, etc.
    business_context: str = Field(description="Business context") # A table named t_users might be technically "Users," but the business context is "Active subscribers eligible for renewal."
    data_quality_notes: List[str] = Field(default_factory=list, description="Data quality observations") # "Column 'email' has 20% null values", "Dates are in mixed formats"


# analysis of a single column within a table

class DataTypeResponse(BaseModel):
    """Data type response model"""
    sql_type: str = Field(description="SQL data type (TEXT, INTEGER, REAL, DATE, BOOLEAN)") # run sql queries
    python_type: str = Field(description="Python data type") # to draw charts 
    description: str = Field(description="Column description")
    business_meaning: str = Field(description="Business meaning")   # A column named "amt" might technically be a REAL, but its business meaning is "Total purchase amount in USD."
    constraints: List[str] = Field(default_factory=list, description="SQL constraints")   # Identifies rules like UNIQUE, NOT NULL to helps in writing correct SQL queries later.
    is_nullable: bool = Field(default=True, description="Can contain NULL")
    suggested_index: bool = Field(default=False, description="Should be indexed")


class ExistingDatabaseAnalyzer:
    """Analyze existing SQLite database tables and save metadata to vector database"""
    
    def __init__(
        self,
        source_db_path: str,
        vector_db_path: str = "./chroma_db_768dim",
        llm_model: str = "qwen2.5:7b",
        ollama_base_url: str = "http://localhost:11434",
        temperature: float = 0.1,
        embedding_model: str = "nomic-embed-text",
        chunk_size: int = 10000, # loads 10k rows at a time
        sample_size: int = 1000 # how much data the LLM sees
    ):
        self.source_db_path = source_db_path
        self.vector_db_path = vector_db_path
        self.embedding_model = embedding_model
        self.ollama_base_url = ollama_base_url
        self.chunk_size = chunk_size
        self.sample_size = sample_size
        
        # Initialize Ollama LLM
        try:
            self.llm = ChatOllama(
                model=llm_model,
                base_url=ollama_base_url,
                temperature=temperature,
            )
            logger.info(f"Initialized Ollama with model: {llm_model}")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {e}")
            raise
        
        # Initialize parsers
        self.metadata_parser = PydanticOutputParser(pydantic_object=MetadataResponse)
        self.datatype_parser = PydanticOutputParser(pydantic_object=DataTypeResponse)
        
        self.setup_prompts()
        self.setup_vector_database()
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding from Ollama
        
        Input - text string
        Sends a POST request to Ollama server  - http://localhost:11434/api/embeddings
        Asks the embedding model to generate embedding for the text
        Output - list of floats (embedding vector)
           
        If ollama server crashes or embedding fails, returns a zero vector as fallback. (list of 768 zeros for nomic-embed-text)     
        
        """
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/embeddings",
                json={"model": self.embedding_model, "prompt": text}
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            # Return zero vector as fallback - nomic-embed-text produces 768-dim
            return [0.0] * 768
    
    
    def setup_prompts(self):
        """Setup prompt templates"""
        
        # Metadata analysis prompt (understand table as a whole)
        self.metadata_prompt = PromptTemplate(
            
            input_variables=["table_name", "columns", "sample_data", "row_count"],
            partial_variables={"format_instructions": self.metadata_parser.get_format_instructions()}, # automatically injects below, long complex instruction 
            template="""Analyze this database table and provide metadata:

Table Name: {table_name}
Total Rows: {row_count}
Columns: {columns}
Sample Data (first 5 rows):
{sample_data}

Determine:
1. Detailed business description and purpose
2. Suggested primary key column (if any)
3. Data category (sales, financial, educational, healthcare, etc.)
4. Business context
5. Any data quality observations

{format_instructions}"""
        )
        
        # Data type analysis prompt (understand individual column)
        self.datatype_prompt = PromptTemplate(
            input_variables=["table_name", "column_name", "sample_values", "unique_count", "null_count", "total_rows"],
            partial_variables={"format_instructions": self.datatype_parser.get_format_instructions()},
            template="""Analyze this column and determine its data type and business meaning:

Table: {table_name}
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
    
    def setup_vector_database(self):
        """Create vector database with ChromaDB"""
        try:
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(
                path=self.vector_db_path,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Create or get collections
            self.table_collection = self.chroma_client.get_or_create_collection(
                name="table_metadata",
                metadata={"description": "Table-level metadata"}
            )
            
            self.column_collection = self.chroma_client.get_or_create_collection(
                name="column_metadata",
                metadata={"description": "Column-level metadata"}
            )
            
            logger.info(f"✅ Vector database initialized at: {self.vector_db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")
            raise
    
    def get_table_names(self) -> List[str]:
        """Get all table names from source database"""
        conn = sqlite3.connect(self.source_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables
    
    def analyze_table(self, table_name: str) -> Dict[str, Any]:
        """Analyze a single table using SQL-based statistics (no full load)"""
        logger.info(f"🔍 Analyzing table: {table_name}")
        
        conn = sqlite3.connect(self.source_db_path)
        
        # 1. Get row count efficiently
        count_query = f"SELECT COUNT(*) as total FROM {table_name}"
        total_rows = pd.read_sql_query(count_query, conn).iloc[0]['total']
        
        # 2. Get column names from PRAGMA
        schema_query = f"PRAGMA table_info({table_name})"
        columns_info = pd.read_sql_query(schema_query, conn)
        column_names = columns_info['name'].tolist()
        
        logger.info(f"   Found {total_rows} rows and {len(column_names)} columns")
        
        # 3. Get small sample for LLM analysis (only sample_size rows)
        sample_query = f"SELECT * FROM {table_name} ORDER BY RANDOM() LIMIT {min(self.sample_size, total_rows)}"
        sample_df = pd.read_sql_query(sample_query, conn)
        
        # 4. Get table metadata using LLM (using sample)
        metadata = self._analyze_table_metadata(table_name, sample_df, total_rows)
        
        # 5. Analyze each column using SQL stats (not Pandas)
        column_analyses = []
        for i, col in enumerate(column_names, 1):
            logger.info(f"   Analyzing column {i}/{len(column_names)}: {col}")
            col_analysis = self._analyze_column_efficient(conn, table_name, col, total_rows)
            column_analyses.append(col_analysis)
        
        conn.close()
        
        return {
            'table_name': table_name,
            'metadata': metadata,
            'column_analyses': column_analyses,
            'row_count': total_rows
        }
    
    def _analyze_table_metadata(self, table_name: str, df: pd.DataFrame, total_rows: int) -> Dict:
        """Analyze table metadata using LLM with sample data"""
        try:
            sample_data = df.head(5).to_string()
            columns = ", ".join(df.columns)
            
            chain = self.metadata_prompt | self.llm | StrOutputParser()
            
            response_text = chain.invoke({
                "table_name": table_name,
                "columns": columns,
                "sample_data": sample_data,
                "row_count": total_rows
            })
            
            result = self._parse_with_fallback(response_text, self.metadata_parser, {
                "table_name": table_name,
                "description": f"Table {table_name}",
                "suggested_primary_key": None,
                "category": "unknown",
                "business_context": "General data",
                "data_quality_notes": []
            })
            
            return result.model_dump() if hasattr(result, 'model_dump') else result
            
        except Exception as e:
            logger.warning(f"⚠️  Error analyzing table metadata: {e}")
            return {
                "table_name": table_name,
                "description": f"Table {table_name}",
                "suggested_primary_key": None,
                "category": "unknown",
                "business_context": "General data",
                "data_quality_notes": []
            }
    
    def _analyze_column_efficient(self, conn: sqlite3.Connection, table_name: str, column_name: str, total_rows: int) -> Dict:
        """Analyze column using SQL aggregations (no data loading)"""
        try:
            # Get statistics via SQL (no full data loading)
            stats_query = f"""
            SELECT 
                COUNT(DISTINCT "{column_name}") as unique_count,
                COUNT(*) - COUNT("{column_name}") as null_count,
                COUNT(*) as total_count
            FROM {table_name}
            """
            
            stats = pd.read_sql_query(stats_query, conn).iloc[0]
            
            # Get sample values for LLM analysis (only 20 distinct values)
            sample_query = f"""
            SELECT DISTINCT "{column_name}" 
            FROM {table_name} 
            WHERE "{column_name}" IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 20
            """
            
            sample_df = pd.read_sql_query(sample_query, conn)
            sample_values = sample_df[column_name].tolist() if not sample_df.empty else []
            
            # Get a small sample for type detection fallback
            type_detect_query = f'SELECT "{column_name}" FROM {table_name} LIMIT 100'
            type_detect_df = pd.read_sql_query(type_detect_query, conn)
            
            chain = self.datatype_prompt | self.llm | StrOutputParser()
            
            response_text = chain.invoke({
                "table_name": table_name,
                "column_name": column_name,
                "sample_values": str(sample_values),
                "unique_count": int(stats['unique_count']),
                "null_count": int(stats['null_count']),
                "total_rows": total_rows
            })
            
            fallback_data = self._auto_detect_type(type_detect_df[column_name])
            result = self._parse_with_fallback(response_text, self.datatype_parser, fallback_data)
            
            # Add statistics
            analysis = result.model_dump() if hasattr(result, 'model_dump') else result
            analysis['unique_count'] = int(stats['unique_count'])
            analysis['null_count'] = int(stats['null_count'])
            analysis['column_name'] = column_name
            
            return analysis
            
        except Exception as e:
            logger.warning(f"⚠️  Error analyzing column {column_name}: {e}")
            # Use fallback with small sample
            try:
                type_detect_query = f'SELECT "{column_name}" FROM {table_name} LIMIT 100'
                type_detect_df = pd.read_sql_query(type_detect_query, conn)
                fallback = self._auto_detect_type(type_detect_df[column_name])
            except Exception:
                fallback = {
                    "sql_type": "TEXT",
                    "python_type": "str",
                    "description": "Auto-detected column",
                    "business_meaning": "Data column",
                    "constraints": [],
                    "is_nullable": True,
                    "suggested_index": False
                }
            
            fallback['column_name'] = column_name
            fallback['unique_count'] = 0
            fallback['null_count'] = 0
            return fallback
    
    def _analyze_column(self, table_name: str, column_name: str, column_data: pd.Series) -> Dict:
        """Legacy method - kept for backward compatibility"""
        try:
            sample_values = column_data.dropna().head(10).tolist()
            unique_count = column_data.nunique()
            null_count = int(column_data.isna().sum())
            total_rows = len(column_data)
            
            chain = self.datatype_prompt | self.llm | StrOutputParser()
            
            response_text = chain.invoke({
                "table_name": table_name,
                "column_name": column_name,
                "sample_values": str(sample_values),
                "unique_count": unique_count,
                "null_count": null_count,
                "total_rows": total_rows
            })
            
            fallback_data = self._auto_detect_type(column_data)
            result = self._parse_with_fallback(response_text, self.datatype_parser, fallback_data)
            
            # Add statistics
            analysis = result.model_dump() if hasattr(result, 'model_dump') else result
            analysis['unique_count'] = unique_count
            analysis['null_count'] = null_count
            analysis['column_name'] = column_name
            
            return analysis
            
        except Exception as e:
            logger.warning(f"⚠️  Error analyzing column {column_name}: {e}")
            fallback = self._auto_detect_type(column_data)
            fallback['column_name'] = column_name
            fallback['unique_count'] = column_data.nunique()
            fallback['null_count'] = int(column_data.isna().sum())
            return fallback
    
    def _parse_with_fallback(self, response_text: str, parser, fallback_data: dict = None):
        """Parse LLM response with fallback"""
        try:
            return parser.parse(response_text)
        except Exception as e:
            logger.debug(f"Pydantic parsing failed: {e}")
            try:
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    json_str = json_str.replace("'", '"')
                    json_str = re.sub(r',\s*}', '}', json_str)
                    json_str = re.sub(r',\s*]', ']', json_str)
                    return json.loads(json_str)
            except Exception:
                pass
            
            return fallback_data if fallback_data else {"result": response_text, "success": False}
    
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
            "is_nullable": bool(column_data.isna().any()),
            "suggested_index": False
        }
    
    def save_analysis(self, analysis: Dict[str, Any]):
        """Save analysis results to vector database"""
        try:
            table_name = analysis['table_name']
            metadata = analysis['metadata']
            
            # Create semantic document for table
            table_doc = f"""
Table: {table_name}
Description: {metadata.get('description', '')}
Category: {metadata.get('category', 'unknown')}
Business Context: {metadata.get('business_context', '')}
Primary Key: {metadata.get('suggested_primary_key', 'None')}
Data Quality: {', '.join(metadata.get('data_quality_notes', []))}
Row Count: {analysis.get('row_count', 0)}
Column Count: {len(analysis['column_analyses'])}
"""
            
            # Get embedding
            table_embedding = self._get_embedding(table_doc)
            
            # Store in table collection
            self.table_collection.upsert(
                ids=[f"table_{table_name}"],
                documents=[table_doc],
                embeddings=[table_embedding],
                metadatas=[{
                    "table_name": table_name,
                    "description": metadata.get('description', ''),
                    "category": metadata.get('category', 'unknown'),
                    "business_context": metadata.get('business_context', ''),
                    "suggested_primary_key": metadata.get('suggested_primary_key', ''),
                    "data_quality_notes": json.dumps(metadata.get('data_quality_notes', [])),
                    "row_count": analysis.get('row_count', 0),
                    "column_count": len(analysis['column_analyses'])
                }]
            )
            
            # Store column metadata
            column_ids = []
            column_docs = []
            column_embeddings = []
            column_metadatas = []
            
            for col_analysis in analysis['column_analyses']:
                col_name = col_analysis.get('column_name', '')
                col_id = f"column_{table_name}_{col_name}"
                
                col_doc = f"""
Table: {table_name}
Column: {col_name}
Type: {col_analysis.get('sql_type', 'TEXT')} ({col_analysis.get('python_type', 'str')})
Description: {col_analysis.get('description', '')}
Business Meaning: {col_analysis.get('business_meaning', '')}
Constraints: {', '.join(col_analysis.get('constraints', []))}
Nullable: {col_analysis.get('is_nullable', True)}
Unique Values: {col_analysis.get('unique_count', 0)}
Null Count: {col_analysis.get('null_count', 0)}
"""
                
                col_embedding = self._get_embedding(col_doc)
                
                column_ids.append(col_id)
                column_docs.append(col_doc)
                column_embeddings.append(col_embedding)
                column_metadatas.append({
                    "table_name": table_name,
                    "column_name": col_name,
                    "sql_type": col_analysis.get('sql_type', 'TEXT'),
                    "python_type": col_analysis.get('python_type', 'str'),
                    "description": col_analysis.get('description', ''),
                    "business_meaning": col_analysis.get('business_meaning', ''),
                    "constraints": json.dumps(col_analysis.get('constraints', [])),
                    "is_nullable": str(col_analysis.get('is_nullable', True)),
                    "suggested_index": str(col_analysis.get('suggested_index', False)),
                    "unique_count": col_analysis.get('unique_count', 0),
                    "null_count": col_analysis.get('null_count', 0)
                })
            
            if column_ids:
                self.column_collection.upsert(
                    ids=column_ids,
                    documents=column_docs,
                    embeddings=column_embeddings,
                    metadatas=column_metadatas
                )
            
            logger.info(f"💾 Saved analysis for table: {table_name} to vector database")
            
        except Exception as e:
            logger.error(f"Failed to save analysis: {e}")
            raise
    
    def analyze_all_tables(self):
        """Analyze all tables in the source database"""
        tables = self.get_table_names()
        logger.info(f"\n📊 Found {len(tables)} table(s) to analyze: {tables}\n")
        
        for i, table_name in enumerate(tables, 1):
            try:
                logger.info(f"[{i}/{len(tables)}] Processing: {table_name}")
                analysis = self.analyze_table(table_name)
                self.save_analysis(analysis)
                logger.info(f"✅ Successfully analyzed and saved: {table_name}\n")
            except Exception as e:
                logger.error(f"❌ Failed to analyze {table_name}: {e}\n")
        
        logger.info("🎉 Analysis complete!")
        self.print_summary()
    
    def print_summary(self):
        """Print summary of analyzed data"""
        table_count = self.table_collection.count()
        column_count = self.column_collection.count()
        
        print("\n" + "="*80)
        print("📊 ANALYSIS SUMMARY")
        print("="*80)
        print(f"Tables Analyzed: {table_count}")
        print(f"Total Columns: {column_count}")
        print(f"Vector Database: {self.vector_db_path}")
        print("="*80 + "\n")
    
    def search_tables(self, query: str, n_results: int = 5):
        """Search tables using semantic similarity"""
        query_embedding = self._get_embedding(query)
        results = self.table_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results
    
    def search_columns(self, query: str, n_results: int = 10):
        """Search columns using semantic similarity"""
        query_embedding = self._get_embedding(query)
        results = self.column_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Analyze existing SQLite database tables and save metadata to vector database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s analysis.db
  %(prog)s analysis.db --vector-db ./chroma_db_new
  %(prog)s analysis.db --model qwen2.5:7b --embedding-model nomic-embed-text
  %(prog)s analysis.db --ollama-url http://localhost:11434
        """
    )
    
    parser.add_argument('source_db', help='Path to source database (e.g., analysis.db)')
    parser.add_argument('--vector-db', default='./chroma_db_768dim', help='Path to vector database (default: ./chroma_db_768dim)')
    parser.add_argument('--model', default='qwen2.5:7b', help='Ollama model to use (default: qwen2.5:7b)')
    parser.add_argument('--embedding-model', default='nomic-embed-text', help='Ollama embedding model - nomic-embed-text (768-dim) or mxbai-embed-large (1024-dim) (default: nomic-embed-text)')
    parser.add_argument('--ollama-url', default='http://localhost:11434', help='Ollama base URL (default: http://localhost:11434)')
    parser.add_argument('--temperature', type=float, default=0.1, help='LLM temperature (default: 0.1)')
    parser.add_argument('--chunk-size', type=int, default=10000, help='Number of rows to process at once for large tables (default: 10000)')
    parser.add_argument('--sample-size', type=int, default=1000, help='Number of rows to sample for analysis (default: 1000)')
    
    args = parser.parse_args()
    
    # Check if source database exists
    if not os.path.exists(args.source_db):
        print(f"❌ Error: Source database not found: {args.source_db}")
        return
    
    print("\n" + "="*80)
    print("🔍 DATABASE ANALYZER (Vector DB Edition)")
    print("="*80)
    print(f"Source Database: {args.source_db}")
    print(f"Vector Database: {args.vector_db}")
    print(f"LLM Model: {args.model}")
    print(f"Embedding Model: {args.embedding_model}")
    print(f"Ollama URL: {args.ollama_url}")
    print("="*80 + "\n")
    
    try:
        analyzer = ExistingDatabaseAnalyzer(
            source_db_path=args.source_db,
            vector_db_path=args.vector_db,
            llm_model=args.model,
            embedding_model=args.embedding_model,
            ollama_base_url=args.ollama_url,
            temperature=args.temperature,
            chunk_size=args.chunk_size,
            sample_size=args.sample_size
        )
        
        analyzer.analyze_all_tables()
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
