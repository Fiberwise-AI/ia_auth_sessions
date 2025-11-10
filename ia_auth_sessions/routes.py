"""
Example authentication routes for FastAPI.

These can be used as-is or customized for your application.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from .models import UserCreate, UserLogin, User
from .dependencies import get_user_manager, get_session_manager, get_current_user
from .user_manager import UserManager
from .session_manager import SessionManager
from .middleware import SessionMiddleware
from typing import Dict, Any

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    user_manager: UserManager = Depends(get_user_manager)
):
    """
    Register a new user.

    Returns user object (without password).
    """
    try:
        user = await user_manager.create_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            full_name=user_data.full_name
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login")
async def login(
    credentials: UserLogin,
    request: Request,
    response: Response,
    user_manager: UserManager = Depends(get_user_manager),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Login and create session.

    Sets session cookie in response.
    """
    # Authenticate user
    user = await user_manager.authenticate_user(
        credentials.email,
        credentials.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Create session with metadata
    metadata = {
        "ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown")
    }
    signed_session_id = await session_manager.create_session(
        user_id=user["id"],
        metadata=metadata
    )

    # Get middleware to set cookie
    middleware = None
    for m in request.app.middleware:
        if isinstance(m, SessionMiddleware):
            middleware = m
            break

    if middleware:
        middleware.set_session_cookie(response, signed_session_id)

    return {
        "message": "Login successful",
        "user": user
    }


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Logout and destroy session.

    Deletes session cookie.
    """
    session_id = current_user.get("session_id")
    if session_id:
        await session_manager.destroy_session(session_id)

    # Delete session cookie directly
    response.delete_cookie(key="session", path="/")

    return {"message": "Logout successful"}


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get current user information.

    Requires authentication.
    """
    return current_user


@router.post("/logout-all")
async def logout_all(
    response: Response,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Logout from all devices.

    Destroys all sessions for current user.
    """
    count = await session_manager.destroy_all_user_sessions(current_user["id"])

    # Delete current session cookie directly
    response.delete_cookie(key="session", path="/")

    return {
        "message": f"Logged out from {count} device(s)",
        "sessions_destroyed": count
    }
