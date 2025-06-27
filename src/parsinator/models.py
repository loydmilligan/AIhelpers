"""
Data models for Parsinator task generation
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Set
from datetime import datetime
from enum import Enum
import json
from pathlib import Path

class TaskStatus(Enum):
    """Valid task status values"""
    TODO = "to-do"
    IN_PROGRESS = "in-progress" 
    DONE = "done"

class TaskPriority(Enum):
    """Valid task priority values"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class Task:
    """Represents a single task"""
    id: int
    title: str
    description: str
    priority: TaskPriority
    dependencies: List[int] = field(default_factory=list)
    status: TaskStatus = TaskStatus.TODO
    
    def __post_init__(self):
        """Validate task data after initialization"""
        if not self.title.strip():
            raise ValueError("Task title cannot be empty")
        if not self.description.strip():
            raise ValueError("Task description cannot be empty")
        if self.id <= 0:
            raise ValueError("Task ID must be positive")
        
        # Convert string enums if needed
        if isinstance(self.priority, str):
            self.priority = TaskPriority(self.priority)
        if isinstance(self.status, str):
            self.status = TaskStatus(self.status)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "dependencies": self.dependencies.copy(),
            "status": self.status.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary"""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            priority=TaskPriority(data["priority"]),
            dependencies=data.get("dependencies", []),
            status=TaskStatus(data.get("status", "to-do"))
        )
    
    def is_blocked_by(self, completed_task_ids: Set[int]) -> bool:
        """Check if task is blocked by incomplete dependencies"""
        return not all(dep_id in completed_task_ids for dep_id in self.dependencies)
    
    def add_dependency(self, task_id: int) -> None:
        """Add a dependency if not already present"""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
    
    def remove_dependency(self, task_id: int) -> None:
        """Remove a dependency if present"""
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)

@dataclass
class BriefContent:
    """Represents parsed content from a brief file"""
    file_path: Path
    brief_type: str  # setup, feature, deployment
    title: str
    description: str
    tasks: List[str] = field(default_factory=list)  # Raw task descriptions from brief
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate brief content"""
        if not self.title.strip():
            raise ValueError("Brief title cannot be empty")
        if self.brief_type not in ["setup", "feature", "deployment"]:
            raise ValueError(f"Invalid brief type: {self.brief_type}")

@dataclass 
class ProjectMetadata:
    """Represents project-level metadata"""
    name: str
    description: str
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)
    total_tasks: int = 0
    completed_tasks: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        return {
            "created": self.created.isoformat(),
            "updated": self.updated.isoformat(), 
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], name: str = "Generated Project") -> 'ProjectMetadata':
        """Create metadata from dictionary"""
        created = datetime.fromisoformat(data.get("created", datetime.now().isoformat()))
        updated = datetime.fromisoformat(data.get("updated", datetime.now().isoformat()))
        
        return cls(
            name=name,
            description=data.get("description", "Generated from project briefs"),
            created=created,
            updated=updated
        )

class TaskCollection:
    """Manages a collection of tasks with dependency validation"""
    
    def __init__(self):
        self._tasks: Dict[int, Task] = {}
        self._next_id = 1
    
    def add_task(self, task: Task) -> None:
        """Add a task to the collection"""
        if task.id in self._tasks:
            raise ValueError(f"Task with ID {task.id} already exists")
        
        # Validate dependencies exist
        for dep_id in task.dependencies:
            if dep_id not in self._tasks:
                raise ValueError(f"Dependency {dep_id} does not exist for task {task.id}")
        
        self._tasks[task.id] = task
        self._next_id = max(self._next_id, task.id + 1)
    
    def create_task(self, title: str, description: str, priority: TaskPriority, 
                   dependencies: List[int] = None) -> Task:
        """Create a new task with auto-assigned ID"""
        if dependencies is None:
            dependencies = []
            
        task = Task(
            id=self._next_id,
            title=title,
            description=description,
            priority=priority,
            dependencies=dependencies
        )
        
        self.add_task(task)
        return task
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """Get task by ID"""
        return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks sorted by ID"""
        return sorted(self._tasks.values(), key=lambda t: t.id)
    
    def get_completed_task_ids(self) -> Set[int]:
        """Get IDs of all completed tasks"""
        return {t.id for t in self._tasks.values() if t.status == TaskStatus.DONE}
    
    def get_unlocked_tasks(self) -> List[Task]:
        """Get tasks that are not blocked by dependencies"""
        completed_ids = self.get_completed_task_ids()
        return [t for t in self._tasks.values() 
                if t.status == TaskStatus.TODO and not t.is_blocked_by(completed_ids)]
    
    def validate_dependencies(self) -> List[str]:
        """Validate all task dependencies and return any errors"""
        errors = []
        
        for task in self._tasks.values():
            # Check for self-dependency
            if task.id in task.dependencies:
                errors.append(f"Task {task.id} depends on itself")
            
            # Check for missing dependencies
            for dep_id in task.dependencies:
                if dep_id not in self._tasks:
                    errors.append(f"Task {task.id} depends on non-existent task {dep_id}")
        
        # Check for circular dependencies (simplified check)
        if self._has_circular_dependencies():
            errors.append("Circular dependencies detected in task graph")
        
        return errors
    
    def _has_circular_dependencies(self) -> bool:
        """Check for circular dependencies using DFS"""
        visited = set()
        rec_stack = set()
        
        def has_cycle(task_id: int) -> bool:
            if task_id in rec_stack:
                return True
            if task_id in visited:
                return False
            
            visited.add(task_id)
            rec_stack.add(task_id)
            
            task = self._tasks.get(task_id)
            if task:
                for dep_id in task.dependencies:
                    if has_cycle(dep_id):
                        return True
            
            rec_stack.remove(task_id)
            return False
        
        for task_id in self._tasks:
            if task_id not in visited:
                if has_cycle(task_id):
                    return True
        
        return False
    
    def to_tasks_json(self, metadata: ProjectMetadata) -> Dict[str, Any]:
        """Convert collection to tasks.json format"""
        return {
            "master": {
                "tasks": [task.to_dict() for task in self.get_all_tasks()],
                "metadata": metadata.to_dict()
            }
        }
    
    @classmethod
    def from_tasks_json(cls, data: Dict[str, Any]) -> tuple['TaskCollection', ProjectMetadata]:
        """Create collection and metadata from tasks.json format"""
        collection = cls()
        
        # Load metadata
        metadata_dict = data.get("master", {}).get("metadata", {})
        metadata = ProjectMetadata.from_dict(metadata_dict)
        
        # Load tasks
        tasks_data = data.get("master", {}).get("tasks", [])
        for task_data in tasks_data:
            task = Task.from_dict(task_data)
            collection._tasks[task.id] = task
            collection._next_id = max(collection._next_id, task.id + 1)
        
        return collection, metadata

class TaskGenerator:
    """Generates tasks from brief content"""
    
    def __init__(self):
        self.task_collection = TaskCollection()
        
    def generate_from_briefs(self, briefs: List[BriefContent], 
                           existing_collection: TaskCollection = None) -> TaskCollection:
        """
        Generate tasks from multiple brief files
        
        Args:
            briefs: List of parsed brief content
            existing_collection: Existing tasks for additive sessions
            
        Returns:
            TaskCollection with generated tasks
        """
        if existing_collection:
            self.task_collection = existing_collection
        
        # Process briefs in order: setup -> feature -> deployment
        ordered_briefs = self._order_briefs(briefs)
        
        for brief in ordered_briefs:
            self._generate_tasks_from_brief(brief)
        
        # Validate the final collection
        errors = self.task_collection.validate_dependencies()
        if errors:
            raise ValueError(f"Task generation validation failed: {errors}")
        
        return self.task_collection
    
    def _order_briefs(self, briefs: List[BriefContent]) -> List[BriefContent]:
        """Order briefs by type: setup -> feature -> deployment"""
        type_order = {"setup": 0, "feature": 1, "deployment": 2}
        return sorted(briefs, key=lambda b: (type_order.get(b.brief_type, 1), b.file_path.name))
    
    def _generate_tasks_from_brief(self, brief: BriefContent) -> None:
        """Generate tasks from a single brief"""
        # This is a placeholder - actual implementation will be in Task 6
        # For now, create simple tasks based on the brief content
        
        base_priority = self._get_priority_for_brief_type(brief.brief_type)
        
        for i, task_desc in enumerate(brief.tasks):
            if task_desc.strip():
                task = self.task_collection.create_task(
                    title=f"Task from {brief.file_path.name}",
                    description=task_desc.strip(),
                    priority=base_priority
                )
    
    def _get_priority_for_brief_type(self, brief_type: str) -> TaskPriority:
        """Get default priority based on brief type"""
        priorities = {
            "setup": TaskPriority.HIGH,
            "feature": TaskPriority.HIGH, 
            "deployment": TaskPriority.MEDIUM
        }
        return priorities.get(brief_type, TaskPriority.MEDIUM)