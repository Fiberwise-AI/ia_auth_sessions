# IA Auth Sessions

Standard session-based authentication for FastAPI applications using secure signed cookies.

## Features

- **Signed Cookies**: HMAC-SHA256 via `itsdangerous` prevents tampering
- **Bcrypt Password Hashing**: Industry standard with automatic salt generation
- **Secure Cookie Flags**: HttpOnly, Secure, SameSite protection
- **Session Management**: Create, validate, destroy, and auto-cleanup
- **Database Agnostic**: PostgreSQL and SQLite via NexusQL
- **WebSocket Support**: Authenticate WebSocket connections

## Available Routes

- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and create session
- `POST /auth/logout` - Logout and destroy session
- `GET /auth/me` - Get current user info
- `POST /auth/logout-all` - Logout from all devices

## Installation

```bash
pip install ia-auth-sessions
```

For local development:
```bash
pip install -e ../ia_auth_sessions
```

## Publishing

See [PUBLISHING.md](PUBLISHING.md) for instructions on publishing to PyPI.

To test the build locally:
```bash
python test_publish.py --skip-tests
```

## Quick Start

```python
from fastapi import FastAPI, Depends
from ia_auth_sessions import SessionMiddleware, get_current_user
from ia_auth_sessions.routes import router as auth_router

app = FastAPI()

# Add middleware and routes
app.add_middleware(SessionMiddleware, secret_key="your-secret-key", ...)
app.include_router(auth_router)

# Protected route
@app.get("/protected")
async def protected(user: dict = Depends(get_current_user)):
    return {"message": f"Hello {user['username']}!"}
```

See [USAGE.md](USAGE.md) for complete setup instructions.

## Documentation

- **[USAGE.md](USAGE.md)** - Complete setup guide, examples, and API reference
- **[ARCHITECTURE_NOTES.md](ARCHITECTURE_NOTES.md)** - Design decisions and architecture

## Database Schema

Automatically creates:
- `users`: User accounts with bcrypt-hashed passwords
- `sessions`: Active sessions with metadata and expiry timestamps

## License

MIT
