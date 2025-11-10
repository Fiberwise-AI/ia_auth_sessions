# Using ia_auth_sessions in Your Project

This guide shows how to integrate `ia_auth_sessions` into a FastAPI project.

## Installation

### Local Development

Install in editable mode from the ia_auth_sessions directory:

```bash
cd your_project
pip install -e ../ia_auth_sessions
```

### Production

Install from PyPI (once published):

```bash
pip install ia-auth-sessions
```

Or add to requirements.txt:

```
ia-auth-sessions>=0.1.0
```

## Setup in main.py

```python
from fastapi import FastAPI
from ia_auth_sessions import SessionMiddleware, SessionManager, UserManager
from ia_auth_sessions.routes import router as auth_router
from nexusql import DatabaseManager
from contextlib import asynccontextmanager
from pathlib import Path
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    db_manager = DatabaseManager(os.getenv('DATABASE_URL'))

    # Apply ia_auth_sessions migrations
    auth_migrations = Path(__file__).parent.parent / "ia_auth_sessions" / "ia_auth_sessions" / "database" / "migrations"
    await db_manager.initialize(apply_schema=True, app_migration_paths=[str(auth_migrations)])

    # Create managers
    session_manager = SessionManager(
        db_manager=db_manager,
        secret_key=os.getenv('AUTH_SECRET_KEY'),
        max_age=int(os.getenv('AUTH_SESSION_MAX_AGE', '604800'))
    )
    user_manager = UserManager(db_manager)

    # Store in app.state for dependency injection
    app.state.db_manager = db_manager
    app.state.session_manager = session_manager
    app.state.user_manager = user_manager

    yield

    db_manager.disconnect()

app = FastAPI(lifespan=lifespan)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv('AUTH_SECRET_KEY'),
    db_manager=None,  # Retrieved from app.state
    session_cookie_name='session',
    max_age=604800,  # 7 days
    cookie_secure=False,  # Set True in production
    cookie_httponly=True,
    cookie_samesite='lax'
)

# Include auth routes
app.include_router(auth_router)
```

## Environment Variables

Add to your .env file:

```bash
# Database
DATABASE_URL=postgresql://localhost/myapp

# Auth (generate with: openssl rand -hex 32)
AUTH_SECRET_KEY=your-secret-key-min-32-chars-long
AUTH_SESSION_MAX_AGE=604800  # 7 days
AUTH_COOKIE_SECURE=false  # true in production
```

## Protecting Routes

```python
from fastapi import APIRouter, Depends
from ia_auth_sessions import get_current_user, get_current_active_user

router = APIRouter()

@router.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    """Requires authentication."""
    return {"message": f"Hello {user['username']}!"}

@router.get("/admin")
async def admin_route(user: dict = Depends(get_current_active_user)):
    """Requires active user."""
    return {"message": "Admin access"}
```

## WebSocket Authentication

```python
@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    # Get session manager from app state
    session_manager = websocket.app.state.session_manager

    # Validate session cookie
    session_cookie = websocket.cookies.get("session")
    if not session_cookie:
        await websocket.close(code=1008, reason="Not authenticated")
        return

    user = await session_manager.validate_session(session_cookie)
    if not user:
        await websocket.close(code=1008, reason="Invalid session")
        return

    # User is authenticated, proceed with websocket
    try:
        while True:
            data = await websocket.receive_text()
            # Process message
    except WebSocketDisconnect:
        pass
```

## Available Routes

The included `ia_auth_sessions.routes` router provides:

- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and create session
- `POST /auth/logout` - Logout and destroy session
- `GET /auth/me` - Get current user info
- `POST /auth/logout-all` - Logout from all devices

## Comparison to ia_modules.auth

| Feature | ia_modules.auth | ia_auth_sessions |
|---------|-----------------|------------------|
| Session Storage | Database | Database |
| Password Hashing | SHA-256 | bcrypt |
| Cookie Signing | Custom | itsdangerous |
| Middleware | Auto-protects all routes | Manual route protection |
| Setup | More automatic | More explicit control |

Choose `ia_auth_sessions` when:
- You want explicit control over which routes require auth
- You prefer industry-standard libraries (bcrypt, itsdangerous)
- You want a standalone, reusable package

Choose `ia_modules.auth` when:
- You want automatic route protection
- You're already using ia_modules extensively
