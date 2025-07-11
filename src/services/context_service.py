"""
Core context preservation service with capture, storage, and restoration logic.

This service handles all business logic for managing AI session contexts including
compression, validation, optimization, and tool-specific formatting.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func

from models.session_context import SessionContext, ContextSnapshot
from utils.context_compression import (
    compress_context, decompress_context, estimate_context_size,
    optimize_context_for_storage, validate_context_size
)
from schemas.context_schemas import (
    ContextCaptureRequest, ContextMetadata, ContextSearchRequest,
    ContextUpdateRequest, ContextFormatType
)

logger = logging.getLogger(__name__)


class ContextValidationError(Exception):
    """Raised when context data validation fails."""
    pass


class ContextCompressionUtility:
    """Utility class for context compression operations."""
    
    @staticmethod
    def compress_with_metadata(context_data: Dict[str, Any]) -> Tuple[bytes, Dict[str, Any]]:
        """
        Compress context data and return compression metadata.
        
        Returns:
            Tuple of (compressed_data, compression_metadata)
        """
        try:
            # Optimize data for compression
            optimized_data = optimize_context_for_storage(context_data)
            
            # Get size estimates
            uncompressed_size, compressed_size, compression_ratio = estimate_context_size(optimized_data)
            
            # Compress the data
            compressed_data = compress_context(optimized_data)
            
            # Create metadata
            metadata = {
                "uncompressed_size": uncompressed_size,
                "compressed_size": len(compressed_data),
                "compression_ratio": len(compressed_data) / uncompressed_size,
                "optimization_applied": True,
                "compression_algorithm": "zlib"
            }
            
            return compressed_data, metadata
            
        except Exception as e:
            raise ContextValidationError(f"Failed to compress context: {str(e)}")


class ContextService:
    """
    Core service for context preservation operations.
    
    Handles context capture, storage, retrieval, and management with support
    for compression, search, and tool-specific optimization.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize the context service.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self.compression_util = ContextCompressionUtility()
    
    def capture_context(
        self, 
        user_id: int, 
        request: ContextCaptureRequest
    ) -> ContextMetadata:
        """
        Capture and store new context data.
        
        Args:
            user_id: ID of the user capturing the context
            request: Context capture request with data and metadata
            
        Returns:
            Metadata for the captured context
            
        Raises:
            ContextValidationError: If context data is invalid or too large
        """
        try:
            # Validate context data size
            if not validate_context_size(request.context_data):
                raise ContextValidationError("Context data exceeds maximum size limit")
            
            # Process context data
            if request.auto_compress:
                # Compress with metadata
                compressed_data, compression_metadata = self.compression_util.compress_with_metadata(
                    request.context_data
                )
                
                # Store as compressed JSON in database
                context_json = {
                    "data": compressed_data.hex(),  # Store as hex string
                    "compressed": True,
                    "metadata": compression_metadata
                }
            else:
                # Store uncompressed
                context_json = {
                    "data": request.context_data,
                    "compressed": False,
                    "metadata": {"uncompressed_size": len(str(request.context_data))}
                }
            
            # Create database record
            context_record = SessionContext(
                user_id=user_id,
                ai_tool=request.ai_tool,
                context_data=context_json,
                session_metadata=compression_metadata if request.auto_compress else {},
                title=request.title,
                description=request.description,
                tags=request.tags or []
            )
            
            self.db.add(context_record)
            self.db.commit()
            self.db.refresh(context_record)
            
            # Return metadata
            return self._create_metadata_from_record(context_record)
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, ContextValidationError):
                raise
            raise ContextValidationError(f"Failed to capture context: {str(e)}")
    
    def restore_context(
        self, 
        context_id: int, 
        user_id: int,
        format_type: Optional[ContextFormatType] = None
    ) -> Dict[str, Any]:
        """
        Restore context data by ID.
        
        Args:
            context_id: ID of the context to restore
            user_id: ID of the user requesting the context
            format_type: Optional format optimization for specific tools
            
        Returns:
            Restored context data
            
        Raises:
            ContextValidationError: If context not found or access denied
        """
        try:
            # Find context record
            context_record = self.db.query(SessionContext).filter(
                and_(
                    SessionContext.id == context_id,
                    SessionContext.user_id == user_id
                )
            ).first()
            
            if not context_record:
                raise ContextValidationError(f"Context {context_id} not found or access denied")
            
            # Extract context data
            context_json = context_record.context_data
            
            if context_json.get("compressed", False):
                # Decompress data
                compressed_hex = context_json["data"]
                compressed_bytes = bytes.fromhex(compressed_hex)
                context_data = decompress_context(compressed_bytes)
            else:
                # Use uncompressed data
                context_data = context_json["data"]
            
            # Apply format optimization if requested
            if format_type:
                context_data = self._optimize_for_tool(context_data, format_type)
            
            return context_data
            
        except Exception as e:
            if isinstance(e, ContextValidationError):
                raise
            raise ContextValidationError(f"Failed to restore context: {str(e)}")
    
    def update_context(
        self, 
        context_id: int, 
        user_id: int, 
        request: ContextUpdateRequest
    ) -> ContextMetadata:
        """
        Update existing context.
        
        Args:
            context_id: ID of the context to update
            user_id: ID of the user updating the context
            request: Update request with new data
            
        Returns:
            Updated context metadata
            
        Raises:
            ContextValidationError: If context not found or update fails
        """
        try:
            # Find context record
            context_record = self.db.query(SessionContext).filter(
                and_(
                    SessionContext.id == context_id,
                    SessionContext.user_id == user_id
                )
            ).first()
            
            if not context_record:
                raise ContextValidationError(f"Context {context_id} not found or access denied")
            
            # Update metadata fields
            if request.title is not None:
                context_record.title = request.title
            
            if request.description is not None:
                context_record.description = request.description
            
            if request.tags is not None:
                context_record.tags = request.tags
            
            # Update context data if provided
            if request.context_data is not None:
                if not validate_context_size(request.context_data):
                    raise ContextValidationError("Updated context data exceeds maximum size limit")
                
                # Compress and store new data
                compressed_data, compression_metadata = self.compression_util.compress_with_metadata(
                    request.context_data
                )
                
                context_json = {
                    "data": compressed_data.hex(),
                    "compressed": True,
                    "metadata": compression_metadata
                }
                
                context_record.context_data = context_json
                context_record.session_metadata = compression_metadata
            
            # Update timestamp
            context_record.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(context_record)
            
            return self._create_metadata_from_record(context_record)
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, ContextValidationError):
                raise
            raise ContextValidationError(f"Failed to update context: {str(e)}")
    
    def delete_context(self, context_id: int, user_id: int) -> bool:
        """
        Delete a context.
        
        Args:
            context_id: ID of the context to delete
            user_id: ID of the user deleting the context
            
        Returns:
            True if deleted successfully
            
        Raises:
            ContextValidationError: If context not found or deletion fails
        """
        try:
            # Find context record
            context_record = self.db.query(SessionContext).filter(
                and_(
                    SessionContext.id == context_id,
                    SessionContext.user_id == user_id
                )
            ).first()
            
            if not context_record:
                raise ContextValidationError(f"Context {context_id} not found or access denied")
            
            self.db.delete(context_record)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, ContextValidationError):
                raise
            raise ContextValidationError(f"Failed to delete context: {str(e)}")
    
    def search_contexts(
        self, 
        user_id: int, 
        request: ContextSearchRequest
    ) -> Tuple[List[ContextMetadata], int]:
        """
        Search contexts with filtering and pagination.
        
        Args:
            user_id: ID of the user searching
            request: Search request with filters and pagination
            
        Returns:
            Tuple of (matching_contexts, total_count)
        """
        try:
            # Build base query
            query = self.db.query(SessionContext).filter(SessionContext.user_id == user_id)
            
            # Apply filters
            if request.ai_tool:
                query = query.filter(SessionContext.ai_tool == request.ai_tool)
            
            if request.tags:
                # Filter by any of the specified tags
                tag_filters = [SessionContext.tags.contains([tag]) for tag in request.tags]
                query = query.filter(or_(*tag_filters))
            
            if request.date_from:
                query = query.filter(SessionContext.created_at >= request.date_from)
            
            if request.date_to:
                query = query.filter(SessionContext.created_at <= request.date_to)
            
            if request.query:
                # Text search in title and description
                text_filter = or_(
                    SessionContext.title.ilike(f"%{request.query}%"),
                    SessionContext.description.ilike(f"%{request.query}%")
                )
                query = query.filter(text_filter)
            
            # Get total count
            total_count = query.count()
            
            # Apply sorting
            sort_column = getattr(SessionContext, request.sort_by, SessionContext.created_at)
            if request.sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # Apply pagination
            query = query.offset(request.offset).limit(request.limit)
            
            # Execute query
            contexts = query.all()
            
            # Convert to metadata
            metadata_list = [self._create_metadata_from_record(ctx) for ctx in contexts]
            
            return metadata_list, total_count
            
        except Exception as e:
            raise ContextValidationError(f"Failed to search contexts: {str(e)}")
    
    def get_context_preview(self, context_id: int, user_id: int) -> Dict[str, Any]:
        """
        Get a preview of context data without full restoration.
        
        Args:
            context_id: ID of the context
            user_id: ID of the user requesting the preview
            
        Returns:
            Dictionary with preview data and summary
        """
        try:
            context_record = self.db.query(SessionContext).filter(
                and_(
                    SessionContext.id == context_id,
                    SessionContext.user_id == user_id
                )
            ).first()
            
            if not context_record:
                raise ContextValidationError(f"Context {context_id} not found or access denied")
            
            # Get basic metadata
            metadata = self._create_metadata_from_record(context_record)
            
            # Generate summary
            summary = self._generate_context_summary(context_record)
            
            # Create preview data (small sample)
            preview_data = self._create_preview_data(context_record)
            
            return {
                "metadata": metadata,
                "summary": summary,
                "preview_data": preview_data
            }
            
        except Exception as e:
            if isinstance(e, ContextValidationError):
                raise
            raise ContextValidationError(f"Failed to get context preview: {str(e)}")
    
    def create_snapshot(
        self, 
        context_id: int, 
        user_id: int, 
        description: Optional[str] = None
    ) -> int:
        """
        Create a snapshot of the current context state.
        
        Args:
            context_id: ID of the context to snapshot
            user_id: ID of the user creating the snapshot
            description: Optional description for the snapshot
            
        Returns:
            ID of the created snapshot
        """
        try:
            context_record = self.db.query(SessionContext).filter(
                and_(
                    SessionContext.id == context_id,
                    SessionContext.user_id == user_id
                )
            ).first()
            
            if not context_record:
                raise ContextValidationError(f"Context {context_id} not found or access denied")
            
            # Create snapshot using the model method
            snapshot = context_record.create_snapshot(
                snapshot_data=context_record.context_data,
                description=description
            )
            
            self.db.add(snapshot)
            self.db.commit()
            self.db.refresh(snapshot)
            
            return snapshot.id
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, ContextValidationError):
                raise
            raise ContextValidationError(f"Failed to create snapshot: {str(e)}")
    
    def _create_metadata_from_record(self, record: SessionContext) -> ContextMetadata:
        """Convert database record to metadata object."""
        context_size = record.get_context_size()
        compression_ratio = None
        
        if record.session_metadata and "compression_ratio" in record.session_metadata:
            compression_ratio = record.session_metadata["compression_ratio"]
        
        return ContextMetadata(
            id=record.id,
            user_id=record.user_id,
            ai_tool=record.ai_tool,
            title=record.title,
            description=record.description,
            tags=record.get_tags_list(),
            created_at=record.created_at,
            updated_at=record.updated_at,
            context_size=context_size,
            compression_ratio=compression_ratio
        )
    
    def _optimize_for_tool(self, context_data: Dict[str, Any], format_type: ContextFormatType) -> Dict[str, Any]:
        """Apply tool-specific optimizations to context data."""
        if format_type == ContextFormatType.CLAUDE_CODE:
            # Optimize for Claude Code format
            return {
                "files": context_data.get("code_files", {}),
                "conversation": context_data.get("conversation", []),
                "project_context": context_data.get("project_state", {}),
                "instructions": context_data.get("custom_data", {}).get("instructions", "")
            }
        elif format_type == ContextFormatType.CURSOR:
            # Optimize for Cursor format
            return {
                "workspace": context_data.get("code_files", {}),
                "chat_history": context_data.get("conversation", []),
                "project_config": context_data.get("project_state", {})
            }
        else:
            # Return generic format
            return context_data
    
    def _generate_context_summary(self, record: SessionContext) -> str:
        """Generate a brief summary of context content."""
        summary_parts = []
        
        if record.title:
            summary_parts.append(f"Title: {record.title}")
        
        summary_parts.append(f"AI Tool: {record.ai_tool}")
        
        if record.get_tags_list():
            summary_parts.append(f"Tags: {', '.join(record.get_tags_list())}")
        
        # Add size information
        size_mb = record.get_context_size() / (1024 * 1024)
        summary_parts.append(f"Size: {size_mb:.2f}MB")
        
        return " | ".join(summary_parts)
    
    def _create_preview_data(self, record: SessionContext) -> Dict[str, Any]:
        """Create preview data with limited information."""
        context_data = record.context_data
        
        preview = {
            "has_conversation": "conversation" in str(context_data),
            "has_code_files": "code_files" in str(context_data),
            "has_project_state": "project_state" in str(context_data),
            "data_size": record.get_context_size(),
            "created": record.created_at.isoformat(),
            "last_updated": record.updated_at.isoformat()
        }
        
        # Add compression info if available
        if record.session_metadata and "compression_ratio" in record.session_metadata:
            preview["compression_ratio"] = record.session_metadata["compression_ratio"]
            preview["compression_savings"] = f"{(1 - record.session_metadata['compression_ratio']) * 100:.1f}%"
        
        return preview