"""
Prompt model for storing and managing AI prompts.

Handles prompt storage, versioning, categorization, and metadata.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Any, Dict
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class PromptCategory(str, Enum):
    """Prompt category enumeration."""
    CODING = "coding"
    ANALYSIS = "analysis"
    DOCUMENTATION = "documentation"
    DEBUGGING = "debugging"
    TESTING = "testing"
    REFACTORING = "refactoring"
    REVIEW = "review"
    PLANNING = "planning"
    GENERAL = "general"


class Prompt(BaseModel):
    """
    Prompt model for storing AI prompts with versioning and metadata.
    
    Attributes:
        title: Prompt title
        content: Current prompt content
        category: Prompt category
        tags: JSON array of tags for categorization
        description: Optional description of the prompt
        owner_id: Foreign key to the user who owns this prompt
        team_id: Optional foreign key to team if shared
        version: Current version number
        is_active: Whether the prompt is active
        is_public: Whether the prompt is publicly shareable
        usage_count: Number of times this prompt has been used
        effectiveness_score: AI-calculated effectiveness score
        owner: Relationship to the owning user
        team: Relationship to the owning team (if any)
        versions: Relationship to prompt versions
        analytics: Relationship to prompt analytics
    """
    
    __tablename__ = "prompts"
    
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[PromptCategory] = mapped_column(
        String(50), 
        default=PromptCategory.GENERAL,
        index=True,
        nullable=False
    )
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    description: Mapped[Optional[str]] = mapped_column(Text)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    team_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teams.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    effectiveness_score: Mapped[Optional[float]] = mapped_column()
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="prompts")
    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="prompts")
    versions: Mapped[List["PromptVersion"]] = relationship(
        "PromptVersion",
        back_populates="prompt",
        cascade="all, delete-orphan",
        order_by="PromptVersion.version_number.desc()"
    )
    analytics: Mapped[Optional["PromptAnalytics"]] = relationship(
        "PromptAnalytics",
        back_populates="prompt",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_prompts_owner_category", "owner_id", "category"),
        Index("ix_prompts_team_category", "team_id", "category"),
        Index("ix_prompts_public_category", "is_public", "category"),
        Index("ix_prompts_usage_effectiveness", "usage_count", "effectiveness_score"),
        Index("ix_prompts_created_at_active", "created_at", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<Prompt(id={self.id}, title='{self.title}', version={self.version})>"
    
    def create_version(self, content: str, user_id: int) -> "PromptVersion":
        """Create a new version of this prompt."""
        new_version = PromptVersion(
            prompt_id=self.id,
            content=content,
            version_number=self.version + 1,
            created_by=user_id
        )
        self.version += 1
        self.content = content
        return new_version
    
    def increment_usage(self) -> None:
        """Increment usage count."""
        self.usage_count += 1
    
    def get_tags_list(self) -> List[str]:
        """Get tags as a list."""
        return self.tags or []
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the prompt."""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the prompt."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)


class PromptVersion(BaseModel):
    """
    Prompt version model for tracking prompt history.
    
    Attributes:
        prompt_id: Foreign key to the parent prompt
        content: Version content
        version_number: Version number
        created_by: User ID who created this version
        prompt: Relationship to the parent prompt
    """
    
    __tablename__ = "prompt_versions"
    
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Relationships
    prompt: Mapped["Prompt"] = relationship("Prompt", back_populates="versions")
    
    # Indexes
    __table_args__ = (
        Index("ix_prompt_versions_prompt_version", "prompt_id", "version_number"),
        Index("ix_prompt_versions_created_by", "created_by"),
    )
    
    def __repr__(self) -> str:
        return f"<PromptVersion(id={self.id}, prompt_id={self.prompt_id}, version={self.version_number})>"