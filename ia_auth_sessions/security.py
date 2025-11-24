"""
Security utilities using modern password hashing.

Uses pwdlib, a maintained modern alternative to passlib that works with Python 3.13+
"""
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

# Use bcrypt - industry standard for password hashing
# Automatically handles salting and uses strong work factor
pwd_hash = PasswordHash((BcryptHasher(),))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The bcrypt hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_hash.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain text password to hash

    Returns:
        Bcrypt hashed password with automatic salt
    """
    return pwd_hash.hash(password)
