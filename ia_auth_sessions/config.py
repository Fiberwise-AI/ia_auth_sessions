"""
Configuration using pydantic-settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class AuthSettings(BaseSettings):
    """Authentication configuration from environment variables."""

    # Required
    auth_secret_key: str  # Min 32 chars recommended

    # Optional
    auth_session_cookie_name: str = "session"
    auth_session_max_age: int = 604800  # 7 days
    auth_cookie_secure: bool = False  # Set True in production
    auth_cookie_httponly: bool = True
    auth_cookie_samesite: str = "lax"
    auth_cookie_domain: Optional[str] = None
    auth_cookie_path: str = "/"

    class Config:
        env_file = ".env"
        case_sensitive = False
