# IA Auth Sessions

Standard session-based authentication for FastAPI applications using secure signed cookies.

## Features

- **Secure Cookie-Based Sessions**: Uses `itsdangerous` for cryptographically signed session cookies
- **Industry-Standard Password Hashing**: Uses `bcrypt` via `passlib`
- **FastAPI Middleware**: Automatic session injection into requests
- **Database Agnostic**: Works with any database via NexusQL
- **Dependency Injection**: Clean FastAPI dependencies for protected routes
- **Session Management**: Create, validate, destroy sessions with automatic cleanup
- **User Management**: Built-in user model with secure password storage

## Installation

```bash
pip install ia-auth-sessions
```

## Quick Start

```python
from fastapi import FastAPI, Depends
from ia_auth_sessions import SessionMiddleware, get_current_user, create_session
from nexusql import DatabaseManager

# Initialize FastAPI app
app = FastAPI()

# Setup database
db_manager = DatabaseManager("postgresql://localhost/myapp")

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key-min-32-chars",
    db_manager=db_manager,
    session_cookie_name="session",
    max_age=86400 * 7  # 7 days
)

# Protected route
@app.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    return {"message": f"Hello {user['username']}!"}
```

## How It Works

1. **Session Creation**: When user logs in, a session ID is stored in database and signed cookie is set
2. **Session Validation**: Middleware validates signature and checks database on each request
3. **Automatic Injection**: Valid session user is injected into `request.state.user`
4. **Dependency Helpers**: Use `Depends(get_current_user)` to protect routes

## Comparison: Sessions vs JWT

| Feature | Sessions (This Package) | JWT Tokens |
|---------|------------------------|------------|
| Storage | Server-side (database) | Client-side (token) |
| Revocation | Immediate (delete session) | Requires blacklist |
| Overhead | Database query per request | Token verification only |
| Security | Server controls everything | Cannot revoke until expiry |
| Best For | Traditional web apps | APIs, mobile apps |

## API Reference

### Middleware

```python
from ia_auth_sessions import SessionMiddleware

app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key",  # Min 32 chars
    db_manager=db_manager,
    session_cookie_name="session",
    max_age=86400 * 7,  # Session lifetime in seconds
    cookie_secure=True,  # HTTPS only (production)
    cookie_httponly=True,  # No JavaScript access
    cookie_samesite="lax"  # CSRF protection
)
```

### Dependencies

```python
from ia_auth_sessions import get_current_user, get_current_active_user

# Get current user (raises 401 if not authenticated)
@app.get("/profile")
async def profile(user: dict = Depends(get_current_user)):
    return user

# Get current active user (raises 403 if inactive)
@app.get("/admin")
async def admin(user: dict = Depends(get_current_active_user)):
    return user
```

### Session Manager

```python
from ia_auth_sessions import SessionManager

session_mgr = SessionManager(db_manager, secret_key)

# Create session
session_id = await session_mgr.create_session(user_id, metadata={"ip": "1.2.3.4"})

# Validate session
user = await session_mgr.validate_session(session_id)

# Destroy session
await session_mgr.destroy_session(session_id)

# Cleanup expired sessions
await session_mgr.cleanup_expired_sessions()
```

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

# Authenticate
user = await user_mgr.authenticate_user("user@example.com", "password")

# Get user
user = await user_mgr.get_user_by_id(user_id)
user = await user_mgr.get_user_by_email("user@example.com")
```

## Database Schema

The package automatically creates these tables via NexusQL migrations:

- `users`: User accounts with hashed passwords
- `sessions`: Active sessions with metadata and expiry

## Security Features

- **Signed Cookies**: Uses HMAC-SHA256 via `itsdangerous` to prevent tampering
- **Bcrypt Password Hashing**: Industry standard with automatic salt generation
- **Secure Cookie Flags**: HttpOnly, Secure, SameSite protection
- **Session Expiry**: Automatic cleanup of expired sessions
- **Active Session Management**: Destroy sessions on logout or security events

## Environment Variables

```bash
# Required
AUTH_SECRET_KEY=your-secret-key-min-32-chars

# Optional
AUTH_SESSION_COOKIE_NAME=session
AUTH_SESSION_MAX_AGE=604800  # 7 days in seconds
AUTH_COOKIE_SECURE=true  # HTTPS only
AUTH_COOKIE_HTTPONLY=true
AUTH_COOKIE_SAMESITE=lax
```

## License

MIT
