"""
Session context model for preserving AI session state.

Handles storing and retrieving AI session contexts across different tools.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Text, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class SessionContext(BaseModel):
    """
    Session context model for preserving AI session state.
    
    Attributes:
        user_id: Foreign key to the user who owns this context
        ai_tool: Name of the AI tool (e.g., 'claude-code', 'cursor', 'chatgpt')
        context_data: JSON data containing the session context
        metadata: Additional metadata about the session
        title: Optional title for the session
        description: Optional description of the session
        tags: Optional tags for categorization
        user: Relationship to the owning user
        snapshots: Relationship to context snapshots
    """
    
    __tablename__ = "session_contexts"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    ai_tool: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    context_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    session_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    title: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="session_contexts")
    snapshots: Mapped[List["ContextSnapshot"]] = relationship(
        "ContextSnapshot",
        back_populates="session_context",
        cascade="all, delete-orphan",
        order_by="ContextSnapshot.created_at.desc()"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_session_contexts_user_tool", "user_id", "ai_tool"),
        Index("ix_session_contexts_tool_created", "ai_tool", "created_at"),
        Index("ix_session_contexts_user_created", "user_id", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<SessionContext(id={self.id}, user_id={self.user_id}, tool='{self.ai_tool}')>"
    
    def create_snapshot(self, snapshot_data: Dict[str, Any], description: Optional[str] = None) -> "ContextSnapshot":
        """Create a snapshot of the current context."""
        snapshot = ContextSnapshot(
            session_context_id=self.id,
            snapshot_data=snapshot_data,
            description=description
        )
        return snapshot
    
    def get_context_size(self) -> int:
        """Get the approximate size of the context data."""
        import json
        return len(json.dumps(self.context_data, default=str))
    
    def get_tags_list(self) -> List[str]:
        """Get tags as a list."""
        return self.tags or []
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the context."""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the context."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)


class ContextSnapshot(BaseModel):
    """
    Context snapshot model for tracking context changes over time.
    
    Attributes:
        session_context_id: Foreign key to the parent session context
        snapshot_data: JSON data containing the snapshot
        description: Optional description of the snapshot
        session_context: Relationship to the parent session context
    """
    
    __tablename__ = "context_snapshots"
    
    session_context_id: Mapped[int] = mapped_column(
        ForeignKey("session_contexts.id"), 
        nullable=False, 
        index=True
    )
    snapshot_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    session_context: Mapped["SessionContext"] = relationship(
        "SessionContext", 
        back_populates="snapshots"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_context_snapshots_session_created", "session_context_id", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<ContextSnapshot(id={self.id}, session_id={self.session_context_id})>"
    
    def get_snapshot_size(self) -> int:
        """Get the approximate size of the snapshot data."""
        import json
        return len(json.dumps(self.snapshot_data, default=str))