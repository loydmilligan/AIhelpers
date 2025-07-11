"""
FastAPI routers package.

Contains all API route handlers organized by feature area.
"""

from .prompts import prompt_router

__all__ = ["prompt_router"]