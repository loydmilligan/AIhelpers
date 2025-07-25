from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
project_root = Path(__file__).parent.parent.parent
env_files = [
    project_root / ".env",
    project_root / ".env.txt"
]

for env_file in env_files:
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded environment from: {env_file}")
        break

# Add the src directory to Python path so we can import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
sys.path.insert(0, src_dir)

# Import our existing CLI logic
from prompt_generator import parse_template, assemble_prompt
from utils import save_as_json

# Import Parsinator service
from parsinator_service import get_parsinator_service

# Import routers
from routers.prompts import prompt_router
from api.context_endpoints import context_router

# Import authentication modules
from auth import (
    hash_password, verify_password, create_tokens_for_user,
    require_auth, optional_auth, get_current_user_context
)
from auth.schemas import (
    UserRegistrationRequest, UserLoginRequest, TokenResponse, 
    UserProfileResponse, UserProfileUpdateRequest, PasswordChangeRequest,
    PasswordResetRequest, PasswordResetConfirmRequest, LoginResponse, 
    RegisterResponse, AuthenticationResponse, ErrorResponse, SuccessResponse,
    EmailVerificationRequest, ResendVerificationRequest
)
from auth.subscription_schemas import (
    SubscriptionStatusResponse, SubscriptionChangeRequest, SubscriptionChangeResponse,
    UsageStatsResponse, TierLimits, UsageStatistics, RemainingUsage,
    SubscriptionHealthResponse
)
from auth.usage_limits import (
    check_prompt_limit, check_brief_limit, check_validation_limit,
    get_usage_stats, track_prompt_usage, track_brief_usage, track_validation_usage
)
from auth.utils import (
    generate_password_reset_token, verify_password_reset_token,
    validate_email_address, format_user_display_name, generate_verification_token
)
from models.user import User, SubscriptionTier
from models.prompt import Prompt
from config.database import get_db_session
from services.prompt_analytics import PromptAnalyticsService
from services.subscription_service import SubscriptionService
from services.email_service import email_service

app = FastAPI(title="AI Prompt Helper API", version="1.0.0")

# =============================================================================
# API ENDPOINT SECURITY SUMMARY
# =============================================================================
# 
# PROTECTED ENDPOINTS (Require Authentication):
# - POST /api/generate - Requires check_prompt_limit (includes auth)
# - POST /api/parsinator/process-brief - Requires check_brief_limit (includes auth)
# - POST /api/parsinator/validate-brief - Requires check_validation_limit (includes auth)
# - GET  /auth/profile - Requires auth
# - PUT  /auth/profile - Requires auth  
# - POST /auth/change-password - Requires auth
# - POST /auth/logout - Requires auth
# - GET  /auth/subscription/status - Requires auth
# - POST /auth/subscription/change - Requires auth
# - GET  /auth/subscription/usage - Requires auth
#
# PARTIALLY PROTECTED ENDPOINTS (Optional Authentication):
# - POST /api/parse-template - Optional auth for usage tracking
#
# PUBLIC ENDPOINTS (No Authentication Required):
# - GET  /api/templates - Browse available templates
# - GET  /api/parsinator/health - Health check
# - GET  /api/parsinator/templates - Browse brief templates
# - GET  /auth/health - Auth system health check
# - GET  /auth/subscription/health - Subscription health check
# - POST /auth/register - User registration
# - POST /auth/login - User login
# - POST /auth/reset-password - Password reset request
# - POST /auth/confirm-reset - Password reset confirmation
# - POST /auth/verify-email - Email verification
# - POST /auth/resend-verification - Resend verification email
#
# =============================================================================

# Include routers
app.include_router(prompt_router)
app.include_router(context_router)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class GeneratePromptRequest(BaseModel):
    template_name: str
    user_data: Dict[str, str]

class TemplateResponse(BaseModel):
    templates: List[str]

class PlaceholdersResponse(BaseModel):
    placeholders: List[str]

class GeneratePromptResponse(BaseModel):
    generated_prompt: str
    success: bool
    error: str = None

# Parsinator Pydantic models
class ProcessBriefRequest(BaseModel):
    brief_text: str
    project_name: str = "Web Project"

class ProcessBriefResponse(BaseModel):
    success: bool
    tasks: Optional[Dict] = None
    summary: Optional[Dict] = None
    error: Optional[str] = None
    task_count: int = 0

class ValidateBriefRequest(BaseModel):
    brief_text: str

class ValidateBriefResponse(BaseModel):
    valid: bool
    brief_type: Optional[str] = None
    errors: List[str] = []
    warnings: List[str] = []

class ParsinatorHealthResponse(BaseModel):
    healthy: bool
    message: Optional[str] = None
    error: Optional[str] = None
    available_templates: Optional[int] = None

class BriefTemplatesResponse(BaseModel):
    templates: List[str] = []
    count: int = 0
    error: Optional[str] = None

# Get paths
prompts_dir = os.path.join(os.path.dirname(src_dir), "prompts")
meta_prompt_path = os.path.join(prompts_dir, "meta_prompt.md")
static_dir = os.path.join(current_dir, "static")

# Authentication endpoints
@app.post("/auth/register", response_model=RegisterResponse)
async def register_user(request: UserRegistrationRequest, db: Session = Depends(get_db_session)):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address already registered"
            )
        
        # Validate email format
        is_valid_email, normalized_email = validate_email_address(request.email)
        if not is_valid_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email address format"
            )
        
        # Hash password
        hashed_password = hash_password(request.password)
        
        # Generate email verification token
        verification_token = generate_verification_token()
        
        # Create new user
        new_user = User(
            email=normalized_email,
            name=format_user_display_name(request.name),
            hashed_password=hashed_password,
            subscription_tier=SubscriptionTier.FREE,
            is_active=True,
            is_email_verified=False,
            email_verification_token=verification_token
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Send verification email
        email_sent = await email_service.send_verification_email(
            to_email=new_user.email,
            verification_token=verification_token,
            user_name=new_user.name
        )
        
        # Create tokens (for immediate access to non-verification-required features)
        tokens = create_tokens_for_user(new_user)
        
        return RegisterResponse(
            success=True,
            message="User registered successfully. Please check your email to verify your account.",
            user=UserResponse.from_orm(new_user),
            tokens=TokenResponse(**tokens),
            verification_required=True
        )
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address already registered"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/auth/login", response_model=LoginResponse)
async def login_user(request: UserLoginRequest, db: Session = Depends(get_db_session)):
    """Authenticate user and return tokens"""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == request.email).first()
        
        if not user or not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is inactive"
            )
        
        # Create tokens
        tokens = create_tokens_for_user(user)
        
        return LoginResponse(
            success=True,
            message="Login successful",
            user=UserProfileResponse.from_orm(user),
            tokens=TokenResponse(**tokens)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@app.get("/auth/profile", response_model=UserProfileResponse)
async def get_user_profile(current_user: User = Depends(require_auth)):
    """Get current user profile"""
    return UserProfileResponse.from_orm(current_user)

@app.put("/auth/profile", response_model=UserProfileResponse)
async def update_user_profile(
    request: UserProfileUpdateRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db_session)
):
    """Update user profile"""
    try:
        # Update name if provided
        if request.name is not None:
            current_user.name = format_user_display_name(request.name)
        
        # Update email if provided
        if request.email is not None:
            # Validate email format
            is_valid_email, normalized_email = validate_email_address(request.email)
            if not is_valid_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid email address format"
                )
            
            # Check if email is already taken by another user
            existing_user = db.query(User).filter(
                User.email == normalized_email,
                User.id != current_user.id
            ).first()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email address already in use"
                )
            
            current_user.email = normalized_email
        
        db.commit()
        db.refresh(current_user)
        
        return UserProfileResponse.from_orm(current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {str(e)}"
        )

@app.post("/auth/change-password", response_model=SuccessResponse)
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db_session)
):
    """Change user password"""
    try:
        # Verify current password
        if not verify_password(request.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_hashed_password = hash_password(request.new_password)
        
        # Update password
        current_user.hashed_password = new_hashed_password
        db.commit()
        
        return SuccessResponse(
            success=True,
            message="Password changed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )

@app.post("/auth/reset-password", response_model=SuccessResponse)
async def reset_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db_session)
):
    """Initiate password reset"""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == request.email).first()
        
        if not user:
            # Don't reveal if email exists or not
            return SuccessResponse(
                success=True,
                message="If the email exists, a reset link has been sent"
            )
        
        # Generate reset token
        reset_token = generate_password_reset_token(user.email)
        
        # Send password reset email
        email_sent = await email_service.send_password_reset_email(
            to_email=user.email,
            reset_token=reset_token,
            user_name=user.name
        )
        
        # Always return success to prevent email enumeration attacks
        return SuccessResponse(
            success=True,
            message="If the email exists, a reset link has been sent"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )

@app.post("/auth/confirm-reset", response_model=SuccessResponse)
async def confirm_password_reset(
    request: PasswordResetConfirmRequest,
    db: Session = Depends(get_db_session)
):
    """Confirm password reset with token"""
    try:
        # Verify reset token
        email = verify_password_reset_token(request.token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Hash new password
        new_hashed_password = hash_password(request.new_password)
        
        # Update password
        user.hashed_password = new_hashed_password
        db.commit()
        
        return SuccessResponse(
            success=True,
            message="Password reset successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset confirmation failed: {str(e)}"
        )

@app.post("/auth/logout", response_model=SuccessResponse)
async def logout_user(current_user: User = Depends(require_auth)):
    """Logout user (client should discard tokens)"""
    return SuccessResponse(
        success=True,
        message="Logout successful"
    )

@app.get("/auth/health", response_model=SuccessResponse)
async def auth_health_check():
    """Check authentication system health"""
    return SuccessResponse(
        success=True,
        message="Authentication system is healthy"
    )


@app.post("/auth/verify-email", response_model=SuccessResponse)
async def verify_email(request: EmailVerificationRequest, db: Session = Depends(get_db_session)):
    """Verify user email with verification token"""
    try:
        # Find user by verification token
        user = db.query(User).filter(
            User.email_verification_token == request.token,
            User.is_email_verified == False
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        # Mark email as verified
        user.is_email_verified = True
        user.email_verification_token = None
        user.email_verified_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        return SuccessResponse(
            success=True,
            message="Email verified successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email"
        )


@app.post("/auth/resend-verification", response_model=SuccessResponse)
async def resend_verification(request: ResendVerificationRequest, db: Session = Depends(get_db_session)):
    """Resend email verification token"""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == request.email).first()
        
        if not user:
            # Don't reveal if email exists or not for security
            return SuccessResponse(
                success=True,
                message="If the email address exists and is unverified, a verification email has been sent"
            )
        
        # Only send if email is not already verified
        if user.is_email_verified:
            return SuccessResponse(
                success=True,
                message="Email is already verified"
            )
        
        # Generate new verification token
        verification_token = generate_verification_token()
        user.email_verification_token = verification_token
        
        db.commit()
        
        # Send verification email
        email_sent = await email_service.send_verification_email(
            to_email=user.email,
            verification_token=verification_token,
            user_name=user.name
        )
        
        if not email_sent:
            # Log the error but don't expose it to the user
            return SuccessResponse(
                success=True,
                message="If the email address exists and is unverified, a verification email has been sent"
            )
        
        return SuccessResponse(
            success=True,
            message="If the email address exists and is unverified, a verification email has been sent"
        )
        
    except Exception as e:
        db.rollback()
        # Log the error but don't expose it to the user
        return SuccessResponse(
            success=True,
            message="If the email address exists and is unverified, a verification email has been sent"
        )


# Subscription management endpoints
@app.get("/auth/subscription/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(current_user: User = Depends(require_auth), db: Session = Depends(get_db_session)):
    """Get current subscription status and usage statistics"""
    try:
        service = SubscriptionService(db)
        status_data = service.get_subscription_status(current_user)
        
        # Calculate remaining usage
        current_usage = status_data["current_usage"]
        tier_limits = status_data["tier_limits"]
        
        remaining_usage = {}
        for key, current_val in current_usage.items():
            if key == "prompts_generated":
                limit = tier_limits.get("monthly_prompts", 0)
            elif key == "briefs_processed":
                limit = tier_limits.get("monthly_briefs", 0)
            elif key == "briefs_validated":
                limit = tier_limits.get("monthly_validations", 0)
            else:
                continue
                
            if isinstance(limit, int):
                remaining_usage[key] = max(0, limit - current_val)
            else:
                remaining_usage[key] = "unlimited"
        
        # Calculate next reset date
        from datetime import datetime, timezone
        current_date = datetime.now(timezone.utc)
        if current_date.month == 12:
            next_reset = current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            next_reset = current_date.replace(month=current_date.month + 1, day=1)
        next_reset = next_reset.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return SubscriptionStatusResponse(
            user_id=status_data["user_id"],
            subscription_tier=status_data["subscription_tier"],
            is_premium=status_data["is_premium"],
            can_create_teams=status_data["can_create_teams"],
            tier_limits=TierLimits(**tier_limits),
            current_usage=UsageStatistics(**current_usage),
            remaining_usage=RemainingUsage(**remaining_usage),
            month_start=status_data["month_start"],
            subscription_active=status_data["subscription_active"],
            next_reset_date=next_reset.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting subscription status: {str(e)}"
        )


@app.post("/auth/subscription/change", response_model=SubscriptionChangeResponse)
async def change_subscription_tier(
    request: SubscriptionChangeRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db_session)
):
    """Change user's subscription tier"""
    try:
        service = SubscriptionService(db)
        result = service.change_subscription_tier(current_user, request.new_tier)
        
        return SubscriptionChangeResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error changing subscription: {str(e)}"
        )


@app.get("/auth/subscription/usage", response_model=UsageStatsResponse)
async def get_detailed_usage_stats(current_user: User = Depends(require_auth), db: Session = Depends(get_db_session)):
    """Get detailed usage statistics for current month"""
    try:
        service = SubscriptionService(db)
        from datetime import datetime, timezone
        
        current_date = datetime.now(timezone.utc)
        month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        usage_stats = service.get_usage_statistics(current_user.id, month_start, current_date)
        tier_limits = service.USAGE_LIMITS.get(current_user.subscription_tier, {})
        
        # Calculate remaining usage
        remaining_usage = {}
        usage_percentage = {}
        
        for key, current_val in usage_stats.items():
            if key == "prompts_generated":
                limit = tier_limits.get("monthly_prompts", 0)
            elif key == "briefs_processed":
                limit = tier_limits.get("monthly_briefs", 0)
            elif key == "briefs_validated":
                limit = tier_limits.get("monthly_validations", 0)
            else:
                continue
                
            if isinstance(limit, int):
                remaining_usage[key] = max(0, limit - current_val)
                usage_percentage[key] = (current_val / limit * 100) if limit > 0 else 0
            else:
                remaining_usage[key] = "unlimited"
                usage_percentage[key] = "unlimited"
        
        return UsageStatsResponse(
            user_id=current_user.id,
            subscription_tier=current_user.subscription_tier.value,
            month_start=month_start.isoformat(),
            current_usage=UsageStatistics(**usage_stats),
            tier_limits=TierLimits(**tier_limits),
            remaining_usage=RemainingUsage(**remaining_usage),
            usage_percentage=usage_percentage
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting usage statistics: {str(e)}"
        )


@app.get("/auth/subscription/health", response_model=SubscriptionHealthResponse)
async def subscription_health_check(db: Session = Depends(get_db_session)):
    """Check subscription system health"""
    try:
        # Test basic subscription service functionality
        service = SubscriptionService(db)
        
        # Test database connectivity
        db.execute("SELECT 1")
        
        # Check if we can query usage metrics
        from models.analytics import UsageMetrics
        db.query(UsageMetrics).limit(1).all()
        
        return SubscriptionHealthResponse(
            healthy=True,
            message="Subscription system is operational",
            services_status={
                "usage_tracking": True,
                "limit_enforcement": True,
                "tier_management": True
            }
        )
        
    except Exception as e:
        return SubscriptionHealthResponse(
            healthy=False,
            message=f"Subscription system error: {str(e)}",
            services_status={
                "usage_tracking": False,
                "limit_enforcement": False,
                "tier_management": False
            }
        )


@app.get("/api/templates", response_model=TemplateResponse)
async def get_templates():
    """Get list of available prompt templates"""
    try:
        templates = []
        prompts_path = Path(prompts_dir)
        
        # Find all .md files that are templates (not meta_prompt.md)
        for template_file in prompts_path.glob("*.md"):
            if template_file.name != "meta_prompt.md":
                templates.append(template_file.name)
        
        return TemplateResponse(templates=sorted(templates))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading templates: {str(e)}")

class ParseTemplateRequest(BaseModel):
    template_name: str

@app.post("/api/parse-template", response_model=PlaceholdersResponse)
async def parse_template_endpoint(
    request: ParseTemplateRequest,
    current_user: Optional[User] = Depends(optional_auth),
    db: Session = Depends(get_db_session)
):
    """Parse a template and return its placeholders
    
    This endpoint supports optional authentication:
    - Unauthenticated users can parse templates for exploration
    - Authenticated users have their usage tracked for analytics
    """
    template_name = request.template_name
    try:
        template_path = Path(prompts_dir) / template_name
        
        if not template_path.exists():
            raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
        
        placeholders = parse_template(template_path)
        
        # Track usage for authenticated users
        if current_user:
            from models.analytics import UserActivity
            activity = UserActivity.create_activity(
                user_id=current_user.id,
                activity_type="template_parsed",
                data={
                    "template_name": template_name,
                    "placeholder_count": len(placeholders)
                }
            )
            db.add(activity)
            db.commit()
        
        return PlaceholdersResponse(placeholders=placeholders)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing template: {str(e)}")

@app.post("/api/generate", response_model=GeneratePromptResponse)
async def generate_prompt(request: GeneratePromptRequest, current_user: User = Depends(check_prompt_limit), db: Session = Depends(get_db_session)):
    """Generate the final prompt using AI"""
    import time
    start_time = time.time()
    
    try:
        template_path = Path(prompts_dir) / request.template_name
        
        if not template_path.exists():
            raise HTTPException(status_code=404, detail=f"Template '{request.template_name}' not found")
        
        # Read template content
        template_content = template_path.read_text()
        
        # Check if meta-prompt exists
        meta_prompt_file = Path(meta_prompt_path)
        if not meta_prompt_file.exists():
            raise HTTPException(status_code=500, detail="Meta-prompt file not found")
        
        # Generate the final prompt using AI
        final_prompt = assemble_prompt(template_content, request.user_data, meta_prompt_file)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Check if generation was successful (basic error check)
        success = not final_prompt.startswith("An error occurred:")
        
        # Try to find corresponding database prompt for analytics
        try:
            # Look for a prompt with matching title (from template name)
            template_title = request.template_name.replace('_', ' ').replace('-', ' ').title()
            if template_title.endswith('.md'):
                template_title = template_title[:-3]
            if template_title.endswith(' Template'):
                template_title = template_title[:-9]
                
            db_prompt = db.query(Prompt).filter(
                Prompt.title.ilike(f"%{template_title}%"),
                Prompt.is_active == True
            ).first()
            
            if db_prompt:
                # Track usage in database
                analytics_service = PromptAnalyticsService(db)
                analytics_service.track_usage(
                    prompt_id=db_prompt.id,
                    user_id=current_user.id,
                    response_time=response_time,
                    success=success,
                    context_data={
                        "template_name": request.template_name,
                        "user_data_keys": list(request.user_data.keys())
                    }
                )
        except Exception as analytics_error:
            # Don't fail the main request if analytics fails
            print(f"Analytics tracking failed: {analytics_error}")
        
        if not success:
            return GeneratePromptResponse(
                generated_prompt="",
                success=False,
                error=final_prompt
            )
        
        # Track successful usage
        try:
            subscription_service = SubscriptionService(db)
            subscription_service.increment_usage(
                user_id=current_user.id,
                activity_type="prompt_generated",
                context_data={
                    "template_name": request.template_name,
                    "user_data_keys": list(request.user_data.keys()),
                    "response_time": response_time,
                    "success": True
                }
            )
        except Exception as tracking_error:
            # Don't fail the main request if tracking fails
            print(f"Usage tracking failed: {tracking_error}")
        
        return GeneratePromptResponse(
            generated_prompt=final_prompt,
            success=True
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return GeneratePromptResponse(
            generated_prompt="",
            success=False,
            error=f"Error generating prompt: {str(e)}"
        )

# Parsinator API endpoints
@app.get("/api/parsinator/health", response_model=ParsinatorHealthResponse)
async def parsinator_health_check():
    """Check if Parsinator functionality is working correctly"""
    try:
        service = get_parsinator_service()
        result = service.health_check()
        
        return ParsinatorHealthResponse(
            healthy=result["healthy"],
            message=result.get("message"),
            error=result.get("error"),
            available_templates=result.get("available_templates")
        )
    except Exception as e:
        return ParsinatorHealthResponse(
            healthy=False,
            error=f"Health check failed: {str(e)}"
        )

@app.post("/api/parsinator/process-brief", response_model=ProcessBriefResponse)
async def process_brief(request: ProcessBriefRequest, current_user: User = Depends(check_brief_limit), db: Session = Depends(get_db_session)):
    """Process a project brief and generate tasks"""
    try:
        service = get_parsinator_service()
        result = service.process_brief_text(request.brief_text, request.project_name)
        
        # Track successful usage
        if result.success:
            try:
                subscription_service = SubscriptionService(db)
                subscription_service.increment_usage(
                    user_id=current_user.id,
                    activity_type="brief_processed",
                    context_data={
                        "project_name": request.project_name,
                        "task_count": result.task_count,
                        "success": True
                    }
                )
            except Exception as tracking_error:
                # Don't fail the main request if tracking fails
                print(f"Usage tracking failed: {tracking_error}")
        
        return ProcessBriefResponse(
            success=result.success,
            tasks=result.tasks,
            summary=result.summary,
            error=result.error,
            task_count=result.task_count
        )
    except Exception as e:
        return ProcessBriefResponse(
            success=False,
            error=f"Error processing brief: {str(e)}"
        )

@app.post("/api/parsinator/validate-brief", response_model=ValidateBriefResponse)
async def validate_brief(request: ValidateBriefRequest, current_user: User = Depends(check_validation_limit), db: Session = Depends(get_db_session)):
    """Validate a project brief format"""
    try:
        service = get_parsinator_service()
        result = service.validate_brief_text(request.brief_text)
        
        # Track successful usage
        if result.valid:
            try:
                subscription_service = SubscriptionService(db)
                subscription_service.increment_usage(
                    user_id=current_user.id,
                    activity_type="brief_validated",
                    context_data={
                        "brief_type": result.brief_type,
                        "valid": result.valid,
                        "error_count": len(result.errors or []),
                        "warning_count": len(result.warnings or [])
                    }
                )
            except Exception as tracking_error:
                # Don't fail the main request if tracking fails
                print(f"Usage tracking failed: {tracking_error}")
        
        return ValidateBriefResponse(
            valid=result.valid,
            brief_type=result.brief_type,
            errors=result.errors or [],
            warnings=result.warnings or []
        )
    except Exception as e:
        return ValidateBriefResponse(
            valid=False,
            errors=[f"Error validating brief: {str(e)}"]
        )

@app.get("/api/parsinator/templates", response_model=BriefTemplatesResponse)
async def get_brief_templates():
    """Get available brief templates"""
    try:
        service = get_parsinator_service()
        result = service.get_brief_templates()
        
        if "error" in result:
            return BriefTemplatesResponse(error=result["error"])
        
        return BriefTemplatesResponse(
            templates=result.get("templates", []),
            count=result.get("count", 0)
        )
    except Exception as e:
        return BriefTemplatesResponse(
            error=f"Error getting templates: {str(e)}"
        )

# Mount the static files directory (serve the frontend)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
