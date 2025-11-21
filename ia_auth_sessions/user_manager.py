"""
User management with secure password handling.
"""
from typing import Optional, Dict, Any
from datetime import datetime, UTC
import uuid
from nexusql import DatabaseManager
from .security import hash_password, verify_password


class UserManager:
    """Manages user accounts with secure password storage."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize user manager.

        Args:
            db_manager: NexusQL database manager
        """
        self.db = db_manager

    async def create_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new user with hashed password.

        Args:
            email: User email (unique)
            username: Username (unique)
            password: Plain text password (will be hashed)
            full_name: Optional full name

        Returns:
            Created user dict (without password)

        Raises:
            Exception if email or username already exists
        """
        # Check if email exists
        existing = self.db.fetch_one(
            "SELECT id FROM users WHERE email = :email",
            {"email": email}
        )
        if existing:
            raise ValueError("Email already registered")

        # Check if username exists
        existing = self.db.fetch_one(
            "SELECT id FROM users WHERE username = :username",
            {"username": username}
        )
        if existing:
            raise ValueError("Username already taken")

        # Hash password using bcrypt
        hashed_password = hash_password(password)

        # Create user
        user_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        # Insert user
        self.db.execute(
            """
            INSERT INTO users (id, email, username, hashed_password, full_name, is_active, is_verified, created_at)
            VALUES (:id, :email, :username, :hashed_password, :full_name, :is_active, :is_verified, :created_at)
            """,
            {
                "id": user_id,
                "email": email,
                "username": username,
                "hashed_password": hashed_password,
                "full_name": full_name,
                "is_active": True,
                "is_verified": False,
                "created_at": now
            }
        )

        # Fetch the created user
        user = self.db.fetch_one(
            "SELECT id, email, username, full_name, is_active, is_verified, created_at FROM users WHERE id = :id",
            {"id": user_id}
        )

        return dict(user) if user else None

    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user by email and password.

        Args:
            email: User email
            password: Plain text password

        Returns:
            User dict if credentials valid, None otherwise
        """
        query = """
        SELECT id, email, username, hashed_password, full_name, is_active, is_verified, created_at
        FROM users
        WHERE email = :email
        """
        user = self.db.fetch_one(query, {"email": email})

        if not user:
            return None

        # Verify password using bcrypt
        if not verify_password(password, user["hashed_password"]):
            return None

        # Return user without password
        user_dict = dict(user)
        del user_dict["hashed_password"]
        return user_dict

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User dict if found, None otherwise
        """
        query = """
        SELECT id, email, username, full_name, is_active, is_verified, created_at, last_login
        FROM users
        WHERE id = :user_id
        """
        user = self.db.fetch_one(query, {"user_id": user_id})
        return dict(user) if user else None

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User dict if found, None otherwise
        """
        query = """
        SELECT id, email, username, full_name, is_active, is_verified, created_at, last_login
        FROM users
        WHERE email = :email
        """
        user = self.db.fetch_one(query, {"email": email})
        return dict(user) if user else None

    async def update_user(
        self,
        user_id: str,
        full_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update user fields.

        Args:
            user_id: User ID
            full_name: New full name (if provided)
            is_active: New active status (if provided)
            is_verified: New verified status (if provided)

        Returns:
            Updated user dict if found, None otherwise
        """
        updates = []
        params = []
        param_num = 1

        if full_name is not None:
            updates.append(f"full_name = ${param_num}")
            params.append(full_name)
            param_num += 1

        if is_active is not None:
            updates.append(f"is_active = ${param_num}")
            params.append(is_active)
            param_num += 1

        if is_verified is not None:
            updates.append(f"is_verified = ${param_num}")
            params.append(is_verified)
            param_num += 1

        if not updates:
            return await self.get_user_by_id(user_id)

        params.append(user_id)
        query = f"""
        UPDATE users
        SET {', '.join(updates)}
        WHERE id = ${param_num}
        RETURNING id, email, username, full_name, is_active, is_verified, created_at, last_login
        """

        user = self.db.fetch_one(query, params)
        return dict(user) if user else None

    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            old_password: Current password (for verification)
            new_password: New password

        Returns:
            True if password changed, False if old password incorrect
        """
        # Get current hashed password
        user = self.db.fetch_one(
            "SELECT hashed_password FROM users WHERE id = :user_id",
            {"user_id": user_id}
        )

        if not user:
            return False

        # Verify old password
        if not verify_password(old_password, user["hashed_password"]):
            return False

        # Hash new password
        new_hashed = hash_password(new_password)

        # Update password
        self.db.execute(
            "UPDATE users SET hashed_password = :hashed_password WHERE id = :user_id",
            {"hashed_password": new_hashed, "user_id": user_id}
        )

        return True
