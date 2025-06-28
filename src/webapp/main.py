from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
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

# Mount the static files directory (serve the frontend)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
