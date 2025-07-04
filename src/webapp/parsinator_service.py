"""
Parsinator Service Layer for Web Application

This module provides web-friendly wrapper functions around the Parsinator CLI
functionality, handling file operations, error formatting, and response
structuring for the FastAPI web application.
"""

import os
import sys
import json
import tempfile
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

# Add the src directory to Python path so we can import parsinator modules
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

try:
    from parsinator.utils import FileHandler, FileIOError
    from parsinator.parser import BriefParser, ParsingError
    from parsinator.templates import TemplateManager
    from parsinator.id_manager import TaskIDManager
    from parsinator.enhanced_generator import EnhancedTaskGenerator, TaskGenerationError
except ImportError as e:
    print(f"Warning: Could not import Parsinator modules: {e}")
    # We'll handle this gracefully in the service functions


@dataclass
class ProcessBriefResult:
    """Result of processing a brief"""
    success: bool
    tasks: Optional[Dict] = None
    summary: Optional[Dict] = None
    error: Optional[str] = None
    task_count: int = 0


@dataclass
class ValidateBriefResult:
    """Result of validating a brief"""
    valid: bool
    brief_type: Optional[str] = None
    errors: List[str] = None
    warnings: List[str] = None


class ParsinatorService:
    """Service class for Parsinator web operations"""
    
    def __init__(self):
        self.file_handler = None
        self.brief_parser = None
        self.template_manager = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize Parsinator components with error handling"""
        try:
            self.file_handler = FileHandler()
            self.brief_parser = BriefParser()
            self.template_manager = TemplateManager()
        except Exception as e:
            print(f"Warning: Could not initialize Parsinator components: {e}")
    
    def health_check(self) -> Dict[str, Union[bool, str]]:
        """Check if Parsinator functionality is working correctly"""
        try:
            if not all([self.file_handler, self.brief_parser, self.template_manager]):
                return {
                    "healthy": False,
                    "error": "Parsinator components not initialized properly"
                }
            
            # Try a simple operation
            templates = self.template_manager.list_templates()
            
            return {
                "healthy": True,
                "message": "Parsinator is working correctly",
                "available_templates": len(templates) if templates else 0
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": f"Health check failed: {str(e)}"
            }
    
    def process_brief_text(self, brief_text: str, project_name: str = "Web Project") -> ProcessBriefResult:
        """Process a brief from text content"""
        temp_file = None
        temp_dir = None
        
        try:
            # Create temporary file for the brief
            temp_dir = tempfile.mkdtemp()
            temp_file = Path(temp_dir) / "brief.md"
            temp_file.write_text(brief_text)
            
            # Process the brief
            return self._process_brief_file(temp_file, project_name)
            
        except Exception as e:
            return ProcessBriefResult(
                success=False,
                error=f"Error processing brief text: {str(e)}"
            )
        finally:
            # Cleanup temporary files
            if temp_file and temp_file.exists():
                temp_file.unlink()
            if temp_dir and Path(temp_dir).exists():
                os.rmdir(temp_dir)
    
    def process_brief_file(self, file_path: str, project_name: str = "Web Project") -> ProcessBriefResult:
        """Process a brief from a file path"""
        try:
            brief_path = Path(file_path)
            if not brief_path.exists():
                return ProcessBriefResult(
                    success=False,
                    error=f"Brief file not found: {file_path}"
                )
            
            return self._process_brief_file(brief_path, project_name)
            
        except Exception as e:
            return ProcessBriefResult(
                success=False,
                error=f"Error processing brief file: {str(e)}"
            )
    
    def _process_brief_file(self, brief_path: Path, project_name: str) -> ProcessBriefResult:
        """Internal method to process a brief file"""
        try:
            if not all([self.file_handler, self.brief_parser]):
                return ProcessBriefResult(
                    success=False,
                    error="Parsinator components not available"
                )
            
            # Create temporary output directory
            with tempfile.TemporaryDirectory() as temp_output_dir:
                output_dir = Path(temp_output_dir)
                
                # Initialize task generator (no output_dir parameter)
                task_generator = EnhancedTaskGenerator()
                
                # Process the brief file (expects a list)
                collection = task_generator.process_brief_files([str(brief_path)])
                
                # Generate output files
                tasks_file = output_dir / "tasks.json"
                summary_file = output_dir / "generation_summary.json"
                
                # Generate tasks.json
                task_generator.generate_tasks_json(tasks_file, project_name)
                
                # Generate summary
                summary_data = task_generator.get_generation_summary()
                summary_file.write_text(json.dumps(summary_data, indent=2))
                
                # Read the generated files
                tasks_data = None
                
                if tasks_file.exists():
                    tasks_data = json.loads(tasks_file.read_text())
                
                task_count = 0
                if tasks_data and "master" in tasks_data and "tasks" in tasks_data["master"]:
                    task_count = len(tasks_data["master"]["tasks"])
                
                return ProcessBriefResult(
                    success=True,
                    tasks=tasks_data,
                    summary=summary_data,
                    task_count=task_count
                )
                
        except TaskGenerationError as e:
            return ProcessBriefResult(
                success=False,
                error=f"Task generation error: {str(e)}"
            )
        except Exception as e:
            return ProcessBriefResult(
                success=False,
                error=f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            )
    
    def validate_brief_text(self, brief_text: str) -> ValidateBriefResult:
        """Validate a brief from text content"""
        temp_file = None
        temp_dir = None
        
        try:
            # Create temporary file for the brief
            temp_dir = tempfile.mkdtemp()
            temp_file = Path(temp_dir) / "brief.md"
            temp_file.write_text(brief_text)
            
            return self._validate_brief_file(temp_file)
            
        except Exception as e:
            return ValidateBriefResult(
                valid=False,
                errors=[f"Error validating brief: {str(e)}"]
            )
        finally:
            # Cleanup temporary files
            if temp_file and temp_file.exists():
                temp_file.unlink()
            if temp_dir and Path(temp_dir).exists():
                os.rmdir(temp_dir)
    
    def _validate_brief_file(self, brief_path: Path) -> ValidateBriefResult:
        """Internal method to validate a brief file"""
        try:
            if not all([self.brief_parser, self.template_manager]):
                return ValidateBriefResult(
                    valid=False,
                    errors=["Parsinator components not available"]
                )
            
            # Parse the brief to detect type and validate structure
            brief_data = self.brief_parser.parse_brief(brief_path)
            brief_type = self.brief_parser.detect_brief_type(brief_data)
            
            # Validate against template
            validation_result = self.template_manager.validate_brief(brief_data, brief_type)
            
            return ValidateBriefResult(
                valid=validation_result.is_valid,
                brief_type=brief_type,
                errors=validation_result.errors or [],
                warnings=validation_result.warnings or []
            )
            
        except ParsingError as e:
            return ValidateBriefResult(
                valid=False,
                errors=[f"Parsing error: {str(e)}"]
            )
        except Exception as e:
            return ValidateBriefResult(
                valid=False,
                errors=[f"Validation error: {str(e)}"]
            )
    
    def get_brief_templates(self) -> Dict[str, List[str]]:
        """Get available brief templates"""
        try:
            if not self.template_manager:
                return {"error": "Template manager not available"}
            
            templates = self.template_manager.list_templates()
            return {
                "templates": templates or [],
                "count": len(templates) if templates else 0
            }
            
        except Exception as e:
            return {"error": f"Error getting templates: {str(e)}"}


# Global service instance
_parsinator_service = None

def get_parsinator_service() -> ParsinatorService:
    """Get or create the global Parsinator service instance"""
    global _parsinator_service
    if _parsinator_service is None:
        _parsinator_service = ParsinatorService()
    return _parsinator_service