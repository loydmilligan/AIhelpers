"""
Task ID Management System for Parsinator
Handles automatic ID assignment for both initial and additive sessions
"""
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
import logging
from parsinator.models import Task, TaskCollection, ProjectMetadata, BriefContent, TaskPriority
from parsinator.utils import FileHandler, FileIOError

logger = logging.getLogger(__name__)

class TaskIDManager:
    """
    Manages task ID assignment with support for additive sessions
    """
    
    def __init__(self, existing_tasks_file: Optional[str] = None):
        """
        Initialize TaskIDManager
        
        Args:
            existing_tasks_file: Path to existing tasks.json for additive sessions
        """
        self.file_handler = FileHandler()
        self.existing_collection: Optional[TaskCollection] = None
        self.existing_metadata: Optional[ProjectMetadata] = None
        self.next_available_id = 1
        self.reserved_ids: Set[int] = set()
        
        if existing_tasks_file:
            self._load_existing_tasks(existing_tasks_file)
    
    def _load_existing_tasks(self, tasks_file: str) -> None:
        """Load existing tasks and determine next available ID"""
        try:
            existing_data = self.file_handler.read_tasks_json(tasks_file)
            
            if existing_data:
                self.existing_collection, self.existing_metadata = TaskCollection.from_tasks_json(existing_data)
                
                # Find the highest existing ID
                existing_tasks = self.existing_collection.get_all_tasks()
                if existing_tasks:
                    max_id = max(task.id for task in existing_tasks)
                    self.next_available_id = max_id + 1
                    self.reserved_ids = {task.id for task in existing_tasks}
                    
                    logger.info(f"Loaded {len(existing_tasks)} existing tasks, next ID: {self.next_available_id}")
                else:
                    logger.info("No existing tasks found, starting from ID 1")
            else:
                logger.info("Empty tasks file, starting from ID 1")
                
        except FileIOError as e:
            logger.warning(f"Could not load existing tasks file {tasks_file}: {e}")
            # Continue with fresh start
        except Exception as e:
            logger.error(f"Error loading existing tasks: {e}")
            raise
    
    def assign_task_ids(self, briefs: List[BriefContent]) -> TaskCollection:
        """
        Assign IDs to tasks from parsed briefs
        
        Args:
            briefs: List of parsed brief content
            
        Returns:
            TaskCollection with assigned IDs
        """
        # Start with existing collection or create new one
        if self.existing_collection:
            collection = self.existing_collection
        else:
            collection = TaskCollection()
            collection._next_id = self.next_available_id
        
        # Process briefs in dependency order: setup -> feature -> deployment
        ordered_briefs = self._order_briefs(briefs)
        
        # Track dependencies between briefs
        brief_dependencies = self._analyze_brief_dependencies(ordered_briefs)
        
        # Generate tasks for each brief
        brief_task_mappings = {}  # Maps brief filename to list of task IDs
        
        for brief in ordered_briefs:
            brief_tasks = self._generate_tasks_for_brief(brief, collection, brief_dependencies)
            brief_task_mappings[brief.file_path.name] = brief_tasks
            
            logger.info(f"Generated {len(brief_tasks)} tasks for {brief.file_path.name}")
        
        return collection
    
    def _order_briefs(self, briefs: List[BriefContent]) -> List[BriefContent]:
        """Order briefs by type and filename for consistent processing"""
        type_order = {"setup": 0, "feature": 1, "deployment": 2}
        return sorted(briefs, key=lambda b: (type_order.get(b.brief_type, 1), b.file_path.name))
    
    def _analyze_brief_dependencies(self, briefs: List[BriefContent]) -> Dict[str, List[str]]:
        """
        Analyze dependencies between briefs based on type and content
        
        Args:
            briefs: Ordered list of briefs
            
        Returns:
            Dictionary mapping brief types to their dependencies
        """
        dependencies = {}
        brief_types = [brief.brief_type for brief in briefs]
        
        # Standard dependencies based on brief types
        if "setup" in brief_types:
            dependencies["feature"] = ["setup"]
            dependencies["deployment"] = ["setup"]
        
        if "feature" in brief_types and "deployment" in brief_types:
            if "deployment" not in dependencies:
                dependencies["deployment"] = []
            dependencies["deployment"].append("feature")
        
        # Analyze content for additional dependencies
        for brief in briefs:
            content_lower = brief.description.lower() + " ".join(brief.tasks).lower()
            
            # Look for explicit dependency mentions
            if "depends on" in content_lower or "requires" in content_lower:
                dependencies.setdefault(brief.brief_type, [])
                # This could be enhanced with more sophisticated analysis
        
        return dependencies
    
    def _generate_tasks_for_brief(self, brief: BriefContent, collection: TaskCollection, 
                                 brief_dependencies: Dict[str, List[str]]) -> List[int]:
        """
        Generate tasks for a single brief with proper ID assignment
        
        Args:
            brief: Brief content to process
            collection: TaskCollection to add tasks to
            brief_dependencies: Dependencies between brief types
            
        Returns:
            List of generated task IDs
        """
        generated_task_ids = []
        
        # Determine base priority for this brief type
        base_priority = self._get_priority_for_brief_type(brief.brief_type)
        
        # Find dependency IDs from previous briefs
        dependency_ids = self._resolve_brief_dependencies(brief, brief_dependencies, collection)
        
        # Process each task description from the brief
        for i, task_desc in enumerate(brief.tasks):
            if not task_desc.strip():
                continue
            
            # Parse task title and description
            title, description = self._parse_task_description(task_desc)
            
            # Determine task-specific priority
            task_priority = self._determine_task_priority(title, description, base_priority)
            
            # Determine dependencies for this specific task
            task_dependencies = self._determine_task_dependencies(
                i, title, description, generated_task_ids, dependency_ids
            )
            
            # Create the task
            task = collection.create_task(
                title=title,
                description=description,
                priority=task_priority,
                dependencies=task_dependencies
            )
            
            generated_task_ids.append(task.id)
            
            logger.debug(f"Created task {task.id}: {title[:50]}...")
        
        return generated_task_ids
    
    def _get_priority_for_brief_type(self, brief_type: str) -> TaskPriority:
        """Get default priority based on brief type"""
        priorities = {
            "setup": TaskPriority.HIGH,
            "feature": TaskPriority.HIGH,
            "deployment": TaskPriority.MEDIUM
        }
        return priorities.get(brief_type, TaskPriority.MEDIUM)
    
    def _parse_task_description(self, task_desc: str) -> Tuple[str, str]:
        """
        Parse a task description into title and description
        
        Args:
            task_desc: Raw task description from brief
            
        Returns:
            Tuple of (title, description)
        """
        # Remove common formatting
        task_desc = task_desc.strip()
        
        # Handle "Title: Description" format
        if ": " in task_desc:
            parts = task_desc.split(": ", 1)
            title = parts[0].strip()
            description = parts[1].strip()
            
            # Clean up title (remove bold markdown, etc.)
            title = title.replace("**", "").replace("*", "").strip()
            
            return title, description
        else:
            # Use first part as title, full text as description
            words = task_desc.split()
            if len(words) > 6:
                title = " ".join(words[:6]) + "..."
            else:
                title = task_desc
            
            return title, task_desc
    
    def _determine_task_priority(self, title: str, description: str, base_priority: TaskPriority) -> TaskPriority:
        """
        Determine priority for a specific task based on content
        
        Args:
            title: Task title
            description: Task description  
            base_priority: Default priority for the brief type
            
        Returns:
            TaskPriority for this task
        """
        title_lower = title.lower()
        desc_lower = description.lower()
        combined = f"{title_lower} {desc_lower}"
        
        # High priority indicators
        high_priority_keywords = [
            "critical", "essential", "foundation", "core", "must-have", "required",
            "setup", "infrastructure", "framework", "basic", "fundamental"
        ]
        
        # Low priority indicators  
        low_priority_keywords = [
            "optional", "nice-to-have", "enhancement", "improvement", "optimization",
            "polish", "extra", "bonus", "future"
        ]
        
        # Check for priority keywords
        if any(keyword in combined for keyword in high_priority_keywords):
            return TaskPriority.HIGH
        elif any(keyword in combined for keyword in low_priority_keywords):
            return TaskPriority.LOW
        
        return base_priority
    
    def _resolve_brief_dependencies(self, current_brief: BriefContent, 
                                   brief_dependencies: Dict[str, List[str]], 
                                   collection: TaskCollection) -> List[int]:
        """
        Resolve dependencies from other briefs to specific task IDs
        
        Args:
            current_brief: Brief being processed
            brief_dependencies: Map of brief type dependencies
            collection: Current task collection
            
        Returns:
            List of task IDs that this brief depends on
        """
        dependency_ids = []
        
        # Get brief-level dependencies
        brief_deps = brief_dependencies.get(current_brief.brief_type, [])
        
        # Find the last tasks from dependency briefs
        all_tasks = collection.get_all_tasks()
        
        for dep_brief_type in brief_deps:
            # Find tasks that were likely generated from the dependency brief
            # This is a heuristic - in a production system you'd track this more explicitly
            dep_tasks = [t for t in all_tasks if self._task_likely_from_brief_type(t, dep_brief_type)]
            
            if dep_tasks:
                # Use the last task from the dependency brief as the dependency
                last_dep_task = max(dep_tasks, key=lambda t: t.id)
                dependency_ids.append(last_dep_task.id)
        
        return dependency_ids
    
    def _task_likely_from_brief_type(self, task: Task, brief_type: str) -> bool:
        """
        Heuristic to determine if a task likely came from a specific brief type
        
        Args:
            task: Task to analyze
            brief_type: Brief type to check against
            
        Returns:
            True if task likely from this brief type
        """
        title_lower = task.title.lower()
        desc_lower = task.description.lower()
        combined = f"{title_lower} {desc_lower}"
        
        # Keywords associated with each brief type
        type_keywords = {
            "setup": ["setup", "structure", "cli", "directory", "framework", "foundation", "install", "configure"],
            "feature": ["implement", "create", "build", "feature", "functionality", "interface", "component"],
            "deployment": ["test", "documentation", "deploy", "release", "quality", "error handling", "performance"]
        }
        
        keywords = type_keywords.get(brief_type, [])
        return any(keyword in combined for keyword in keywords)
    
    def _determine_task_dependencies(self, task_index: int, title: str, description: str,
                                   previous_task_ids: List[int], brief_dependencies: List[int]) -> List[int]:
        """
        Determine dependencies for a specific task
        
        Args:
            task_index: Index of this task within the brief
            title: Task title
            description: Task description
            previous_task_ids: IDs of previously created tasks in this brief
            brief_dependencies: Dependencies from other briefs
            
        Returns:
            List of task ID dependencies
        """
        dependencies = []
        
        # Add brief-level dependencies (usually only for first task in brief)
        if task_index == 0 and brief_dependencies:
            dependencies.extend(brief_dependencies)
        
        # Add sequential dependencies within the brief
        # Most tasks depend on the previous task in the same brief
        if previous_task_ids:
            # For setup and feature briefs, each task typically depends on the previous one
            if task_index > 0:
                dependencies.append(previous_task_ids[-1])  # Depend on immediately previous task
        
        # Analyze content for explicit dependencies
        title_lower = title.lower()
        desc_lower = description.lower()
        
        # Look for dependency keywords
        if any(word in desc_lower for word in ["requires", "depends", "after", "once", "following"]):
            # This could be enhanced with more sophisticated dependency parsing
            pass
        
        return dependencies
    
    def get_next_available_id(self) -> int:
        """Get the next available task ID"""
        while self.next_available_id in self.reserved_ids:
            self.next_available_id += 1
        return self.next_available_id
    
    def reserve_id(self, task_id: int) -> None:
        """Reserve a task ID to prevent conflicts"""
        self.reserved_ids.add(task_id)
        if task_id >= self.next_available_id:
            self.next_available_id = task_id + 1
    
    def get_generation_summary(self, collection: TaskCollection) -> Dict[str, any]:
        """
        Get a summary of the task generation process
        
        Args:
            collection: TaskCollection that was generated
            
        Returns:
            Dictionary with generation statistics
        """
        all_tasks = collection.get_all_tasks()
        
        # Count tasks by priority
        priority_counts = {}
        for priority in TaskPriority:
            priority_counts[priority.value] = len([t for t in all_tasks if t.priority == priority])
        
        # Count tasks by dependency level
        dependency_counts = {
            "no_dependencies": len([t for t in all_tasks if not t.dependencies]),
            "has_dependencies": len([t for t in all_tasks if t.dependencies])
        }
        
        return {
            "total_tasks": len(all_tasks),
            "new_tasks": len(all_tasks) - len(self.reserved_ids) if self.reserved_ids else len(all_tasks),
            "existing_tasks": len(self.reserved_ids) if self.reserved_ids else 0,
            "priority_distribution": priority_counts,
            "dependency_distribution": dependency_counts,
            "id_range": {
                "min": min(t.id for t in all_tasks) if all_tasks else 0,
                "max": max(t.id for t in all_tasks) if all_tasks else 0
            }
        }