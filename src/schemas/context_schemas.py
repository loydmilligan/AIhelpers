"""
Pydantic models for context-related API requests and responses.

This module defines the data validation and serialization schemas used by
the context preservation API endpoints.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator, constr
from enum import Enum


class ContextFormatType(str, Enum):
    """Supported context format types for tool-specific optimization."""
    CLAUDE_CODE = "claude-code"
    CURSOR = "cursor"
    CHATGPT = "chatgpt"
    COPILOT = "copilot"
    GENERIC = "generic"


class ContextCaptureRequest(BaseModel):
    """
    Request model for capturing new context data.
    
    Attributes:
        ai_tool: Name of the AI tool the context is for
        title: Optional title for the context
        description: Optional description
        tags: Optional list of tags for categorization
        context_data: The actual context data to store
        auto_compress: Whether to automatically compress the context data
    """
    ai_tool: constr(min_length=1, max_length=50) = Field(
        ..., 
        description="AI tool name (e.g., 'claude-code', 'cursor')"
    )
    title: Optional[constr(max_length=200)] = Field(
        None, 
        description="Optional title for the context"
    )
    description: Optional[str] = Field(
        None, 
        description="Optional description of the context"
    )
    tags: Optional[List[constr(max_length=50)]] = Field(
        default_factory=list,
        description="Optional tags for categorization"
    )
    context_data: Dict[str, Any] = Field(
        ..., 
        description="The context data to store"
    )
    auto_compress: bool = Field(
        True, 
        description="Whether to automatically compress the context data"
    )
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is None:
            return []
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")
        return list(set(v))  # Remove duplicates
    
    @validator('context_data')
    def validate_context_data(cls, v):
        if not v:
            raise ValueError("Context data cannot be empty")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "ai_tool": "claude-code",
                "title": "React Component Development Session",
                "description": "Working on user authentication components",
                "tags": ["react", "auth", "frontend"],
                "context_data": {
                    "conversation": [
                        {"role": "user", "content": "Help me create a login component"},
                        {"role": "assistant", "content": "I'll help you create a React login component..."}
                    ],
                    "code_files": {
                        "src/components/Login.tsx": "import React from 'react'..."
                    },
                    "project_state": {
                        "framework": "React",
                        "typescript": True
                    }
                },
                "auto_compress": True
            }
        }


class ContextMetadata(BaseModel):
    """
    Metadata for a stored context.
    
    Attributes:
        id: Unique identifier for the context
        user_id: ID of the user who owns this context
        ai_tool: Name of the AI tool
        title: Title of the context
        description: Description of the context
        tags: List of tags
        created_at: When the context was created
        updated_at: When the context was last updated
        context_size: Size of the context data in bytes
        compression_ratio: Compression ratio achieved (compressed/original)
    """
    id: int = Field(..., description="Unique context identifier")
    user_id: int = Field(..., description="User ID who owns this context")
    ai_tool: str = Field(..., description="AI tool name")
    title: Optional[str] = Field(None, description="Context title")
    description: Optional[str] = Field(None, description="Context description")
    tags: List[str] = Field(default_factory=list, description="Context tags")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    context_size: int = Field(..., description="Context data size in bytes")
    compression_ratio: Optional[float] = Field(None, description="Compression ratio")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "user_id": 123,
                "ai_tool": "claude-code",
                "title": "React Component Development Session",
                "description": "Working on user authentication components",
                "tags": ["react", "auth", "frontend"],
                "created_at": "2024-01-11T10:00:00Z",
                "updated_at": "2024-01-11T11:30:00Z",
                "context_size": 15420,
                "compression_ratio": 0.32
            }
        }


class ContextRestoreResponse(BaseModel):
    """
    Response model for context restoration.
    
    Attributes:
        success: Whether the operation was successful
        context_data: The restored context data
        metadata: Context metadata
        format_optimized: Whether the data was optimized for a specific tool
        error: Error message if operation failed
    """
    success: bool = Field(..., description="Whether restoration was successful")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Restored context data")
    metadata: Optional[ContextMetadata] = Field(None, description="Context metadata")
    format_optimized: bool = Field(False, description="Whether data was format-optimized")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "context_data": {
                    "conversation": [
                        {"role": "user", "content": "Help me create a login component"}
                    ],
                    "code_files": {
                        "src/components/Login.tsx": "import React from 'react'..."
                    }
                },
                "metadata": {
                    "id": 1,
                    "ai_tool": "claude-code",
                    "title": "React Component Development Session"
                },
                "format_optimized": True,
                "error": None
            }
        }


class ContextSearchRequest(BaseModel):
    """
    Request model for searching contexts.
    
    Attributes:
        query: Optional text search query
        ai_tool: Filter by AI tool
        tags: Filter by tags (any of these tags)
        date_from: Filter contexts created after this date
        date_to: Filter contexts created before this date
        limit: Maximum number of results
        offset: Results offset for pagination
        sort_by: Sort field
        sort_order: Sort order (asc/desc)
    """
    query: Optional[str] = Field(None, description="Text search query")
    ai_tool: Optional[str] = Field(None, description="Filter by AI tool")
    tags: Optional[List[str]] = Field(default_factory=list, description="Filter by tags")
    date_from: Optional[datetime] = Field(None, description="Filter contexts created after this date")
    date_to: Optional[datetime] = Field(None, description="Filter contexts created before this date")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Results offset for pagination")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", regex="^(asc|desc)$", description="Sort order")
    
    @validator('query')
    def validate_query(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError("Search query must be at least 2 characters")
        return v.strip() if v else None
    
    class Config:
        schema_extra = {
            "example": {
                "query": "react component",
                "ai_tool": "claude-code",
                "tags": ["react", "frontend"],
                "date_from": "2024-01-01T00:00:00Z",
                "date_to": "2024-01-31T23:59:59Z",
                "limit": 10,
                "offset": 0,
                "sort_by": "created_at",
                "sort_order": "desc"
            }
        }


class ContextSearchResponse(BaseModel):
    """
    Response model for context search results.
    
    Attributes:
        success: Whether the search was successful
        contexts: List of matching contexts
        total_count: Total number of matching contexts
        has_more: Whether there are more results available
        error: Error message if search failed
    """
    success: bool = Field(..., description="Whether search was successful")
    contexts: List[ContextMetadata] = Field(default_factory=list, description="Matching contexts")
    total_count: int = Field(0, description="Total number of matching contexts")
    has_more: bool = Field(False, description="Whether there are more results")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "contexts": [
                    {
                        "id": 1,
                        "ai_tool": "claude-code",
                        "title": "React Component Development",
                        "tags": ["react", "frontend"],
                        "created_at": "2024-01-11T10:00:00Z"
                    }
                ],
                "total_count": 5,
                "has_more": True,
                "error": None
            }
        }


class ContextUpdateRequest(BaseModel):
    """
    Request model for updating existing context.
    
    Attributes:
        title: New title for the context
        description: New description
        tags: New tags list
        context_data: Updated context data (optional)
    """
    title: Optional[constr(max_length=200)] = Field(None, description="New title")
    description: Optional[str] = Field(None, description="New description")
    tags: Optional[List[constr(max_length=50)]] = Field(None, description="New tags")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Updated context data")
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None and len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")
        return list(set(v)) if v else None
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Updated React Component Development Session",
                "description": "Added authentication and routing components",
                "tags": ["react", "auth", "routing", "frontend"],
                "context_data": {
                    "conversation": [
                        {"role": "user", "content": "Now let's add routing..."}
                    ]
                }
            }
        }


class ContextPreviewResponse(BaseModel):
    """
    Response model for context preview (metadata + summary).
    
    Attributes:
        success: Whether preview generation was successful
        metadata: Context metadata
        summary: Brief summary of the context content
        preview_data: Small sample of the context data
        error: Error message if preview failed
    """
    success: bool = Field(..., description="Whether preview was successful")
    metadata: Optional[ContextMetadata] = Field(None, description="Context metadata")
    summary: Optional[str] = Field(None, description="Brief content summary")
    preview_data: Optional[Dict[str, Any]] = Field(None, description="Sample context data")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "metadata": {
                    "id": 1,
                    "title": "React Component Development",
                    "ai_tool": "claude-code",
                    "tags": ["react", "frontend"]
                },
                "summary": "Development session focused on creating React authentication components with TypeScript",
                "preview_data": {
                    "conversation_messages": 12,
                    "code_files": ["Login.tsx", "Register.tsx"],
                    "project_framework": "React"
                },
                "error": None
            }
        }


class SuccessResponse(BaseModel):
    """
    Generic success response model.
    
    Attributes:
        success: Whether the operation was successful
        message: Success message
        data: Optional additional data
    """
    success: bool = Field(..., description="Whether operation was successful")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional additional data")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Context deleted successfully",
                "data": {"context_id": 1}
            }
        }