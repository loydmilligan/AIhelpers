"""
Prompt analytics service for usage tracking and effectiveness calculation.

Handles analytics data collection, aggregation, and reporting.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text
from datetime import datetime, timedelta

from ..models.prompt import Prompt
from ..models.analytics import PromptAnalytics, UserActivity, UsageMetrics
from ..models.user import User


class PromptAnalyticsService:
    """Service class for prompt analytics operations."""
    
    def __init__(self, db_session: Session):
        """Initialize with database session."""
        self.db = db_session
    
    def track_usage(
        self,
        prompt_id: int,
        user_id: int,
        response_time: Optional[float] = None,
        success: bool = True,
        feedback_score: Optional[float] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track a prompt usage event.
        
        Args:
            prompt_id: ID of the prompt used
            user_id: ID of the user who used the prompt
            response_time: Time taken to generate response (seconds)
            success: Whether the prompt usage was successful
            feedback_score: Optional user feedback score (0-1)
            context_data: Optional additional context data
            
        Returns:
            True if tracking was successful, False otherwise
        """
        try:
            # Get or create analytics record
            analytics = self.db.query(PromptAnalytics).filter(
                PromptAnalytics.prompt_id == prompt_id
            ).first()
            
            if not analytics:
                analytics = PromptAnalytics(prompt_id=prompt_id, usage_count=0)
                self.db.add(analytics)
                self.db.flush()
            
            # Update analytics
            analytics.increment_usage(response_time, success)
            
            # Update prompt usage count
            prompt = self.db.query(Prompt).filter(Prompt.id == prompt_id).first()
            if prompt:
                prompt.increment_usage()
            
            # Track user activity
            activity_data = {
                "prompt_id": prompt_id,
                "response_time": response_time,
                "success": success
            }
            if context_data:
                activity_data.update(context_data)
            
            activity = UserActivity.create_activity(
                user_id=user_id,
                activity_type="prompt_used",
                data=activity_data
            )
            self.db.add(activity)
            
            # Add user feedback if provided
            if feedback_score is not None:
                analytics.add_user_rating(user_id, feedback_score)
            
            # Create daily usage metric
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            daily_metric = self.db.query(UsageMetrics).filter(
                UsageMetrics.metric_name == "daily_prompt_usage",
                UsageMetrics.date == today,
                UsageMetrics.user_id == user_id
            ).first()
            
            if daily_metric:
                daily_metric.metric_value += 1
            else:
                daily_metric = UsageMetrics.create_metric(
                    metric_name="daily_prompt_usage",
                    metric_value=1,
                    date=today,
                    user_id=user_id
                )
                self.db.add(daily_metric)
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error tracking usage: {e}")
            return False
    
    def calculate_effectiveness(self, prompt_id: int) -> Optional[float]:
        """
        Calculate effectiveness score for a prompt.
        
        Args:
            prompt_id: Prompt ID
            
        Returns:
            Effectiveness score (0-1) if calculable, None otherwise
        """
        analytics = self.db.query(PromptAnalytics).filter(
            PromptAnalytics.prompt_id == prompt_id
        ).first()
        
        if not analytics or analytics.usage_count == 0:
            return None
        
        # Base effectiveness on multiple factors
        factors = []
        weights = []
        
        # Success rate (40% weight)
        if analytics.success_rate is not None:
            factors.append(analytics.success_rate)
            weights.append(0.4)
        
        # User ratings (30% weight)
        avg_rating = analytics.get_average_rating()
        if avg_rating is not None:
            factors.append(avg_rating)
            weights.append(0.3)
        
        # Usage frequency (20% weight) - normalize to 0-1 scale
        usage_score = min(analytics.usage_count / 100.0, 1.0)  # Cap at 100 uses
        factors.append(usage_score)
        weights.append(0.2)
        
        # Response time (10% weight) - lower is better
        if analytics.avg_response_time is not None:
            # Assume 5 seconds is maximum acceptable time
            time_score = max(0, 1 - (analytics.avg_response_time / 5.0))
            factors.append(time_score)
            weights.append(0.1)
        
        # Calculate weighted average
        if not factors:
            return None
        
        # Normalize weights if some factors are missing
        total_weight = sum(weights)
        if total_weight == 0:
            return None
        
        effectiveness = sum(f * w for f, w in zip(factors, weights)) / total_weight
        
        # Update the analytics record
        analytics.effectiveness_score = effectiveness
        self.db.commit()
        
        return effectiveness
    
    def get_prompt_analytics(
        self,
        prompt_id: int,
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive analytics for a prompt.
        
        Args:
            prompt_id: Prompt ID
            user_id: Optional user ID for access control
            
        Returns:
            Analytics data if accessible, None otherwise
        """
        # Check access
        prompt = self.db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if not prompt:
            return None
        
        if user_id and not (prompt.owner_id == user_id or prompt.is_public):
            return None
        
        analytics = self.db.query(PromptAnalytics).filter(
            PromptAnalytics.prompt_id == prompt_id
        ).first()
        
        if not analytics:
            return {
                "prompt_id": prompt_id,
                "usage_count": 0,
                "effectiveness_score": None,
                "avg_response_time": None,
                "success_rate": None,
                "user_ratings": {},
                "last_used": None
            }
        
        return {
            "prompt_id": prompt_id,
            "usage_count": analytics.usage_count,
            "effectiveness_score": analytics.effectiveness_score,
            "avg_response_time": analytics.avg_response_time,
            "success_rate": analytics.success_rate,
            "user_ratings": analytics.user_ratings or {},
            "last_used": analytics.last_used.isoformat() if analytics.last_used else None,
            "average_rating": analytics.get_average_rating()
        }
    
    def get_user_analytics(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get analytics data for a user.
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            User analytics data
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get user's prompt usage activities
        activities = self.db.query(UserActivity).filter(
            UserActivity.user_id == user_id,
            UserActivity.activity_type == "prompt_used",
            UserActivity.timestamp >= cutoff_date
        ).all()
        
        # Get user's prompts
        user_prompts = self.db.query(Prompt).filter(
            Prompt.owner_id == user_id,
            Prompt.is_active == True
        ).all()
        
        # Calculate statistics
        total_usage = len(activities)
        unique_prompts_used = len(set(
            activity.data.get("prompt_id") for activity in activities 
            if activity.data and "prompt_id" in activity.data
        ))
        
        # Daily usage
        daily_usage = {}
        for activity in activities:
            date_key = activity.timestamp.date().isoformat()
            daily_usage[date_key] = daily_usage.get(date_key, 0) + 1
        
        # Prompt effectiveness
        total_effectiveness = 0
        prompts_with_scores = 0
        for prompt in user_prompts:
            if prompt.effectiveness_score is not None:
                total_effectiveness += prompt.effectiveness_score
                prompts_with_scores += 1
        
        avg_effectiveness = (
            total_effectiveness / prompts_with_scores 
            if prompts_with_scores > 0 else None
        )
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_prompt_usage": total_usage,
            "unique_prompts_used": unique_prompts_used,
            "owned_prompts": len(user_prompts),
            "avg_effectiveness": avg_effectiveness,
            "daily_usage": daily_usage,
            "most_active_day": max(daily_usage.items(), key=lambda x: x[1])[0] if daily_usage else None
        }
    
    def get_top_prompts(
        self,
        user_id: Optional[int] = None,
        category: Optional[str] = None,
        days: int = 30,
        limit: int = 10,
        metric: str = "usage"
    ) -> List[Dict[str, Any]]:
        """
        Get top prompts by various metrics.
        
        Args:
            user_id: Optional user ID for filtering
            category: Optional category filter
            days: Number of days to consider
            limit: Maximum number of prompts to return
            metric: Metric to sort by ('usage', 'effectiveness', 'rating')
            
        Returns:
            List of top prompts with their metrics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(Prompt, PromptAnalytics).join(
            PromptAnalytics, Prompt.id == PromptAnalytics.prompt_id, isouter=True
        ).filter(
            Prompt.is_active == True,
            Prompt.updated_at >= cutoff_date
        )
        
        # Access control
        if user_id:
            query = query.filter(
                or_(
                    Prompt.owner_id == user_id,
                    Prompt.is_public == True
                )
            )
        else:
            query = query.filter(Prompt.is_public == True)
        
        # Category filter
        if category:
            query = query.filter(Prompt.category == category)
        
        # Sort by metric
        if metric == "usage":
            query = query.order_by(desc(PromptAnalytics.usage_count))
        elif metric == "effectiveness":
            query = query.order_by(desc(PromptAnalytics.effectiveness_score))
        elif metric == "rating":
            # This would require calculating average rating on the fly
            query = query.order_by(desc(PromptAnalytics.usage_count))  # Fallback
        
        results = query.limit(limit).all()
        
        top_prompts = []
        for prompt, analytics in results:
            prompt_data = {
                "prompt": prompt,
                "usage_count": analytics.usage_count if analytics else 0,
                "effectiveness_score": analytics.effectiveness_score if analytics else None,
                "avg_response_time": analytics.avg_response_time if analytics else None,
                "average_rating": analytics.get_average_rating() if analytics else None
            }
            top_prompts.append(prompt_data)
        
        return top_prompts
    
    def generate_report(
        self,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive analytics report.
        
        Args:
            user_id: Optional user ID for user-specific report
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Comprehensive analytics report
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Base queries
        prompt_query = self.db.query(Prompt).filter(Prompt.is_active == True)
        activity_query = self.db.query(UserActivity).filter(
            UserActivity.timestamp >= start_date,
            UserActivity.timestamp <= end_date
        )
        
        if user_id:
            prompt_query = prompt_query.filter(Prompt.owner_id == user_id)
            activity_query = activity_query.filter(UserActivity.user_id == user_id)
        
        # Get data
        prompts = prompt_query.all()
        activities = activity_query.all()
        
        # Calculate metrics
        total_prompts = len(prompts)
        total_activities = len(activities)
        
        # Activity breakdown
        activity_types = {}
        for activity in activities:
            activity_types[activity.activity_type] = activity_types.get(activity.activity_type, 0) + 1
        
        # Category breakdown
        category_stats = {}
        for prompt in prompts:
            cat = prompt.category.value
            category_stats[cat] = category_stats.get(cat, 0) + 1
        
        # Top prompts
        top_by_usage = self.get_top_prompts(user_id, limit=5, metric="usage")
        top_by_effectiveness = self.get_top_prompts(user_id, limit=5, metric="effectiveness")
        
        return {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "summary": {
                "total_prompts": total_prompts,
                "total_activities": total_activities,
                "activity_types": activity_types,
                "category_distribution": category_stats
            },
            "top_prompts": {
                "by_usage": top_by_usage,
                "by_effectiveness": top_by_effectiveness
            }
        }


# Convenience functions for direct use
def track_usage(
    db: Session,
    prompt_id: int,
    user_id: int,
    **kwargs
) -> bool:
    """Track prompt usage using the service."""
    service = PromptAnalyticsService(db)
    return service.track_usage(prompt_id, user_id, **kwargs)


def calculate_effectiveness(db: Session, prompt_id: int) -> Optional[float]:
    """Calculate prompt effectiveness using the service."""
    service = PromptAnalyticsService(db)
    return service.calculate_effectiveness(prompt_id)