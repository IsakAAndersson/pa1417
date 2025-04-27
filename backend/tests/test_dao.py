from unittest.mock import patch

# Pre-patch getValidator before any imports occur
mock_validator = patch('src.util.validators.getValidator', return_value={
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "type"],
        "properties": {
            "name": {
                "bsonType": "string",
                "description": "must be a string and is required"
            },
            "type": {
                "bsonType": "string",
                "description": "must be a string and is required"
            },
            "active": {
                "bsonType": "bool",
                "description": "must be a boolean"
            }
        }
    }
})
mock_validator.start()

import pytest
import mongomock
import pymongo
from pymongo.errors import WriteError
from unittest.mock import MagicMock
import os
from bson import ObjectId
from src.util.dao import DAO


# Make sure to stop the patch when tests are done
@pytest.fixture(scope="session", autouse=True)
def cleanup():
    yield
    mock_validator.stop()


# Setup a mongomock client for testing
@pytest.fixture
def mongo_mock():
    with patch('pymongo.MongoClient') as mock_client:
        mock_db = MagicMock()
        mock_collection = mongomock.MongoClient().db.collection
        mock_db.edutask = MagicMock()
        mock_db.edutask.list_collection_names.return_value = []
        mock_db.edutask.create_collection = MagicMock()
        mock_db.edutask.__getitem__.return_value = mock_collection
        mock_client.return_value = mock_db
        yield mock_client


# Test fixture for the DAO object
@pytest.fixture
def dao(mongo_mock):
    with patch('dotenv.dotenv_values', return_value={'MONGO_URL': 'mongodb://localhost:27017'}):
        with patch.dict(os.environ, {'MONGO_URL': 'mongodb://testhost:27017'}):
            return DAO("test_collection")


# Test cases for the create method
def test_create_valid_document(dao):
    """Test creating a valid document with all required fields"""
    inserted_id = ObjectId()
    dao.collection.insert_one = MagicMock(return_value=MagicMock(inserted_id=inserted_id))
    dao.collection.find_one = MagicMock(return_value={
        "_id": inserted_id,
        "name": "Test Item",
        "type": "test"
    })
    
    data = {
        "name": "Test Item",
        "type": "test"
    }
    result = dao.create(data)
    assert result is not None
    assert "_id" in result
    assert result["name"] == "Test Item"
    assert result["type"] == "test"


def test_create_document_with_optional_field(dao):
    """Test creating a document with required and optional fields"""
    inserted_id = ObjectId()
    dao.collection.insert_one = MagicMock(return_value=MagicMock(inserted_id=inserted_id))
    dao.collection.find_one = MagicMock(return_value={
        "_id": inserted_id,
        "name": "Test Item",
        "type": "test",
        "active": True
    })
    
    data = {
        "name": "Test Item",
        "type": "test",
        "active": True
    }
    result = dao.create(data)
    assert result is not None
    assert result["active"] is True


def test_create_without_required_field(dao):
    """Test creating a document missing a required field should fail"""
    dao.collection.insert_one = MagicMock(side_effect=WriteError("Document failed validation"))
    
    data = {
        "name": "Test Item",
        # "type" field is missing
    }
    
    with pytest.raises(WriteError):
        dao.create(data)


def test_create_with_wrong_field_type(dao):
    """Test creating a document with wrong field type should fail"""
    dao.collection.insert_one = MagicMock(side_effect=WriteError("Document failed validation"))
    
    data = {
        "name": "Test Item",
        "type": "test",
        "active": "not a boolean"  # Should be a boolean
    }
    
    with pytest.raises(WriteError):
        dao.create(data)


def test_create_with_extra_fields(dao):
    """Test creating a document with extra fields should succeed"""
    inserted_id = ObjectId()
    dao.collection.insert_one = MagicMock(return_value=MagicMock(inserted_id=inserted_id))
    dao.collection.find_one = MagicMock(return_value={
        "_id": inserted_id,
        "name": "Test Item",
        "type": "test",
        "extra_field": "extra value"
    })
    
    data = {
        "name": "Test Item",
        "type": "test",
        "extra_field": "extra value"
    }
    result = dao.create(data)
    assert result is not None
    assert result["extra_field"] == "extra value"


def test_create_handles_database_error(dao):
    """Test that other database errors are properly propagated"""
    dao.collection.insert_one = MagicMock(side_effect=Exception("Database connection error"))
    
    data = {
        "name": "Test Item",
        "type": "test"
    }
    
    with pytest.raises(Exception):
        dao.create(data)


def test_to_json_conversion(dao):
    """Test that the to_json method correctly converts MongoDB documents"""
    # Create a document with an ObjectId
    obj_id = ObjectId()
    doc = {
        "_id": obj_id,
        "name": "Test Item"
    }
    
    # Mock insert_one and find_one to return our test document
    dao.collection.insert_one = MagicMock(return_value=MagicMock(inserted_id=obj_id))
    dao.collection.find_one = MagicMock(return_value=doc)
    
    result = dao.create({"name": "Test Item", "type": "test"})
    
    # The ObjectId should be properly serialized
    assert isinstance(result["_id"], dict)
    assert "$oid" in result["_id"]
    assert result["_id"]["$oid"] == str(obj_id)


def test_dao_uses_environment_variable():
    """Test that DAO uses the MONGO_URL from environment variables"""
    with patch('dotenv.dotenv_values', return_value={'MONGO_URL': 'mongodb://default:27017'}):
        with patch.dict(os.environ, {'MONGO_URL': 'mongodb://custom:27017'}):
            with patch('pymongo.MongoClient') as mock_client:
                mock_db = MagicMock()
                mock_collection = MagicMock()
                mock_db.edutask = MagicMock()
                mock_db.edutask.list_collection_names.return_value = []
                mock_db.edutask.create_collection = MagicMock()
                mock_db.edutask.__getitem__.return_value = mock_collection
                mock_client.return_value = mock_db
                
                with patch('src.util.validators.getValidator'):
                    dao = DAO("test_collection")
                    
                    # Check that the client was created with the correct URL
                    mock_client.assert_called_once_with('mongodb://custom:27017')


def test_create_with_unique_constraint(dao):
    """Test that uniqueness constraints are enforced"""
    # First insert succeeds
    inserted_id1 = ObjectId()
    # Second insert fails with DuplicateKeyError

    dao.collection.insert_one = MagicMock(side_effect=[
        MagicMock(inserted_id=inserted_id1),  
        pymongo.errors.DuplicateKeyError("Duplicate key error")
    ])

    dao.collection.find_one = MagicMock(return_value={
        "_id": inserted_id1,
        "name": "Test Item 1",
        "type": "test",
        "code": "ABC123"
    })
    
    data1 = {
        "name": "Test Item 1",
        "type": "test",
        "code": "ABC123"
    }
    
    data2 = {
        "name": "Test Item 2",
        "type": "test",
        "code": "ABC123"  # Same code as data1
    }
    
    result1 = dao.create(data1)
    assert result1 is not None
    assert result1["code"] == "ABC123"
    
    # Second insert should fail with DuplicateKeyError
    with pytest.raises(pymongo.errors.DuplicateKeyError):
        dao.create(data2)


def test_create_with_nested_document(dao):
    """Test creating a document with nested document structure"""
    inserted_id = ObjectId()
    dao.collection.insert_one = MagicMock(return_value=MagicMock(inserted_id=inserted_id))
    dao.collection.find_one = MagicMock(return_value={
        "_id": inserted_id,
        "name": "Test Item",
        "type": "test",
        "metadata": {
            "created_by": "user1",
            "tags": ["test", "integration"]
        }
    })
    
    data = {
        "name": "Test Item",
        "type": "test",
        "metadata": {
            "created_by": "user1",
            "tags": ["test", "integration"]
        }
    }
    
    result = dao.create(data)
    assert result is not None
    assert "metadata" in result
    assert result["metadata"]["created_by"] == "user1"
    assert "tags" in result["metadata"]
    assert len(result["metadata"]["tags"]) == 2


def test_create_with_array_field(dao):
    """Test creating a document with array fields"""
    inserted_id = ObjectId()
    dao.collection.insert_one = MagicMock(return_value=MagicMock(inserted_id=inserted_id))
    dao.collection.find_one = MagicMock(return_value={
        "_id": inserted_id,
        "name": "Test Item",
        "type": "test",
        "tags": ["tag1", "tag2", "tag3"]
    })
    
    data = {
        "name": "Test Item",
        "type": "test",
        "tags": ["tag1", "tag2", "tag3"]
    }
    
    result = dao.create(data)
    assert result is not None
    assert "tags" in result
    assert len(result["tags"]) == 3
    assert "tag2" in result["tags"]