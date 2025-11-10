"""
HTML routes for authentication pages (login, register).

These routes serve Jinja2 templates for browser-based authentication.
"""
from fastapi import APIRouter, Depends, Request, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import logging
import os

from .dependencies import get_user_manager, get_session_manager
from .user_manager import UserManager
from .session_manager import SessionManager
from .middleware import SessionMiddleware

logger = logging.getLogger(__name__)

# Setup Jinja2 templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

router = APIRouter(prefix="/auth", tags=["authentication-html"])

# Get frontend URL from environment or construct from port
FRONTEND_PORT = int(os.getenv('FRONTEND_PORT', '5173'))
FRONTEND_URL = os.getenv('FRONTEND_URL', f'http://localhost:{FRONTEND_PORT}/')


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    """Render login page."""
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "app_name": getattr(request.app.state, "app_name", "IA Chat App"),
            "error": error
        }
    )


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    user_manager: UserManager = Depends(get_user_manager),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Handle login form submission."""
    logger.info(f"Login attempt for email: {email}")

    try:
        # Authenticate user
        user = await user_manager.authenticate_user(email, password)

        if not user:
            logger.warning(f"Failed login attempt for: {email}")
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "app_name": getattr(request.app.state, "app_name", "IA Chat App"),
                    "error": "Incorrect email or password"
                },
                status_code=401
            )

        if not user.get("is_active"):
            logger.warning(f"Login attempt for inactive account: {email}")
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "app_name": getattr(request.app.state, "app_name", "IA Chat App"),
                    "error": "Account is inactive"
                },
                status_code=403
            )

        # Create session
        metadata = {
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        signed_session_id = await session_manager.create_session(
            user_id=user["id"],
            metadata=metadata
        )

        # Set session cookie
        response.set_cookie(
            key="session",
            value=signed_session_id,
            max_age=604800,
            httponly=True,
            samesite="lax"
        )

        logger.info(f"Successful login for: {email}")

        # Redirect to app
        return RedirectResponse(url=FRONTEND_URL, status_code=303, headers=response.headers)

    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "app_name": getattr(request.app.state, "app_name", "IA Chat App"),
                "error": "An error occurred. Please try again."
            },
            status_code=500
        )


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, error: str = None):
    """Render registration page."""
    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "app_name": getattr(request.app.state, "app_name", "IA Chat App"),
            "error": error
        }
    )


@router.post("/register", response_class=HTMLResponse)
async def register_submit(
    request: Request,
    response: Response,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(None),
    user_manager: UserManager = Depends(get_user_manager),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Handle registration form submission."""
    logger.info(f"Registration attempt for email: {email}, username: {username}")

    try:
        # Create user
        user = await user_manager.create_user(
            email=email,
            username=username,
            password=password,
            full_name=full_name
        )

        # Auto-login after registration
        metadata = {
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        signed_session_id = await session_manager.create_session(
            user_id=user["id"],
            metadata=metadata
        )

        # Set session cookie
        response.set_cookie(
            key="session",
            value=signed_session_id,
            max_age=604800,
            httponly=True,
            samesite="lax"
        )

        logger.info(f"Successful registration for: {email}")

        # Redirect to app
        return RedirectResponse(url=FRONTEND_URL, status_code=303, headers=response.headers)

    except ValueError as e:
        logger.warning(f"Registration failed for {email}: {e}")
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "app_name": getattr(request.app.state, "app_name", "IA Chat App"),
                "error": str(e)
            },
            status_code=400
        )
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "app_name": getattr(request.app.state, "app_name", "IA Chat App"),
                "error": "An error occurred. Please try again."
            },
            status_code=500
        )
