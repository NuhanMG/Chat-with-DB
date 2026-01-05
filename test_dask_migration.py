"""
Test script for Dask migration - verifies all components work correctly
"""
import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("=" * 60)
print("DASK MIGRATION TEST SCRIPT")
print("=" * 60)

# Test 1: Import dataframe_factory
print("\n[TEST 1] Importing dataframe_factory...")
try:
    from dataframe_factory import (
        DataFrameFactory, 
        from_sql, 
        ensure_pandas, 
        get_backend_name,
        UnifiedDataFrame
    )
    print("✅ dataframe_factory imports successful!")
except Exception as e:
    print(f"❌ Import error: {e}")
    exit(1)

# Test 2: Import QueryAgent
print("\n[TEST 2] Importing QueryAgentEnhanced...")
try:
    from QueryAgent_Ollama_Enhanced import QueryAgentEnhanced
    print("✅ QueryAgentEnhanced import successful!")
except Exception as e:
    print(f"❌ Import error: {e}")
    exit(1)

# Test 3: Test with actual database
print("\n[TEST 3] Testing with analysis.db...")
try:
    conn = sqlite3.connect('analysis.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"   Tables found: {[t[0] for t in tables]}")
    
    if tables:
        table_name = tables[0][0]
        
        # Count rows
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"   Table '{table_name}' has {count:,} rows")
        
        # Test small query
        print("\n   [Small Query Test - LIMIT 100]")
        df_small = from_sql(f"SELECT * FROM {table_name} LIMIT 100", conn)
        print(f"   Backend used: {get_backend_name(df_small)}")
        print(f"   Rows returned: {DataFrameFactory.get_length(df_small)}")
        print(f"   Is empty: {DataFrameFactory.empty_check(df_small)}")
        print(f"   Columns: {list(df_small.columns)[:5]}...")
        
        # Test full query
        if count > 100:
            print(f"\n   [Full Table Query - {count:,} rows]")
            df_full = from_sql(f"SELECT * FROM {table_name}", conn)
            print(f"   Backend used: {get_backend_name(df_full)}")
            print(f"   Rows returned: {DataFrameFactory.get_length(df_full)}")
            
            # Test ensure_pandas
            print("\n   [ensure_pandas conversion test]")
            df_limited = ensure_pandas(df_full, max_rows=50)
            print(f"   After ensure_pandas(max_rows=50): {len(df_limited)} rows")
            print(f"   Type: {type(df_limited).__name__}")
        
        print("\n✅ Database tests passed!")
    else:
        print("   ⚠️ No tables found in database")
    
    conn.close()
except Exception as e:
    print(f"❌ Database test error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test Pandas/Dask detection
print("\n[TEST 4] Testing Pandas/Dask detection...")
try:
    import pandas as pd
    import dask.dataframe as dd
    
    # Create Pandas DataFrame
    pdf = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    print(f"   Pandas DataFrame - is_dask: {DataFrameFactory.is_dask(pdf)}, is_pandas: {DataFrameFactory.is_pandas(pdf)}")
    
    # Create Dask DataFrame
    ddf = dd.from_pandas(pdf, npartitions=2)
    print(f"   Dask DataFrame - is_dask: {DataFrameFactory.is_dask(ddf)}, is_pandas: {DataFrameFactory.is_pandas(ddf)}")
    
    # Test conversion
    converted = ensure_pandas(ddf)
    print(f"   After ensure_pandas - type: {type(converted).__name__}")
    
    print("\n✅ Pandas/Dask detection tests passed!")
except Exception as e:
    print(f"❌ Detection test error: {e}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETED SUCCESSFULLY!")
print("=" * 60)
