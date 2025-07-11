"""
FastAPI router for enhanced prompt management endpoints.

Provides comprehensive REST API for prompt CRUD operations, search,
versioning, and analytics.
"""

import time
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...config.database import get_db_session
from ...auth import require_auth, optional_auth
from ...models.user import User
from ...models.prompt import PromptCategory
from ...services.prompt_service import PromptService
from ...services.prompt_search import PromptSearchService
from ...services.prompt_version import PromptVersionService
from ...services.prompt_analytics import PromptAnalyticsService
from ..schemas.prompt import (
    PromptCreate, PromptUpdate, PromptResponse, PromptListResponse,
    PromptSearchRequest, PromptSearchResponse, PromptVersionResponse,
    PromptAnalyticsResponse, PromptDiffRequest, PromptDiffResponse,
    PromptVersionCreateRequest, PromptRevertRequest, PromptUsageTrackRequest,
    PromptStatsResponse, PromptTrendingResponse, PromptSimilarResponse,
    PromptTopResponse, PromptReportResponse, PromptTagsResponse,
    PromptCategoriesResponse, ErrorResponse, SuccessResponse
)

prompt_router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@prompt_router.post("/", response_model=PromptResponse)
async def create_prompt(
    prompt_data: PromptCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db_session)
):
    """Create a new prompt."""
    try:
        service = PromptService(db)
        prompt = service.create_prompt(
            title=prompt_data.title,
            content=prompt_data.content,
            owner_id=current_user.id,
            category=PromptCategory(prompt_data.category.value),
            description=prompt_data.description,
            tags=prompt_data.tags,
            team_id=prompt_data.team_id,
            is_public=prompt_data.is_public
        )
        return PromptResponse.from_orm(prompt)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create prompt: {str(e)}"
        )


@prompt_router.get("/", response_model=PromptListResponse)
async def list_prompts(
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    owner_only: bool = Query(False, description="Only return user's own prompts"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: Optional[User] = Depends(optional_auth),
    db: Session = Depends(get_db_session)
):
    """List prompts with filtering and pagination."""
    try:
        service = PromptService(db)
        
        # Convert category string to enum if provided
        category_enum = None
        if category:
            try:
                category_enum = PromptCategory(category)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid category: {category}"
                )
        
        offset = (page - 1) * page_size
        user_id = current_user.id if current_user else None
        
        prompts, total_count = service.list_prompts(
            user_id=user_id,
            category=category_enum,
            tags=tags,
            is_public=is_public,
            owner_only=owner_only,
            limit=page_size,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        prompt_responses = [PromptResponse.from_orm(prompt) for prompt in prompts]
        
        return PromptListResponse(
            prompts=prompt_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_more=offset + page_size < total_count
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list prompts: {str(e)}"
        )


@prompt_router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: int,
    current_user: Optional[User] = Depends(optional_auth),
    db: Session = Depends(get_db_session)
):
    """Get a specific prompt by ID."""
    try:
        service = PromptService(db)
        user_id = current_user.id if current_user else None
        
        prompt = service.get_prompt(prompt_id, user_id)
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt not found or access denied"
            )
        
        return PromptResponse.from_orm(prompt)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prompt: {str(e)}"
        )


@prompt_router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: int,
    prompt_data: PromptUpdate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db_session)
):
    """Update an existing prompt."""
    try:
        service = PromptService(db)
        
        # Convert category to enum if provided
        category = None
        if prompt_data.category:
            category = PromptCategory(prompt_data.category.value)
        
        prompt = service.update_prompt(
            prompt_id=prompt_id,
            user_id=current_user.id,
            title=prompt_data.title,
            content=prompt_data.content,
            description=prompt_data.description,
            category=category,
            tags=prompt_data.tags,
            is_public=prompt_data.is_public
        )
        
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt not found or access denied"
            )
        
        return PromptResponse.from_orm(prompt)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update prompt: {str(e)}"
        )


@prompt_router.delete("/{prompt_id}", response_model=SuccessResponse)
async def delete_prompt(
    prompt_id: int,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db_session)
):
    """Delete a prompt (soft delete)."""
    try:
        service = PromptService(db)
        success = service.delete_prompt(prompt_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt not found or access denied"
            )
        
        return SuccessResponse(
            success=True,
            message="Prompt deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete prompt: {str(e)}"
        )


@prompt_router.post("/search", response_model=PromptSearchResponse)
async def search_prompts(
    search_request: PromptSearchRequest,
    current_user: Optional[User] = Depends(optional_auth),
    db: Session = Depends(get_db_session)
):
    """Search prompts using full-text search."""
    try:
        start_time = time.time()
        service = PromptSearchService(db)
        user_id = current_user.id if current_user else None
        
        # Convert category to enum if provided
        category = None
        if search_request.category:
            category = PromptCategory(search_request.category.value)
        
        results, total_count = service.search_prompts(
            query=search_request.query,
            user_id=user_id,
            category=category,
            tags=search_request.tags,
            owner_id=search_request.owner_id,
            is_public=search_request.is_public,
            limit=search_request.limit,
            offset=search_request.offset,
            min_score=search_request.min_score
        )
        
        search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return PromptSearchResponse(
            results=results,
            total_count=total_count,
            query=search_request.query,
            search_time_ms=search_time
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@prompt_router.get("/{prompt_id}/versions", response_model=List[PromptVersionResponse])
async def get_prompt_versions(
    prompt_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: Optional[User] = Depends(optional_auth),
    db: Session = Depends(get_db_session)
):
    """Get version history for a prompt."""
    try:
        service = PromptVersionService(db)
        user_id = current_user.id if current_user else None
        
        offset = (page - 1) * page_size
        versions, total_count = service.get_version_history(
            prompt_id, user_id, page_size, offset
        )
        
        return [PromptVersionResponse.from_orm(v) for v in versions]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get versions: {str(e)}"
        )


@prompt_router.post("/{prompt_id}/versions", response_model=PromptVersionResponse)
async def create_prompt_version(
    prompt_id: int,
    version_data: PromptVersionCreateRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db_session)
):
    """Create a new version of a prompt."""
    try:
        service = PromptVersionService(db)
        version = service.create_version(
            prompt_id=prompt_id,
            content=version_data.content,
            user_id=current_user.id,
            change_description=version_data.change_description
        )
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt not found or access denied"
            )
        
        return PromptVersionResponse.from_orm(version)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create version: {str(e)}"
        )


@prompt_router.post("/{prompt_id}/revert", response_model=PromptResponse)
async def revert_prompt(
    prompt_id: int,
    revert_data: PromptRevertRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db_session)
):
    """Revert a prompt to a previous version."""
    try:
        service = PromptVersionService(db)
        prompt = service.revert_to_version(
            prompt_id=prompt_id,
            version_number=revert_data.version_number,
            user_id=current_user.id
        )
        
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt or version not found, or access denied"
            )
        
        return PromptResponse.from_orm(prompt)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revert prompt: {str(e)}"
        )


@prompt_router.post("/{prompt_id}/diff", response_model=PromptDiffResponse)
async def diff_prompt_versions(
    prompt_id: int,
    diff_request: PromptDiffRequest,
    current_user: Optional[User] = Depends(optional_auth),
    db: Session = Depends(get_db_session)
):
    """Generate diff between two prompt versions."""
    try:
        service = PromptVersionService(db)
        user_id = current_user.id if current_user else None
        
        diff_data = service.diff_versions(
            prompt_id=prompt_id,
            version1=diff_request.version1,
            version2=diff_request.version2,
            user_id=user_id
        )
        
        if not diff_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt or versions not found, or access denied"
            )
        
        return PromptDiffResponse(**diff_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate diff: {str(e)}"
        )


@prompt_router.get("/{prompt_id}/analytics", response_model=PromptAnalyticsResponse)
async def get_prompt_analytics(
    prompt_id: int,
    current_user: Optional[User] = Depends(optional_auth),
    db: Session = Depends(get_db_session)
):
    """Get analytics data for a prompt."""
    try:
        service = PromptAnalyticsService(db)
        user_id = current_user.id if current_user else None
        
        analytics = service.get_prompt_analytics(prompt_id, user_id)
        if not analytics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt not found or access denied"
            )
        
        return PromptAnalyticsResponse(**analytics)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )


@prompt_router.post("/{prompt_id}/track-usage", response_model=SuccessResponse)
async def track_prompt_usage(
    prompt_id: int,
    usage_data: PromptUsageTrackRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db_session)
):
    """Track usage of a prompt."""
    try:
        service = PromptAnalyticsService(db)
        success = service.track_usage(
            prompt_id=prompt_id,
            user_id=current_user.id,
            response_time=usage_data.response_time,
            success=usage_data.success,
            feedback_score=usage_data.feedback_score,
            context_data=usage_data.context_data
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to track usage"
            )
        
        return SuccessResponse(
            success=True,
            message="Usage tracked successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track usage: {str(e)}"
        )


@prompt_router.get("/stats/user", response_model=PromptStatsResponse)
async def get_user_prompt_stats(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db_session)
):
    """Get prompt statistics for the current user."""
    try:
        service = PromptService(db)
        stats = service.get_user_prompt_stats(current_user.id)
        return PromptStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user stats: {str(e)}"
        )


@prompt_router.get("/trending", response_model=PromptTrendingResponse)
async def get_trending_prompts(
    category: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(optional_auth),
    db: Session = Depends(get_db_session)
):
    """Get trending prompts."""
    try:
        service = PromptSearchService(db)
        user_id = current_user.id if current_user else None
        
        category_enum = None
        if category:
            category_enum = PromptCategory(category)
        
        prompts = service.get_trending_prompts(
            user_id=user_id,
            category=category_enum,
            days=days,
            limit=limit
        )
        
        prompt_responses = [PromptResponse.from_orm(prompt) for prompt in prompts]
        
        return PromptTrendingResponse(
            prompts=prompt_responses,
            period_days=days
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trending prompts: {str(e)}"
        )


@prompt_router.get("/{prompt_id}/similar", response_model=PromptSimilarResponse)
async def get_similar_prompts(
    prompt_id: int,
    limit: int = Query(10, ge=1, le=50),
    current_user: Optional[User] = Depends(optional_auth),
    db: Session = Depends(get_db_session)
):
    """Get prompts similar to the specified prompt."""
    try:
        service = PromptSearchService(db)
        user_id = current_user.id if current_user else None
        
        similar_prompts = service.get_similar_prompts(
            prompt_id=prompt_id,
            user_id=user_id,
            limit=limit
        )
        
        return PromptSimilarResponse(
            similar_prompts=similar_prompts,
            reference_prompt_id=prompt_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get similar prompts: {str(e)}"
        )


@prompt_router.get("/categories", response_model=PromptCategoriesResponse)
async def get_prompt_categories():
    """Get available prompt categories."""
    categories = [category.value for category in PromptCategory]
    return PromptCategoriesResponse(categories=categories)


@prompt_router.get("/tags", response_model=PromptTagsResponse)
async def get_popular_tags(
    limit: int = Query(50, ge=1, le=100),
    current_user: Optional[User] = Depends(optional_auth),
    db: Session = Depends(get_db_session)
):
    """Get popular tags from all prompts."""
    try:
        # This is a simplified implementation
        # In production, you might want to cache this or use a more efficient query
        from sqlalchemy import func
        from ...models.prompt import Prompt
        
        query = db.query(Prompt).filter(Prompt.is_active == True)
        
        # Access control
        user_id = current_user.id if current_user else None
        if user_id:
            query = query.filter(
                (Prompt.owner_id == user_id) | (Prompt.is_public == True)
            )
        else:
            query = query.filter(Prompt.is_public == True)
        
        prompts = query.all()
        
        # Collect all tags
        tag_counts = {}
        for prompt in prompts:
            if prompt.tags:
                for tag in prompt.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Sort by frequency and take top tags
        popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        tags = [tag for tag, count in popular_tags[:limit]]
        
        return PromptTagsResponse(tags=tags, count=len(tags))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tags: {str(e)}"
        )