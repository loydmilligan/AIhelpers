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


def require_usage_quota(action_type: str) -> Callable[[User, Session], User]:
    """
    Create a dependency that requires available usage quota for a specific action.
    
    Args:
        action_type: Type of action to check ('prompt', 'brief', 'validation')
        
    Returns:
        Dependency function that checks usage quota
    """
    def check_quota(
        user: User = Depends(require_auth),
        db: Session = Depends(get_db_session)
    ) -> User:
        """
        Check if user has available quota for the specified action.
        
        Args:
            user: Authenticated user
            db: Database session
            
        Returns:
            User object if quota is available
            
        Raises:
            HTTPException: If quota is exceeded
        """
        from ..services.subscription_service import SubscriptionService
        
        service = SubscriptionService(db)
        can_perform, error_message = service.check_usage_limits(user, action_type)
        
        if not can_perform:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "usage_limit_exceeded",
                    "message": error_message,
                    "action_type": action_type,
                    "tier": user.subscription_tier.value
                }
            )
        
        return user
    
    return check_quota


def get_usage_tracker(action_type: str) -> Callable[[User, Session], None]:
    """
    Create a dependency that tracks usage after successful operations.
    
    Args:
        action_type: Type of action to track
        
    Returns:
        Dependency function that tracks usage
    """
    def track_usage(
        user: User = Depends(require_auth),
        db: Session = Depends(get_db_session)
    ) -> None:
        """
        Track usage for the specified action type.
        
        Args:
            user: Authenticated user
            db: Database session
        """
        from ..services.subscription_service import SubscriptionService
        
        try:
            service = SubscriptionService(db)
            
            # Map action types to activity types
            activity_type_map = {
                "prompt": "prompt_generated",
                "brief": "brief_processed",
                "validation": "brief_validated"
            }
            
            activity_type = activity_type_map.get(action_type, action_type)
            service.increment_usage(user.id, activity_type)
            
        except Exception as e:
            # Don't fail the main operation if tracking fails
            print(f"Warning: Failed to track usage for user {user.id}: {str(e)}")
    
    return track_usage


def require_subscription_feature(feature: str) -> Callable[[User], User]:
    """
    Create a dependency that requires a specific subscription feature.
    
    Args:
        feature: Feature name to check ('team_creation', 'advanced_features')
        
    Returns:
        Dependency function that checks feature availability
    """
    def check_feature(user: User = Depends(require_auth)) -> User:
        """
        Check if user's subscription tier includes the required feature.
        
        Args:
            user: Authenticated user
            
        Returns:
            User object if feature is available
            
        Raises:
            HTTPException: If feature is not available in user's tier
        """
        from ..services.subscription_service import SubscriptionService
        
        tier_features = SubscriptionService.USAGE_LIMITS.get(user.subscription_tier, {})
        
        if not tier_features.get(feature, False):
            feature_names = {
                "team_creation": "team creation",
                "advanced_features": "advanced features"
            }
            
            feature_name = feature_names.get(feature, feature)
            
            if user.subscription_tier == SubscriptionTier.FREE:
                upgrade_suggestion = "Upgrade to PROFESSIONAL or TEAM tier"
            elif user.subscription_tier == SubscriptionTier.PROFESSIONAL and feature == "team_creation":
                upgrade_suggestion = "Upgrade to TEAM tier"
            else:
                upgrade_suggestion = "Contact support for feature access"
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "feature_not_available",
                    "message": f"{feature_name.title()} is not available in your current subscription tier",
                    "feature": feature,
                    "current_tier": user.subscription_tier.value,
                    "upgrade_suggestion": upgrade_suggestion
                }
            )
        
        return user
    
    return check_feature


# Convenience dependencies for common usage checks
require_prompt_quota = require_usage_quota("prompt")
require_brief_quota = require_usage_quota("brief")
require_validation_quota = require_usage_quota("validation")

# Feature-specific dependencies
require_team_creation = require_subscription_feature("team_creation")
require_advanced_features = require_subscription_feature("advanced_features")

# Usage tracking dependencies
track_prompt_usage = get_usage_tracker("prompt")
track_brief_usage = get_usage_tracker("brief")
track_validation_usage = get_usage_tracker("validation")