"""
Enhanced Task Generator that integrates ID Management and Brief Parsing
"""
from typing import List, Dict, Optional, Any
from pathlib import Path
import logging
from datetime import datetime

from parsinator.models import BriefContent, TaskCollection, ProjectMetadata
from parsinator.parser import BriefParser
from parsinator.id_manager import TaskIDManager
from parsinator.dependency_mapper import DependencyMapper, DependencyAnalysis
from parsinator.utils import FileHandler, FileIOError

logger = logging.getLogger(__name__)

class EnhancedTaskGenerator:
    """
    Complete task generation system that combines parsing, ID management, and output
    """
    
    def __init__(self, existing_tasks_file: Optional[str] = None):
        """
        Initialize the enhanced task generator
        
        Args:
            existing_tasks_file: Path to existing tasks.json for additive sessions
        """
        self.parser = BriefParser()
        self.id_manager = TaskIDManager(existing_tasks_file)
        self.dependency_mapper = DependencyMapper()
        self.file_handler = FileHandler()
        
        self.processed_briefs: List[BriefContent] = []
        self.generated_collection: Optional[TaskCollection] = None
        self.dependency_analysis: Optional[DependencyAnalysis] = None
        self.generation_metadata: Dict[str, Any] = {}
        
    def process_brief_files(self, brief_files: List[str]) -> TaskCollection:
        """
        Process multiple brief files and generate a complete task collection
        
        Args:
            brief_files: List of paths to brief files
            
        Returns:
            TaskCollection with all generated tasks
            
        Raises:
            FileIOError: If any brief file cannot be read
            ValueError: If brief parsing or task generation fails
        """
        logger.info(f"Processing {len(brief_files)} brief files")
        
        # Parse all brief files
        self.processed_briefs = []
        for brief_file in brief_files:
            try:
                brief_content = self.parser.parse_brief_file(brief_file)
                self.processed_briefs.append(brief_content)
                logger.info(f"Parsed {brief_file}: {len(brief_content.tasks)} tasks found")
                
            except Exception as e:
                logger.error(f"Failed to parse {brief_file}: {e}")
                raise
        
        # Generate task collection with proper ID management
        self.generated_collection = self.id_manager.assign_task_ids(self.processed_briefs)
        
        # Perform advanced dependency analysis
        logger.info("Performing advanced dependency analysis...")
        self.dependency_analysis = self.dependency_mapper.analyze_dependencies(
            self.processed_briefs, self.generated_collection
        )
        
        # Apply high-confidence dependencies
        applied_deps = self.dependency_mapper.apply_dependencies(
            self.generated_collection, self.dependency_analysis.suggested_dependencies,
            confidence_threshold=0.7
        )
        logger.info(f"Applied {applied_deps} high-confidence dependencies")
        
        # Validate the generated collection
        validation_errors = self.generated_collection.validate_dependencies()
        if validation_errors:
            logger.warning(f"Dependency validation warnings: {validation_errors}")
            # Don't raise exception for warnings, just log them
        
        # Store generation metadata
        self.generation_metadata = self._collect_generation_metadata()
        
        logger.info(f"Successfully generated {len(self.generated_collection.get_all_tasks())} tasks")
        return self.generated_collection
    
    def process_brief_directory(self, directory: str) -> TaskCollection:
        """
        Process all brief files in a directory
        
        Args:
            directory: Directory containing brief files
            
        Returns:
            TaskCollection with all generated tasks
        """
        brief_files = self.file_handler.find_brief_files(directory)
        brief_file_paths = [str(bf) for bf in brief_files]
        
        if not brief_file_paths:
            raise FileIOError(f"No brief files found in {directory}")
        
        return self.process_brief_files(brief_file_paths)
    
    def generate_tasks_json(self, output_path: str, project_name: str = "Generated Project") -> None:
        """
        Generate tasks.json file from the processed briefs
        
        Args:
            output_path: Path where to write tasks.json
            project_name: Name of the project for metadata
        """
        if not self.generated_collection:
            raise ValueError("No tasks have been generated yet. Call process_brief_files first.")
        
        # Create or update project metadata
        if self.id_manager.existing_metadata:
            metadata = self.id_manager.existing_metadata
            metadata.updated = datetime.now()
            # Update task counts
            all_tasks = self.generated_collection.get_all_tasks()
            metadata.total_tasks = len(all_tasks)
            metadata.completed_tasks = len([t for t in all_tasks if t.status.value == "done"])
        else:
            # Create new metadata
            description = self._generate_project_description()
            metadata = ProjectMetadata(
                name=project_name,
                description=description
            )
            all_tasks = self.generated_collection.get_all_tasks()
            metadata.total_tasks = len(all_tasks)
            metadata.completed_tasks = 0
        
        # Generate the JSON structure
        tasks_json = self.generated_collection.to_tasks_json(metadata)
        
        # Write to file
        self.file_handler.write_tasks_json(output_path, tasks_json)
        logger.info(f"Generated tasks.json with {len(self.generated_collection.get_all_tasks())} tasks")
    
    def get_generation_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the generation process
        
        Returns:
            Dictionary with detailed generation statistics
        """
        if not self.generated_collection:
            return {"error": "No tasks generated yet"}
        
        # Get ID manager summary
        id_summary = self.id_manager.get_generation_summary(self.generated_collection)
        
        # Add brief processing summary
        brief_summary = {
            "briefs_processed": len(self.processed_briefs),
            "brief_types": {
                brief_type: len([b for b in self.processed_briefs if b.brief_type == brief_type])
                for brief_type in ["setup", "feature", "deployment"]
            },
            "briefs_by_file": [
                {
                    "file": brief.file_path.name,
                    "type": brief.brief_type,
                    "title": brief.title,
                    "tasks_extracted": len(brief.tasks)
                }
                for brief in self.processed_briefs
            ]
        }
        
        # Add dependency analysis summary
        dependency_summary = {}
        if self.dependency_analysis:
            dependency_summary = {
                "dependencies_suggested": len(self.dependency_analysis.suggested_dependencies),
                "dependency_statistics": self.dependency_analysis.statistics,
                "warnings": self.dependency_analysis.warnings,
                "confidence_distribution": {
                    "high_confidence": len([d for d in self.dependency_analysis.suggested_dependencies if d.confidence >= 0.8]),
                    "medium_confidence": len([d for d in self.dependency_analysis.suggested_dependencies if 0.5 <= d.confidence < 0.8]),
                    "low_confidence": len([d for d in self.dependency_analysis.suggested_dependencies if d.confidence < 0.5])
                }
            }
        
        # Combine all summaries
        return {
            "generation_timestamp": datetime.now().isoformat(),
            "id_management": id_summary,
            "brief_processing": brief_summary,
            "dependency_analysis": dependency_summary,
            "collection_stats": {
                "total_tasks": len(self.generated_collection.get_all_tasks()),
                "unlocked_tasks": len(self.generated_collection.get_unlocked_tasks()),
                "dependency_errors": self.generated_collection.validate_dependencies()
            }
        }
    
    def _collect_generation_metadata(self) -> Dict[str, Any]:
        """Collect metadata about the generation process"""
        return {
            "generation_time": datetime.now().isoformat(),
            "briefs_processed": len(self.processed_briefs),
            "tasks_generated": len(self.generated_collection.get_all_tasks()) if self.generated_collection else 0,
            "brief_files": [brief.file_path.name for brief in self.processed_briefs]
        }
    
    def _generate_project_description(self) -> str:
        """Generate a project description based on processed briefs"""
        if not self.processed_briefs:
            return "Generated from project briefs using Parsinator"
        
        brief_types = [brief.brief_type for brief in self.processed_briefs]
        brief_titles = [brief.title for brief in self.processed_briefs]
        
        # Create description based on brief content
        if len(self.processed_briefs) == 1:
            return f"Generated from {self.processed_briefs[0].brief_type} brief: {self.processed_briefs[0].title}"
        else:
            type_summary = ", ".join(set(brief_types))
            return f"Generated from {len(self.processed_briefs)} briefs ({type_summary}) using Parsinator task generation system"
    
    def get_dependency_analysis(self) -> Optional[DependencyAnalysis]:
        """Get the detailed dependency analysis results"""
        return self.dependency_analysis

class TaskGenerationError(Exception):
    """Exception raised during task generation process"""
    pass