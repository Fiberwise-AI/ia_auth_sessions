"""
FastAPI dependencies for authentication.
"""
from fastapi import Request, HTTPException, status, Depends
from typing import Dict, Any
from nexusql import DatabaseManager
from .session_manager import SessionManager
from .user_manager import UserManager


def get_db_manager(request: Request) -> DatabaseManager:
    """
    Get database manager from app state.

    Must be stored in app.state.db_manager during startup.
    """
    if not hasattr(request.app.state, "db_manager"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database manager not initialized"
        )
    return request.app.state.db_manager


def get_session_manager(request: Request) -> SessionManager:
    """
    Get session manager from app state.

    Must be stored in app.state.session_manager during startup.
    """
    if not hasattr(request.app.state, "session_manager"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session manager not initialized"
        )
    return request.app.state.session_manager


def get_user_manager(request: Request) -> UserManager:
    """
    Get user manager from app state.

    Must be stored in app.state.user_manager during startup.
    """
    if not hasattr(request.app.state, "user_manager"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User manager not initialized"
        )
    return request.app.state.user_manager


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Get current authenticated user from session.

    Requires SessionMiddleware to be installed.
    Raises 401 if not authenticated.

    Usage:
        @app.get("/protected")
        async def protected(user: dict = Depends(get_current_user)):
            return {"username": user["username"]}
    """
    if not hasattr(request.state, "user") or request.state.user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Cookie"}
        )

    return request.state.user


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current active user (additional check for is_active).

    Raises 403 if user is not active.

    Usage:
        @app.get("/admin")
        async def admin(user: dict = Depends(get_current_active_user)):
            return {"username": user["username"]}
    """
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return current_user


async def get_current_verified_user(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get current verified user (must be active and verified).

    Raises 403 if user is not verified.

    Usage:
        @app.get("/sensitive")
        async def sensitive(user: dict = Depends(get_current_verified_user)):
            return {"data": "sensitive"}
    """
    if not current_user.get("is_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )

    return current_user
