from dotenv import dotenv_values
import pymongo
import pytest
import os
from pymongo.errors import WriteError, DuplicateKeyError
from bson import ObjectId
from src.util.dao import DAO
from src.util.validators import getValidator
import time



"""
Test suite for the DAO class.
Tests CRUD operations against a real MongoDB instance.
"""


# @pytest.fixture(scope="class")
# def mongo_client():
#     """Create a MongoDB client for testing"""
#     # Using the environment URL or a fallback for testing
#     config = dotenv_values(".env")
#     mongo_url = config.get("MONGO_URL", "mongodb://root:root@localhost:27017/?authSource=admin")
    
#     # Allow some time for connection retries in containerized environments
#     max_tries = 5
#     current_try = 0
    
#     while current_try < max_tries:
#         try:
#             client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
#             # Validate connection
#             client.admin.command('ping')
#             print(f"Successfully connected to MongoDB at {mongo_url}")
#             return client
#         except Exception as e:
#             current_try += 1
#             if current_try >= max_tries:
#                 pytest.skip(f"Could not connect to MongoDB: {e}")
#             print(f"Connection attempt {current_try} failed: {e}. Retrying...")
#             time.sleep(2)

@pytest.fixture(scope="function")
def dao():
    """Create a DAO instance and prepare the test collection"""
    

    MONGO_URL = "mongodb://root:root@edutask-mongodb:27017"

    mongo_client = pymongo.MongoClient(MONGO_URL)

    if mongo_client is None:
        pytest.skip("MongoDB connection not available")

    db = mongo_client.edutask

    collection_name = "test_email"

    email_collection = db.get_collection("test_email")

    
    email_validator = getValidator(email_collection.name)

    if collection_name in db.list_collection_names():
        db.drop_collection(collection_name)

    db.create_collection(collection_name, validator=email_validator)
    
    dao_instance = DAO(collection_name)

    dao_instance.collection.delete_many({})
    yield dao_instance

    dao_instance.collection.delete_many({})

    mongo_client.close()

    dao_instance.drop()

class TestDAO:
    @pytest.mark.ass3
    def test_create_document_with_valid_input(self, dao):
        """Test case: Create operation with valid input, all fields present, unique constraint not violated"""
        doc = {"email": "test@example.com"}
        result = dao.create(doc)
        
        # Single focused assertion
        assert result["email"] == "test@example.com"
    
    @pytest.mark.ass3
    def test_create_document_email_saved_correctly(self, dao):
        """Test case: Create operation verifying email is saved correctly"""
        doc = {"email": "test@example.com"}
        result = dao.create(doc)
        
        # Single focused assertion on email
        assert result["email"] == "test@example.com"
    
    @pytest.mark.ass3
    def test_create_document_unique_constraint_violated(self, dao):
        """Test case: Create operation with valid input, all fields present, unique constraint violated"""
        doc1 = {"email": "dup@example.com"}
        doc2 = {"email": "dup@example.com"}
        
        dao.create(doc1)
        
        # Single focused assertion: Should raise DuplicateKeyError
        with pytest.raises(DuplicateKeyError):
            dao.create(doc2)
    
    @pytest.mark.ass3
    def test_create_document_missing_required_field(self, dao):
        """Test case: Create operation with valid input but missing required fields"""
        doc = {}
        
        # Single focused assertion: Should raise WriteError
        with pytest.raises(WriteError):
            dao.create(doc)
    
    # @pytest.mark.ass3
    # def test_create_document_with_tasks_array(self, dao):
    #     """Test case: Create operation with valid input including optional tasks array"""
    #     doc = {
    #         "firstName": "Olle",
    #         "lastName": "Olsson",
    #         "email": "olle@example.com",
    #         "tasks": []
    #     }
    #     result = dao.create(doc)
        
    #     # Single focused assertion
    #     assert isinstance(result["tasks"], list)
    
    # @pytest.mark.ass3
    # def test_create_document_with_tasks_content(self, dao):
    #     """Test case: Create operation verifying tasks content"""
    #     doc = {
    #         "firstName": "Olle",
    #         "lastName": "Olsson",
    #         "email": "olle@example.com",
    #         "tasks": []
    #     }
    #     result = dao.create(doc)
        
    #     # Single focused assertion on tasks being empty
    #     assert result["tasks"] == []
    
    # @pytest.mark.ass3
    # def test_create_document_with_objectid_tasks(self, dao):
    #     """Test case: Create operation with valid input including tasks with ObjectIds"""
    #     doc = {
    #         "firstName": "Lisa",
    #         "lastName": "Larsson",
    #         "email": "lisa@example.com",
    #         "tasks": [ObjectId(), ObjectId()]
    #     }
    #     result = dao.create(doc)
        
    #     # Single focused assertion on tasks being a list
    #     assert isinstance(result["tasks"], list)
    
    # @pytest.mark.ass3
    # def test_create_document_with_objectid_tasks_content(self, dao):
    #     """Test case: Create operation verifying ObjectId tasks content"""
    #     task_ids = [ObjectId(), ObjectId()]
    #     doc = {
    #         "firstName": "Lisa",
    #         "lastName": "Larsson",
    #         "email": "lisa@example.com",
    #         "tasks": task_ids
    #     }
    #     result = dao.create(doc)
        
    #     # Single focused assertion that each task is correctly stored as an ObjectId
    #     assert len(result["tasks"]) == 2
    
    # @pytest.mark.ass3
    # def test_create_document_with_invalid_tasks(self, dao):
    #     """Test case: Create operation with invalid task type"""
    #     doc = {
    #         "firstName": "Felix",
    #         "lastName": "Felsson",
    #         "email": "felix@example.com",
    #         "tasks": ["not_an_objectid"]
    #     }
        
    #     # Single focused assertion: Should raise WriteError
    #     with pytest.raises(WriteError):
    #         dao.create(doc)
    
    @pytest.mark.ass3
    def test_find_existing_document(self, dao):
        """Test case: Read operation with existing document ID"""
        doc = {"email": "find@example.com"}
        created = dao.create(doc)
        
        # Find the document by querying the collection directly
        found = dao.collection.find_one({"email": "find@example.com"})
        
        # Single focused assertion
        assert found is not None
    
    # @pytest.mark.ass3
    # def test_find_document_has_correct_firstname(self, dao):
    #     """Test case: Read operation verifying firstName content"""
    #     doc = {"firstName": "Find", "lastName": "Me", "email": "find@example.com"}
    #     dao.create(doc)
        
    #     found = dao.collection.find_one({"email": "find@example.com"})
        
    #     # Single focused assertion on firstName
    #     assert found["firstName"] == "Find"
    
    @pytest.mark.ass3
    def test_find_nonexisting_document(self, dao):
        """Test case: Read operation with non-existing document ID"""
        found = dao.collection.find_one({"email": "notfound@example.com"})
        
        # Single focused assertion
        assert found is None
    
    # @pytest.mark.ass3
    # def test_update_document(self, dao):
    #     """Test case: Update operation with valid input"""
    #     doc = {"email": "upp@example.com"}
    #     created = dao.create(doc)
        
    #     # Update the document
    #     dao.update(created["_id"]["$oid"], {"$set": {"lastName": "Updated"}})
        
    #     # Single focused assertion
    #     updated = dao.collection.find_one({"email": "upp@example.com"})
    #     assert updated["lastName"] == "Updated"
    
    @pytest.mark.ass3
    def test_delete_document(self, dao):
        """Test case: Delete operation with existing document ID"""
        doc = {"email": "del@example.com"}
        created = dao.create(doc)
        
        # Delete the document
        dao.delete(created["_id"]["$oid"])
        
        # Single focused assertion
        found = dao.collection.find_one({"email": "del@example.com"})
        assert found is None
    
    # @pytest.mark.ass3
    # def test_drop_collection(self, dao):
    #     """Test case: Drop operation"""
    #     # First create a document to ensure collection exists
    #     doc = {"email": "drop@example.com"}
    #     dao.create(doc)
        
    #     # Drop the collection
    #     dao.drop()

    #     assert "test_collection" not in dao.list_collection_names()