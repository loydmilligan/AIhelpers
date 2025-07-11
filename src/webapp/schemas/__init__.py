"""
Pydantic schemas for API requests and responses.

This package contains all Pydantic schemas for the web API:
- Prompt schemas for prompt management endpoints
- Response schemas for consistent API responses
"""

from .prompt import (
    PromptCreate, PromptUpdate, PromptResponse, PromptSearchRequest,
    PromptListResponse, PromptVersionResponse, PromptAnalyticsResponse,
    PromptSearchResponse, PromptDiffResponse, PromptStatsResponse
)

__all__ = [
    "PromptCreate",
    "PromptUpdate", 
    "PromptResponse",
    "PromptSearchRequest",
    "PromptListResponse",
    "PromptVersionResponse",
    "PromptAnalyticsResponse",
    "PromptSearchResponse",
    "PromptDiffResponse",
    "PromptStatsResponse"
]