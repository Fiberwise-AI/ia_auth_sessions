"""
Session management using signed cookies and database storage.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json
import secrets
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from nexusql import DatabaseManager


class SessionManager:
    """
    Manages sessions using industry-standard signed cookies.

    Sessions are stored in database and session IDs are signed using itsdangerous
    to prevent tampering. This is the same approach used by Flask sessions.
    """

    def __init__(self, db_manager: DatabaseManager, secret_key: str, max_age: int = 86400 * 7):
        """
        Initialize session manager.

        Args:
            db_manager: NexusQL database manager
            secret_key: Secret key for signing (min 32 chars recommended)
            max_age: Session lifetime in seconds (default 7 days)
        """
        if len(secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters")

        self.db = db_manager
        self.max_age = max_age

        # Use itsdangerous for cryptographically signed session tokens
        # Same library used by Flask for session cookies
        self.serializer = URLSafeTimedSerializer(
            secret_key=secret_key,
            salt="session-cookie"  # Additional salt for session cookies
        )

    async def create_session(
        self,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new session for a user.

        Args:
            user_id: User ID to create session for
            metadata: Optional metadata (IP, user agent, etc.)

        Returns:
            Signed session ID to store in cookie
        """
        # Generate cryptographically secure random session ID
        session_id = secrets.token_urlsafe(32)

        expires_at = datetime.utcnow() + timedelta(seconds=self.max_age)

        # Store session in database
        now = datetime.utcnow()
        query = """
        INSERT INTO sessions (id, user_id, expires_at, metadata, created_at)
        VALUES (:id, :user_id, :expires_at, :metadata, :created_at)
        """
        self.db.execute(
            query,
            {
                "id": session_id,
                "user_id": user_id,
                "expires_at": expires_at,
                "metadata": json.dumps(metadata or {}),
                "created_at": now
            }
        )

        # Update user's last login
        self.db.execute(
            "UPDATE users SET last_login = :last_login WHERE id = :user_id",
            {"last_login": now, "user_id": user_id}
        )

        # Return signed session ID for cookie
        # The signature prevents tampering - if client modifies it, validation fails
        return self.serializer.dumps(session_id)

    async def validate_session(self, signed_session_id: str) -> Optional[Dict[str, Any]]:
        """
        Validate a signed session ID and return user.

        Args:
            signed_session_id: Signed session ID from cookie

        Returns:
            User dict if valid, None if invalid/expired
        """
        try:
            # Verify signature and extract session ID
            # max_age enforces expiry at signature level (in addition to DB)
            session_id = self.serializer.loads(
                signed_session_id,
                max_age=self.max_age
            )
        except (BadSignature, SignatureExpired):
            # Signature invalid or expired
            return None

        # Get session from database
        query = """
        SELECT s.id, s.user_id, s.expires_at, s.metadata,
               u.id, u.email, u.username, u.full_name, u.is_active, u.is_verified, u.created_at, u.last_login
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.id = :session_id AND s.expires_at > :now
        """
        result = self.db.fetch_one(query, {"session_id": session_id, "now": datetime.utcnow()})

        if not result:
            return None

        # Return user data
        return {
            "id": result["id"],
            "email": result["email"],
            "username": result["username"],
            "full_name": result["full_name"],
            "is_active": result["is_active"],
            "is_verified": result["is_verified"],
            "created_at": result["created_at"],
            "last_login": result["last_login"],
            "session_id": session_id
        }

    async def destroy_session(self, session_id: str) -> bool:
        """
        Destroy a session (logout).

        Args:
            session_id: Session ID to destroy (unsigned)

        Returns:
            True if session was destroyed, False if not found
        """
        result = self.db.execute(
            "DELETE FROM sessions WHERE id = :session_id", {"session_id": session_id}
        )
        # Result may be int (rowcount) or list depending on database adapter
        return bool(result) if isinstance(result, (int, list)) else False

    async def destroy_all_user_sessions(self, user_id: str) -> int:
        """
        Destroy all sessions for a user (logout everywhere).

        Args:
            user_id: User ID

        Returns:
            Number of sessions destroyed
        """
        result = self.db.execute(
            "DELETE FROM sessions WHERE user_id = :user_id", {"user_id": user_id}
        )
        # Result may be int (rowcount) or list depending on database adapter
        if isinstance(result, list):
            return len(result)
        return result if isinstance(result, int) else 0

    async def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions from database.

        Should be run periodically (e.g., daily cron job).

        Returns:
            Number of sessions cleaned up
        """
        result = self.db.execute(
            "DELETE FROM sessions WHERE expires_at < :now", {"now": datetime.utcnow()}
        )
        return result
