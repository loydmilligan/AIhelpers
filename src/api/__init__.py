"""
API modules package initialization.

Contains FastAPI routers and endpoints for various application features.
"""

from .context_endpoints import context_router

__all__ = ["context_router"]