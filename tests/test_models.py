"""
Tests for Pydantic models.
"""
import pytest
from pydantic import ValidationError
from datetime import datetime, UTC
from ia_auth_sessions.models import UserCreate, UserLogin, User, Session


def test_user_create_valid():
    """Test valid user creation model."""
    user = UserCreate(
        email="test@example.com",
        username="testuser",
        password="SecurePass123"
    )
    
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.password == "SecurePass123"
    assert user.full_name is None


def test_user_create_with_full_name():
    """Test user creation with full name."""
    user = UserCreate(
        email="test@example.com",
        username="testuser",
        password="SecurePass123",
        full_name="Test User"
    )
    
    assert user.full_name == "Test User"


def test_user_create_invalid_email():
    """Test that invalid email is rejected."""
    with pytest.raises(ValidationError):
        UserCreate(
            email="notanemail",
            username="testuser",
            password="SecurePass123"
        )


def test_user_create_short_password():
    """Test that short password is rejected."""
    with pytest.raises(ValidationError):
        UserCreate(
            email="test@example.com",
            username="testuser",
            password="short"
        )


def test_user_create_short_username():
    """Test that short username is rejected."""
    with pytest.raises(ValidationError):
        UserCreate(
            email="test@example.com",
            username="ab",  # Too short (min 3)
            password="SecurePass123"
        )


def test_user_create_invalid_username_chars():
    """Test that username with invalid characters is rejected."""
    with pytest.raises(ValidationError):
        UserCreate(
            email="test@example.com",
            username="user@name",  # @ not allowed
            password="SecurePass123"
        )


def test_user_login_valid():
    """Test valid login model."""
    login = UserLogin(
        email="test@example.com",
        password="MyPassword123"
    )
    
    assert login.email == "test@example.com"
    assert login.password == "MyPassword123"


def test_user_model():
    """Test User model."""
    now = datetime.now(UTC)
    user = User(
        id="user123",
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        is_active=True,
        is_verified=False,
        created_at=now,
        last_login=now
    )
    
    assert user.id == "user123"
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.full_name == "Test User"
    assert user.is_active is True
    assert user.is_verified is False


def test_session_model():
    """Test Session model."""
    now = datetime.now(UTC)
    session = Session(
        id="session123",
        user_id="user123",
        expires_at=now,
        created_at=now,
        metadata={"ip": "127.0.0.1"}
    )
    
    assert session.id == "session123"
    assert session.user_id == "user123"
    assert session.metadata == {"ip": "127.0.0.1"}
