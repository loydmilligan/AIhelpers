"""
Prompt search service with PostgreSQL full-text search capabilities.

Provides advanced search functionality for prompts using PostgreSQL's
full-text search features, including ranking and advanced filtering.
"""

import re
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text
from sqlalchemy.dialects.postgresql import TSVECTOR

from ..models.prompt import Prompt, PromptCategory
from ..models.user import User


class PromptSearchService:
    """Service class for advanced prompt search functionality."""
    
    def __init__(self, db_session: Session):
        """Initialize with database session."""
        self.db = db_session
    
    def search_prompts(
        self,
        query: str,
        user_id: Optional[int] = None,
        category: Optional[PromptCategory] = None,
        tags: Optional[List[str]] = None,
        owner_id: Optional[int] = None,
        is_public: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
        min_score: float = 0.1
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Search prompts using PostgreSQL full-text search.
        
        Args:
            query: Search query string
            user_id: Optional user ID for access control
            category: Filter by category
            tags: Filter by tags
            owner_id: Filter by owner
            is_public: Filter by public status
            limit: Maximum number of results
            offset: Offset for pagination
            min_score: Minimum relevance score threshold
            
        Returns:
            Tuple of (search results with scores, total count)
        """
        # Build the search query
        search_query = self._build_search_query(query)
        
        # Base query with full-text search
        base_query = self.db.query(
            Prompt,
            func.ts_rank_cd(
                func.to_tsvector('english', 
                    func.concat(Prompt.title, ' ', Prompt.content, ' ', 
                               func.coalesce(Prompt.description, ''))
                ),
                func.plainto_tsquery('english', search_query)
            ).label('rank')
        ).filter(
            Prompt.is_active == True,
            func.to_tsvector('english', 
                func.concat(Prompt.title, ' ', Prompt.content, ' ', 
                           func.coalesce(Prompt.description, ''))
            ).op('@@')(func.plainto_tsquery('english', search_query))
        )
        
        # Access control
        if user_id:
            base_query = base_query.filter(
                or_(
                    Prompt.owner_id == user_id,
                    Prompt.is_public == True
                    # TODO: Add team access
                )
            )
        else:
            # Anonymous users only see public prompts
            base_query = base_query.filter(Prompt.is_public == True)
        
        # Additional filters
        if category:
            base_query = base_query.filter(Prompt.category == category)
        
        if owner_id:
            base_query = base_query.filter(Prompt.owner_id == owner_id)
        
        if is_public is not None:
            base_query = base_query.filter(Prompt.is_public == is_public)
        
        if tags:
            # Filter by any of the provided tags
            for tag in tags:
                base_query = base_query.filter(Prompt.tags.contains([tag]))
        
        # Apply minimum score filter
        if min_score > 0:
            base_query = base_query.having(
                func.ts_rank_cd(
                    func.to_tsvector('english', 
                        func.concat(Prompt.title, ' ', Prompt.content, ' ', 
                                   func.coalesce(Prompt.description, ''))
                    ),
                    func.plainto_tsquery('english', search_query)
                ) >= min_score
            )
        
        # Get total count
        count_query = base_query.statement.with_only_columns([func.count()])
        total_count = self.db.execute(count_query).scalar()
        
        # Order by relevance score and apply pagination
        results = base_query.order_by(desc('rank')).offset(offset).limit(limit).all()
        
        # Format results
        formatted_results = []
        for prompt, score in results:
            result = {
                'prompt': prompt,
                'relevance_score': float(score),
                'highlights': self._generate_highlights(prompt, query)
            }
            formatted_results.append(result)
        
        return formatted_results, total_count
    
    def search_by_tags(
        self,
        tags: List[str],
        user_id: Optional[int] = None,
        match_all: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Prompt], int]:
        """
        Search prompts by tags.
        
        Args:
            tags: List of tags to search for
            user_id: Optional user ID for access control
            match_all: Whether to match all tags (AND) or any tag (OR)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            Tuple of (prompts, total count)
        """
        query = self.db.query(Prompt).filter(Prompt.is_active == True)
        
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
        
        # Tag filtering
        if match_all:
            # All tags must be present
            for tag in tags:
                query = query.filter(Prompt.tags.contains([tag]))
        else:
            # Any tag can be present
            tag_conditions = []
            for tag in tags:
                tag_conditions.append(Prompt.tags.contains([tag]))
            query = query.filter(or_(*tag_conditions))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and order by usage
        prompts = query.order_by(desc(Prompt.usage_count)).offset(offset).limit(limit).all()
        
        return prompts, total_count
    
    def get_similar_prompts(
        self,
        prompt_id: int,
        user_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find prompts similar to the given prompt.
        
        Args:
            prompt_id: ID of the reference prompt
            user_id: Optional user ID for access control
            limit: Maximum number of similar prompts to return
            
        Returns:
            List of similar prompts with similarity scores
        """
        # Get the reference prompt
        reference_prompt = self.db.query(Prompt).filter(
            Prompt.id == prompt_id,
            Prompt.is_active == True
        ).first()
        
        if not reference_prompt:
            return []
        
        # Use the prompt's content and title for similarity search
        search_text = f"{reference_prompt.title} {reference_prompt.content}"
        
        # Find similar prompts using full-text search
        results, _ = self.search_prompts(
            query=search_text,
            user_id=user_id,
            limit=limit + 1  # +1 to exclude the reference prompt
        )
        
        # Filter out the reference prompt and format results
        similar_prompts = []
        for result in results:
            if result['prompt'].id != prompt_id:
                similar_prompts.append({
                    'prompt': result['prompt'],
                    'similarity_score': result['relevance_score']
                })
        
        return similar_prompts[:limit]
    
    def get_trending_prompts(
        self,
        user_id: Optional[int] = None,
        category: Optional[PromptCategory] = None,
        days: int = 7,
        limit: int = 20
    ) -> List[Prompt]:
        """
        Get trending prompts based on recent usage.
        
        Args:
            user_id: Optional user ID for access control
            category: Optional category filter
            days: Number of days to consider for trending calculation
            limit: Maximum number of prompts to return
            
        Returns:
            List of trending prompts
        """
        from datetime import datetime, timedelta
        
        # Calculate trending score based on recent usage
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(Prompt).filter(
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
        
        # Order by a combination of usage count and effectiveness
        prompts = query.order_by(
            desc(Prompt.usage_count),
            desc(Prompt.effectiveness_score),
            desc(Prompt.updated_at)
        ).limit(limit).all()
        
        return prompts
    
    def _build_search_query(self, query: str) -> str:
        """
        Build and sanitize the search query for PostgreSQL full-text search.
        
        Args:
            query: Raw search query
            
        Returns:
            Sanitized search query
        """
        # Remove special characters and normalize whitespace
        sanitized = re.sub(r'[^\w\s]', ' ', query)
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        # Split into terms and remove empty ones
        terms = [term for term in sanitized.split() if term]
        
        if not terms:
            return ''
        
        # Join terms for plainto_tsquery (it handles the logic internally)
        return ' '.join(terms)
    
    def _generate_highlights(self, prompt: Prompt, query: str) -> Dict[str, str]:
        """
        Generate search result highlights.
        
        Args:
            prompt: Prompt object
            query: Original search query
            
        Returns:
            Dictionary with highlighted text snippets
        """
        query_terms = self._build_search_query(query).lower().split()
        
        def highlight_text(text: str, max_length: int = 200) -> str:
            """Highlight matching terms in text."""
            if not text:
                return ""
            
            text_lower = text.lower()
            highlighted = text
            
            # Simple highlighting (in production, consider using PostgreSQL's ts_headline)
            for term in query_terms:
                if term in text_lower:
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    highlighted = pattern.sub(f'<mark>{term}</mark>', highlighted)
            
            # Truncate if too long
            if len(highlighted) > max_length:
                highlighted = highlighted[:max_length] + '...'
            
            return highlighted
        
        return {
            'title': highlight_text(prompt.title, 100),
            'content': highlight_text(prompt.content, 300),
            'description': highlight_text(prompt.description or '', 150)
        }


# Convenience function for direct use
def search_prompts(
    db: Session,
    query: str,
    user_id: Optional[int] = None,
    **filters
) -> Tuple[List[Dict[str, Any]], int]:
    """Search prompts using the search service."""
    service = PromptSearchService(db)
    return service.search_prompts(query=query, user_id=user_id, **filters)


def build_search_query(terms: List[str]) -> str:
    """
    Build a PostgreSQL full-text search query from search terms.
    
    Args:
        terms: List of search terms
        
    Returns:
        Formatted search query
    """
    if not terms:
        return ''
    
    # Join terms with AND logic for stricter matching
    sanitized_terms = []
    for term in terms:
        # Remove special characters
        clean_term = re.sub(r'[^\w]', '', term)
        if clean_term:
            sanitized_terms.append(clean_term)
    
    return ' & '.join(sanitized_terms) if sanitized_terms else ''