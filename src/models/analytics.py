"""
Analytics model for tracking usage and performance metrics.

Handles user activity tracking, prompt analytics, and usage metrics.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Index, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class UserActivity(BaseModel):
    """
    User activity model for tracking user actions and behavior.
    
    Attributes:
        user_id: Foreign key to the user
        activity_type: Type of activity (e.g., 'prompt_created', 'prompt_used')
        data: JSON data containing activity details
        timestamp: When the activity occurred
        ip_address: Optional IP address of the user
        user_agent: Optional user agent string
        user: Relationship to the user
    """
    
    __tablename__ = "user_activities"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # Support IPv6
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="activities")
    
    # Indexes
    __table_args__ = (
        Index("ix_user_activities_user_type", "user_id", "activity_type"),
        Index("ix_user_activities_type_timestamp", "activity_type", "timestamp"),
        Index("ix_user_activities_user_timestamp", "user_id", "timestamp"),
    )
    
    def __repr__(self) -> str:
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, type='{self.activity_type}')>"
    
    @classmethod
    def create_activity(cls, user_id: int, activity_type: str, data: Optional[Dict[str, Any]] = None,
                       ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> "UserActivity":
        """Create a new user activity record."""
        return cls(
            user_id=user_id,
            activity_type=activity_type,
            data=data or {},
            ip_address=ip_address,
            user_agent=user_agent
        )


class PromptAnalytics(BaseModel):
    """
    Prompt analytics model for tracking prompt performance and usage.
    
    Attributes:
        prompt_id: Foreign key to the prompt
        usage_count: Number of times the prompt has been used
        effectiveness_score: AI-calculated effectiveness score (0-1)
        avg_response_time: Average response time in seconds
        success_rate: Success rate of prompt usage (0-1)
        user_ratings: JSON data containing user ratings
        last_used: When the prompt was last used
        prompt: Relationship to the prompt
    """
    
    __tablename__ = "prompt_analytics"
    
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id"), nullable=False, index=True, unique=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    effectiveness_score: Mapped[Optional[float]] = mapped_column(Float)
    avg_response_time: Mapped[Optional[float]] = mapped_column(Float)
    success_rate: Mapped[Optional[float]] = mapped_column(Float)
    user_ratings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    prompt: Mapped["Prompt"] = relationship("Prompt", back_populates="analytics")
    
    # Indexes
    __table_args__ = (
        Index("ix_prompt_analytics_usage_effectiveness", "usage_count", "effectiveness_score"),
        Index("ix_prompt_analytics_score_updated", "effectiveness_score", "updated_at"),
        Index("ix_prompt_analytics_last_used", "last_used"),
    )
    
    def __repr__(self) -> str:
        return f"<PromptAnalytics(id={self.id}, prompt_id={self.prompt_id}, usage={self.usage_count})>"
    
    def increment_usage(self, response_time: Optional[float] = None, success: bool = True) -> None:
        """Increment usage count and update metrics."""
        self.usage_count += 1
        self.last_used = datetime.utcnow()
        
        if response_time is not None:
            if self.avg_response_time is None:
                self.avg_response_time = response_time
            else:
                # Update running average
                self.avg_response_time = (self.avg_response_time * (self.usage_count - 1) + response_time) / self.usage_count
        
        if self.success_rate is None:
            self.success_rate = 1.0 if success else 0.0
        else:
            # Update running success rate
            total_successes = self.success_rate * (self.usage_count - 1)
            if success:
                total_successes += 1
            self.success_rate = total_successes / self.usage_count
    
    def add_user_rating(self, user_id: int, rating: float, comment: Optional[str] = None) -> None:
        """Add a user rating for this prompt."""
        if not self.user_ratings:
            self.user_ratings = {}
        
        self.user_ratings[str(user_id)] = {
            'rating': rating,
            'comment': comment,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_average_rating(self) -> Optional[float]:
        """Get the average user rating."""
        if not self.user_ratings:
            return None
        
        ratings = [r['rating'] for r in self.user_ratings.values() if isinstance(r, dict) and 'rating' in r]
        return sum(ratings) / len(ratings) if ratings else None


class UsageMetrics(BaseModel):
    """
    Usage metrics model for tracking system-wide usage statistics.
    
    Attributes:
        metric_name: Name of the metric (e.g., 'daily_active_users', 'prompts_created')
        metric_value: Numeric value of the metric
        metric_data: Optional JSON data with additional metric details
        date: Date for the metric (for time-series data)
        user_id: Optional user ID for user-specific metrics
        team_id: Optional team ID for team-specific metrics
    """
    
    __tablename__ = "usage_metrics"
    
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    metric_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)
    team_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teams.id"), index=True)
    
    # Indexes
    __table_args__ = (
        Index("ix_usage_metrics_name_date", "metric_name", "date"),
        Index("ix_usage_metrics_user_date", "user_id", "date"),
        Index("ix_usage_metrics_team_date", "team_id", "date"),
        Index("ix_usage_metrics_name_value", "metric_name", "metric_value"),
    )
    
    def __repr__(self) -> str:
        return f"<UsageMetrics(id={self.id}, metric='{self.metric_name}', value={self.metric_value})>"
    
    @classmethod
    def create_metric(cls, metric_name: str, metric_value: float, date: Optional[datetime] = None,
                     user_id: Optional[int] = None, team_id: Optional[int] = None,
                     metric_data: Optional[Dict[str, Any]] = None) -> "UsageMetrics":
        """Create a new usage metric record."""
        return cls(
            metric_name=metric_name,
            metric_value=metric_value,
            date=date or datetime.utcnow(),
            user_id=user_id,
            team_id=team_id,
            metric_data=metric_data
        )