"""
Tests for SessionManager.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from ia_auth_sessions.session_manager import SessionManager
from ia_auth_sessions import initialize_database
from nexusql import DatabaseManager


@pytest_asyncio.fixture
async def db_manager():
    """Create test database manager."""
    db = DatabaseManager("sqlite:///:memory:")
    await db.initialize()

    # Initialize auth schema
    await initialize_database(db)

    # Create test user
    await db.execute(
        "INSERT INTO users (id, email, username, hashed_password, created_at) VALUES (?, ?, ?, ?, ?)",
        ["user1", "test@example.com", "testuser", "hashed", datetime.utcnow().isoformat()]
    )

    yield db

    db.disconnect()


@pytest.mark.asyncio
async def test_create_session(db_manager):
    """Test session creation."""
    session_mgr = SessionManager(db_manager, secret_key="a" * 32, max_age=3600)

    signed_session_id = await session_mgr.create_session("user1", {"ip": "127.0.0.1"})

    assert signed_session_id is not None
    assert isinstance(signed_session_id, str)
    assert len(signed_session_id) > 32  # Signed token is longer than raw session ID


@pytest.mark.asyncio
async def test_validate_session(db_manager):
    """Test session validation."""
    session_mgr = SessionManager(db_manager, secret_key="a" * 32, max_age=3600)

    # Create session
    signed_session_id = await session_mgr.create_session("user1")

    # Validate session
    user = await session_mgr.validate_session(signed_session_id)

    assert user is not None
    assert user["id"] == "user1"
    assert user["email"] == "test@example.com"
    assert user["username"] == "testuser"


@pytest.mark.asyncio
async def test_invalid_signature(db_manager):
    """Test that tampered signatures are rejected."""
    session_mgr = SessionManager(db_manager, secret_key="a" * 32, max_age=3600)

    # Create session
    signed_session_id = await session_mgr.create_session("user1")

    # Tamper with signature
    tampered = signed_session_id + "tampered"

    # Should fail validation
    user = await session_mgr.validate_session(tampered)
    assert user is None


@pytest.mark.asyncio
async def test_destroy_session(db_manager):
    """Test session destruction."""
    session_mgr = SessionManager(db_manager, secret_key="a" * 32, max_age=3600)

    # Create session
    signed_session_id = await session_mgr.create_session("user1")

    # Get raw session ID (unsigned)
    session_id = session_mgr.serializer.loads(signed_session_id)

    # Destroy session
    result = await session_mgr.destroy_session(session_id)
    assert result is True

    # Should no longer validate
    user = await session_mgr.validate_session(signed_session_id)
    assert user is None


@pytest.mark.asyncio
async def test_destroy_all_user_sessions(db_manager):
    """Test destroying all sessions for a user."""
    session_mgr = SessionManager(db_manager, secret_key="a" * 32, max_age=3600)

    # Create multiple sessions
    await session_mgr.create_session("user1")
    await session_mgr.create_session("user1")
    await session_mgr.create_session("user1")

    # Destroy all
    count = await session_mgr.destroy_all_user_sessions("user1")
    assert count == 3
