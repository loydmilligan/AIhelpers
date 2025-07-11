"""
User model for authentication and profile management.

Handles user accounts, authentication, and subscription tiers.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class SubscriptionTier(str, Enum):
    """Subscription tier enumeration."""
    FREE = "free"
    PROFESSIONAL = "professional"
    TEAM = "team"


class User(BaseModel):
    """
    User model for authentication and profile management.
    
    Attributes:
        email: User's email address (unique)
        name: User's display name
        hashed_password: Hashed password for authentication
        subscription_tier: User's subscription level
        is_active: Whether the user account is active
        prompts: Relationship to user's prompts
        owned_teams: Relationship to teams owned by user
        team_memberships: Relationship to team memberships
        session_contexts: Relationship to user's session contexts
        activities: Relationship to user's activity logs
    """
    
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        SQLEnum(SubscriptionTier), 
        default=SubscriptionTier.FREE,
        index=True,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    prompts: Mapped[List["Prompt"]] = relationship(
        "Prompt", 
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    owned_teams: Mapped[List["Team"]] = relationship(
        "Team",
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    team_memberships: Mapped[List["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="[TeamMember.user_id]"
    )
    session_contexts: Mapped[List["SessionContext"]] = relationship(
        "SessionContext",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    activities: Mapped[List["UserActivity"]] = relationship(
        "UserActivity",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_users_subscription_tier_created_at", "subscription_tier", "created_at"),
        Index("ix_users_is_active_created_at", "is_active", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', tier='{self.subscription_tier}')>"
    
    def is_premium(self) -> bool:
        """Check if user has premium subscription."""
        return self.subscription_tier in (SubscriptionTier.PROFESSIONAL, SubscriptionTier.TEAM)
    
    def can_create_teams(self) -> bool:
        """Check if user can create teams."""
        return self.subscription_tier == SubscriptionTier.TEAM
    
    def to_dict(self) -> dict:
        """Convert to dictionary, excluding sensitive fields."""
        data = super().to_dict()
        # Remove sensitive fields
        data.pop('hashed_password', None)
        return data