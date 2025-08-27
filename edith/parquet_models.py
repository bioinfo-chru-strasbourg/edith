from typing import Dict, Any, Optional, List
from flask_login import UserMixin
import hashlib

class ParquetModel:
    """Base class for Parquet-based models"""
    _table_name = None
    _store = None  # Will be set at runtime
    
    @classmethod
    def set_store(cls, store):
        """Set the ParquetStore for all models"""
        cls._store = store
    
    @classmethod
    def query(cls):
        """Return a query object to mimic SQLAlchemy's query interface"""
        return ParquetQuery(cls)
    
    @classmethod
    def get(cls, id):
        """Get a record by ID"""
        if not cls._store:
            return None
        record = cls._store.get_record(cls._table_name, id)
        if record:
            return cls.from_dict(record)
        return None
        
    @classmethod
    def invalidate_cache(cls):
        """Invalidate the cache for this model's table"""
        if cls._store:
            cls._store.invalidate_cache(cls._table_name)
        
    @classmethod
    def from_dict(cls, data):
        """Create an instance from a dictionary"""
        instance = cls()
        for key, value in data.items():
            setattr(instance, key, value)
        return instance
    
    def to_dict(self):
        """Convert instance to dictionary for storage"""
        return {key: getattr(self, key) for key in self.__class__.__annotations__ if hasattr(self, key)}
    
    def save(self):
        """Save the instance to the store"""
        if not self._store:
            return False
            
        data = self.to_dict()
        
        if hasattr(self, 'id') and getattr(self, 'id') is not None:
            # Update existing record
            return self._store.update_record(self._table_name, self.id, data)
        else:
            # Add new record
            self.id = self._store.add_record(self._table_name, data)
            return True
    
    def delete(self):
        """Delete the instance from the store"""
        if not self._store or not hasattr(self, 'id'):
            return False
            
        return self._store.delete_record(self._table_name, self.id)
        

class ParquetQuery:
    """Class to mimic SQLAlchemy's query interface for Parquet models"""
    
    def __init__(self, model_class):
        self.model_class = model_class
        self.filters = {}
        self.sort_field = None
        self.sort_direction = None
        self.limit_count = None
    
    def filter_by(self, **kwargs):
        """Filter by keyword arguments"""
        self.filters.update(kwargs)
        return self
        
    def order_by(self, field, ascending=True):
        """Order results by a field"""
        self.sort_field = field
        self.sort_direction = ascending
        return self
        
    def limit(self, count):
        """Limit the number of results"""
        self.limit_count = count
        return self
    
    def first(self):
        """Get the first result"""
        if not self.model_class._store:
            return None
            
        # Get filtered records using optimized query
        results = self.model_class._store.get_records(
            self.model_class._table_name, 
            self.filters,
            sort_field=self.sort_field,
            sort_ascending=self.sort_direction,
            limit=1
        )
        
        if results:
            return self.model_class.from_dict(results[0])
        return None
    
    def all(self):
        """Get all results"""
        if not self.model_class._store:
            return []
            
        # Get filtered records using optimized query
        results = self.model_class._store.get_records(
            self.model_class._table_name, 
            self.filters,
            sort_field=self.sort_field,
            sort_ascending=self.sort_direction,
            limit=self.limit_count
        )
        
        return [self.model_class.from_dict(record) for record in results]
    
    def count(self):
        """Count the results"""
        if not self.model_class._store:
            return 0
            
        # For count, we don't need sorting or limits, just the count
        return self.model_class._store.count_records(self.model_class._table_name, self.filters)


class Users(UserMixin, ParquetModel):
    """User model for Parquet storage"""
    _table_name = 'users'
    
    id: int
    username: str
    password: str
    email: str = None
    theme: str = 'default'
    is_admin: bool = False
    groups: str = None
    
    def update_profile(self, infos_get: dict):
        """Update user profile"""
        if infos_get:
            password = hashlib.sha256(
                infos_get.get("password").encode("UTF-8")
            ).hexdigest()
            if password == self.password:
                infos_update = {}

                # Group
                self.groups = infos_get.get("groups")

                # Email
                if infos_get.get("email", None):
                    self.email = infos_get.get("email")
                    infos_update["email"] = self.email

                # New Password
                new_password1 = hashlib.sha256(
                    infos_get.get("new_password1").encode("UTF-8")
                ).hexdigest()
                new_password2 = hashlib.sha256(
                    infos_get.get("new_password2").encode("UTF-8")
                ).hexdigest()
                if (
                    new_password1
                    and new_password2
                    and infos_get.get("new_password1", None)
                ):
                    if new_password1 == new_password2:
                        new_password = new_password1
                        infos_update["password"] = new_password
                        self.password = new_password
                    else:
                        return {
                            "error": f"User '{self.username}' not updated (wrong new password)!"
                        }

                # Update if needed
                if infos_update:
                    # Update attributes
                    for key, value in infos_update.items():
                        setattr(self, key, value)
                    
                    # Save to store
                    self.save()
                    return {"success": f"User '{self.username}' updated!"}
                else:
                    return {"info": f"User '{self.username}' not updated (no need)!"}
            else:
                return {
                    "error": f"User '{self.username}' not updated (wrong password)!"
                }
        else:
            return {"info": f"User '{self.username}' not updated (no need)!"}


class Runs(ParquetModel):
    """Runs model for Parquet storage"""
    _table_name = 'runs'
    
    id: int
    name: str
    mtime: float = 0
    last_modified: str = None
    input_path: str = None
    input_mtime: float = 0
    input_last_modified: str = None
    input_samplesheet: str = None
    input_rtacomplete: str = None
    analysis_path: str = None
    analysis_mtime: float = 0
    analysis_last_modified: str = None
    analysis_api_json: str = None
    analysis_api_info: str = None
    repository_path: str = None
    repository_mtime: float = 0
    repository_last_modified: str = None
    repository_starkcomplete: str = None
    repository_analysislog: str = None
    archives_path: str = None
    archives_mtime: float = 0
    archives_last_modified: str = None
    archives_starkcomplete: str = None
    archives_analysislog: str = None
    project: str = None
    group: str = None
    description: str = None
    status_sequencing: str = None
    status_analysis: str = None
    status_repository: str = None
    status_archives: str = None
    samples: int = 0
