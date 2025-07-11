"""
Pydantic schemas for subscription management requests and responses.

Defines data models for subscription tier management, usage statistics,
and subscription change operations.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

from ..models.user import SubscriptionTier


class SubscriptionChangeRequest(BaseModel):
    """Request model for changing subscription tier."""
    
    new_tier: SubscriptionTier = Field(
        ...,
        description="New subscription tier to change to"
    )
    
    @validator('new_tier')
    def validate_tier(cls, v):
        """Validate that the tier is a valid subscription tier."""
        if v not in SubscriptionTier:
            raise ValueError(f"Invalid subscription tier: {v}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "new_tier": "professional"
            }
        }


class UsageStatistics(BaseModel):
    """Model for usage statistics data."""
    
    prompts_generated: int = Field(
        default=0,
        description="Number of prompts generated this month"
    )
    briefs_processed: int = Field(
        default=0,
        description="Number of briefs processed this month"
    )
    briefs_validated: int = Field(
        default=0,
        description="Number of briefs validated this month"
    )
    total_activities: int = Field(
        default=0,
        description="Total number of activities this month"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "prompts_generated": 25,
                "briefs_processed": 5,
                "briefs_validated": 8,
                "total_activities": 38
            }
        }


class TierLimits(BaseModel):
    """Model for subscription tier limits."""
    
    monthly_prompts: Union[int, str] = Field(
        ...,
        description="Monthly prompt generation limit ('unlimited' for premium tiers)"
    )
    monthly_briefs: Union[int, str] = Field(
        ...,
        description="Monthly brief processing limit ('unlimited' for premium tiers)"
    )
    monthly_validations: Union[int, str] = Field(
        ...,
        description="Monthly brief validation limit ('unlimited' for premium tiers)"
    )
    team_creation: bool = Field(
        ...,
        description="Whether user can create teams"
    )
    advanced_features: bool = Field(
        ...,
        description="Whether user has access to advanced features"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "monthly_prompts": 50,
                "monthly_briefs": 10,
                "monthly_validations": 20,
                "team_creation": False,
                "advanced_features": False
            }
        }


class RemainingUsage(BaseModel):
    """Model for remaining usage counts."""
    
    prompts_generated: Union[int, str] = Field(
        ...,
        description="Remaining prompt generations ('unlimited' for premium tiers)"
    )
    briefs_processed: Union[int, str] = Field(
        ...,
        description="Remaining brief processing ('unlimited' for premium tiers)"
    )
    briefs_validated: Union[int, str] = Field(
        ...,
        description="Remaining brief validations ('unlimited' for premium tiers)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "prompts_generated": 25,
                "briefs_processed": 5,
                "briefs_validated": 12
            }
        }


class SubscriptionStatusResponse(BaseModel):
    """Response model for subscription status information."""
    
    user_id: int = Field(
        ...,
        description="User ID"
    )
    subscription_tier: str = Field(
        ...,
        description="Current subscription tier"
    )
    is_premium: bool = Field(
        ...,
        description="Whether user has premium subscription"
    )
    can_create_teams: bool = Field(
        ...,
        description="Whether user can create teams"
    )
    tier_limits: TierLimits = Field(
        ...,
        description="Usage limits for current tier"
    )
    current_usage: UsageStatistics = Field(
        ...,
        description="Current month usage statistics"
    )
    remaining_usage: RemainingUsage = Field(
        ...,
        description="Remaining usage for current month"
    )
    month_start: str = Field(
        ...,
        description="Start of current billing month (ISO format)"
    )
    subscription_active: bool = Field(
        ...,
        description="Whether subscription is active"
    )
    next_reset_date: str = Field(
        ...,
        description="When usage limits will reset (ISO format)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "subscription_tier": "free",
                "is_premium": False,
                "can_create_teams": False,
                "tier_limits": {
                    "monthly_prompts": 50,
                    "monthly_briefs": 10,
                    "monthly_validations": 20,
                    "team_creation": False,
                    "advanced_features": False
                },
                "current_usage": {
                    "prompts_generated": 25,
                    "briefs_processed": 5,
                    "briefs_validated": 8,
                    "total_activities": 38
                },
                "remaining_usage": {
                    "prompts_generated": 25,
                    "briefs_processed": 5,
                    "briefs_validated": 12
                },
                "month_start": "2025-01-01T00:00:00+00:00",
                "subscription_active": True,
                "next_reset_date": "2025-02-01T00:00:00+00:00"
            }
        }


class SubscriptionChangeResponse(BaseModel):
    """Response model for subscription tier changes."""
    
    success: bool = Field(
        ...,
        description="Whether the subscription change was successful"
    )
    message: str = Field(
        ...,
        description="Success or error message"
    )
    old_tier: str = Field(
        ...,
        description="Previous subscription tier"
    )
    new_tier: str = Field(
        ...,
        description="New subscription tier"
    )
    changed_at: str = Field(
        ...,
        description="When the change occurred (ISO format)"
    )
    immediate_effect: bool = Field(
        ...,
        description="Whether the change takes immediate effect"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Subscription changed from free to professional",
                "old_tier": "free",
                "new_tier": "professional",
                "changed_at": "2025-01-11T22:30:00+00:00",
                "immediate_effect": True
            }
        }


class UsageStatsResponse(BaseModel):
    """Response model for detailed usage statistics."""
    
    user_id: int = Field(
        ...,
        description="User ID"
    )
    subscription_tier: str = Field(
        ...,
        description="Current subscription tier"
    )
    month_start: str = Field(
        ...,
        description="Start of current billing month (ISO format)"
    )
    current_usage: UsageStatistics = Field(
        ...,
        description="Current month usage statistics"
    )
    tier_limits: TierLimits = Field(
        ...,
        description="Usage limits for current tier"
    )
    remaining_usage: RemainingUsage = Field(
        ...,
        description="Remaining usage for current month"
    )
    usage_percentage: Dict[str, Union[float, str]] = Field(
        ...,
        description="Percentage of limits used for each action type"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "subscription_tier": "free",
                "month_start": "2025-01-01T00:00:00+00:00",
                "current_usage": {
                    "prompts_generated": 25,
                    "briefs_processed": 5,
                    "briefs_validated": 8,
                    "total_activities": 38
                },
                "tier_limits": {
                    "monthly_prompts": 50,
                    "monthly_briefs": 10,
                    "monthly_validations": 20,
                    "team_creation": False,
                    "advanced_features": False
                },
                "remaining_usage": {
                    "prompts_generated": 25,
                    "briefs_processed": 5,
                    "briefs_validated": 12
                },
                "usage_percentage": {
                    "prompts_generated": 50.0,
                    "briefs_processed": 50.0,
                    "briefs_validated": 40.0
                }
            }
        }


class UpgradeOption(BaseModel):
    """Model for subscription upgrade options."""
    
    tier: str = Field(
        ...,
        description="Subscription tier name"
    )
    price: str = Field(
        ...,
        description="Monthly price"
    )
    benefits: List[str] = Field(
        ...,
        description="List of benefits for this tier"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "tier": "PROFESSIONAL",
                "price": "$19/month",
                "benefits": [
                    "Unlimited prompt generations",
                    "Unlimited brief processing",
                    "Priority support",
                    "Advanced analytics"
                ]
            }
        }


class UsageLimitExceededResponse(BaseModel):
    """Response model for usage limit exceeded errors."""
    
    error: str = Field(
        default="usage_limit_exceeded",
        description="Error type identifier"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    current_tier: str = Field(
        ...,
        description="User's current subscription tier"
    )
    current_usage: int = Field(
        ...,
        description="Current usage count for the action"
    )
    limit: int = Field(
        ...,
        description="Usage limit for the action"
    )
    action_type: str = Field(
        ...,
        description="Type of action that was limited"
    )
    upgrade_options: List[UpgradeOption] = Field(
        ...,
        description="Available upgrade options"
    )
    reset_date: str = Field(
        ...,
        description="When usage limits will reset (ISO format)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "error": "usage_limit_exceeded",
                "message": "Monthly limit exceeded: 50/50 prompt generations used this month",
                "current_tier": "free",
                "current_usage": 50,
                "limit": 50,
                "action_type": "prompt",
                "upgrade_options": [
                    {
                        "tier": "PROFESSIONAL",
                        "price": "$19/month",
                        "benefits": [
                            "Unlimited prompt generations",
                            "Unlimited brief processing",
                            "Priority support",
                            "Advanced analytics"
                        ]
                    }
                ],
                "reset_date": "2025-02-01T00:00:00+00:00"
            }
        }


class SubscriptionHealthResponse(BaseModel):
    """Response model for subscription system health check."""
    
    healthy: bool = Field(
        ...,
        description="Whether subscription system is healthy"
    )
    message: str = Field(
        ...,
        description="Health status message"
    )
    services_status: Dict[str, bool] = Field(
        ...,
        description="Status of individual subscription services"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "healthy": True,
                "message": "Subscription system is operational",
                "services_status": {
                    "usage_tracking": True,
                    "limit_enforcement": True,
                    "tier_management": True
                }
            }
        }