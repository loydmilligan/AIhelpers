"""
Pydantic schemas package initialization.

Contains data validation and serialization schemas for API requests and responses.
"""

from .context_schemas import (
    ContextCaptureRequest,
    ContextRestoreResponse,
    ContextMetadata,
    ContextSearchRequest
)

# Create a namespace for context schemas
class ContextSchemas:
    """Namespace for context-related schemas."""
    ContextCaptureRequest = ContextCaptureRequest
    ContextRestoreResponse = ContextRestoreResponse
    ContextMetadata = ContextMetadata
    ContextSearchRequest = ContextSearchRequest

__all__ = [
    "ContextSchemas",
    "ContextCaptureRequest",
    "ContextRestoreResponse", 
    "ContextMetadata",
    "ContextSearchRequest"
]