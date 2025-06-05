from dotenv import dotenv_values
import pymongo
import pytest
import os
from pymongo.errors import WriteError, DuplicateKeyError
from bson import ObjectId
from src.util.dao import DAO
from src.util.validators import getValidator
import time

MONGO_URL = os.getenv("MONGO_URL", "mongodb://root:root@localhost:27017/?authSource=admin")

"""
Test suite for the DAO class.
Tests CRUD operations against a real MongoDB instance.
"""

@pytest.fixture(scope="function")
def dao():
    """Create a DAO instance and prepare the test collection"""
    

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
    
    @pytest.mark.ass3
    def test_find_nonexisting_document(self, dao):
        """Test case: Read operation with non-existing document ID"""
        found = dao.collection.find_one({"email": "notfound@example.com"})
        
        # Single focused assertion
        assert found is None
    
    
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
    