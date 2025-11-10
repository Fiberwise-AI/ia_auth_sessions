"""
Example FastAPI app using ia-auth-sessions.
"""
from fastapi import FastAPI, Depends
from ia_auth_sessions import (
    SessionMiddleware,
    get_current_user,
    get_current_active_user
)
from ia_auth_sessions.routes import router as auth_router
from ia_auth_sessions.session_manager import SessionManager
from ia_auth_sessions.user_manager import UserManager
from nexusql import DatabaseManager
from contextlib import asynccontextmanager
from pathlib import Path


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context for startup/shutdown."""
    # Initialize database
    db_manager = DatabaseManager("postgresql://localhost/myapp")

    # Apply migrations
    migrations_dir = Path(__file__).parent.parent / "ia_auth_sessions" / "database" / "migrations"
    await db_manager.initialize(apply_schema=True, app_migration_paths=[str(migrations_dir)])

    # Create managers
    session_manager = SessionManager(db_manager, secret_key="your-secret-key-min-32-chars-here")
    user_manager = UserManager(db_manager)

    # Store in app state for dependency injection
    app.state.db_manager = db_manager
    app.state.session_manager = session_manager
    app.state.user_manager = user_manager

    yield

    # Cleanup
    db_manager.disconnect()


# Create app
app = FastAPI(title="Example App", lifespan=lifespan)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key-min-32-chars-here",
    db_manager=None,  # Will be set during middleware init
    session_cookie_name="session",
    max_age=86400 * 7,  # 7 days
    cookie_secure=False,  # Set True in production
    cookie_httponly=True,
    cookie_samesite="lax"
)

# Include auth routes
app.include_router(auth_router)


# Example protected route
@app.get("/")
async def root():
    """Public route."""
    return {"message": "Hello World"}


@app.get("/protected")
async def protected(user: dict = Depends(get_current_user)):
    """Protected route - requires authentication."""
    return {
        "message": f"Hello {user['username']}!",
        "user": user
    }


@app.get("/admin")
async def admin(user: dict = Depends(get_current_active_user)):
    """Admin route - requires active user."""
    return {
        "message": f"Admin access for {user['username']}",
        "user": user
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
