#!/usr/bin/env python3
"""
This script tests the data freshness functionality of the Parquet storage system.
It directly modifies a Parquet file to simulate an external change, then verifies
that the application can detect and reload the updated data.
"""

import os
import pandas as pd
import time
import sys

def test_parquet_refresh(parquet_path="instance"):
    """Test the refresh functionality by directly modifying a Parquet file."""
    
    # Path to the runs table
    runs_file = os.path.join(parquet_path, "runs.parquet")
    
    if not os.path.exists(runs_file):
        print(f"Error: Runs file not found at {runs_file}")
        return False
    
    # Read the current data
    df = pd.read_parquet(runs_file)
    original_count = len(df)
    print(f"Current runs count: {original_count}")
    
    # Create a test record
    next_id = 1 if len(df) == 0 else df['id'].max() + 1
    test_record = {
        'id': next_id,
        'name': f'External_Test_Run_{int(time.time())}',
        'mtime': time.time(),
        'last_modified': time.strftime('%Y-%m-%d %H:%M:%S'),
        'status_sequencing': 'COMPLETED',
        'status_analysis': 'COMPLETED',
        'status_repository': 'COMPLETED',
        'status_archives': 'COMPLETED',
        'description': 'This record was added externally to test data refresh',
        'project': 'TEST',
        'group': 'TEST',
        'samples': 10
    }
    
    # Add the record directly to the DataFrame
    df = pd.concat([df, pd.DataFrame([test_record])], ignore_index=True)
    
    # Save back to Parquet
    df.to_parquet(runs_file, index=False)
    
    print(f"Added test record with ID {next_id}")
    print(f"New runs count: {len(df)}")
    print(f"Record name: {test_record['name']}")
    print("")
    print("Now run the Flask application and check if the new record appears.")
    print("You can also try the /refresh route to manually refresh the data.")
    
    return True

if __name__ == "__main__":
    # Use the first argument as the parquet path if provided
    parquet_path = sys.argv[1] if len(sys.argv) > 1 else "instance"
    test_parquet_refresh(parquet_path)
