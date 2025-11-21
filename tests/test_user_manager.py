"""
Tests for UserManager.
"""
import pytest
import pytest_asyncio
from ia_auth_sessions.user_manager import UserManager
from ia_auth_sessions.security import verify_password
from ia_auth_sessions import initialize_database
from nexusql import DatabaseManager
from datetime import datetime


@pytest_asyncio.fixture
async def db_manager():
    """Create test database manager."""
    db = DatabaseManager("sqlite:///:memory:")
    await db.initialize()

    # Initialize auth schema
    await initialize_database(db)

    yield db

    db.disconnect()


@pytest.mark.asyncio
async def test_create_user(db_manager):
    """Test user creation."""
    user_mgr = UserManager(db_manager)

    user = await user_mgr.create_user(
        email="test@example.com",
        username="testuser",
        password="SecurePass123",
        full_name="Test User"
    )

    assert user["email"] == "test@example.com"
    assert user["username"] == "testuser"
    assert user["full_name"] == "Test User"
    assert "hashed_password" not in user  # Password should not be in response


@pytest.mark.asyncio
async def test_password_is_hashed(db_manager):
    """Test that passwords are properly hashed."""
    user_mgr = UserManager(db_manager)

    await user_mgr.create_user(
        email="test@example.com",
        username="testuser",
        password="SecurePass123"
    )

    # Get hashed password from DB
    result = db_manager.fetch_one(
        "SELECT hashed_password FROM users WHERE email = :email",
        {"email": "test@example.com"}
    )

    # Should be hashed (bcrypt starts with $2b$)
    assert result["hashed_password"].startswith("$2b$")
    assert result["hashed_password"] != "SecurePass123"

    # Verify password works
    assert verify_password("SecurePass123", result["hashed_password"])


@pytest.mark.asyncio
async def test_duplicate_email(db_manager):
    """Test that duplicate emails are rejected."""
    user_mgr = UserManager(db_manager)

    await user_mgr.create_user(
        email="test@example.com",
        username="user1",
        password="password"
    )

    with pytest.raises(ValueError, match="Email already registered"):
        await user_mgr.create_user(
            email="test@example.com",
            username="user2",
            password="password"
        )


@pytest.mark.asyncio
async def test_duplicate_username(db_manager):
    """Test that duplicate usernames are rejected."""
    user_mgr = UserManager(db_manager)

    await user_mgr.create_user(
        email="test1@example.com",
        username="testuser",
        password="password"
    )

    with pytest.raises(ValueError, match="Username already taken"):
        await user_mgr.create_user(
            email="test2@example.com",
            username="testuser",
            password="password"
        )


@pytest.mark.asyncio
async def test_authenticate_user(db_manager):
    """Test user authentication."""
    user_mgr = UserManager(db_manager)

    # Create user
    await user_mgr.create_user(
        email="test@example.com",
        username="testuser",
        password="SecurePass123"
    )

    # Authenticate with correct password
    user = await user_mgr.authenticate_user("test@example.com", "SecurePass123")
    assert user is not None
    assert user["email"] == "test@example.com"

    # Authenticate with wrong password
    user = await user_mgr.authenticate_user("test@example.com", "WrongPassword")
    assert user is None


@pytest.mark.asyncio
async def test_get_user_by_id(db_manager):
    """Test getting user by ID."""
    user_mgr = UserManager(db_manager)

    created_user = await user_mgr.create_user(
        email="test@example.com",
        username="testuser",
        password="password"
    )

    user = await user_mgr.get_user_by_id(created_user["id"])
    assert user is not None
    assert user["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_change_password(db_manager):
    """Test password change."""
    user_mgr = UserManager(db_manager)

    user = await user_mgr.create_user(
        email="test@example.com",
        username="testuser",
        password="OldPassword123"
    )

    # Change password
    success = await user_mgr.change_password(
        user["id"],
        "OldPassword123",
        "NewPassword456"
    )
    assert success is True

    # Old password should not work
    auth_user = await user_mgr.authenticate_user("test@example.com", "OldPassword123")
    assert auth_user is None

    # New password should work
    auth_user = await user_mgr.authenticate_user("test@example.com", "NewPassword456")
    assert auth_user is not None


@pytest.mark.asyncio
async def test_change_password_wrong_old_password(db_manager):
    """Test that password change fails with wrong old password."""
    user_mgr = UserManager(db_manager)

    user = await user_mgr.create_user(
        email="test@example.com",
        username="testuser",
        password="CorrectPassword123"
    )

    # Try to change with wrong old password
    success = await user_mgr.change_password(
        user["id"],
        "WrongOldPassword",
        "NewPassword456"
    )
    assert success is False

    # Original password should still work
    auth_user = await user_mgr.authenticate_user("test@example.com", "CorrectPassword123")
    assert auth_user is not None


@pytest.mark.asyncio
async def test_change_password_nonexistent_user(db_manager):
    """Test that password change fails for nonexistent user."""
    user_mgr = UserManager(db_manager)

    success = await user_mgr.change_password(
        "nonexistent-id",
        "OldPassword",
        "NewPassword"
    )
    assert success is False


@pytest.mark.asyncio
async def test_get_user_by_email(db_manager):
    """Test getting user by email."""
    user_mgr = UserManager(db_manager)

    created_user = await user_mgr.create_user(
        email="test@example.com",
        username="testuser",
        password="password"
    )

    user = await user_mgr.get_user_by_email("test@example.com")
    assert user is not None
    assert user["id"] == created_user["id"]
    assert user["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(db_manager):
    """Test getting nonexistent user by email."""
    user_mgr = UserManager(db_manager)

    user = await user_mgr.get_user_by_email("nonexistent@example.com")
    assert user is None
