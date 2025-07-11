"""
Authentication middleware for FastAPI.

Provides optional middleware for authentication handling.
"""

from typing import Optional
from fastapi import Request, Response
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from ..config.database import get_db_session
from .oauth2 import get_current_user


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling authentication across the application.
    
    Note: With FastAPI's dependency injection system, middleware is often
    not necessary for authentication. This is provided for specific use cases.
    """
    
    def __init__(self, app, public_paths: Optional[list] = None):
        """
        Initialize authentication middleware.
        
        Args:
            app: FastAPI application instance
            public_paths: List of paths that don't require authentication
        """
        super().__init__(app)
        self.public_paths = public_paths or [
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/templates",
            "/api/parsinator/health",
            "/auth/login",
            "/auth/register",
            "/auth/reset-password",
            "/auth/confirm-reset"
        ]
        self.security = HTTPBearer(auto_error=False)
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request through authentication middleware.
        
        Args:
            request: HTTP request
            call_next: Next middleware in chain
            
        Returns:
            HTTP response
        """
        # Check if path is public
        if request.url.path in self.public_paths:
            response = await call_next(request)
            return response
        
        # Check for authentication token
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Extract token
        token = authorization.split(" ")[1]
        
        # Validate token and get user
        try:
            # Get database session
            db = next(get_db_session())
            user = get_current_user(token, db)
            
            # Add user to request state
            request.state.user = user
            
            # Continue to next middleware/endpoint
            response = await call_next(request)
            return response
            
        except Exception as e:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authentication token"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        finally:
            # Clean up database session
            if 'db' in locals():
                db.close()


class OptionalAuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds user context when authentication is present,
    but doesn't require it.
    """
    
    def __init__(self, app):
        """
        Initialize optional authentication middleware.
        
        Args:
            app: FastAPI application instance
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with optional authentication.
        
        Args:
            request: HTTP request
            call_next: Next middleware in chain
            
        Returns:
            HTTP response
        """
        # Check for authentication token
        authorization = request.headers.get("Authorization")
        
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            
            try:
                # Get database session
                db = next(get_db_session())
                user = get_current_user(token, db)
                
                # Add user to request state
                request.state.user = user
                
            except Exception:
                # If authentication fails, continue without user
                request.state.user = None
            finally:
                # Clean up database session
                if 'db' in locals():
                    db.close()
        else:
            request.state.user = None
        
        # Continue to next middleware/endpoint
        response = await call_next(request)
        return response


def get_user_from_request(request: Request) -> Optional[dict]:
    """
    Get user information from request state.
    
    Args:
        request: HTTP request with user state
        
    Returns:
        User information if available, None otherwise
    """
    user = getattr(request.state, 'user', None)
    if user:
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "subscription_tier": user.subscription_tier.value,
            "is_premium": user.is_premium(),
        }
    return None


def require_auth_middleware(public_paths: Optional[list] = None):
    """
    Factory function to create authentication middleware.
    
    Args:
        public_paths: List of paths that don't require authentication
        
    Returns:
        Middleware class configured with public paths
    """
    def middleware_factory(app):
        return AuthenticationMiddleware(app, public_paths)
    
    return middleware_factory


def optional_auth_middleware():
    """
    Factory function to create optional authentication middleware.
    
    Returns:
        Optional authentication middleware class
    """
    def middleware_factory(app):
        return OptionalAuthenticationMiddleware(app)
    
    return middleware_factory