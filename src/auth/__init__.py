"""
Authentication package for AIhelpers.

Provides OAuth2 authentication with JWT tokens, password hashing,
and user management for the AIhelpers application.
"""

from .oauth2 import create_access_token, verify_token, get_current_user, create_tokens_for_user
from .password import hash_password, verify_password
from .dependencies import require_auth, optional_auth, require_subscription_tier
from .utils import generate_password_reset_token, verify_password_reset_token

__all__ = [
    "create_access_token",
    "verify_token", 
    "get_current_user",
    "create_tokens_for_user",
    "hash_password",
    "verify_password",
    "require_auth",
    "optional_auth",
    "require_subscription_tier",
    "generate_password_reset_token",
    "verify_password_reset_token",
]