# Usage Guide

Complete setup instructions and API reference for ia_auth_sessions.

## Table of Contents

- [Quick Start](#quick-start)
- [Complete Setup](#complete-setup)
- [Environment Variables](#environment-variables)
- [Protected Routes](#protected-routes)
- [WebSocket Authentication](#websocket-authentication)
- [Manual Session Management](#manual-session-management)
- [API Reference](#api-reference)

## Quick Start

Minimal setup for getting started quickly:

```python
from fastapi import FastAPI, Depends
from ia_auth_sessions import SessionMiddleware, get_current_user
from ia_auth_sessions.routes import router as auth_router
from nexusql import DatabaseManager

app = FastAPI()

# Add middleware and routes
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key-min-32-chars",
    db_manager=DatabaseManager("postgresql://localhost/myapp"),
    max_age=86400 * 7  # 7 days
)
app.include_router(auth_router)

# Protected route
@app.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    return {"message": f"Hello {user['username']}!"}
```

## Complete Setup

For production applications with proper database migrations and lifecycle management:

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

    # Apply migrations
    auth_migrations = Path(__file__).parent.parent / "ia_auth_sessions" / "ia_auth_sessions" / "database" / "migrations"
    await db_manager.initialize(apply_schema=True, app_migration_paths=[str(auth_migrations)])

    # Create managers and store in app.state
    app.state.session_manager = SessionManager(
        db_manager=db_manager,
        secret_key=os.getenv('AUTH_SECRET_KEY'),
        max_age=int(os.getenv('AUTH_SESSION_MAX_AGE', '604800'))
    )
    app.state.user_manager = UserManager(db_manager)

    yield

    db_manager.disconnect()

app = FastAPI(lifespan=lifespan)

# Add middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv('AUTH_SECRET_KEY'),
    max_age=604800,
    cookie_secure=False,  # Set True in production
    cookie_httponly=True,
    cookie_samesite='lax'
)

app.include_router(auth_router)
```

## Environment Variables

```bash
# Required
DATABASE_URL=postgresql://localhost/myapp
AUTH_SECRET_KEY=your-secret-key-min-32-chars  # Generate with: openssl rand -hex 32

# Optional
AUTH_SESSION_MAX_AGE=604800  # 7 days
AUTH_COOKIE_SECURE=false  # true in production
```

## Protected Routes

### Basic Authentication

Require users to be logged in:

```python
from fastapi import Depends
from ia_auth_sessions import get_current_user

@app.get("/profile")
async def profile(user: dict = Depends(get_current_user)):
    return {
        "username": user["username"],
        "email": user["email"],
        "full_name": user["full_name"]
    }
```

### Active User Requirement

Require users to be both logged in and active:

```python
from ia_auth_sessions import get_current_active_user

@app.get("/admin")
async def admin_panel(user: dict = Depends(get_current_active_user)):
    return {"message": f"Welcome to admin, {user['username']}"}
```

### Manual Session Validation

For more control over authentication:

```python
from fastapi import Request

@app.get("/custom-auth")
async def custom_auth(request: Request):
    session_manager = request.app.state.session_manager
    session_cookie = request.cookies.get("session")

    if not session_cookie:
        return {"authenticated": False}

    user = await session_manager.validate_session(session_cookie)
    if not user:
        return {"authenticated": False}

    return {
        "authenticated": True,
        "user": user
    }
```

## WebSocket Authentication

Authenticate WebSocket connections using session cookies:

```python
from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    # Validate session
    session_manager = websocket.app.state.session_manager
    session_cookie = websocket.cookies.get("session")

    if not session_cookie:
        await websocket.close(code=1008, reason="Not authenticated")
        return

    user = await session_manager.validate_session(session_cookie)
    if not user:
        await websocket.close(code=1008, reason="Invalid session")
        return

    # User authenticated - handle messages
    try:
        while True:
            data = await websocket.receive_text()
            # Process message with authenticated user
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        pass
```

## Manual Session Management

For custom authentication flows or advanced use cases:

### User Manager

```python
from ia_auth_sessions import UserManager

user_mgr = UserManager(db_manager)

# Create user
user = await user_mgr.create_user(
    email="user@example.com",
    username="john",
    password="secure-password",
    full_name="John Doe"
)

# Authenticate user
user = await user_mgr.authenticate_user("user@example.com", "password")
if user:
    print(f"Authenticated: {user['username']}")

# Get user by ID
user = await user_mgr.get_user_by_id(user_id)

# Get user by email
user = await user_mgr.get_user_by_email("user@example.com")

# Update user
await user_mgr.update_user(user_id, full_name="John Smith")

# Deactivate user
await user_mgr.deactivate_user(user_id)
```

### Session Manager

```python
from ia_auth_sessions import SessionManager

session_mgr = SessionManager(db_manager, secret_key, max_age=604800)

# Create session
session_id = await session_mgr.create_session(
    user_id,
    metadata={"ip": "192.168.1.1", "user_agent": "Mozilla/5.0"}
)

# Validate session
user = await session_mgr.validate_session(session_id)
if user:
    print(f"Valid session for: {user['username']}")

# Destroy single session (logout)
await session_mgr.destroy_session(session_id)

# Destroy all sessions for a user (logout all devices)
await session_mgr.destroy_all_user_sessions(user_id)

# Cleanup expired sessions (run periodically)
deleted_count = await session_mgr.cleanup_expired_sessions()
print(f"Cleaned up {deleted_count} expired sessions")
```

## API Reference

### SessionMiddleware

```python
from ia_auth_sessions import SessionMiddleware

app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key",       # Min 32 chars, required
    db_manager=db_manager,              # DatabaseManager instance, optional
    session_cookie_name="session",      # Cookie name, default: "session"
    max_age=86400 * 7,                  # Session lifetime in seconds, default: 7 days
    cookie_secure=True,                 # HTTPS only, default: False (set True in production)
    cookie_httponly=True,               # No JavaScript access, default: True
    cookie_samesite="lax"               # CSRF protection, default: "lax"
)
```

### Dependencies

#### get_current_user

Requires authentication. Raises 401 if not authenticated.

```python
from ia_auth_sessions import get_current_user

async def my_route(user: dict = Depends(get_current_user)):
    # user contains: id, username, email, full_name, is_active, created_at, updated_at
    pass
```

#### get_current_active_user

Requires authentication and active status. Raises 401 if not authenticated, 403 if inactive.

```python
from ia_auth_sessions import get_current_active_user

async def my_route(user: dict = Depends(get_current_active_user)):
    # user is guaranteed to be active
    pass
```

### UserManager Methods

```python
# Create user
user = await user_mgr.create_user(
    email: str,
    username: str,
    password: str,
    full_name: str = None
) -> dict

# Authenticate user
user = await user_mgr.authenticate_user(
    email: str,
    password: str
) -> dict | None

# Get user
user = await user_mgr.get_user_by_id(user_id: str) -> dict | None
user = await user_mgr.get_user_by_email(email: str) -> dict | None

# Update user
await user_mgr.update_user(user_id: str, **updates)

# Deactivate/reactivate user
await user_mgr.deactivate_user(user_id: str)
await user_mgr.reactivate_user(user_id: str)
```

### SessionManager Methods

```python
# Create session
session_id = await session_mgr.create_session(
    user_id: str,
    metadata: dict = None
) -> str

# Validate session
user = await session_mgr.validate_session(
    session_id: str
) -> dict | None

# Destroy session(s)
await session_mgr.destroy_session(session_id: str)
await session_mgr.destroy_all_user_sessions(user_id: str)

# Cleanup
deleted_count = await session_mgr.cleanup_expired_sessions() -> int
```

## Best Practices

### Security

1. **Always use HTTPS in production** - Set `cookie_secure=True`
2. **Generate strong secret keys** - Use `openssl rand -hex 32`
3. **Set appropriate session lifetimes** - Balance security and UX
4. **Run cleanup periodically** - Schedule `cleanup_expired_sessions()` with a cron job or background task

### Performance

1. **Reuse database connections** - Store `db_manager` in `app.state`
2. **Index session lookups** - Migrations include proper indexes
3. **Cleanup regularly** - Prevents session table bloat

### Error Handling

```python
from fastapi import HTTPException

@app.post("/login")
async def login(email: str, password: str):
    user = await user_mgr.authenticate_user(email, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="Account is inactive")

    session_id = await session_mgr.create_session(user["id"])
    return {"session_id": session_id}
```
