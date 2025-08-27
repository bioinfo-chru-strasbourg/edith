import os
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import datetime
import sys
from typing import Dict, List, Any, Optional, Union, Callable
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ParquetStore")

class ParquetStore:
    """
    Class to handle Parquet storage for EDITH.
    This replaces SQLAlchemy with direct Parquet file storage using PyArrow for efficient queries.
    """
    
    def __init__(self, base_path: str = "instance", cache_ttl: int = 30):
        """
        Initialize the ParquetStore.
        
        Args:
            base_path: Directory where parquet files will be stored
            cache_ttl: Cache time-to-live in seconds (0 to disable caching)
        """
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        self.cache_ttl = cache_ttl
        self.tables_meta = {}  # Stores metadata about tables
        self.query_cache = {}  # Cache for query results
        self.file_mtimes = {}  # Track file modification times
        self._initialize_tables()
    
    def _get_file_path(self, table_name: str) -> str:
        """Get the path to a specific table's parquet file."""
        return os.path.join(self.base_path, f"{table_name}.parquet")
    
    def _get_table_metadata(self, table_name: str) -> Dict[str, Any]:
        """
        Get metadata about a table (schema, num_rows, etc.) without loading the data
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with table metadata or empty dict if file doesn't exist
        """
        file_path = self._get_file_path(table_name)
        
        if not os.path.exists(file_path):
            return {}
            
        try:
            # Get file metadata without loading data
            parquet_file = pq.ParquetFile(file_path)
            mtime = os.path.getmtime(file_path)
            
            return {
                'schema': parquet_file.schema,
                'num_rows': parquet_file.metadata.num_rows,
                'num_row_groups': parquet_file.metadata.num_row_groups,
                'mtime': mtime,
                'file_path': file_path
            }
        except Exception as e:
            logger.error(f"Error getting metadata for {table_name}: {str(e)}")
            return {}
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if a cached query result is still valid.
        
        Args:
            cache_key: Key to check in the cache
            
        Returns:
            True if cache is valid, False otherwise
        """
        if self.cache_ttl <= 0 or cache_key not in self.query_cache:
            return False
            
        cache_entry = self.query_cache[cache_key]
        table_name = cache_entry.get('table_name')
        
        if not table_name:
            return False
            
        # Check if file has been modified since cache was created
        current_mtime = os.path.getmtime(self._get_file_path(table_name))
        cache_mtime = cache_entry.get('mtime', 0)
        
        # Check time-to-live
        cache_time = cache_entry.get('time', 0)
        current_time = time.time()
        
        # Cache is valid if the file hasn't been modified and TTL hasn't expired
        return (current_mtime <= cache_mtime) and (current_time - cache_time <= self.cache_ttl)
    
    def _initialize_tables(self):
        """Initialize table metadata and create default tables if they don't exist."""
        # Define default tables
        default_tables = {
            'users': pd.DataFrame({
                'id': [],
                'username': [], 
                'password': [], 
                'email': [], 
                'theme': [], 
                'is_admin': [], 
                'groups': []
            }),
            'runs': pd.DataFrame({
                'id': [],
                'name': [],
                'mtime': [],
                'last_modified': [],
                'input_path': [],
                'input_mtime': [],
                'input_last_modified': [],
                'input_samplesheet': [],
                'input_rtacomplete': [],
                'repository_path': [],
                'repository_mtime': [],
                'repository_last_modified': [],
                'repository_starkcomplete': [],
                'archives_path': [],
                'archives_mtime': [],
                'archives_last_modified': [],
                'archives_starkcomplete': [],
                'project': [],
                'group': [],
                'description': [],
                'status_sequencing': [],
                'status_analysis': [],
                'status_repository': [],
                'status_archives': [],
                'samples': []
            })
        }
        
        # Get metadata for existing tables or create defaults
        for table_name, default_df in default_tables.items():
            file_path = self._get_file_path(table_name)
            
            if os.path.exists(file_path):
                # Just get metadata, don't load the entire table
                self.tables_meta[table_name] = self._get_table_metadata(table_name)
            else:
                # Create default table if it doesn't exist
                default_df.to_parquet(file_path, index=False)
                self.tables_meta[table_name] = self._get_table_metadata(table_name)
    
    def invalidate_cache(self, table_name: Optional[str] = None):
        """
        Invalidate the query cache for a specific table or all tables.
        
        Args:
            table_name: Name of the table to invalidate cache for, or None for all tables
        """
        if table_name:
            # Remove specific table entries
            keys_to_remove = [k for k, v in self.query_cache.items() 
                             if v.get('table_name') == table_name]
            for key in keys_to_remove:
                self.query_cache.pop(key, None)
                
            # Update metadata
            self.tables_meta[table_name] = self._get_table_metadata(table_name)
        else:
            # Clear entire cache
            self.query_cache = {}
            
            # Update all metadata
            for table_name in self.tables_meta.keys():
                self.tables_meta[table_name] = self._get_table_metadata(table_name)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the query cache.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            'cache_size': len(self.query_cache),
            'cache_ttl': self.cache_ttl,
            'tables_tracked': len(self.tables_meta),
            'entries_by_table': {},
            'memory_usage': 0  # Approximate
        }
        
        # Count entries per table
        for entry in self.query_cache.values():
            table = entry.get('table_name', 'unknown')
            if table not in stats['entries_by_table']:
                stats['entries_by_table'][table] = 0
            stats['entries_by_table'][table] += 1
            
            # Rough estimate of memory usage
            if 'result' in entry:
                result = entry['result']
                if hasattr(result, 'memory_usage'):
                    # For DataFrames
                    stats['memory_usage'] += result.memory_usage(deep=True).sum()
                elif isinstance(result, list):
                    # For lists of dictionaries
                    stats['memory_usage'] += sum(sys.getsizeof(item) for item in result)
        
        return stats
                
        return result
    
    def _save_dataframe(self, table_name: str, df: pd.DataFrame):
        """
        Save a DataFrame to a Parquet file.
        
        Args:
            table_name: Name of the table to save
            df: DataFrame to save
        """
        file_path = self._get_file_path(table_name)
        df.to_parquet(file_path, index=False)
        
        # Update metadata after save
        self.tables_meta[table_name] = self._get_table_metadata(table_name)
        
        # Invalidate cache for this table
        self.invalidate_cache(table_name)
    
    def add_record(self, table_name: str, record: Dict[str, Any]) -> int:
        """
        Add a new record to a table.
        
        Args:
            table_name: Name of the table
            record: Record to add as a dictionary
            
        Returns:
            ID of the newly added record
        """
        file_path = self._get_file_path(table_name)
        if not os.path.exists(file_path):
            raise ValueError(f"Table {table_name} does not exist")
            
        # Load the table efficiently
        df = pd.read_parquet(file_path)
        
        # Generate a new ID if not provided
        if 'id' not in record:
            next_id = 1 if len(df) == 0 else df['id'].max() + 1
            record['id'] = next_id
        
        # Append the new record
        df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
        
        # Save the updated DataFrame
        self._save_dataframe(table_name, df)
        
        return record['id']
    
    def get_record(self, table_name: str, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a record by ID.
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to retrieve
            
        Returns:
            Record as a dictionary or None if not found
        """
        # Generate a cache key for this query
        cache_key = f"get_record:{table_name}:{record_id}"
        
        # Check if we have a valid cached result
        if self._is_cache_valid(cache_key):
            return self.query_cache[cache_key]['result']
        
        file_path = self._get_file_path(table_name)
        if not os.path.exists(file_path):
            return None
        
        try:
            # Use PyArrow to read only the necessary columns and filter efficiently
            parquet_file = pq.ParquetFile(file_path)
            
            # Use predicate pushdown to filter at the file level for better performance
            # First read just the id column to find matching row(s)
            ids_table = parquet_file.read(columns=['id'])
            ids = ids_table.column('id').to_numpy()
            
            # Find the matching row index
            match_indices = [i for i, val in enumerate(ids) if val == record_id]
            
            if not match_indices:
                return None
            
            # Read just the matching row with all columns
            df = pd.read_parquet(file_path, filters=[('id', '=', record_id)])
            
            if len(df) == 0:
                return None
                
            result = df.iloc[0].to_dict()
            
            # Cache the result
            if self.cache_ttl > 0:
                self.query_cache[cache_key] = {
                    'result': result,
                    'table_name': table_name,
                    'mtime': os.path.getmtime(file_path),
                    'time': time.time()
                }
                
            return result
            
        except Exception as e:
            logger.error(f"Error getting record {record_id} from {table_name}: {str(e)}")
            return None
    
    def count_records(self, table_name: str, filter_dict: Dict[str, Any] = None) -> int:
        """
        Count records with optional filtering, without loading the entire dataset.
        
        Args:
            table_name: Name of the table
            filter_dict: Dictionary of field=value to filter by
            
        Returns:
            Count of matching records
        """
        # Generate a unique cache key for this query
        filter_str = str(sorted(filter_dict.items())) if filter_dict else "None"
        cache_key = f"count_records:{table_name}:{filter_str}"
        
        # Check if we have a valid cached result
        if self._is_cache_valid(cache_key):
            return self.query_cache[cache_key]['result']
        
        file_path = self._get_file_path(table_name)
        if not os.path.exists(file_path):
            return 0
        
        try:
            # Construct filters for PyArrow/Parquet's predicate pushdown
            filters = None
            if filter_dict:
                filters = []
                for field, value in filter_dict.items():
                    filters.append((field, '=', value))
            
            # Use PyArrow to efficiently count rows without loading all data
            # First open the parquet file
            parquet_file = pq.ParquetFile(file_path)
            
            if not filters:
                # If no filters, just use the metadata which is very fast
                count = parquet_file.metadata.num_rows
            else:
                # If filters, we need to do a filtered read but only get the count
                table = pq.read_table(file_path, filters=filters)
                count = len(table)
            
            # Cache the result
            if self.cache_ttl > 0:
                self.query_cache[cache_key] = {
                    'result': count,
                    'table_name': table_name,
                    'mtime': os.path.getmtime(file_path),
                    'time': time.time()
                }
                
            return count
            
        except Exception as e:
            logger.error(f"Error counting records from {table_name} with filters {filter_dict}: {str(e)}")
            return 0
    
    def get_records(self, table_name: str, filter_dict: Dict[str, Any] = None, 
                    sort_field: str = None, sort_ascending: bool = True, 
                    limit: int = None) -> List[Dict[str, Any]]:
        """
        Get records with optional filtering, sorting and limit.
        
        Args:
            table_name: Name of the table
            filter_dict: Dictionary of field=value to filter by
            sort_field: Field to sort by
            sort_ascending: Sort direction (True for ascending, False for descending)
            limit: Maximum number of records to return
            
        Returns:
            List of records as dictionaries
        """
        # Generate a unique cache key for this query
        filter_str = str(sorted(filter_dict.items())) if filter_dict else "None"
        sort_str = f"{sort_field}:{sort_ascending}" if sort_field else "None"
        limit_str = str(limit) if limit else "None"
        cache_key = f"get_records:{table_name}:{filter_str}:{sort_str}:{limit_str}"
        
        # Check if we have a valid cached result
        if self._is_cache_valid(cache_key):
            return self.query_cache[cache_key]['result']
        
        file_path = self._get_file_path(table_name)
        if not os.path.exists(file_path):
            return []
        
        try:
            # Construct filters for PyArrow/Parquet's predicate pushdown
            # This allows filtering at the Parquet level, not in Python memory
            filters = None
            if filter_dict:
                # Convert to PyArrow/Pandas filter format
                filters = []
                for field, value in filter_dict.items():
                    filters.append((field, '=', value))
            
            # Read the filtered data directly from Parquet
            df = pd.read_parquet(file_path, filters=filters)
            
            # Apply sorting if requested
            if sort_field and sort_field in df.columns:
                df = df.sort_values(by=sort_field, ascending=sort_ascending)
            
            # Apply limit if requested
            if limit is not None and limit > 0:
                df = df.head(limit)
            
            # Convert to list of dicts
            result = df.to_dict(orient='records')
            
            # Cache the result
            if self.cache_ttl > 0:
                self.query_cache[cache_key] = {
                    'result': result,
                    'table_name': table_name,
                    'mtime': os.path.getmtime(file_path),
                    'time': time.time()
                }
                
            return result
            
        except Exception as e:
            logger.error(f"Error getting records from {table_name} with filters {filter_dict}: {str(e)}")
            return []
    
    def update_record(self, table_name: str, record_id: int, update_dict: Dict[str, Any]) -> bool:
        """
        Update a record by ID.
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to update
            update_dict: Dictionary of field=value to update
            
        Returns:
            True if successful, False otherwise
        """
        file_path = self._get_file_path(table_name)
        if not os.path.exists(file_path):
            return False
        
        try:
            # Read the table
            df = pd.read_parquet(file_path)
            
            # Find the record by ID
            idx = df.index[df['id'] == record_id]
            
            if len(idx) == 0:
                return False
            
            # Update fields
            for field, value in update_dict.items():
                if field in df.columns:
                    df.at[idx[0], field] = value
            
            # Save the updated DataFrame
            self._save_dataframe(table_name, df)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating record {record_id} in {table_name}: {str(e)}")
            return False
    
    def delete_record(self, table_name: str, record_id: int) -> bool:
        """
        Delete a record by ID.
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to delete
            
        Returns:
            True if successful, False otherwise
        """
        file_path = self._get_file_path(table_name)
        if not os.path.exists(file_path):
            return False
            
        try:
            # Read the table
            df = pd.read_parquet(file_path)
            original_len = len(df)
            
            # Filter out the record with the given ID
            df = df[df['id'] != record_id]
            
            if len(df) == original_len:
                return False
                
            # Save the updated DataFrame
            self._save_dataframe(table_name, df)
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting record {record_id} from {table_name}: {str(e)}")
            return False
        
    def execute_query(self, table_name: str, query_func: Callable[[pd.DataFrame], pd.DataFrame]) -> pd.DataFrame:
        """
        Execute a query using a function that operates on a DataFrame.
        This is for complex queries that can't be expressed with filters.
        
        Args:
            table_name: Name of the table
            query_func: Function that takes a DataFrame and returns a modified DataFrame
            
        Returns:
            DataFrame with query results
        """
        # Generate a unique cache key for this query
        func_hash = str(hash(query_func.__code__.co_code))
        cache_key = f"execute_query:{table_name}:{func_hash}"
        
        # Check if we have a valid cached result
        if self._is_cache_valid(cache_key):
            return self.query_cache[cache_key]['result']
        
        file_path = self._get_file_path(table_name)
        if not os.path.exists(file_path):
            return pd.DataFrame()
        
        try:
            # Read the table
            df = pd.read_parquet(file_path)
            
            # Execute the query function
            result = query_func(df)
            
            # Cache the result
            if self.cache_ttl > 0:
                self.query_cache[cache_key] = {
                    'result': result,
                    'table_name': table_name,
                    'mtime': os.path.getmtime(file_path),
                    'time': time.time()
                }
                
            return result
            
        except Exception as e:
            logger.error(f"Error executing query on {table_name}: {str(e)}")
            return pd.DataFrame()
