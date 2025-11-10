# ia_auth_sessions Architecture Notes

## Current Architecture Issues

The `ia_auth_sessions` package currently contains FastAPI application-specific code, which makes it less reusable as a library. This is a design concern that needs to be addressed.

### What Currently Exists in ia_auth_sessions

**Application-Specific Code (Should NOT be in a library):**
- `html_routes.py` - FastAPI route handlers for `/auth/login` and `/auth/register`
- `api_routes.py` - FastAPI API endpoints
- `templates/` directory - Jinja2 HTML templates for login/register pages
- Hardcoded redirect logic to frontend URLs
- Application-specific UI/UX decisions

**Library Code (Should remain in ia_auth_sessions):**
- `UserManager` - User CRUD operations (create, authenticate, get user)
- `SessionManager` - Session creation, validation, and lifecycle management
- `SessionMiddleware` - Request/response processing for session cookies
- `security.py` - Password hashing, token signing/verification
- Database models and schemas
- Core authentication primitives

### Problems with Current Design

1. **Not Reusable** - Every app using `ia_auth_sessions` gets the same login UI, redirect behavior, and route structure
2. **Tight Coupling** - Library code mixed with FastAPI application code
3. **Limited Flexibility** - Can't customize authentication flow without modifying the package
4. **Maintenance Burden** - Application logic in a library makes it harder to version and maintain

### Proposed Refactor

**ia_auth_sessions (Pure Library)**
```
ia_auth_sessions/
├── __init__.py
├── user_manager.py        # User CRUD operations
├── session_manager.py     # Session lifecycle management
├── middleware.py          # SessionMiddleware for FastAPI
├── security.py            # Password hashing, token signing
├── models.py              # Pydantic models for users/sessions
└── dependencies.py        # FastAPI dependency injection helpers
```

**ia_chat_app/backend/app/auth/ (Application Code)**
```
app/auth/
├── __init__.py
├── routes_html.py         # Login/register HTML routes (moved from ia_auth_sessions)
├── routes_api.py          # Auth API endpoints (moved from ia_auth_sessions)
├── templates/
│   ├── login.html
│   └── register.html
└── config.py              # Auth-related configuration
```

### Benefits of Refactor

1. **Reusability** - Other projects can use `ia_auth_sessions` as a library and build their own auth UI
2. **Separation of Concerns** - Library handles core logic, application handles UI/UX
3. **Flexibility** - Each app can implement custom authentication flows
4. **Better Testing** - Can test library code independently from application code
5. **Clearer Boundaries** - Library provides primitives, application composes them

### Migration Steps

1. Create `ia_chat_app/backend/app/auth/` directory
2. Move `html_routes.py` → `app/auth/routes_html.py`
3. Move `api_routes.py` → `app/auth/routes_api.py`
4. Move `templates/` directory → `app/auth/templates/`
5. Update imports in `ia_chat_app/backend/main.py`
6. Remove route modules from `ia_auth_sessions/__init__.py`
7. Update `ia_auth_sessions` to only export core managers and middleware
8. Test that authentication still works after refactor

### Example Usage After Refactor

**ia_auth_sessions (library) provides:**
```python
from ia_auth_sessions import UserManager, SessionManager, SessionMiddleware

# Use the managers to build custom auth flows
user_manager = UserManager(db_manager)
session_manager = SessionManager(db_manager, secret_key="...")

# Add middleware to FastAPI app
app.add_middleware(SessionMiddleware, ...)
```

**ia_chat_app (application) implements:**
```python
from ia_auth_sessions import UserManager, SessionManager
from app.auth import routes_html, routes_api

# Application-specific auth routes using the library managers
app.include_router(routes_html.router)  # Custom login/register pages
app.include_router(routes_api.router)   # Custom API endpoints
```

### Notes

- This makes `ia_auth_sessions` a true utility library like `passlib` or `itsdangerous`
- Applications have full control over authentication UI and flow
- Library focuses on doing one thing well: managing users and sessions
- Similar pattern to how FastAPI Users, Django Auth, or Flask-Login work

## Decision Pending

Should we proceed with this refactor or keep the current monolithic design?
