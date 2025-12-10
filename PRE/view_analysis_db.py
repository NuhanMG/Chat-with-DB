#!/usr/bin/env python3
"""
View contents of analysis.db (your actual data database)
"""
import sqlite3
import argparse
import os
import pandas as pd


def view_tables_list(db_path: str):
    """Display list of all tables in the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        
        if not tables:
            print("📋 No tables found in database.")
            return []
        
        table_info = []
        for table in tables:
            table_name = table[0]
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            # Get column count
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            col_count = len(columns)
            
            table_info.append([table_name, row_count, col_count])
        
        # Create DataFrame
        df = pd.DataFrame(table_info, columns=['Table Name', 'Rows', 'Columns'])
        
        print("\n" + "="*80)
        print("📊 TABLES IN DATABASE")
        print("="*80)
        print(df.to_string(index=False))
        print(f"\nTotal Tables: {len(tables)}")
        print("="*80 + "\n")
        
        return [t[0] for t in tables]
        
    except sqlite3.Error as e:
        print(f"❌ Error reading database: {e}")
        return []
    finally:
        conn.close()


def view_table_schema(db_path: str, table_name: str):
    """Display schema (structure) of a specific table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        if not columns:
            print(f"❌ Table '{table_name}' not found or has no columns.")
            return
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Create DataFrame
        schema_data = []
        for col in columns:
            schema_data.append([
                col[1],  # name
                col[2],  # type
                '✗' if col[3] == 0 else '✓',  # not null
                col[4],  # default value
                '✓' if col[5] == 1 else '✗'   # primary key
            ])
        
        df = pd.DataFrame(schema_data, columns=['Column Name', 'Type', 'Not Null', 'Default', 'Primary Key'])
        
        print("\n" + "="*100)
        print(f"📋 TABLE SCHEMA: {table_name}")
        print("="*100)
        print(f"Total Rows: {row_count:,}")
        print(f"Total Columns: {len(columns)}")
        print("-"*100)
        print(df.to_string(index=False))
        print("="*100 + "\n")
        
    except sqlite3.Error as e:
        print(f"❌ Error reading table schema: {e}")
    finally:
        conn.close()


def view_table_sample(db_path: str, table_name: str, limit: int = 10):
    """Display sample data from a table"""
    conn = sqlite3.connect(db_path)
    
    try:
        # Get sample data using pandas
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print(f"📋 Table '{table_name}' is empty.")
            return
        
        print("\n" + "="*120)
        print(f"📊 SAMPLE DATA: {table_name} (First {limit} rows)")
        print("="*120)
        
        # Set display options for better formatting
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 50)
        
        print(df.to_string(index=True))
        print("="*120 + "\n")
        
    except sqlite3.Error as e:
        print(f"❌ Error reading table data: {e}")
    except pd.io.sql.DatabaseError as e:
        print(f"❌ Error reading table data: {e}")
    finally:
        conn.close()


def view_table_stats(db_path: str, table_name: str):
    """Display statistics for numeric and text columns"""
    conn = sqlite3.connect(db_path)
    
    try:
        # Read entire table into pandas
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        
        if df.empty:
            print(f"📋 Table '{table_name}' is empty.")
            return
        
        print("\n" + "="*120)
        print(f"📈 COLUMN STATISTICS: {table_name}")
        print("="*120)
        
        # Numeric columns statistics
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_cols) > 0:
            print("\n🔢 Numeric Columns:")
            print("-"*120)
            stats = df[numeric_cols].describe()
            print(stats.to_string())
        
        # Text columns statistics
        text_cols = df.select_dtypes(include=['object']).columns
        if len(text_cols) > 0:
            print("\n📝 Text Columns:")
            print("-"*120)
            for col in text_cols:
                unique_count = df[col].nunique()
                null_count = df[col].isnull().sum()
                most_common = df[col].value_counts().head(1)
                
                print(f"\n  Column: {col}")
                print(f"    Unique Values: {unique_count}")
                print(f"    Null Values: {null_count}")
                if not most_common.empty:
                    print(f"    Most Common: {most_common.index[0]} (count: {most_common.values[0]})")
        
        # DateTime columns
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        if len(datetime_cols) > 0:
            print("\n📅 DateTime Columns:")
            print("-"*120)
            for col in datetime_cols:
                print(f"\n  Column: {col}")
                print(f"    Min Date: {df[col].min()}")
                print(f"    Max Date: {df[col].max()}")
                print(f"    Null Count: {df[col].isnull().sum()}")
        
        print("\n" + "="*120 + "\n")
        
    except sqlite3.Error as e:
        print(f"❌ Error reading table data: {e}")
    except pd.io.sql.DatabaseError as e:
        print(f"❌ Error reading table data: {e}")
    finally:
        conn.close()


def view_database_summary(db_path: str):
    """Display overall database summary"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        
        if not tables:
            print("📋 No tables found in database.")
            return
        
        total_rows = 0
        total_columns = 0
        table_info = []
        
        for table in tables:
            table_name = table[0]
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            total_rows += row_count
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            col_count = len(columns)
            total_columns += col_count
            
            # Get column names
            col_names = [col[1] for col in columns]
            
            table_info.append([
                table_name,
                row_count,
                col_count,
                ', '.join(col_names[:3]) + ('...' if len(col_names) > 3 else '')
            ])
        
        # Create DataFrame
        df = pd.DataFrame(table_info, columns=['Table Name', 'Rows', 'Columns', 'Sample Columns'])
        
        print("\n" + "="*120)
        print("📊 DATABASE SUMMARY")
        print("="*120)
        print(f"Database: {db_path}")
        print(f"Total Tables: {len(tables)}")
        print(f"Total Rows (all tables): {total_rows:,}")
        print(f"Total Columns (all tables): {total_columns}")
        print("\n" + "-"*120)
        print("Tables Overview:")
        print("-"*120)
        print(df.to_string(index=False))
        print("="*120 + "\n")
        
    except sqlite3.Error as e:
        print(f"❌ Error reading database: {e}")
    finally:
        conn.close()


def view_entire_schema(db_path: str):
    """Display schema and sample data for ALL tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        
        if not tables:
            print("📋 No tables found in database.")
            return
            
        print("\n" + "="*120)
        print(f"📚 FULL DATABASE SCHEMA REPORT: {db_path}")
        print("="*120)
        
        for i, table in enumerate(tables, 1):
            table_name = table[0]
            print(f"\nTable {i}/{len(tables)}: {table_name}")
            view_table_schema(db_path, table_name)
            view_table_sample(db_path, table_name, limit=3)
            
    except sqlite3.Error as e:
        print(f"❌ Error reading database: {e}")
    finally:
        conn.close()


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="View contents of analysis.db (your data database)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View database summary
  %(prog)s analysis.db
  
  # View ENTIRE database schema (all tables)
  %(prog)s analysis.db --full-schema

  # List all tables
  %(prog)s analysis.db --list
  
  # View table schema/structure
  %(prog)s analysis.db --schema --table ecom
  
  # View sample data (first 10 rows)
  %(prog)s analysis.db --sample --table ecom
  
  # View sample data (first 20 rows)
  %(prog)s analysis.db --sample --table ecom --limit 20
  
  # View column statistics
  %(prog)s analysis.db --stats --table ecom
  
  # View everything for a table
  %(prog)s analysis.db --all --table ecom
        """
    )
    
    parser.add_argument('database', help='Path to analysis database (e.g., analysis.db)')
    parser.add_argument('--list', action='store_true', help='List all tables')
    parser.add_argument('--schema', action='store_true', help='Show table schema/structure')
    parser.add_argument('--sample', action='store_true', help='Show sample data')
    parser.add_argument('--stats', action='store_true', help='Show column statistics')
    parser.add_argument('--table', type=str, help='Specify table name')
    parser.add_argument('--limit', type=int, default=10, help='Number of sample rows (default: 10)')
    parser.add_argument('--all', action='store_true', help='Show all information for a table')
    parser.add_argument('--full-schema', action='store_true', help='Show schema and sample for ALL tables')
    
    args = parser.parse_args()
    
    # Check if database exists
    if not os.path.exists(args.database):
        print(f"❌ Error: Database not found: {args.database}")
        return
    
    # Show full schema for all tables
    if args.full_schema:
        view_entire_schema(args.database)
        return

    # Show all info for a table
    if args.all:
        if not args.table:
            print("❌ Error: --all requires --table <table_name>")
            return
        view_table_schema(args.database, args.table)
        view_table_sample(args.database, args.table, args.limit)
        view_table_stats(args.database, args.table)
        return
    
    # Default: show summary if no options specified
    if not (args.list or args.schema or args.sample or args.stats):
        view_database_summary(args.database)
        return
    
    # List tables
    if args.list:
        view_tables_list(args.database)
    
    # Show schema
    if args.schema:
        if not args.table:
            print("❌ Error: --schema requires --table <table_name>")
            return
        view_table_schema(args.database, args.table)
    
    # Show sample data
    if args.sample:
        if not args.table:
            print("❌ Error: --sample requires --table <table_name>")
            return
        view_table_sample(args.database, args.table, args.limit)
    
    # Show statistics
    if args.stats:
        if not args.table:
            print("❌ Error: --stats requires --table <table_name>")
            return
        view_table_stats(args.database, args.table)


if __name__ == "__main__":
    main()
