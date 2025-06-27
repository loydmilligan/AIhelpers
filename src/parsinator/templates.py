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
        
        self._templates["feature"] = BriefTemplate(
            name="Feature Brief",
            description="Template for individual feature implementation",
            required_sections=feature_sections
        )
        
        # Deployment Brief Template
        deployment_sections = [
            TemplateSection("Project Name", True, r"## Project Name"),
            TemplateSection("Deployment Goal", True, r"## Deployment Goal"),
            TemplateSection("Target Environment", True, r"## Target Environment"),
            TemplateSection("Core Deployment Tasks", True, r"## Core Deployment Tasks"),
            TemplateSection("Quality Assurance", True, r"## Quality Assurance"),
            TemplateSection("Success Criteria", True, r"## Success Criteria"),
        ]
        
        self._templates["deployment"] = BriefTemplate(
            name="Deployment Brief",
            description="Template for testing, documentation, and release preparation",
            required_sections=deployment_sections
        )
    
    def find_template_files(self) -> Dict[str, Path]:
        """Find actual template files on disk"""
        template_files = {}
        
        for template_dir in self.template_dirs:
            if template_dir.exists():
                # Look for our known template files
                patterns = {
                    "setup": "project_brief_template.md",
                    "feature": "feature_brief_template.md", 
                    "deployment": "deployment_brief_template.md"
                }
                
                for template_type, filename in patterns.items():
                    template_path = template_dir / filename
                    if template_path.exists():
                        template_files[template_type] = template_path
                        
                break  # Use first directory that exists
        
        return template_files
    
    def get_template_types(self) -> List[str]:
        """Get list of available template types"""
        return list(self._templates.keys())
    
    def get_template(self, template_type: str) -> Optional[BriefTemplate]:
        """Get template by type"""
        return self._templates.get(template_type)
    
    def detect_brief_type(self, brief_content: str) -> Optional[str]:
        """
        Automatically detect what type of brief this is based on content
        
        Args:
            brief_content: Content of the brief file
            
        Returns:
            Template type if detected, None otherwise
        """
        # Look for type indicators in the content
        content_lower = brief_content.lower()
        
        # Check for setup indicators
        setup_keywords = ["setup", "infrastructure", "project structure", "cli project", "foundation"]
        if any(keyword in content_lower for keyword in setup_keywords):
            return "setup"
        
        # Check for deployment indicators  
        deployment_keywords = ["deployment", "release", "testing", "documentation", "quality assurance"]
        if any(keyword in content_lower for keyword in deployment_keywords):
            return "deployment"
        
        # Default to feature if not clearly setup or deployment
        return "feature"
    
    def validate_brief(self, brief_content: str, template_type: str = None) -> Tuple[bool, List[str]]:
        """
        Validate brief content against template
        
        Args:
            brief_content: Content of the brief file
            template_type: Type of template to validate against, or None to auto-detect
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if template_type is None:
            template_type = self.detect_brief_type(brief_content)
            
        if template_type is None:
            return False, ["Could not determine brief type"]
        
        template = self.get_template(template_type)
        if template is None:
            return False, [f"Unknown template type: {template_type}"]
        
        errors = []
        
        # Check for required sections
        for section in template.required_sections:
            if section.pattern:
                if not re.search(section.pattern, brief_content, re.IGNORECASE):
                    errors.append(f"Missing required section: {section.name}")
            else:
                # Simple string search if no pattern provided
                if section.name.lower() not in brief_content.lower():
                    errors.append(f"Missing required section: {section.name}")
        
        return len(errors) == 0, errors
    
    def get_validation_report(self, brief_content: str, template_type: str = None) -> str:
        """
        Get a detailed validation report for a brief
        
        Args:
            brief_content: Content of the brief file
            template_type: Type of template to validate against
            
        Returns:
            Formatted validation report
        """
        if template_type is None:
            detected_type = self.detect_brief_type(brief_content)
            template_type = detected_type or "unknown"
        
        is_valid, errors = self.validate_brief(brief_content, template_type)
        
        # Check if we can find template files
        template_files = self.find_template_files()
        
        report = []
        report.append(f"📋 Brief Validation Report")
        report.append(f"   Template Type: {template_type}")
        report.append(f"   Content Length: {len(brief_content)} characters")
        report.append(f"   Template Files Found: {len(template_files)}")
        report.append("")
        
        if is_valid:
            report.append("✅ Brief is valid!")
        else:
            report.append(f"❌ Brief has {len(errors)} validation errors:")
            for error in errors:
                report.append(f"   • {error}")
        
        return "\n".join(report)

    def list_templates(self) -> str:
        """List available templates and their locations"""
        template_files = self.find_template_files()
        
        report = []
        report.append("📋 Available Brief Templates:")
        report.append("")
        
        for template_type in self.get_template_types():
            template = self.get_template(template_type)
            report.append(f"🔹 {template.name} ({template_type})")
            report.append(f"   {template.description}")
            
            if template_type in template_files:
                report.append(f"   📄 File: {template_files[template_type]}")
            else:
                report.append(f"   ⚠️  Template file not found")
            report.append("")
        
        return "\n".join(report)