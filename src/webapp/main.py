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

# Import authentication modules
from auth import (
    hash_password, verify_password, create_tokens_for_user,
    require_auth, optional_auth, get_current_user_context
)
from auth.schemas import (
    UserRegistrationRequest, UserLoginRequest, TokenResponse, 
    UserProfileResponse, UserProfileUpdateRequest, PasswordChangeRequest,
    PasswordResetRequest, PasswordResetConfirmRequest, LoginResponse, 
    RegisterResponse, AuthenticationResponse, ErrorResponse, SuccessResponse
)
from auth.utils import (
    generate_password_reset_token, verify_password_reset_token,
    validate_email_address, format_user_display_name
)
from models.user import User, SubscriptionTier
from config.database import get_db_session

app = FastAPI(title="AI Prompt Helper API", version="1.0.0")

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
        
        # Create new user
        new_user = User(
            email=normalized_email,
            name=format_user_display_name(request.name),
            hashed_password=hashed_password,
            subscription_tier=SubscriptionTier.FREE,
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Create tokens
        tokens = create_tokens_for_user(new_user)
        
        return RegisterResponse(
            success=True,
            message="User registered successfully",
            user=UserProfileResponse.from_orm(new_user),
            tokens=TokenResponse(**tokens)
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
        
        # In a real application, you would send this token via email
        # For now, we'll just return success
        # TODO: Implement email sending
        
        return SuccessResponse(
            success=True,
            message="Password reset link sent to email",
            data={"reset_token": reset_token}  # Remove this in production
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
async def parse_template_endpoint(request: ParseTemplateRequest):
    """Parse a template and return its placeholders"""
    template_name = request.template_name
    try:
        template_path = Path(prompts_dir) / template_name
        
        if not template_path.exists():
            raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
        
        placeholders = parse_template(template_path)
        
        return PlaceholdersResponse(placeholders=placeholders)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing template: {str(e)}")

@app.post("/api/generate", response_model=GeneratePromptResponse)
async def generate_prompt(request: GeneratePromptRequest, current_user: User = Depends(require_auth)):
    """Generate the final prompt using AI"""
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
        
        # Check if generation was successful (basic error check)
        if final_prompt.startswith("An error occurred:"):
            return GeneratePromptResponse(
                generated_prompt="",
                success=False,
                error=final_prompt
            )
        
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
async def process_brief(request: ProcessBriefRequest, current_user: User = Depends(require_auth)):
    """Process a project brief and generate tasks"""
    try:
        service = get_parsinator_service()
        result = service.process_brief_text(request.brief_text, request.project_name)
        
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
async def validate_brief(request: ValidateBriefRequest, current_user: User = Depends(require_auth)):
    """Validate a project brief format"""
    try:
        service = get_parsinator_service()
        result = service.validate_brief_text(request.brief_text)
        
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
