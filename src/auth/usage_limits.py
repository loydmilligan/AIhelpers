"""
Usage limit checking and enforcement utilities.

Provides middleware and utility functions for enforcing subscription tier
usage limits across the AIhelpers platform.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models.user import User, SubscriptionTier
from ..config.database import get_db_session
from ..services.subscription_service import SubscriptionService, UsageLimitError
from .dependencies import require_auth


class UsageLimitExceeded(HTTPException):
    """HTTP exception for usage limit violations with helpful error messages."""
    
    def __init__(self, message: str, tier: SubscriptionTier, limit_type: str, current_usage: int, limit: int):
        self.tier = tier
        self.limit_type = limit_type
        self.current_usage = current_usage
        self.limit = limit
        
        # Create detailed error message with upgrade suggestion
        upgrade_message = self._get_upgrade_message(tier)
        
        detail = {
            "error": "usage_limit_exceeded",
            "message": message,
            "current_usage": current_usage,
            "limit": limit,
            "limit_type": limit_type,
            "tier": tier.value,
            "upgrade_suggestion": upgrade_message
        }
        
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=detail
        )
    
    def _get_upgrade_message(self, tier: SubscriptionTier) -> str:
        """Get appropriate upgrade suggestion based on current tier."""
        if tier == SubscriptionTier.FREE:
            return (
                "Upgrade to PROFESSIONAL ($19/month) for unlimited prompts and briefs, "
                "or TEAM ($49/month) for unlimited access plus team collaboration features."
            )
        elif tier == SubscriptionTier.PROFESSIONAL:
            return (
                "Upgrade to TEAM ($49/month) for unlimited access plus team collaboration features."
            )
        else:
            return "Contact support for enterprise solutions."


def check_monthly_limits(action_type: str) -> Callable:
    """
    Create a dependency that checks monthly usage limits for a specific action.
    
    Args:
        action_type: Type of action to check ('prompt', 'brief', 'validation')
        
    Returns:
        Dependency function that checks usage limits
    """
    def check_limits(
        user: User = Depends(require_auth),
        db: Session = Depends(get_db_session)
    ) -> User:
        """
        Check if user can perform the specified action within their usage limits.
        
        Args:
            user: Authenticated user
            db: Database session
            
        Returns:
            User object if limits allow the action
            
        Raises:
            UsageLimitExceeded: If usage limit is exceeded
        """
        try:
            service = SubscriptionService(db)
            can_perform, error_message = service.check_usage_limits(user, action_type)
            
            if not can_perform:
                # Get detailed usage stats for error
                current_date = datetime.now(timezone.utc)
                month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                usage_stats = service.get_usage_statistics(user.id, month_start, current_date)
                
                # Get the relevant usage count and limit
                tier_limits = service.USAGE_LIMITS.get(user.subscription_tier, {})
                
                if action_type == "prompt":
                    current_usage = usage_stats.get("prompts_generated", 0)
                    limit = tier_limits.get("monthly_prompts", 0)
                elif action_type == "brief":
                    current_usage = usage_stats.get("briefs_processed", 0)
                    limit = tier_limits.get("monthly_briefs", 0)
                elif action_type == "validation":
                    current_usage = usage_stats.get("briefs_validated", 0)
                    limit = tier_limits.get("monthly_validations", 0)
                else:
                    current_usage = 0
                    limit = 0
                
                raise UsageLimitExceeded(
                    message=error_message,
                    tier=user.subscription_tier,
                    limit_type=action_type,
                    current_usage=current_usage,
                    limit=limit
                )
            
            return user
            
        except UsageLimitError as e:
            raise UsageLimitExceeded(
                message=e.message,
                tier=e.tier,
                limit_type=e.limit_type,
                current_usage=e.current_usage,
                limit=e.limit
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error checking usage limits: {str(e)}"
            )
    
    return check_limits


def get_usage_stats(
    user: User = Depends(require_auth),
    db: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Dependency that returns current month usage statistics for the user.
    
    Args:
        user: Authenticated user
        db: Database session
        
    Returns:
        Dictionary containing usage statistics
    """
    try:
        service = SubscriptionService(db)
        current_date = datetime.now(timezone.utc)
        month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        usage_stats = service.get_usage_statistics(user.id, month_start, current_date)
        tier_limits = service.USAGE_LIMITS.get(user.subscription_tier, {})
        
        return {
            "user_id": user.id,
            "subscription_tier": user.subscription_tier.value,
            "month_start": month_start.isoformat(),
            "current_usage": usage_stats,
            "tier_limits": tier_limits,
            "remaining_usage": _calculate_remaining_usage(usage_stats, tier_limits)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting usage statistics: {str(e)}"
        )


def usage_limit_middleware(action_type: str):
    """
    Create a middleware function for usage limit checking.
    
    Args:
        action_type: Type of action to check
        
    Returns:
        Middleware function
    """
    return check_monthly_limits(action_type)


def track_usage_after_success(
    action_type: str,
    context_data: Optional[Dict[str, Any]] = None
) -> Callable:
    """
    Create a dependency that tracks usage after successful operation.
    
    Args:
        action_type: Type of action to track
        context_data: Additional context data to store
        
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
        try:
            service = SubscriptionService(db)
            
            # Map action types to activity types
            activity_type_map = {
                "prompt": "prompt_generated",
                "brief": "brief_processed",
                "validation": "brief_validated"
            }
            
            activity_type = activity_type_map.get(action_type, action_type)
            service.increment_usage(user.id, activity_type, context_data)
            
        except Exception as e:
            # Don't fail the main operation if tracking fails
            print(f"Warning: Failed to track usage for user {user.id}: {str(e)}")
    
    return track_usage


def get_usage_response(tier: SubscriptionTier, action_type: str, current: int, limit: int) -> Dict[str, Any]:
    """
    Generate a helpful error response for usage limit violations.
    
    Args:
        tier: User's subscription tier
        action_type: Type of action that was limited
        current: Current usage count
        limit: Usage limit
        
    Returns:
        Dictionary containing error details and upgrade suggestions
    """
    action_names = {
        "prompt": "prompt generations",
        "brief": "brief processing",
        "validation": "brief validations"
    }
    
    action_name = action_names.get(action_type, action_type)
    
    # Generate tier-specific upgrade suggestions
    if tier == SubscriptionTier.FREE:
        upgrade_options = [
            {
                "tier": "PROFESSIONAL",
                "price": "$19/month",
                "benefits": [
                    "Unlimited prompt generations",
                    "Unlimited brief processing",
                    "Priority support",
                    "Advanced analytics"
                ]
            },
            {
                "tier": "TEAM",
                "price": "$49/month",
                "benefits": [
                    "Everything in PROFESSIONAL",
                    "Team collaboration features",
                    "Shared workspaces",
                    "Admin controls"
                ]
            }
        ]
    elif tier == SubscriptionTier.PROFESSIONAL:
        upgrade_options = [
            {
                "tier": "TEAM",
                "price": "$49/month",
                "benefits": [
                    "Team collaboration features",
                    "Shared workspaces",
                    "Admin controls",
                    "Priority support"
                ]
            }
        ]
    else:
        upgrade_options = []
    
    return {
        "error": "usage_limit_exceeded",
        "message": f"Monthly limit exceeded: {current}/{limit} {action_name} used this month",
        "current_tier": tier.value,
        "current_usage": current,
        "limit": limit,
        "action_type": action_type,
        "upgrade_options": upgrade_options,
        "reset_date": _get_next_month_reset_date().isoformat()
    }


def _calculate_remaining_usage(usage_stats: Dict[str, int], tier_limits: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate remaining usage for each action type.
    
    Args:
        usage_stats: Current usage statistics
        tier_limits: Tier limits configuration
        
    Returns:
        Dictionary containing remaining usage counts
    """
    remaining = {}
    
    # Calculate remaining for each limit type
    for limit_key, limit_value in tier_limits.items():
        if limit_key == "monthly_prompts":
            current = usage_stats.get("prompts_generated", 0)
            usage_key = "prompts_generated"
        elif limit_key == "monthly_briefs":
            current = usage_stats.get("briefs_processed", 0)
            usage_key = "briefs_processed"
        elif limit_key == "monthly_validations":
            current = usage_stats.get("briefs_validated", 0)
            usage_key = "briefs_validated"
        else:
            continue
        
        if isinstance(limit_value, int):
            remaining[usage_key] = max(0, limit_value - current)
        else:
            remaining[usage_key] = "unlimited"
    
    return remaining


def _get_next_month_reset_date() -> datetime:
    """
    Get the date when usage limits will reset (first day of next month).
    
    Returns:
        Datetime object for next month's first day
    """
    current_date = datetime.now(timezone.utc)
    
    # Calculate next month
    if current_date.month == 12:
        next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
    else:
        next_month = current_date.replace(month=current_date.month + 1, day=1)
    
    return next_month.replace(hour=0, minute=0, second=0, microsecond=0)


# Convenience dependencies for specific action types
check_prompt_limit = check_monthly_limits("prompt")
check_brief_limit = check_monthly_limits("brief")
check_validation_limit = check_monthly_limits("validation")

# Usage tracking dependencies
track_prompt_usage = track_usage_after_success("prompt")
track_brief_usage = track_usage_after_success("brief")
track_validation_usage = track_usage_after_success("validation")