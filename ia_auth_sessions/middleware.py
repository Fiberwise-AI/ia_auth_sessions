"""
FastAPI middleware for automatic session handling.
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import MutableHeaders
from typing import Optional
from nexusql import DatabaseManager
from .session_manager import SessionManager
import logging

logger = logging.getLogger(__name__)


class SessionMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic session handling via signed cookies.

    This middleware:
    1. Reads session cookie from request
    2. Validates signature and checks database
    3. Injects user into request.state.user if valid
    4. Provides helper to set session cookies in responses

    Usage:
        app.add_middleware(
            SessionMiddleware,
            secret_key="your-secret-key",
            db_manager=db_manager,
            session_cookie_name="session",
            max_age=86400 * 7
        )
    """

    def __init__(
        self,
        app,
        secret_key: str,
        db_manager: DatabaseManager,
        session_cookie_name: str = "session",
        max_age: int = 86400 * 7,  # 7 days default
        cookie_secure: bool = False,  # Set True in production (HTTPS only)
        cookie_httponly: bool = True,  # Prevent JavaScript access
        cookie_samesite: str = "lax",  # CSRF protection
        cookie_domain: Optional[str] = None,
        cookie_path: str = "/"
    ):
        """
        Initialize session middleware.

        Args:
            app: FastAPI application
            secret_key: Secret key for signing (min 32 chars)
            db_manager: NexusQL database manager
            session_cookie_name: Name of session cookie
            max_age: Session lifetime in seconds
            cookie_secure: Only send over HTTPS
            cookie_httponly: Prevent JavaScript access (XSS protection)
            cookie_samesite: SameSite policy (lax/strict/none)
            cookie_domain: Cookie domain
            cookie_path: Cookie path
        """
        super().__init__(app)
        self.session_manager = SessionManager(db_manager, secret_key, max_age)
        self.cookie_name = session_cookie_name
        self.max_age = max_age
        self.cookie_secure = cookie_secure
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
        self.cookie_domain = cookie_domain
        self.cookie_path = cookie_path

    async def dispatch(self, request: Request, call_next):
        """Process request and inject session user."""
        # Initialize request state
        request.state.user = None
        request.state.session_id = None

        # Get session cookie
        session_cookie = request.cookies.get(self.cookie_name)

        if session_cookie:
            # Get session_manager from app.state (set during lifespan)
            session_manager = getattr(request.app.state, 'session_manager', None)
            if not session_manager:
                # Session manager not initialized yet, skip validation
                response = await call_next(request)
                return response

            # Validate session
            user = await session_manager.validate_session(session_cookie)
            if user:
                request.state.user = user
                request.state.session_id = user.get("session_id")
                logger.debug(f"Session validated for user: {user.get('username')}")
            else:
                logger.debug("Invalid or expired session cookie")

        # Process request
        response = await call_next(request)

        return response

    def set_session_cookie(self, response: Response, signed_session_id: str) -> None:
        """
        Helper to set session cookie in response.

        Args:
            response: FastAPI Response object
            signed_session_id: Signed session ID from SessionManager.create_session()
        """
        response.set_cookie(
            key=self.cookie_name,
            value=signed_session_id,
            max_age=self.max_age,
            secure=self.cookie_secure,
            httponly=self.cookie_httponly,
            samesite=self.cookie_samesite,
            domain=self.cookie_domain,
            path=self.cookie_path
        )

    def delete_session_cookie(self, response: Response) -> None:
        """
        Helper to delete session cookie (logout).

        Args:
            response: FastAPI Response object
        """
        response.delete_cookie(
            key=self.cookie_name,
            domain=self.cookie_domain,
            path=self.cookie_path
        )
