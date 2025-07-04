from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
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
async def generate_prompt(request: GeneratePromptRequest):
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
async def process_brief(request: ProcessBriefRequest):
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
async def validate_brief(request: ValidateBriefRequest):
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
