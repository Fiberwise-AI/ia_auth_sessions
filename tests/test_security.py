"""
Tests for security functions.
"""
import pytest
from ia_auth_sessions.security import hash_password, verify_password


def test_hash_password():
    """Test password hashing."""
    password = "MySecurePassword123"
    hashed = hash_password(password)
    
    # Should be bcrypt format
    assert hashed.startswith("$2b$")
    
    # Should be different from original
    assert hashed != password
    
    # Should be longer than original
    assert len(hashed) > len(password)


def test_verify_password_correct():
    """Test password verification with correct password."""
    password = "TestPassword123"
    hashed = hash_password(password)
    
    # Correct password should verify
    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    """Test password verification with incorrect password."""
    password = "TestPassword123"
    wrong_password = "WrongPassword456"
    hashed = hash_password(password)
    
    # Wrong password should fail
    assert verify_password(wrong_password, hashed) is False


def test_same_password_different_hashes():
    """Test that hashing the same password twice produces different hashes."""
    password = "SamePassword123"
    
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    
    # Hashes should be different (due to salt)
    assert hash1 != hash2
    
    # But both should verify successfully
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True
