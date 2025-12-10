#!/usr/bin/env python3
"""View contents of metadata from vector database"""
import argparse
import os
import pandas as pd
import json
import chromadb
from chromadb.config import Settings

def connect_to_vector_db(db_path):
    try:
        if not os.path.exists(db_path):
            print(f"Error: Database path does not exist: {db_path}")
            return None, None, None
            
        client = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
        tc = client.get_collection("table_metadata")
        cc = client.get_collection("column_metadata")
        return client, tc, cc
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None, None, None

def view_summary(db_path):
    _, tc, cc = connect_to_vector_db(db_path)
    if tc and cc:
        print(f"\n{'='*60}")
        print(f"Database: {db_path}")
        print(f"{'='*60}")
        print(f"\nTables: {tc.count()}, Columns: {cc.count()}\n")
        
        # Get all table metadata
        print(f"\n{'='*60}")
        print("TABLE METADATA:")
        print(f"{'='*60}")
        table_data = tc.get()
        for i, (tid, doc, meta) in enumerate(zip(table_data['ids'], table_data['documents'], table_data['metadatas'])):
            print(f"\n[Table {i+1}]")
            print(f"ID: {tid}")
            print(f"Document: {doc}")
            print(f"Metadata: {json.dumps(meta, indent=2)}")
        
        # Get all column metadata
        print(f"\n\n{'='*60}")
        print("COLUMN METADATA:")
        print(f"{'='*60}")
        column_data = cc.get()
        for i, (cid, doc, meta) in enumerate(zip(column_data['ids'], column_data['documents'], column_data['metadatas'])):
            print(f"\n[Column {i+1}]")
            print(f"ID: {cid}")
            print(f"Document: {doc}")
            print(f"Metadata: {json.dumps(meta, indent=2)}")
    else:
        print("Failed to retrieve collections.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        view_summary(sys.argv[1])
    else:
        print("Usage: python view_metadata_simple.py <path_to_vector_db>")
        print("Example: python view_metadata_simple.py ./chroma_db_new")