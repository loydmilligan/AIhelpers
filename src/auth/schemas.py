"""
Pydantic schemas for authentication requests and responses.

Defines data validation models for authentication API endpoints.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime

from ..models.user import SubscriptionTier


class UserRegistrationRequest(BaseModel):
    """Schema for user registration request."""
    
    email: EmailStr
    name: str
    password: str
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        if len(v.strip()) > 100:
            raise ValueError('Name must be less than 100 characters')
        return v.strip()
    
    @validator('password')
    def validate_password(cls, v):
        # Import here to avoid circular imports
        from .password import validate_password_strength
        
        is_valid, error_message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_message)
        return v


class UserLoginRequest(BaseModel):
    """Schema for user login request."""
    
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for token response."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # seconds


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh request."""
    
    refresh_token: str


class AccessTokenResponse(BaseModel):
    """Schema for access token response."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # seconds


class UserResponse(BaseModel):
    """Schema for user response."""
    
    id: int
    email: str
    name: str
    subscription_tier: SubscriptionTier
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """Schema for user profile response."""
    
    id: int
    email: str
    name: str
    subscription_tier: SubscriptionTier
    is_active: bool
    is_premium: bool
    can_create_teams: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserProfileUpdateRequest(BaseModel):
    """Schema for user profile update request."""
    
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Name cannot be empty')
            if len(v.strip()) < 2:
                raise ValueError('Name must be at least 2 characters long')
            if len(v.strip()) > 100:
                raise ValueError('Name must be less than 100 characters')
            return v.strip()
        return v


class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""
    
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        # Import here to avoid circular imports
        from .password import validate_password_strength
        
        is_valid, error_message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_message)
        return v


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    """Schema for password reset confirmation."""
    
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        # Import here to avoid circular imports
        from .password import validate_password_strength
        
        is_valid, error_message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_message)
        return v


class AuthenticationResponse(BaseModel):
    """Schema for authentication response."""
    
    success: bool
    message: str
    user: Optional[UserResponse] = None
    tokens: Optional[TokenResponse] = None


class ErrorResponse(BaseModel):
    """Schema for error response."""
    
    success: bool = False
    error: str
    detail: Optional[str] = None


class SuccessResponse(BaseModel):
    """Schema for success response."""
    
    success: bool = True
    message: str
    data: Optional[dict] = None


class UserContextResponse(BaseModel):
    """Schema for user context response."""
    
    user_id: int
    email: str
    name: str
    subscription_tier: str
    is_premium: bool
    can_create_teams: bool


class SubscriptionTierUpdateRequest(BaseModel):
    """Schema for subscription tier update request."""
    
    subscription_tier: SubscriptionTier
    
    @validator('subscription_tier')
    def validate_subscription_tier(cls, v):
        if v not in [SubscriptionTier.FREE, SubscriptionTier.PROFESSIONAL, SubscriptionTier.TEAM]:
            raise ValueError('Invalid subscription tier')
        return v


class LoginResponse(BaseModel):
    """Schema for login response."""
    
    success: bool
    message: str
    user: UserProfileResponse
    tokens: TokenResponse


class RegisterResponse(BaseModel):
    """Schema for registration response."""
    
    success: bool
    message: str
    user: UserResponse
    tokens: TokenResponse