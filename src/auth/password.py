"""
Password hashing and verification utilities.

Uses bcrypt for secure password hashing with proper salt rounds.
"""

import re
from typing import Optional
from passlib.context import CryptContext

# Create password context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Password strength requirements
MIN_PASSWORD_LENGTH = 8
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
        
    Raises:
        ValueError: If password is empty or None
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to check against
        
    Returns:
        True if password matches, False otherwise
    """
    if not plain_password or not hashed_password:
        return False
    
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength requirements.
    
    Requirements:
    - At least 8 characters
    - At least one lowercase letter
    - At least one uppercase letter
    - At least one digit
    - At least one special character (@$!%*?&)
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password cannot be empty"
    
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
    
    if not PASSWORD_PATTERN.match(password):
        return False, (
            "Password must contain at least one lowercase letter, "
            "one uppercase letter, one digit, and one special character (@$!%*?&)"
        )
    
    return True, None


def needs_rehash(hashed_password: str) -> bool:
    """
    Check if a password hash needs to be rehashed.
    
    This is useful when upgrading bcrypt rounds or changing algorithms.
    
    Args:
        hashed_password: Existing hashed password
        
    Returns:
        True if password needs rehashing, False otherwise
    """
    return pwd_context.needs_update(hashed_password)


def generate_temp_password(length: int = 12) -> str:
    """
    Generate a temporary password for password reset.
    
    Args:
        length: Length of generated password (default: 12)
        
    Returns:
        Generated password string
    """
    import secrets
    import string
    
    # Ensure password meets strength requirements
    chars = string.ascii_letters + string.digits + "@$!%*?&"
    
    while True:
        password = ''.join(secrets.choice(chars) for _ in range(length))
        is_valid, _ = validate_password_strength(password)
        if is_valid:
            return password