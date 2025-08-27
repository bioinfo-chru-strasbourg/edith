#!/usr/bin/env python3
"""
This script tests the PyArrow-based Parquet store for performance and memory usage.
It creates a large dataset and measures the performance of various operations.
"""

import os
import pandas as pd
import numpy as np
import time
import sys
import gc
import psutil
from edith.parquet_store import ParquetStore

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def create_large_dataset(rows=100000, output_path="instance/large_test.parquet"):
    """Create a large test dataset"""
    print(f"Creating test dataset with {rows} rows...")
    
    # Create a DataFrame with random data
    data = {
        'id': range(1, rows + 1),
        'name': [f"Run_{i}" for i in range(rows)],
        'mtime': np.random.random(rows) * 1000000000,
        'description': np.random.choice(['Test', 'Production', 'Development'], size=rows),
        'project': np.random.choice(['A', 'B', 'C', 'D', 'E'], size=rows),
        'group': np.random.choice(['Group1', 'Group2', 'Group3'], size=rows),
        'status_sequencing': np.random.choice(['COMPLETED', 'FAILED', 'IN_PROGRESS'], size=rows),
        'status_analysis': np.random.choice(['COMPLETED', 'FAILED', 'IN_PROGRESS'], size=rows),
        'status_repository': np.random.choice(['COMPLETED', 'FAILED', 'IN_PROGRESS'], size=rows),
        'status_archives': np.random.choice(['COMPLETED', 'FAILED', 'IN_PROGRESS'], size=rows),
        'samples': np.random.randint(1, 100, rows)
    }
    
    # Add some large text fields to simulate real data
    data['repository_path'] = [f"/very/long/path/to/repository/with/lots/of/subdirectories/and/files/run_{i}" * 5 for i in range(rows)]
    data['archives_path'] = [f"/even/longer/path/to/archives/with/even/more/subdirectories/and/files/for/long/term/storage/run_{i}" * 5 for i in range(rows)]
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to Parquet
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    print(f"Dataset created at {output_path}")
    print(f"File size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
    return df

def test_performance(parquet_path, table_name='large_test', file_path=None):
    """Test performance of different access methods"""
    if file_path is None:
        file_path = os.path.join(parquet_path, f"{table_name}.parquet")
    
    if not os.path.exists(file_path):
        print(f"File {file_path} not found. Creating test dataset...")
        create_large_dataset(output_path=file_path)
    
    # Initialize store
    store = ParquetStore(parquet_path, cache_ttl=30)
    
    print("\n=== Memory Usage ===")
    print(f"Initial memory usage: {get_memory_usage():.2f} MB")
    
    # Test 1: Get single record by ID
    print("\n=== Test 1: Get Single Record by ID ===")
    start_time = time.time()
    record = store.get_record(table_name, 50000)
    elapsed = time.time() - start_time
    print(f"Time to get single record by ID: {elapsed:.4f} seconds")
    print(f"Memory usage: {get_memory_usage():.2f} MB")
    
    # Test 2: Get filtered records (small result set)
    print("\n=== Test 2: Get Filtered Records (Small Result) ===")
    start_time = time.time()
    records = store.get_records(table_name, {'project': 'A', 'group': 'Group1'})
    elapsed = time.time() - start_time
    print(f"Time to get filtered records (small): {elapsed:.4f} seconds")
    print(f"Result count: {len(records)}")
    print(f"Memory usage: {get_memory_usage():.2f} MB")
    
    # Test 3: Get all records
    print("\n=== Test 3: Get All Records ===")
    start_time = time.time()
    all_records = store.get_records(table_name, {})
    elapsed = time.time() - start_time
    print(f"Time to get all records: {elapsed:.4f} seconds")
    print(f"Result count: {len(all_records)}")
    print(f"Memory usage: {get_memory_usage():.2f} MB")
    
    # Test 4: Test caching
    print("\n=== Test 4: Test Caching ===")
    # Clear memory
    all_records = None
    records = None
    gc.collect()
    print(f"Memory after gc: {get_memory_usage():.2f} MB")
    
    # First query (should be slow)
    start_time = time.time()
    records = store.get_records(table_name, {'project': 'B', 'group': 'Group2'})
    elapsed1 = time.time() - start_time
    print(f"First query time: {elapsed1:.4f} seconds")
    
    # Second query (should be faster due to caching)
    start_time = time.time()
    records = store.get_records(table_name, {'project': 'B', 'group': 'Group2'})
    elapsed2 = time.time() - start_time
    print(f"Second query time: {elapsed2:.4f} seconds")
    print(f"Cache speedup: {elapsed1/elapsed2:.2f}x")
    print(f"Memory usage: {get_memory_usage():.2f} MB")
    
    # Test 5: Cache invalidation
    print("\n=== Test 5: Cache Invalidation ===")
    store.invalidate_cache(table_name)
    start_time = time.time()
    records = store.get_records(table_name, {'project': 'B', 'group': 'Group2'})
    elapsed3 = time.time() - start_time
    print(f"Query after invalidation: {elapsed3:.4f} seconds")
    print(f"Memory usage: {get_memory_usage():.2f} MB")
    
    # Test 6: Cache statistics
    print("\n=== Test 6: Cache Statistics ===")
    stats = store.get_cache_stats()
    print(f"Cache entries: {stats['cache_size']}")
    print(f"Tables tracked: {stats['tables_tracked']}")
    print(f"Entries by table: {stats['entries_by_table']}")
    print(f"Approx memory usage: {stats['memory_usage'] / 1024 / 1024:.2f} MB")
    
    print("\n=== Tests Complete ===")

if __name__ == "__main__":
    # Use the first argument as the parquet path if provided
    parquet_path = sys.argv[1] if len(sys.argv) > 1 else "instance"
    test_performance(parquet_path)
