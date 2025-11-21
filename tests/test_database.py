"""
Tests for database initialization.
"""
import pytest
import pytest_asyncio
from ia_auth_sessions import initialize_database, drop_tables
from nexusql import DatabaseManager


@pytest_asyncio.fixture
async def db_manager():
    """Create test database manager."""
    db = DatabaseManager("sqlite:///:memory:")
    await db.initialize()
    yield db
    db.disconnect()


@pytest.mark.asyncio
async def test_initialize_database(db_manager):
    """Test that database schema is created correctly."""
    await initialize_database(db_manager)
    
    # Check that users table exists
    users = db_manager.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    assert len(users) == 1
    
    # Check that sessions table exists
    sessions = db_manager.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
    assert len(sessions) == 1


@pytest.mark.asyncio
async def test_drop_tables(db_manager):
    """Test that tables can be dropped."""
    await initialize_database(db_manager)
    
    # Tables should exist
    tables = db_manager.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users', 'sessions')")
    assert len(tables) == 2
    
    # Drop tables
    await drop_tables(db_manager)
    
    # Tables should not exist
    tables = db_manager.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users', 'sessions')")
    assert len(tables) == 0


@pytest.mark.asyncio
async def test_users_table_structure(db_manager):
    """Test that users table has correct columns."""
    await initialize_database(db_manager)
    
    # Try inserting a user to verify table structure
    from datetime import datetime, UTC
    try:
        db_manager.execute(
            """INSERT INTO users (id, email, username, hashed_password, is_active, is_verified, created_at)
               VALUES (:id, :email, :username, :hashed_password, :is_active, :is_verified, :created_at)""",
            {
                "id": "test123",
                "email": "test@example.com",
                "username": "testuser",
                "hashed_password": "hashed",
                "is_active": True,
                "is_verified": False,
                "created_at": datetime.now(UTC)
            }
        )
        # If insert succeeds, table has correct structure
        assert True
    except Exception as e:
        pytest.fail(f"Users table structure is incorrect: {e}")


@pytest.mark.asyncio
async def test_sessions_table_structure(db_manager):
    """Test that sessions table has correct columns."""
    await initialize_database(db_manager)
    
    # Try inserting a session to verify table structure
    from datetime import datetime, UTC, timedelta
    try:
        db_manager.execute(
            """INSERT INTO sessions (id, user_id, expires_at, metadata, created_at)
               VALUES (:id, :user_id, :expires_at, :metadata, :created_at)""",
            {
                "id": "session123",
                "user_id": "user123",
                "expires_at": datetime.now(UTC) + timedelta(days=1),
                "metadata": "{}",
                "created_at": datetime.now(UTC)
            }
        )
        # If insert succeeds, table has correct structure
        assert True
    except Exception as e:
        pytest.fail(f"Sessions table structure is incorrect: {e}")
