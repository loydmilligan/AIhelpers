# Core prompt generation logic
import re
import os
import json
from pathlib import Path
from typing import Optional, Union, Dict, Any
import google.generativeai as genai
from sqlalchemy.orm import Session

# Import database models and services
try:
    from models.prompt import Prompt
    from services.prompt_service import PromptService
    from config.database import get_db_session
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

def parse_template(template_path: Path) -> list[str]:
    """
    Reads a template file and parses it to find placeholders.

    Args:
        template_path: The path to the template file.

    Returns:
        A list of unique placeholder names found in the template.
    """
    try:
        content = template_path.read_text()
        
        # First, try to find {{placeholder}} format
        placeholders = re.findall(r"\{\{([a-zA-Z0-9_]+)\}\}", content)
        
        # If no {{}} placeholders found, look for **[FILL IN: ...] format with section headers
        if not placeholders:
            placeholders = []
            lines = content.split('\n')
            current_section = None
            
            for line in lines:
                # Look for section headers (## Header Name)
                header_match = re.match(r'^## (.+)$', line.strip())
                if header_match:
                    # Convert section header to placeholder name
                    section_name = header_match.group(1)
                    # Remove special characters and convert to snake_case
                    section_name = re.sub(r'[^\w\s]', '', section_name)
                    section_name = re.sub(r'\s+', '_', section_name.strip().lower())
                    current_section = section_name
                
                # Look for FILL IN instructions
                elif '**[FILL IN:' in line and current_section:
                    # Use the current section name as the placeholder
                    if current_section and current_section not in placeholders:
                        placeholders.append(current_section)
        
        return sorted(list(set(placeholders)))
    except FileNotFoundError:
        return []


def parse_template_from_content(content: str) -> list[str]:
    """
    Parse placeholders from template content string.
    
    Args:
        content: The template content string
        
    Returns:
        A list of unique placeholder names found in the template
    """
    # Find {{placeholder}} format
    placeholders = re.findall(r"\{\{([a-zA-Z0-9_]+)\}\}", content)
    
    # If no {{}} placeholders found, look for **[FILL IN: ...] format
    if not placeholders:
        placeholders = []
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            # Look for section headers (## Header Name)
            header_match = re.match(r'^## (.+)$', line.strip())
            if header_match:
                # Convert section header to placeholder name
                section_name = header_match.group(1)
                # Remove special characters and convert to snake_case
                section_name = re.sub(r'[^\w\s]', '', section_name)
                section_name = re.sub(r'\s+', '_', section_name.strip().lower())
                current_section = section_name
            
            # Look for FILL IN instructions
            elif '**[FILL IN:' in line and current_section:
                # Use the current section name as the placeholder
                if current_section and current_section not in placeholders:
                    placeholders.append(current_section)
    
    return sorted(list(set(placeholders)))


def get_template_content(template_identifier: Union[str, int, Path], db_session: Optional[Session] = None) -> Optional[str]:
    """
    Get template content from database or file system.
    
    Args:
        template_identifier: Can be:
            - int: Database prompt ID
            - str: Template filename or prompt title
            - Path: File path to template
        db_session: Optional database session
        
    Returns:
        Template content string or None if not found
    """
    # If it's a Path object, read from file
    if isinstance(template_identifier, Path):
        try:
            return template_identifier.read_text()
        except FileNotFoundError:
            return None
    
    # If database is available, try database first
    if DATABASE_AVAILABLE and db_session:
        service = PromptService(db_session)
        
        # If it's an integer, treat as prompt ID
        if isinstance(template_identifier, int):
            prompt = service.get_prompt(template_identifier)
            if prompt:
                return prompt.content
        
        # If it's a string, try to find by title or partial match
        elif isinstance(template_identifier, str):
            # Remove file extension if present
            search_title = template_identifier
            if search_title.endswith('.md'):
                search_title = search_title[:-3]
            
            # Try exact title match first
            prompts, _ = service.list_prompts(limit=1, sort_by="title")
            for prompt in prompts:
                if prompt.title.lower() == search_title.lower():
                    return prompt.content
            
            # Try partial title match
            prompts, _ = service.list_prompts(limit=10)
            for prompt in prompts:
                if search_title.lower() in prompt.title.lower():
                    return prompt.content
    
    # Fallback to file system
    if isinstance(template_identifier, str):
        # Try to construct file path
        prompts_dir = Path("prompts")
        if not template_identifier.endswith('.md'):
            template_identifier += '.md'
        
        template_path = prompts_dir / template_identifier
        try:
            return template_path.read_text()
        except FileNotFoundError:
            pass
    
    return None


def get_template_placeholders(template_identifier: Union[str, int, Path], db_session: Optional[Session] = None) -> list[str]:
    """
    Get placeholders from a template by identifier.
    
    Args:
        template_identifier: Template identifier (ID, name, or path)
        db_session: Optional database session
        
    Returns:
        List of placeholder names
    """
    content = get_template_content(template_identifier, db_session)
    if content:
        return parse_template_from_content(content)
    return []

def assemble_prompt(template_content: str, user_data: dict, meta_prompt_path: Path) -> str:
    """
    Assembles the final prompt by sending the template, user data, and a meta-prompt to the AI.

    Args:
        template_content: The content of the prompt template.
        user_data: A dictionary containing the user's answers.
        meta_prompt_path: The path to the meta-prompt file.

    Returns:
        The final, assembled prompt generated by the AI.
    """
    try:
        # Configure the API key from an environment variable
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)

        # Load the meta-prompt
        meta_prompt = meta_prompt_path.read_text()

        # Format the final prompt for the AI
        user_data_json = json.dumps(user_data, indent=4)
        formatted_prompt = meta_prompt.replace("{{template}}", template_content).replace("{{user_data}}", user_data_json)

        # Call the Gemini API
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(formatted_prompt)

        return response.text

    except Exception as e:
        return f"An error occurred: {e}"
