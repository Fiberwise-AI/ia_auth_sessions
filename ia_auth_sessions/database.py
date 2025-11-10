"""
Database initialization for ia_auth_sessions.
"""
from nexusql import DatabaseManager
import logging

logger = logging.getLogger(__name__)


AUTH_SCHEMA_SQL = """
-- IA Auth Sessions Database Schema
-- Compatible with PostgreSQL, MySQL, SQLite via NexusQL

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    last_login TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    metadata TEXT,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
"""


async def initialize_database(db_manager: DatabaseManager) -> bool:
    """
    Initialize the authentication database schema.

    Creates users and sessions tables if they don't exist.

    Args:
        db_manager: NexusQL DatabaseManager instance

    Returns:
        True if initialization successful, False otherwise

    Example:
        from nexusql import DatabaseManager
        from ia_auth_sessions import initialize_database

        db_manager = DatabaseManager("postgresql://localhost/myapp")
        success = await initialize_database(db_manager)
    """
    try:
        # Execute the entire schema script
        result = await db_manager.execute_script(AUTH_SCHEMA_SQL)
        
        if not result.success:
            logger.error(f"Failed to execute auth schema: {result.error}")
            return False

        logger.info("Auth database schema initialized")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize auth database: {e}")
        return False


async def drop_tables(db_manager: DatabaseManager) -> bool:
    """
    Drop authentication tables (for testing/cleanup).

    Args:
        db_manager: NexusQL DatabaseManager instance

    Returns:
        True if successful, False otherwise
    """
    try:
        # Drop in reverse order due to foreign keys
        drop_sql = """
        DROP TABLE IF EXISTS sessions;
        DROP TABLE IF EXISTS users;
        """
        result = await db_manager.execute_script(drop_sql)

        if not result.success:
            logger.error(f"Failed to drop auth tables: {result.error}")
            return False

        logger.info("Auth tables dropped")
        return True

    except Exception as e:
        logger.error(f"Failed to drop auth tables: {e}")
        return False
