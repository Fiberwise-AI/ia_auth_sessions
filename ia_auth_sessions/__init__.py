"""
IA Auth Sessions - Industry-standard session-based authentication for FastAPI.
"""

from .session_manager import SessionManager
from .user_manager import UserManager
from .middleware import SessionMiddleware
from .dependencies import get_current_user, get_current_active_user, get_session_manager, get_user_manager
from .models import User, Session, UserCreate, UserLogin
from .security import verify_password, hash_password
from .database import initialize_database, drop_tables
from .routes import router as api_router
from .html_routes import router as html_router

__version__ = "0.1.0"

__all__ = [
    "SessionManager",
    "UserManager",
    "SessionMiddleware",
    "get_current_user",
    "get_current_active_user",
    "get_session_manager",
    "get_user_manager",
    "User",
    "Session",
    "UserCreate",
    "UserLogin",
    "verify_password",
    "hash_password",
    "initialize_database",
    "drop_tables",
    "api_router",
    "html_router",
]
