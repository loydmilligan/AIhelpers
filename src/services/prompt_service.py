"""
Prompt service layer for business logic operations.

Handles CRUD operations, validation, and business rules for prompts.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime

try:
    from ..models.prompt import Prompt, PromptCategory, PromptVersion
    from ..models.analytics import PromptAnalytics, UserActivity
    from ..models.user import User
except ImportError:
    # Fallback for direct imports
    from models.prompt import Prompt, PromptCategory, PromptVersion
    from models.analytics import PromptAnalytics, UserActivity
    from models.user import User


class PromptService:
    """Service class for prompt business logic operations."""
    
    def __init__(self, db_session: Session):
        """Initialize with database session."""
        self.db = db_session
    
    def create_prompt(
        self,
        title: str,
        content: str,
        owner_id: int,
        category: PromptCategory = PromptCategory.GENERAL,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        team_id: Optional[int] = None,
        is_public: bool = False
    ) -> Prompt:
        """
        Create a new prompt.
        
        Args:
            title: Prompt title
            content: Prompt content
            owner_id: ID of the user creating the prompt
            category: Prompt category
            description: Optional description
            tags: Optional list of tags
            team_id: Optional team ID for shared prompts
            is_public: Whether the prompt is publicly visible
            
        Returns:
            Created prompt instance
        """
        prompt = Prompt(
            title=title,
            content=content,
            owner_id=owner_id,
            category=category,
            description=description,
            tags=tags or [],
            team_id=team_id,
            is_public=is_public,
            version=1,
            is_active=True,
            usage_count=0
        )
        
        self.db.add(prompt)
        self.db.flush()  # To get the ID
        
        # Create initial version
        initial_version = PromptVersion(
            prompt_id=prompt.id,
            content=content,
            version_number=1,
            created_by=owner_id
        )
        
        # Create analytics record
        analytics = PromptAnalytics(
            prompt_id=prompt.id,
            usage_count=0
        )
        
        # Track activity
        activity = UserActivity.create_activity(
            user_id=owner_id,
            activity_type="prompt_created",
            data={
                "prompt_id": prompt.id,
                "title": title,
                "category": category.value
            }
        )
        
        self.db.add_all([initial_version, analytics, activity])
        self.db.commit()
        self.db.refresh(prompt)
        
        return prompt
    
    def get_prompt(self, prompt_id: int, user_id: Optional[int] = None) -> Optional[Prompt]:
        """
        Get a prompt by ID with access control.
        
        Args:
            prompt_id: Prompt ID
            user_id: Optional user ID for access control
            
        Returns:
            Prompt instance if found and accessible, None otherwise
        """
        query = self.db.query(Prompt).filter(Prompt.id == prompt_id, Prompt.is_active == True)
        
        # Add access control
        if user_id:
            query = query.filter(
                or_(
                    Prompt.owner_id == user_id,
                    Prompt.is_public == True,
                    # TODO: Add team access check when team_id is available
                )
            )
        else:
            # Only public prompts for anonymous users
            query = query.filter(Prompt.is_public == True)
        
        return query.first()
    
    def update_prompt(
        self,
        prompt_id: int,
        user_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[PromptCategory] = None,
        tags: Optional[List[str]] = None,
        is_public: Optional[bool] = None
    ) -> Optional[Prompt]:
        """
        Update a prompt and create a new version if content changes.
        
        Args:
            prompt_id: Prompt ID
            user_id: ID of user making the update
            title: New title
            content: New content
            description: New description
            category: New category
            tags: New tags
            is_public: New public status
            
        Returns:
            Updated prompt instance if successful, None if not found/authorized
        """
        prompt = self.db.query(Prompt).filter(
            Prompt.id == prompt_id,
            Prompt.owner_id == user_id,  # Only owner can update
            Prompt.is_active == True
        ).first()
        
        if not prompt:
            return None
        
        # Track what changed
        changes = {}
        content_changed = False
        
        if title is not None and title != prompt.title:
            changes["title"] = {"old": prompt.title, "new": title}
            prompt.title = title
        
        if content is not None and content != prompt.content:
            changes["content"] = {"old": prompt.content[:100] + "...", "new": content[:100] + "..."}
            content_changed = True
            # Create new version
            new_version = prompt.create_version(content, user_id)
            self.db.add(new_version)
        
        if description is not None:
            changes["description"] = {"old": prompt.description, "new": description}
            prompt.description = description
        
        if category is not None and category != prompt.category:
            changes["category"] = {"old": prompt.category.value, "new": category.value}
            prompt.category = category
        
        if tags is not None:
            changes["tags"] = {"old": prompt.tags, "new": tags}
            prompt.tags = tags
        
        if is_public is not None and is_public != prompt.is_public:
            changes["is_public"] = {"old": prompt.is_public, "new": is_public}
            prompt.is_public = is_public
        
        if changes:
            prompt.updated_at = datetime.utcnow()
            
            # Track activity
            activity = UserActivity.create_activity(
                user_id=user_id,
                activity_type="prompt_updated",
                data={
                    "prompt_id": prompt_id,
                    "changes": changes,
                    "version_created": content_changed
                }
            )
            self.db.add(activity)
        
        self.db.commit()
        self.db.refresh(prompt)
        
        return prompt
    
    def delete_prompt(self, prompt_id: int, user_id: int) -> bool:
        """
        Soft delete a prompt (set is_active to False).
        
        Args:
            prompt_id: Prompt ID
            user_id: ID of user requesting deletion
            
        Returns:
            True if deleted successfully, False otherwise
        """
        prompt = self.db.query(Prompt).filter(
            Prompt.id == prompt_id,
            Prompt.owner_id == user_id,
            Prompt.is_active == True
        ).first()
        
        if not prompt:
            return False
        
        prompt.is_active = False
        prompt.updated_at = datetime.utcnow()
        
        # Track activity
        activity = UserActivity.create_activity(
            user_id=user_id,
            activity_type="prompt_deleted",
            data={
                "prompt_id": prompt_id,
                "title": prompt.title
            }
        )
        self.db.add(activity)
        
        self.db.commit()
        return True
    
    def list_prompts(
        self,
        user_id: Optional[int] = None,
        category: Optional[PromptCategory] = None,
        tags: Optional[List[str]] = None,
        is_public: Optional[bool] = None,
        owner_only: bool = False,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Prompt], int]:
        """
        List prompts with filtering and pagination.
        
        Args:
            user_id: Optional user ID for access control
            category: Filter by category
            tags: Filter by tags (any of the tags)
            is_public: Filter by public status
            owner_only: Only return prompts owned by user_id
            limit: Maximum number of results
            offset: Offset for pagination
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')
            
        Returns:
            Tuple of (prompts list, total count)
        """
        query = self.db.query(Prompt).filter(Prompt.is_active == True)
        
        # Access control
        if user_id:
            if owner_only:
                query = query.filter(Prompt.owner_id == user_id)
            else:
                query = query.filter(
                    or_(
                        Prompt.owner_id == user_id,
                        Prompt.is_public == True
                        # TODO: Add team access
                    )
                )
        else:
            # Anonymous users only see public prompts
            query = query.filter(Prompt.is_public == True)
        
        # Filters
        if category:
            query = query.filter(Prompt.category == category)
        
        if is_public is not None:
            query = query.filter(Prompt.is_public == is_public)
        
        if tags:
            # Filter by any of the provided tags
            for tag in tags:
                query = query.filter(Prompt.tags.contains([tag]))
        
        # Get total count before pagination
        total_count = query.count()
        
        # Sorting
        sort_column = getattr(Prompt, sort_by, Prompt.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Pagination
        prompts = query.offset(offset).limit(limit).all()
        
        return prompts, total_count
    
    def get_user_prompt_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get prompt statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user's prompt statistics
        """
        user_prompts = self.db.query(Prompt).filter(
            Prompt.owner_id == user_id,
            Prompt.is_active == True
        ).all()
        
        if not user_prompts:
            return {
                "total_prompts": 0,
                "by_category": {},
                "total_usage": 0,
                "avg_effectiveness": None
            }
        
        # Calculate statistics
        total_prompts = len(user_prompts)
        by_category = {}
        total_usage = 0
        effectiveness_scores = []
        
        for prompt in user_prompts:
            # Category stats
            category = prompt.category.value
            by_category[category] = by_category.get(category, 0) + 1
            
            # Usage stats
            total_usage += prompt.usage_count
            
            # Effectiveness scores
            if prompt.effectiveness_score is not None:
                effectiveness_scores.append(prompt.effectiveness_score)
        
        avg_effectiveness = None
        if effectiveness_scores:
            avg_effectiveness = sum(effectiveness_scores) / len(effectiveness_scores)
        
        return {
            "total_prompts": total_prompts,
            "by_category": by_category,
            "total_usage": total_usage,
            "avg_effectiveness": avg_effectiveness
        }


# Convenience functions for direct use
def create_prompt(
    db: Session,
    title: str,
    content: str,
    owner_id: int,
    category: PromptCategory = PromptCategory.GENERAL,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    team_id: Optional[int] = None,
    is_public: bool = False
) -> Prompt:
    """Create a new prompt using the service."""
    service = PromptService(db)
    return service.create_prompt(
        title=title,
        content=content,
        owner_id=owner_id,
        category=category,
        description=description,
        tags=tags,
        team_id=team_id,
        is_public=is_public
    )


def update_prompt(
    db: Session,
    prompt_id: int,
    user_id: int,
    **updates
) -> Optional[Prompt]:
    """Update a prompt using the service."""
    service = PromptService(db)
    return service.update_prompt(prompt_id, user_id, **updates)


def search_prompts(
    db: Session,
    user_id: Optional[int] = None,
    **filters
) -> Tuple[List[Prompt], int]:
    """Search prompts using the service."""
    service = PromptService(db)
    return service.list_prompts(user_id=user_id, **filters)