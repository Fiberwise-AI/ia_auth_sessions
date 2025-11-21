"""
Tests for SessionManager.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, UTC
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
    db.execute(
        "INSERT INTO users (id, email, username, hashed_password, created_at) VALUES (:id, :email, :username, :hashed_password, :created_at)",
        {"id": "user1", "email": "test@example.com", "username": "testuser", "hashed_password": "hashed", "created_at": datetime.now(UTC).isoformat()}
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


@pytest.mark.asyncio
async def test_session_with_metadata(db_manager):
    """Test creating session with metadata."""
    session_mgr = SessionManager(db_manager, secret_key="a" * 32, max_age=3600)

    metadata = {"ip": "192.168.1.1", "user_agent": "Mozilla/5.0"}
    signed_session_id = await session_mgr.create_session("user1", metadata=metadata)

    assert signed_session_id is not None
    
    # Validate session
    user = await session_mgr.validate_session(signed_session_id)
    assert user is not None


@pytest.mark.asyncio
async def test_cleanup_expired_sessions(db_manager):
    """Test cleaning up expired sessions."""
    session_mgr = SessionManager(db_manager, secret_key="a" * 32, max_age=1)  # 1 second expiry

    # Create a session
    await session_mgr.create_session("user1")

    # Wait for it to expire
    import asyncio
    await asyncio.sleep(2)

    # Cleanup
    count = await session_mgr.cleanup_expired_sessions()
    assert count == 1


@pytest.mark.asyncio
async def test_short_secret_key_raises_error():
    """Test that short secret key raises ValueError."""
    db = DatabaseManager("sqlite:///:memory:")
    await db.initialize()

    with pytest.raises(ValueError, match="at least 32 characters"):
        SessionManager(db, secret_key="too_short", max_age=3600)

    db.disconnect()


@pytest.mark.asyncio
async def test_validate_expired_session(db_manager):
    """Test that expired session is rejected."""
    session_mgr = SessionManager(db_manager, secret_key="a" * 32, max_age=1)  # 1 second

    # Create session
    signed_session_id = await session_mgr.create_session("user1")

    # Wait for expiry
    import asyncio
    await asyncio.sleep(2)

    # Should fail validation
    user = await session_mgr.validate_session(signed_session_id)
    assert user is None
