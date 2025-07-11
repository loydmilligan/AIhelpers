"""
Service layer for the AI Coding Workflow Management Platform.

This package contains business logic services for the application:
- PromptService: Core prompt management operations
- PromptSearchService: Full-text search functionality
- PromptVersionService: Version control operations
- PromptAnalyticsService: Analytics and usage tracking
"""

from .prompt_service import PromptService, create_prompt, update_prompt, search_prompts
from .prompt_search import PromptSearchService, search_prompts as search_prompts_advanced
from .prompt_version import PromptVersionService, create_version, revert_version, diff_versions
from .prompt_analytics import PromptAnalyticsService, track_usage, calculate_effectiveness

__all__ = [
    "PromptService",
    "create_prompt",
    "update_prompt", 
    "search_prompts",
    "PromptSearchService",
    "search_prompts_advanced",
    "PromptVersionService",
    "create_version",
    "revert_version",
    "diff_versions",
    "PromptAnalyticsService",
    "track_usage",
    "calculate_effectiveness"
]