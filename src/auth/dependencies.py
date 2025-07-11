"""
FastAPI dependencies for authentication and authorization.

Provides dependency injection for authentication requirements.
"""

from typing import Optional, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..models.user import User, SubscriptionTier
from ..config.database import get_db_session
from .oauth2 import get_current_user


# HTTP Bearer token scheme
security = HTTPBearer()


def get_token_from_header(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Extract token from Authorization header.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        JWT token string
        
    Raises:
        HTTPException: If token is missing or invalid format
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials.credentials


def require_auth(
    token: str = Depends(get_token_from_header),
    db: Session = Depends(get_db_session)
) -> User:
    """
    Dependency that requires authentication.
    
    Args:
        token: JWT token from header
        db: Database session
        
    Returns:
        Authenticated user object
        
    Raises:
        HTTPException: If authentication fails
    """
    return get_current_user(token, db)


def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db_session)
) -> Optional[User]:
    """
    Dependency that provides optional authentication.
    
    Args:
        credentials: Optional HTTP authorization credentials
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials or not credentials.credentials:
        return None
    
    try:
        return get_current_user(credentials.credentials, db)
    except HTTPException:
        return None


def require_subscription_tier(tier: SubscriptionTier) -> Callable[[User], User]:
    """
    Create a dependency that requires a specific subscription tier.
    
    Args:
        tier: Minimum required subscription tier
        
    Returns:
        Dependency function that checks subscription tier
    """
    def check_subscription_tier(user: User = Depends(require_auth)) -> User:
        """
        Check if user has required subscription tier.
        
        Args:
            user: Authenticated user
            
        Returns:
            User object if tier requirement is met
            
        Raises:
            HTTPException: If user doesn't have required tier
        """
        tier_levels = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.PROFESSIONAL: 1,
            SubscriptionTier.TEAM: 2,
        }
        
        user_level = tier_levels.get(user.subscription_tier, 0)
        required_level = tier_levels.get(tier, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Subscription tier '{tier.value}' or higher required"
            )
        
        return user
    
    return check_subscription_tier


def require_free_tier(user: User = Depends(require_auth)) -> User:
    """
    Dependency that requires FREE tier (any authenticated user).
    
    Args:
        user: Authenticated user
        
    Returns:
        User object
    """
    return user


def require_professional_tier(user: User = Depends(require_subscription_tier(SubscriptionTier.PROFESSIONAL))) -> User:
    """
    Dependency that requires PROFESSIONAL tier or higher.
    
    Args:
        user: Authenticated user with professional tier
        
    Returns:
        User object
    """
    return user


def require_team_tier(user: User = Depends(require_subscription_tier(SubscriptionTier.TEAM))) -> User:
    """
    Dependency that requires TEAM tier.
    
    Args:
        user: Authenticated user with team tier
        
    Returns:
        User object
    """
    return user


def require_active_user(user: User = Depends(require_auth)) -> User:
    """
    Dependency that requires an active user account.
    
    Args:
        user: Authenticated user
        
    Returns:
        User object if active
        
    Raises:
        HTTPException: If user account is inactive
    """
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    return user


def require_premium_tier(user: User = Depends(require_auth)) -> User:
    """
    Dependency that requires premium subscription (PROFESSIONAL or TEAM).
    
    Args:
        user: Authenticated user
        
    Returns:
        User object if has premium subscription
        
    Raises:
        HTTPException: If user doesn't have premium subscription
    """
    if not user.is_premium():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required"
        )
    
    return user


def get_current_user_context(user: User = Depends(require_auth)) -> dict:
    """
    Get current user context for API responses.
    
    Args:
        user: Authenticated user
        
    Returns:
        Dictionary containing user context information
    """
    return {
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "subscription_tier": user.subscription_tier.value,
        "is_premium": user.is_premium(),
        "can_create_teams": user.can_create_teams(),
    }