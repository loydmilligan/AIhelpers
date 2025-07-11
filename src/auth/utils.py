"""
Authentication utility functions.

Provides utility functions for token generation, email validation, and other auth-related tasks.
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from email_validator import validate_email, EmailNotValidError


# Password reset token configuration
PASSWORD_RESET_SECRET_KEY = os.getenv("PASSWORD_RESET_SECRET_KEY", "password-reset-secret-key")
PASSWORD_RESET_EXPIRE_MINUTES = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "30"))


def generate_password_reset_token(email: str) -> str:
    """
    Generate a secure password reset token.
    
    Args:
        email: User's email address
        
    Returns:
        Password reset token
    """
    expire = datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
    to_encode = {
        "email": email,
        "exp": expire,
        "type": "password_reset",
        "nonce": secrets.token_hex(16)  # Add randomness to prevent reuse
    }
    
    token = jwt.encode(to_encode, PASSWORD_RESET_SECRET_KEY, algorithm="HS256")
    return token


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify and decode password reset token.
    
    Args:
        token: Password reset token to verify
        
    Returns:
        Email address if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, PASSWORD_RESET_SECRET_KEY, algorithms=["HS256"])
        
        # Check token type
        if payload.get("type") != "password_reset":
            return None
        
        # Check expiration
        expire = payload.get("exp")
        if expire is None:
            return None
        
        if datetime.utcnow() > datetime.fromtimestamp(expire):
            return None
        
        return payload.get("email")
    
    except jwt.JWTError:
        return None


def validate_email_address(email: str) -> tuple[bool, Optional[str]]:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple of (is_valid, normalized_email)
    """
    try:
        validation = validate_email(email)
        return True, validation.email
    except EmailNotValidError:
        return False, None


def generate_verification_token() -> str:
    """
    Generate a secure email verification token.
    
    Returns:
        Verification token
    """
    return secrets.token_urlsafe(32)


def generate_api_key() -> str:
    """
    Generate a secure API key.
    
    Returns:
        API key string
    """
    return secrets.token_urlsafe(32)


def is_strong_password(password: str) -> bool:
    """
    Check if password meets strength requirements.
    
    Args:
        password: Password to check
        
    Returns:
        True if password is strong, False otherwise
    """
    from .password import validate_password_strength
    
    is_valid, _ = validate_password_strength(password)
    return is_valid


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token.
    
    Args:
        length: Length of token in bytes
        
    Returns:
        URL-safe token string
    """
    return secrets.token_urlsafe(length)


def hash_user_data(user_id: int, email: str) -> str:
    """
    Create a hash of user data for cache keys or similar purposes.
    
    Args:
        user_id: User ID
        email: User email
        
    Returns:
        Hash string
    """
    import hashlib
    
    data = f"{user_id}:{email}"
    return hashlib.sha256(data.encode()).hexdigest()


def is_email_domain_allowed(email: str, allowed_domains: Optional[list] = None) -> bool:
    """
    Check if email domain is allowed.
    
    Args:
        email: Email address to check
        allowed_domains: List of allowed domains (None means all domains allowed)
        
    Returns:
        True if domain is allowed, False otherwise
    """
    if not allowed_domains:
        return True
    
    try:
        domain = email.split('@')[1].lower()
        return domain in [d.lower() for d in allowed_domains]
    except IndexError:
        return False


def format_user_display_name(name: str) -> str:
    """
    Format user display name consistently.
    
    Args:
        name: Raw user name
        
    Returns:
        Formatted display name
    """
    if not name:
        return ""
    
    # Remove extra whitespace and capitalize properly
    formatted = ' '.join(word.capitalize() for word in name.split())
    return formatted


def get_user_avatar_url(email: str, size: int = 200) -> str:
    """
    Generate Gravatar URL for user avatar.
    
    Args:
        email: User's email address
        size: Avatar size in pixels
        
    Returns:
        Gravatar URL
    """
    import hashlib
    
    email_hash = hashlib.md5(email.lower().encode()).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=identicon"


def calculate_token_expiry(minutes: int) -> datetime:
    """
    Calculate token expiry time.
    
    Args:
        minutes: Minutes until expiry
        
    Returns:
        Expiry datetime
    """
    return datetime.utcnow() + timedelta(minutes=minutes)


def is_token_expired(exp_timestamp: float) -> bool:
    """
    Check if token is expired.
    
    Args:
        exp_timestamp: Expiry timestamp
        
    Returns:
        True if expired, False otherwise
    """
    return datetime.utcnow() > datetime.fromtimestamp(exp_timestamp)


def sanitize_user_input(input_string: str) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        input_string: Input string to sanitize
        
    Returns:
        Sanitized string
    """
    if not input_string:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
    sanitized = input_string
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized.strip()


def validate_subscription_tier_upgrade(current_tier: str, new_tier: str) -> bool:
    """
    Validate subscription tier upgrade path.
    
    Args:
        current_tier: Current subscription tier
        new_tier: Requested new tier
        
    Returns:
        True if upgrade is valid, False otherwise
    """
    tier_hierarchy = {
        "free": 0,
        "professional": 1,
        "team": 2
    }
    
    current_level = tier_hierarchy.get(current_tier.lower(), 0)
    new_level = tier_hierarchy.get(new_tier.lower(), 0)
    
    # Allow upgrades and same tier (for renewal)
    return new_level >= current_level