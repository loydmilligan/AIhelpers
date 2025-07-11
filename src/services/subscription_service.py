"""
Subscription management service with usage limit enforcement.

Handles subscription tier management, usage tracking, and limit enforcement
for the AIhelpers platform freemium model.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.user import User, SubscriptionTier
from ..models.analytics import UsageMetrics, UserActivity


class UsageLimitError(Exception):
    """Exception raised when usage limits are exceeded."""
    
    def __init__(self, message: str, tier: SubscriptionTier, limit_type: str, current_usage: int, limit: int):
        self.message = message
        self.tier = tier
        self.limit_type = limit_type
        self.current_usage = current_usage
        self.limit = limit
        super().__init__(self.message)


class SubscriptionService:
    """
    Service for managing user subscriptions and usage limits.
    
    Provides methods for checking usage limits, managing subscription tiers,
    and tracking usage statistics with monthly reset functionality.
    """
    
    # Define usage limits per tier
    USAGE_LIMITS = {
        SubscriptionTier.FREE: {
            "monthly_prompts": 50,
            "monthly_briefs": 10,
            "monthly_validations": 20,
            "team_creation": False,
            "advanced_features": False
        },
        SubscriptionTier.PROFESSIONAL: {
            "monthly_prompts": "unlimited",
            "monthly_briefs": "unlimited",
            "monthly_validations": "unlimited",
            "team_creation": False,
            "advanced_features": True
        },
        SubscriptionTier.TEAM: {
            "monthly_prompts": "unlimited",
            "monthly_briefs": "unlimited",
            "monthly_validations": "unlimited",
            "team_creation": True,
            "advanced_features": True
        }
    }
    
    def __init__(self, db: Session):
        """
        Initialize subscription service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_subscription_status(self, user: User) -> Dict[str, Any]:
        """
        Get current subscription status and usage statistics.
        
        Args:
            user: User object
            
        Returns:
            Dictionary containing subscription status and usage stats
        """
        current_date = datetime.now(timezone.utc)
        month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get usage statistics for current month
        usage_stats = self.get_usage_statistics(user.id, month_start, current_date)
        
        # Get tier limits
        tier_limits = self.USAGE_LIMITS.get(user.subscription_tier, {})
        
        return {
            "user_id": user.id,
            "subscription_tier": user.subscription_tier.value,
            "is_premium": user.is_premium(),
            "can_create_teams": user.can_create_teams(),
            "tier_limits": tier_limits,
            "current_usage": usage_stats,
            "month_start": month_start.isoformat(),
            "subscription_active": user.is_active
        }
    
    def change_subscription_tier(self, user: User, new_tier: SubscriptionTier) -> Dict[str, Any]:
        """
        Change user's subscription tier with validation.
        
        Args:
            user: User object
            new_tier: New subscription tier
            
        Returns:
            Dictionary containing change confirmation
            
        Raises:
            HTTPException: If tier change is invalid
        """
        old_tier = user.subscription_tier
        
        # Validate tier change
        if old_tier == new_tier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User is already on {new_tier.value} tier"
            )
        
        # Update subscription tier
        user.subscription_tier = new_tier
        
        # Log the subscription change
        self._track_subscription_change(user.id, old_tier, new_tier)
        
        try:
            self.db.commit()
            self.db.refresh(user)
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update subscription: {str(e)}"
            )
        
        return {
            "success": True,
            "message": f"Subscription changed from {old_tier.value} to {new_tier.value}",
            "old_tier": old_tier.value,
            "new_tier": new_tier.value,
            "changed_at": datetime.now(timezone.utc).isoformat(),
            "immediate_effect": True
        }
    
    def get_usage_statistics(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, int]:
        """
        Get detailed usage statistics for a user within a date range.
        
        Args:
            user_id: User ID
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            Dictionary containing usage counts by type
        """
        # Get activity counts by type
        activity_counts = (
            self.db.query(
                UserActivity.activity_type,
                func.count(UserActivity.id).label('count')
            )
            .filter(
                and_(
                    UserActivity.user_id == user_id,
                    UserActivity.timestamp >= start_date,
                    UserActivity.timestamp <= end_date
                )
            )
            .group_by(UserActivity.activity_type)
            .all()
        )
        
        # Convert to dictionary with relevant usage types
        usage_stats = {
            "prompts_generated": 0,
            "briefs_processed": 0,
            "briefs_validated": 0,
            "total_activities": 0
        }
        
        for activity_type, count in activity_counts:
            if activity_type == "prompt_generated":
                usage_stats["prompts_generated"] = count
            elif activity_type == "brief_processed":
                usage_stats["briefs_processed"] = count
            elif activity_type == "brief_validated":
                usage_stats["briefs_validated"] = count
            usage_stats["total_activities"] += count
        
        return usage_stats
    
    def check_usage_limits(self, user: User, action_type: str) -> Tuple[bool, Optional[str]]:
        """
        Check if user can perform an action based on usage limits.
        
        Args:
            user: User object
            action_type: Type of action ('prompt', 'brief', 'validation')
            
        Returns:
            Tuple of (can_perform_action, error_message)
        """
        # Premium users have unlimited access
        if user.is_premium():
            return True, None
        
        # Get current month usage
        current_date = datetime.now(timezone.utc)
        month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        usage_stats = self.get_usage_statistics(user.id, month_start, current_date)
        
        # Check limits based on action type
        tier_limits = self.USAGE_LIMITS.get(user.subscription_tier, {})
        
        if action_type == "prompt":
            limit = tier_limits.get("monthly_prompts", 0)
            current = usage_stats.get("prompts_generated", 0)
            limit_name = "monthly prompt generations"
        elif action_type == "brief":
            limit = tier_limits.get("monthly_briefs", 0)
            current = usage_stats.get("briefs_processed", 0)
            limit_name = "monthly brief processing"
        elif action_type == "validation":
            limit = tier_limits.get("monthly_validations", 0)
            current = usage_stats.get("briefs_validated", 0)
            limit_name = "monthly brief validations"
        else:
            return False, f"Unknown action type: {action_type}"
        
        # Check if limit is exceeded
        if isinstance(limit, int) and current >= limit:
            error_msg = (
                f"Monthly limit exceeded: {current}/{limit} {limit_name} used. "
                f"Upgrade to PROFESSIONAL for unlimited access."
            )
            return False, error_msg
        
        return True, None
    
    def increment_usage(self, user_id: int, activity_type: str, context_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Track usage by creating a user activity record.
        
        Args:
            user_id: User ID
            activity_type: Type of activity to track
            context_data: Optional context data for the activity
        """
        try:
            # Create user activity record
            activity = UserActivity.create_activity(
                user_id=user_id,
                activity_type=activity_type,
                data=context_data or {}
            )
            
            self.db.add(activity)
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            # Don't fail the main operation if usage tracking fails
            print(f"Warning: Failed to track usage for user {user_id}: {str(e)}")
    
    def _track_subscription_change(self, user_id: int, old_tier: SubscriptionTier, new_tier: SubscriptionTier) -> None:
        """
        Track subscription tier changes for audit purposes.
        
        Args:
            user_id: User ID
            old_tier: Previous subscription tier
            new_tier: New subscription tier
        """
        try:
            # Create activity record for subscription change
            activity = UserActivity.create_activity(
                user_id=user_id,
                activity_type="subscription_changed",
                data={
                    "old_tier": old_tier.value,
                    "new_tier": new_tier.value,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
            self.db.add(activity)
            
            # Create usage metric record
            metric = UsageMetrics.create_metric(
                metric_name="subscription_change",
                metric_value=1,
                user_id=user_id,
                metric_data={
                    "old_tier": old_tier.value,
                    "new_tier": new_tier.value,
                    "change_type": "upgrade" if self._is_upgrade(old_tier, new_tier) else "downgrade"
                }
            )
            
            self.db.add(metric)
            
        except Exception as e:
            # Don't fail the main operation if tracking fails
            print(f"Warning: Failed to track subscription change for user {user_id}: {str(e)}")
    
    def _is_upgrade(self, old_tier: SubscriptionTier, new_tier: SubscriptionTier) -> bool:
        """
        Determine if subscription change is an upgrade.
        
        Args:
            old_tier: Previous subscription tier
            new_tier: New subscription tier
            
        Returns:
            True if it's an upgrade, False if downgrade
        """
        tier_levels = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.PROFESSIONAL: 1,
            SubscriptionTier.TEAM: 2
        }
        
        return tier_levels.get(new_tier, 0) > tier_levels.get(old_tier, 0)


def check_usage_limits(user: User, action_type: str, db: Session) -> None:
    """
    Utility function to check usage limits and raise exception if exceeded.
    
    Args:
        user: User object
        action_type: Type of action to check
        db: Database session
        
    Raises:
        UsageLimitError: If usage limit is exceeded
    """
    service = SubscriptionService(db)
    can_perform, error_message = service.check_usage_limits(user, action_type)
    
    if not can_perform:
        # Get current usage stats for the error
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
        
        raise UsageLimitError(
            message=error_message,
            tier=user.subscription_tier,
            limit_type=action_type,
            current_usage=current_usage,
            limit=limit
        )