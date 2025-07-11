"""
Pydantic schemas for prompt-related API requests and responses.

Defines the data structures used for prompt management API endpoints.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

from ...models.prompt import PromptCategory


class PromptCategorySchema(str, Enum):
    """Prompt category schema for API."""
    CODING = "coding"
    ANALYSIS = "analysis"
    DOCUMENTATION = "documentation"
    DEBUGGING = "debugging"
    TESTING = "testing"
    REFACTORING = "refactoring"
    REVIEW = "review"
    PLANNING = "planning"
    GENERAL = "general"


class PromptCreate(BaseModel):
    """Schema for creating a new prompt."""
    title: str = Field(..., min_length=1, max_length=200, description="Prompt title")
    content: str = Field(..., min_length=1, description="Prompt content")
    description: Optional[str] = Field(None, max_length=1000, description="Optional prompt description")
    category: PromptCategorySchema = Field(PromptCategorySchema.GENERAL, description="Prompt category")
    tags: Optional[List[str]] = Field(None, description="List of tags for categorization")
    team_id: Optional[int] = Field(None, description="Optional team ID for shared prompts")
    is_public: bool = Field(False, description="Whether the prompt is publicly visible")
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            # Remove duplicates and empty tags
            v = [tag.strip() for tag in v if tag and tag.strip()]
            v = list(dict.fromkeys(v))  # Remove duplicates while preserving order
            # Limit to 10 tags
            if len(v) > 10:
                raise ValueError("Maximum 10 tags allowed")
        return v
    
    @validator('title')
    def validate_title(cls, v):
        return v.strip()
    
    @validator('content')
    def validate_content(cls, v):
        return v.strip()


class PromptUpdate(BaseModel):
    """Schema for updating an existing prompt."""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="New prompt title")
    content: Optional[str] = Field(None, min_length=1, description="New prompt content")
    description: Optional[str] = Field(None, max_length=1000, description="New prompt description")
    category: Optional[PromptCategorySchema] = Field(None, description="New prompt category")
    tags: Optional[List[str]] = Field(None, description="New list of tags")
    is_public: Optional[bool] = Field(None, description="New public status")
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            v = [tag.strip() for tag in v if tag and tag.strip()]
            v = list(dict.fromkeys(v))
            if len(v) > 10:
                raise ValueError("Maximum 10 tags allowed")
        return v


class PromptResponse(BaseModel):
    """Schema for prompt response data."""
    id: int
    title: str
    content: str
    description: Optional[str]
    category: str
    tags: List[str]
    owner_id: int
    team_id: Optional[int]
    version: int
    is_active: bool
    is_public: bool
    usage_count: int
    effectiveness_score: Optional[float]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, prompt):
        """Create from SQLAlchemy model."""
        return cls(
            id=prompt.id,
            title=prompt.title,
            content=prompt.content,
            description=prompt.description,
            category=prompt.category.value if hasattr(prompt.category, 'value') else prompt.category,
            tags=prompt.tags or [],
            owner_id=prompt.owner_id,
            team_id=prompt.team_id,
            version=prompt.version,
            is_active=prompt.is_active,
            is_public=prompt.is_public,
            usage_count=prompt.usage_count,
            effectiveness_score=prompt.effectiveness_score,
            created_at=prompt.created_at,
            updated_at=prompt.updated_at
        )


class PromptListResponse(BaseModel):
    """Schema for prompt list responses."""
    prompts: List[PromptResponse]
    total_count: int
    page: int
    page_size: int
    has_more: bool


class PromptVersionResponse(BaseModel):
    """Schema for prompt version data."""
    id: int
    prompt_id: int
    content: str
    version_number: int
    created_by: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class PromptAnalyticsResponse(BaseModel):
    """Schema for prompt analytics data."""
    prompt_id: int
    usage_count: int
    effectiveness_score: Optional[float]
    avg_response_time: Optional[float]
    success_rate: Optional[float]
    user_ratings: Dict[str, Any]
    last_used: Optional[datetime]
    average_rating: Optional[float]


class PromptSearchRequest(BaseModel):
    """Schema for prompt search requests."""
    query: str = Field(..., min_length=1, description="Search query")
    category: Optional[PromptCategorySchema] = Field(None, description="Filter by category")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    owner_id: Optional[int] = Field(None, description="Filter by owner")
    is_public: Optional[bool] = Field(None, description="Filter by public status")
    limit: int = Field(50, ge=1, le=100, description="Maximum results per page")
    offset: int = Field(0, ge=0, description="Results offset for pagination")
    min_score: float = Field(0.1, ge=0.0, le=1.0, description="Minimum relevance score")


class PromptSearchResult(BaseModel):
    """Schema for individual search result."""
    prompt: PromptResponse
    relevance_score: float
    highlights: Dict[str, str]


class PromptSearchResponse(BaseModel):
    """Schema for prompt search responses."""
    results: List[PromptSearchResult]
    total_count: int
    query: str
    search_time_ms: float


class PromptDiffRequest(BaseModel):
    """Schema for prompt diff requests."""
    version1: int = Field(..., ge=1, description="First version number")
    version2: int = Field(..., ge=1, description="Second version number")


class PromptDiffResponse(BaseModel):
    """Schema for prompt diff responses."""
    prompt_id: int
    version1: Dict[str, Any]
    version2: Dict[str, Any]
    diff: Dict[str, Any]


class PromptVersionCreateRequest(BaseModel):
    """Schema for creating a new prompt version."""
    content: str = Field(..., min_length=1, description="New version content")
    change_description: Optional[str] = Field(None, max_length=500, description="Description of changes")


class PromptRevertRequest(BaseModel):
    """Schema for reverting to a prompt version."""
    version_number: int = Field(..., ge=1, description="Version number to revert to")


class PromptUsageTrackRequest(BaseModel):
    """Schema for tracking prompt usage."""
    response_time: Optional[float] = Field(None, ge=0, description="Response time in seconds")
    success: bool = Field(True, description="Whether the usage was successful")
    feedback_score: Optional[float] = Field(None, ge=0, le=1, description="User feedback score (0-1)")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Additional context data")


class PromptStatsResponse(BaseModel):
    """Schema for prompt statistics."""
    total_prompts: int
    by_category: Dict[str, int]
    total_usage: int
    avg_effectiveness: Optional[float]


class PromptTrendingResponse(BaseModel):
    """Schema for trending prompts."""
    prompts: List[PromptResponse]
    period_days: int


class PromptSimilarResponse(BaseModel):
    """Schema for similar prompts."""
    similar_prompts: List[Dict[str, Any]]
    reference_prompt_id: int


class PromptTopResponse(BaseModel):
    """Schema for top prompts."""
    prompts: List[Dict[str, Any]]
    metric: str
    period_days: int


class PromptReportResponse(BaseModel):
    """Schema for analytics reports."""
    report_period: Dict[str, Any]
    summary: Dict[str, Any]
    top_prompts: Dict[str, Any]


class PromptTagsResponse(BaseModel):
    """Schema for available tags."""
    tags: List[str]
    count: int


class PromptCategoriesResponse(BaseModel):
    """Schema for available categories."""
    categories: List[str]


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """Schema for success responses."""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None