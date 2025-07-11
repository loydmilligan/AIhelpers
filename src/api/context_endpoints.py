"""
FastAPI endpoints for context capture, storage, and retrieval.

This module provides RESTful API endpoints for all context management operations
including capture, restoration, search, and HTMX endpoints for frontend integration.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from config.database import get_db_session
from auth.dependencies import require_auth, get_current_user_context
from models.user import User
from services.context_service import ContextService, ContextValidationError
from schemas.context_schemas import (
    ContextCaptureRequest, ContextRestoreResponse, ContextMetadata,
    ContextSearchRequest, ContextSearchResponse, ContextUpdateRequest,
    ContextPreviewResponse, SuccessResponse, ContextFormatType
)

logger = logging.getLogger(__name__)

# Create router for context endpoints
context_router = APIRouter(prefix="/api/context", tags=["context"])


def get_context_service(db: Session = Depends(get_db_session)) -> ContextService:
    """Dependency to get context service instance."""
    return ContextService(db)


@context_router.post("/capture", response_model=ContextMetadata)
async def capture_context(
    request: ContextCaptureRequest,
    current_user: User = Depends(require_auth),
    service: ContextService = Depends(get_context_service)
):
    """
    Capture and store new context data.
    
    This endpoint allows users to save their AI session context including
    conversation history, code files, and project state.
    """
    try:
        logger.info(f"Capturing context for user {current_user.id}, tool: {request.ai_tool}")
        
        metadata = service.capture_context(current_user.id, request)
        
        logger.info(f"Successfully captured context {metadata.id}")
        return metadata
        
    except ContextValidationError as e:
        logger.error(f"Context validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to capture context: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to capture context")


@context_router.get("/{context_id}", response_model=ContextRestoreResponse)
async def get_context(
    context_id: int,
    format_type: Optional[ContextFormatType] = Query(None, description="Format optimization for specific tool"),
    current_user: User = Depends(require_auth),
    service: ContextService = Depends(get_context_service)
):
    """
    Retrieve specific context by ID.
    
    Returns the full context data, optionally optimized for a specific AI tool format.
    """
    try:
        logger.info(f"Retrieving context {context_id} for user {current_user.id}")
        
        context_data = service.restore_context(context_id, current_user.id, format_type)
        
        # Get metadata for the response
        metadata_list, _ = service.search_contexts(
            current_user.id,
            ContextSearchRequest(limit=1, offset=0)
        )
        
        # Find the specific metadata
        metadata = None
        for meta in metadata_list:
            if meta.id == context_id:
                metadata = meta
                break
        
        return ContextRestoreResponse(
            success=True,
            context_data=context_data,
            metadata=metadata,
            format_optimized=format_type is not None,
            error=None
        )
        
    except ContextValidationError as e:
        logger.error(f"Context retrieval error: {str(e)}")
        return ContextRestoreResponse(
            success=False,
            context_data=None,
            metadata=None,
            format_optimized=False,
            error=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to retrieve context: {str(e)}")
        return ContextRestoreResponse(
            success=False,
            context_data=None,
            metadata=None,
            format_optimized=False,
            error="Failed to retrieve context"
        )


@context_router.put("/{context_id}", response_model=ContextMetadata)
async def update_context(
    context_id: int,
    request: ContextUpdateRequest,
    current_user: User = Depends(require_auth),
    service: ContextService = Depends(get_context_service)
):
    """
    Update existing context.
    
    Allows updating context metadata (title, description, tags) and optionally
    the context data itself.
    """
    try:
        logger.info(f"Updating context {context_id} for user {current_user.id}")
        
        metadata = service.update_context(context_id, current_user.id, request)
        
        logger.info(f"Successfully updated context {context_id}")
        return metadata
        
    except ContextValidationError as e:
        logger.error(f"Context update error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update context: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update context")


@context_router.delete("/{context_id}", response_model=SuccessResponse)
async def delete_context(
    context_id: int,
    current_user: User = Depends(require_auth),
    service: ContextService = Depends(get_context_service)
):
    """
    Delete a context.
    
    Permanently removes the context and all associated snapshots.
    """
    try:
        logger.info(f"Deleting context {context_id} for user {current_user.id}")
        
        success = service.delete_context(context_id, current_user.id)
        
        if success:
            logger.info(f"Successfully deleted context {context_id}")
            return SuccessResponse(
                success=True,
                message="Context deleted successfully",
                data={"context_id": context_id}
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to delete context")
        
    except ContextValidationError as e:
        logger.error(f"Context deletion error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete context: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete context")


@context_router.get("/search", response_model=ContextSearchResponse)
async def search_contexts(
    query: Optional[str] = Query(None, description="Text search query"),
    ai_tool: Optional[str] = Query(None, description="Filter by AI tool"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(require_auth),
    service: ContextService = Depends(get_context_service)
):
    """
    Search contexts with filtering and pagination.
    
    Supports text search, filtering by AI tool and tags, and pagination.
    """
    try:
        logger.info(f"Searching contexts for user {current_user.id}")
        
        search_request = ContextSearchRequest(
            query=query,
            ai_tool=ai_tool,
            tags=tags or [],
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        contexts, total_count = service.search_contexts(current_user.id, search_request)
        
        has_more = (offset + limit) < total_count
        
        return ContextSearchResponse(
            success=True,
            contexts=contexts,
            total_count=total_count,
            has_more=has_more,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Failed to search contexts: {str(e)}")
        return ContextSearchResponse(
            success=False,
            contexts=[],
            total_count=0,
            has_more=False,
            error="Failed to search contexts"
        )


@context_router.post("/restore/{context_id}", response_model=ContextRestoreResponse)
async def restore_context_for_tool(
    context_id: int,
    tool_format: ContextFormatType = Query(..., description="Target tool format"),
    current_user: User = Depends(require_auth),
    service: ContextService = Depends(get_context_service)
):
    """
    Restore context optimized for specific tool.
    
    This endpoint retrieves context data and formats it specifically for the
    target AI tool (Claude Code, Cursor, etc.).
    """
    try:
        logger.info(f"Restoring context {context_id} for {tool_format} for user {current_user.id}")
        
        context_data = service.restore_context(context_id, current_user.id, tool_format)
        
        return ContextRestoreResponse(
            success=True,
            context_data=context_data,
            metadata=None,  # Metadata not needed for tool restoration
            format_optimized=True,
            error=None
        )
        
    except ContextValidationError as e:
        logger.error(f"Context restoration error: {str(e)}")
        return ContextRestoreResponse(
            success=False,
            context_data=None,
            metadata=None,
            format_optimized=False,
            error=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to restore context for tool: {str(e)}")
        return ContextRestoreResponse(
            success=False,
            context_data=None,
            metadata=None,
            format_optimized=False,
            error="Failed to restore context"
        )


@context_router.get("/preview/{context_id}", response_model=ContextPreviewResponse)
async def get_context_preview(
    context_id: int,
    current_user: User = Depends(require_auth),
    service: ContextService = Depends(get_context_service)
):
    """
    Get context preview with summary and metadata.
    
    Returns context metadata and a summary without loading the full context data.
    Useful for context browsing and selection interfaces.
    """
    try:
        logger.info(f"Getting preview for context {context_id} for user {current_user.id}")
        
        preview_data = service.get_context_preview(context_id, current_user.id)
        
        return ContextPreviewResponse(
            success=True,
            metadata=preview_data["metadata"],
            summary=preview_data["summary"],
            preview_data=preview_data["preview_data"],
            error=None
        )
        
    except ContextValidationError as e:
        logger.error(f"Context preview error: {str(e)}")
        return ContextPreviewResponse(
            success=False,
            metadata=None,
            summary=None,
            preview_data=None,
            error=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get context preview: {str(e)}")
        return ContextPreviewResponse(
            success=False,
            metadata=None,
            summary=None,
            preview_data=None,
            error="Failed to get context preview"
        )


@context_router.post("/snapshot/{context_id}", response_model=SuccessResponse)
async def create_context_snapshot(
    context_id: int,
    description: Optional[str] = Query(None, description="Snapshot description"),
    current_user: User = Depends(require_auth),
    service: ContextService = Depends(get_context_service)
):
    """
    Create a snapshot of the current context state.
    
    Snapshots allow tracking context changes over time and reverting to
    previous states if needed.
    """
    try:
        logger.info(f"Creating snapshot for context {context_id} for user {current_user.id}")
        
        snapshot_id = service.create_snapshot(context_id, current_user.id, description)
        
        return SuccessResponse(
            success=True,
            message="Snapshot created successfully",
            data={"snapshot_id": snapshot_id, "context_id": context_id}
        )
        
    except ContextValidationError as e:
        logger.error(f"Snapshot creation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create snapshot: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create snapshot")


# HTMX endpoints for frontend integration
@context_router.get("/htmx/list", response_class=HTMLResponse)
async def htmx_context_list(
    request: Request,
    query: Optional[str] = Query(None),
    ai_tool: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_auth),
    service: ContextService = Depends(get_context_service)
):
    """
    HTMX endpoint for context list display.
    
    Returns HTML fragment with context list for dynamic loading.
    """
    try:
        search_request = ContextSearchRequest(
            query=query,
            ai_tool=ai_tool,
            limit=limit,
            offset=offset,
            sort_by="updated_at",
            sort_order="desc"
        )
        
        contexts, total_count = service.search_contexts(current_user.id, search_request)
        
        # Generate HTML for context list
        html_content = "<div class='context-list'>"
        
        if not contexts:
            html_content += "<p class='no-contexts'>No contexts found.</p>"
        else:
            for context in contexts:
                size_mb = context.context_size / (1024 * 1024)
                compression_info = ""
                if context.compression_ratio:
                    savings = (1 - context.compression_ratio) * 100
                    compression_info = f" ({savings:.1f}% compressed)"
                
                html_content += f"""
                <div class='context-item' data-context-id='{context.id}'>
                    <div class='context-header'>
                        <h4>{context.title or 'Untitled Context'}</h4>
                        <span class='context-tool'>{context.ai_tool}</span>
                    </div>
                    <div class='context-meta'>
                        <span class='context-size'>{size_mb:.2f}MB{compression_info}</span>
                        <span class='context-date'>{context.updated_at.strftime('%Y-%m-%d %H:%M')}</span>
                    </div>
                    {f"<div class='context-tags'>{' '.join([f'<span class=\"tag\">{tag}</span>' for tag in context.tags])}</div>" if context.tags else ""}
                    <div class='context-actions'>
                        <button class='btn-preview' onclick='previewContext({context.id})'>Preview</button>
                        <button class='btn-restore' onclick='restoreContext({context.id})'>Restore</button>
                        <button class='btn-delete' onclick='deleteContext({context.id})'>Delete</button>
                    </div>
                </div>
                """
        
        html_content += "</div>"
        
        # Add pagination if needed
        if total_count > limit:
            has_next = (offset + limit) < total_count
            has_prev = offset > 0
            
            html_content += "<div class='pagination'>"
            if has_prev:
                prev_offset = max(0, offset - limit)
                html_content += f"<button hx-get='/api/context/htmx/list?offset={prev_offset}&limit={limit}' hx-target='#context-list' class='btn-pagination'>Previous</button>"
            
            html_content += f"<span class='pagination-info'>Showing {offset + 1}-{min(offset + limit, total_count)} of {total_count}</span>"
            
            if has_next:
                next_offset = offset + limit
                html_content += f"<button hx-get='/api/context/htmx/list?offset={next_offset}&limit={limit}' hx-target='#context-list' class='btn-pagination'>Next</button>"
            
            html_content += "</div>"
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Failed to generate HTMX context list: {str(e)}")
        return HTMLResponse(content="<div class='error'>Failed to load contexts</div>")


@context_router.get("/htmx/save-form", response_class=HTMLResponse)
async def htmx_save_form(request: Request):
    """
    HTMX endpoint for context save form.
    
    Returns HTML form for saving new context.
    """
    html_content = """
    <form class='context-save-form' hx-post='/api/context/capture' hx-target='#save-result'>
        <div class='form-group'>
            <label for='ai_tool'>AI Tool:</label>
            <select name='ai_tool' required>
                <option value='claude-code'>Claude Code</option>
                <option value='cursor'>Cursor</option>
                <option value='chatgpt'>ChatGPT</option>
                <option value='copilot'>GitHub Copilot</option>
                <option value='generic'>Generic</option>
            </select>
        </div>
        
        <div class='form-group'>
            <label for='title'>Title:</label>
            <input type='text' name='title' placeholder='Enter context title...'>
        </div>
        
        <div class='form-group'>
            <label for='description'>Description:</label>
            <textarea name='description' placeholder='Enter context description...' rows='3'></textarea>
        </div>
        
        <div class='form-group'>
            <label for='tags'>Tags (comma-separated):</label>
            <input type='text' name='tags' placeholder='react, frontend, auth...'>
        </div>
        
        <div class='form-group'>
            <label for='context_data'>Context Data (JSON):</label>
            <textarea name='context_data' placeholder='Paste your context data as JSON...' rows='10' required></textarea>
        </div>
        
        <div class='form-actions'>
            <button type='submit' class='btn-primary'>Save Context</button>
            <button type='button' class='btn-secondary' onclick='hideContextForm()'>Cancel</button>
        </div>
    </form>
    """
    
    return HTMLResponse(content=html_content)


@context_router.get("/htmx/preview/{context_id}", response_class=HTMLResponse)
async def htmx_context_preview(
    context_id: int,
    current_user: User = Depends(require_auth),
    service: ContextService = Depends(get_context_service)
):
    """
    HTMX endpoint for context preview display.
    
    Returns HTML fragment with context preview information.
    """
    try:
        preview_data = service.get_context_preview(context_id, current_user.id)
        metadata = preview_data["metadata"]
        summary = preview_data["summary"]
        preview = preview_data["preview_data"]
        
        html_content = f"""
        <div class='context-preview'>
            <div class='preview-header'>
                <h3>{metadata.title or 'Untitled Context'}</h3>
                <span class='context-id'>ID: {metadata.id}</span>
            </div>
            
            <div class='preview-summary'>
                <p>{summary}</p>
            </div>
            
            <div class='preview-details'>
                <div class='detail-row'>
                    <strong>AI Tool:</strong> {metadata.ai_tool}
                </div>
                <div class='detail-row'>
                    <strong>Size:</strong> {preview['data_size'] / (1024*1024):.2f}MB
                </div>
                <div class='detail-row'>
                    <strong>Created:</strong> {metadata.created_at.strftime('%Y-%m-%d %H:%M:%S')}
                </div>
                <div class='detail-row'>
                    <strong>Updated:</strong> {metadata.updated_at.strftime('%Y-%m-%d %H:%M:%S')}
                </div>
                {"<div class='detail-row'><strong>Compression:</strong> " + preview.get('compression_savings', 'None') + "</div>" if 'compression_savings' in preview else ""}
            </div>
            
            <div class='preview-content'>
                <h4>Content Preview:</h4>
                <ul>
                    <li>Conversation: {'✓' if preview.get('has_conversation') else '✗'}</li>
                    <li>Code Files: {'✓' if preview.get('has_code_files') else '✗'}</li>
                    <li>Project State: {'✓' if preview.get('has_project_state') else '✗'}</li>
                </ul>
            </div>
            
            {"<div class='preview-tags'>" + " ".join([f"<span class='tag'>{tag}</span>" for tag in metadata.tags]) + "</div>" if metadata.tags else ""}
            
            <div class='preview-actions'>
                <button class='btn-primary' onclick='restoreContext({context_id})'>Restore Full Context</button>
                <button class='btn-secondary' onclick='hidePreview()'>Close</button>
            </div>
        </div>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Failed to generate HTMX context preview: {str(e)}")
        return HTMLResponse(content="<div class='error'>Failed to load context preview</div>")