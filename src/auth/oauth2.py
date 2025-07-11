"""
OAuth2 implementation with JWT tokens for authentication.

Handles JWT token creation, verification, and user authentication.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models.user import User
from ..config.database import get_db_session


# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# OAuth2 Exception
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Data to encode in token (typically user ID and email)
        expires_delta: Token expiration time (default: ACCESS_TOKEN_EXPIRE_MINUTES)
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create JWT refresh token.
    
    Args:
        data: Data to encode in token (typically user ID)
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token to verify
        token_type: Expected token type ("access" or "refresh")
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
            raise credentials_exception
        
        # Check expiration
        expire = payload.get("exp")
        if expire is None:
            raise credentials_exception
        
        if datetime.utcnow() > datetime.fromtimestamp(expire):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    
    except JWTError:
        raise credentials_exception


def get_current_user(token: str, db: Session) -> User:
    """
    Get current user from JWT token.
    
    Args:
        token: JWT access token
        db: Database session
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    payload = verify_token(token, "access")
    
    # Get user ID from token
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    try:
        user_id = int(user_id)
    except ValueError:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


def create_tokens_for_user(user: User) -> Dict[str, str]:
    """
    Create both access and refresh tokens for a user.
    
    Args:
        user: User object
        
    Returns:
        Dictionary containing access_token and refresh_token
    """
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.name,
        "subscription_tier": user.subscription_tier.value
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


def refresh_access_token(refresh_token: str, db: Session) -> Dict[str, str]:
    """
    Create new access token using refresh token.
    
    Args:
        refresh_token: JWT refresh token
        db: Database session
        
    Returns:
        Dictionary containing new access_token
        
    Raises:
        HTTPException: If refresh token is invalid or user not found
    """
    payload = verify_token(refresh_token, "refresh")
    
    # Get user ID from refresh token
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    try:
        user_id = int(user_id)
    except ValueError:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception
    
    # Create new access token
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.name,
        "subscription_tier": user.subscription_tier.value
    }
    
    access_token = create_access_token(token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


def validate_jwt_secret() -> None:
    """
    Validate JWT secret key configuration.
    
    Raises:
        ValueError: If secret key is not properly configured
    """
    if SECRET_KEY == "your-secret-key-here":
        raise ValueError(
            "JWT_SECRET_KEY environment variable must be set to a secure secret key"
        )
    
    if len(SECRET_KEY) < 32:
        raise ValueError(
            "JWT_SECRET_KEY must be at least 32 characters long"
        )