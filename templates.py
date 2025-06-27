"""
Brief template management and validation
"""
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from parsinator.utils import FileHandler, FileIOError

@dataclass
class TemplateSection:
    """Represents a required section in a brief template"""
    name: str
    required: bool = True
    pattern: Optional[str] = None

@dataclass 
class BriefTemplate:
    """Represents a brief template with validation rules"""
    name: str
    description: str
    required_sections: List[TemplateSection]
    
class TemplateManager:
    """Manages brief templates and validation"""
    
    def __init__(self, template_directories: List[str] = None):
        self.file_handler = FileHandler()
        
        # Default template directories based on your structure
        if template_directories is None:
            template_directories = [
                "../../docs/parsinator/brief_templates",  # From src/parsinator/ to templates
                "./templates",  # Fallback local directory
            ]
        
        self.template_dirs = [Path(d) for d in template_directories]
        self._templates = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default brief template definitions"""
        
        # Project Setup Brief Template
        setup_sections = [
            TemplateSection("Project Name", True, r"## Project Name"),
            TemplateSection("Problem Statement", True, r"## Problem Statement"),
            TemplateSection("Setup Scope", True, r"## Setup Scope"),
            TemplateSection("Core Setup Tasks", True, r"## Core Setup Tasks"),
            TemplateSection("Technical Requirements", True, r"## Technical Requirements"),
            TemplateSection("Success Criteria", True, r"## Success Criteria"),
        ]
        
        self._templates["setup"] = BriefTemplate(
            name="Project Setup Brief",
            description="Template for project infrastructure and setup tasks",
            required_sections=setup_sections
        )
        
        # Feature Brief Template  
        feature_sections = [
            TemplateSection("Feature Name", True, r"## Feature Name"),
            TemplateSection("Problem Statement", True, r"## Problem Statement"),
            TemplateSection("Target Users", True, r"## Target Users"),
            TemplateSection("Feature Scope", True, r"## Feature Scope"),
            TemplateSection("Core Feature Tasks", True, r"## Core Feature Tasks"),
            TemplateSection("Technical Implementation", True, r"## Technical Implementation"),
            TemplateSection("Success Criteria", True, r"## Success Criteria"),
        ]
        
        self._template
