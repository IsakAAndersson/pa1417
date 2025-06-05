import pytest
from src.controllers.usercontroller import UserController
from src.util.dao import DAO
from unittest.mock import Mock, patch

@pytest.fixture
def mock_dao():
    return Mock(spec=DAO)

@pytest.fixture
def user_controller(mock_dao):
    return UserController(mock_dao)

def test_get_user_valid_email_single_user(user_controller, mock_dao):
    # Arrange
    test_user = {"_id": "1", "email": "test@example.com"}
    mock_dao.find.return_value = [test_user]
    
    # Act
    result = user_controller.get_user_by_email("test@example.com")
    
    # Assert
    assert result == test_user
    mock_dao.find.assert_called_once_with({"email": "test@example.com"})

def test_get_user_valid_email_no_user(user_controller, mock_dao):
    # Arrange
    mock_dao.find.return_value = []
    # Act
    result = user_controller.get_user_by_email("test@example.com")
    # Assert
    assert result is None


def test_get_user_invalid_email(user_controller):
    # Act & Assert
    with pytest.raises(ValueError, match="Error: invalid email address"):
        user_controller.get_user_by_email("invalid-email")

def test_get_user_empty_email(user_controller):
    # Act & Assert
    with pytest.raises(ValueError, match="Error: invalid email address"):
        user_controller.get_user_by_email("")

def test_get_user_none_email(user_controller):
    # Act & Assert
    with pytest.raises(TypeError):
        user_controller.get_user_by_email(None)

def test_get_user_database_error(user_controller, mock_dao):
    # Arrange
    mock_dao.find.side_effect = Exception("Database connection error")
    
    # Act & Assert
    with pytest.raises(Exception, match="Database connection error"):
        user_controller.get_user_by_email("test@example.com")

def test_get_user_multiple_users(user_controller, mock_dao, capsys):
    # Arrange
    test_users = [
        {"_id": "1", "email": "test@example.com"},
        {"_id": "2", "email": "test@example.com"}
    ]
    mock_dao.find.return_value = test_users
    
    # Act
    result = user_controller.get_user_by_email("test@example.com")
    
    # Assert
    assert result == test_users[0]  

def test_get_user_multiple_users_warning(user_controller, mock_dao, capsys):
    # Arrange
    test_users = [
        {"_id": "1", "email": "test@example.com"},
        {"_id": "2", "email": "test@example.com"}
    ]
    mock_dao.find.return_value = test_users
    
    # Act
    result = user_controller.get_user_by_email("test@example.com")
    
    # Assert
    captured = capsys.readouterr()
    assert "Error: more than one user found with mail" in captured.out

def test_get_user_missing_at_symbol(user_controller):
    """Test that email without @ symbol raises ValueError"""
    # Act & Assert
    with pytest.raises(ValueError, match="Error: invalid email address"):
        user_controller.get_user_by_email("testexample.com")
