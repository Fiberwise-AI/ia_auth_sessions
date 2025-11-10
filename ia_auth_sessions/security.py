"""
Security utilities using industry-standard libraries.
"""
from passlib.context import CryptContext

# Use bcrypt - industry standard for password hashing
# Automatically handles salting and uses strong work factor
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The bcrypt hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain text password to hash

    Returns:
        Bcrypt hashed password with automatic salt
    """
    return pwd_context.hash(password)
