import os
import shutil
import unittest
import pandas as pd
import tempfile
import hashlib
from edith.parquet_store import ParquetStore
from edith.parquet_models import ParquetModel, Users, Runs

class TestParquetModels(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory for the test data"""
        self.test_dir = tempfile.mkdtemp()
        self.store = ParquetStore(self.test_dir)
        ParquetModel.set_store(self.store)
        
    def tearDown(self):
        """Remove the temporary directory after tests"""
        shutil.rmtree(self.test_dir)
        
    def test_user_creation(self):
        """Test creating a new user"""
        user = Users()
        user.username = "testuser"
        user.password = hashlib.sha256("password123".encode("UTF-8")).hexdigest()
        user.email = "test@example.com"
        user.is_admin = False
        user.groups = "DIAG"
        
        # Save user
        self.assertTrue(user.save())
        
        # Check that user has an ID
        self.assertIsNotNone(user.id)
        
        # Check that user was saved to store
        users_df = self.store.tables['users']
        self.assertEqual(len(users_df), 1)
        
        # Verify user data in store
        saved_user = users_df.iloc[0]
        self.assertEqual(saved_user['username'], "testuser")
        self.assertEqual(saved_user['email'], "test@example.com")
        
    def test_user_retrieval(self):
        """Test retrieving a user"""
        # Create a user first
        user = Users()
        user.username = "testuser2"
        user.password = hashlib.sha256("password123".encode("UTF-8")).hexdigest()
        user.save()
        
        # Get the user ID
        user_id = user.id
        
        # Retrieve the user by ID
        retrieved_user = Users.get(user_id)
        
        # Check if it's the same user
        self.assertEqual(retrieved_user.username, "testuser2")
        
    def test_user_query(self):
        """Test querying users"""
        # Create two users
        user1 = Users()
        user1.username = "user1"
        user1.password = hashlib.sha256("password".encode("UTF-8")).hexdigest()
        user1.save()
        
        user2 = Users()
        user2.username = "user2"
        user2.password = hashlib.sha256("password".encode("UTF-8")).hexdigest()
        user2.save()
        
        # Query all users
        all_users = Users.query().all()
        self.assertEqual(len(all_users), 2)
        
        # Query specific user
        found_user = Users.query().filter_by(username="user2").first()
        self.assertIsNotNone(found_user)
        self.assertEqual(found_user.username, "user2")
        
    def test_user_update(self):
        """Test updating a user"""
        # Create a user
        user = Users()
        user.username = "updateuser"
        user.password = hashlib.sha256("password".encode("UTF-8")).hexdigest()
        user.save()
        
        # Update the user
        user.email = "new@example.com"
        user.save()
        
        # Retrieve the user again
        updated_user = Users.get(user.id)
        self.assertEqual(updated_user.email, "new@example.com")
        
    def test_user_delete(self):
        """Test deleting a user"""
        # Create a user
        user = Users()
        user.username = "deleteuser"
        user.password = hashlib.sha256("password".encode("UTF-8")).hexdigest()
        user.save()
        
        # Count users
        count_before = len(Users.query().all())
        
        # Delete the user
        user.delete()
        
        # Count users again
        count_after = len(Users.query().all())
        
        # Check if user was deleted
        self.assertEqual(count_after, count_before - 1)
        
    def test_runs_model(self):
        """Test basic operations with Runs model"""
        # Create a run
        run = Runs()
        run.name = "TEST_RUN_001"
        run.project = "EXOME"
        run.group = "DIAG"
        run.mtime = 1598918400  # August 31, 2020
        run.save()
        
        # Verify run was saved
        retrieved_run = Runs.get(run.id)
        self.assertEqual(retrieved_run.name, "TEST_RUN_001")
        self.assertEqual(retrieved_run.project, "EXOME")
        
        # Update run
        run.status_analysis = "COMPLETED"
        run.save()
        
        # Verify update
        updated_run = Runs.get(run.id)
        self.assertEqual(updated_run.status_analysis, "COMPLETED")
        
        # Query runs by group
        diag_runs = Runs.query().filter_by(group="DIAG").all()
        self.assertEqual(len(diag_runs), 1)
        
        # Delete run
        run.delete()
        
        # Verify deletion
        deleted_run = Runs.get(run.id)
        self.assertIsNone(deleted_run)
        
if __name__ == "__main__":
    unittest.main()
