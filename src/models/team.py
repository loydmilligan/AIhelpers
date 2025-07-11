"""
Team model for collaboration and shared resources.

Handles team creation, membership, and role management.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from sqlalchemy import Column, String, ForeignKey, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel
from .user import SubscriptionTier


class TeamRole(str, Enum):
    """Team role enumeration."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Team(BaseModel):
    """
    Team model for collaboration and shared resources.
    
    Attributes:
        name: Team name
        description: Optional team description
        owner_id: Foreign key to the user who owns this team
        subscription_tier: Team's subscription level
        is_active: Whether the team is active
        max_members: Maximum number of members allowed
        owner: Relationship to the owning user
        members: Relationship to team members
        prompts: Relationship to team prompts
    """
    
    __tablename__ = "teams"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        String(20),
        default=SubscriptionTier.TEAM,
        index=True,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    max_members: Mapped[int] = mapped_column(default=10, nullable=False)
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="owned_teams")
    members: Mapped[List["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan"
    )
    prompts: Mapped[List["Prompt"]] = relationship(
        "Prompt",
        back_populates="team",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_teams_owner_active", "owner_id", "is_active"),
        Index("ix_teams_name_active", "name", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"
    
    def get_member_count(self) -> int:
        """Get the current number of team members."""
        return len(self.members)
    
    def can_add_member(self) -> bool:
        """Check if team can add more members."""
        return self.get_member_count() < self.max_members
    
    def get_member_by_user_id(self, user_id: int) -> Optional["TeamMember"]:
        """Get team member by user ID."""
        for member in self.members:
            if member.user_id == user_id:
                return member
        return None
    
    def is_member(self, user_id: int) -> bool:
        """Check if user is a member of this team."""
        return self.get_member_by_user_id(user_id) is not None
    
    def get_role(self, user_id: int) -> Optional[TeamRole]:
        """Get user's role in this team."""
        if user_id == self.owner_id:
            return TeamRole.OWNER
        member = self.get_member_by_user_id(user_id)
        return member.role if member else None


class TeamMember(BaseModel):
    """
    Team member model for tracking user membership in teams.
    
    Attributes:
        user_id: Foreign key to the user
        team_id: Foreign key to the team
        role: User's role in the team
        joined_at: When the user joined the team
        invited_by: User ID who invited this member
        is_active: Whether the membership is active
        user: Relationship to the user
        team: Relationship to the team
    """
    
    __tablename__ = "team_members"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)
    role: Mapped[TeamRole] = mapped_column(
        String(20),
        default=TeamRole.MEMBER,
        nullable=False,
        index=True
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    invited_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="team_memberships", foreign_keys=[user_id])
    team: Mapped["Team"] = relationship("Team", back_populates="members")
    
    # Indexes
    __table_args__ = (
        Index("ix_team_members_user_team", "user_id", "team_id"),
        Index("ix_team_members_team_role", "team_id", "role"),
        Index("ix_team_members_active_joined", "is_active", "joined_at"),
    )
    
    def __repr__(self) -> str:
        return f"<TeamMember(id={self.id}, user_id={self.user_id}, team_id={self.team_id}, role='{self.role}')>"
    
    def can_manage_team(self) -> bool:
        """Check if member can manage team settings."""
        return self.role in (TeamRole.OWNER, TeamRole.ADMIN)
    
    def can_invite_members(self) -> bool:
        """Check if member can invite other members."""
        return self.role in (TeamRole.OWNER, TeamRole.ADMIN)
    
    def can_edit_prompts(self) -> bool:
        """Check if member can edit team prompts."""
        return self.role in (TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER)
    
    def can_view_prompts(self) -> bool:
        """Check if member can view team prompts."""
        return self.role in (TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)