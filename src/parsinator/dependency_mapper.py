"""
Advanced Dependency Mapping Logic for Parsinator
Analyzes task relationships and suggests intelligent dependencies
"""
import re
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import logging

from parsinator.models import Task, BriefContent, TaskPriority, TaskCollection

logger = logging.getLogger(__name__)

@dataclass
class DependencyRelationship:
    """Represents a dependency relationship between tasks"""
    from_task_id: int
    to_task_id: int
    relationship_type: str  # "sequential", "prerequisite", "blocking", "optional"
    confidence: float  # 0.0 to 1.0
    reason: str
    
@dataclass
class DependencyAnalysis:
    """Results of dependency analysis"""
    suggested_dependencies: List[DependencyRelationship]
    warnings: List[str]
    statistics: Dict[str, Any]

class DependencyMapper:
    """
    Advanced dependency mapping system that analyzes task relationships
    """
    
    def __init__(self):
        # Keywords that indicate dependencies
        self.dependency_keywords = {
            'prerequisite': ['requires', 'needs', 'depends on', 'after', 'once', 'following'],
            'blocking': ['before', 'prior to', 'must precede', 'prerequisite for'],
            'sequential': ['then', 'next', 'subsequently', 'continue', 'build on'],
            'optional': ['optionally', 'if needed', 'consider', 'may want to']
        }
        
        # Technical implementation patterns
        self.implementation_patterns = {
            'foundation': ['setup', 'initialize', 'create structure', 'establish', 'configure'],
            'implementation': ['implement', 'build', 'create', 'develop', 'code'],
            'integration': ['integrate', 'connect', 'combine', 'merge', 'link'],
            'testing': ['test', 'validate', 'verify', 'check', 'ensure'],
            'documentation': ['document', 'write docs', 'create guide', 'explain'],
            'deployment': ['deploy', 'release', 'publish', 'distribute', 'launch']
        }
        
        # Brief type dependency rules
        self.brief_type_rules = {
            'setup': {
                'priority': 1,
                'typically_blocks': ['feature', 'deployment'],
                'internal_sequential': True
            },
            'feature': {
                'priority': 2,
                'depends_on': ['setup'],
                'typically_blocks': ['deployment'],
                'internal_sequential': False  # Features can often be parallel
            },
            'deployment': {
                'priority': 3,
                'depends_on': ['setup', 'feature'],
                'internal_sequential': True
            }
        }
    
    def analyze_dependencies(self, briefs: List[BriefContent], 
                           task_collection: TaskCollection) -> DependencyAnalysis:
        """
        Perform comprehensive dependency analysis
        
        Args:
            briefs: List of parsed briefs
            task_collection: Collection of generated tasks
            
        Returns:
            DependencyAnalysis with suggested dependencies and insights
        """
        logger.info(f"Analyzing dependencies for {len(briefs)} briefs and {len(task_collection.get_all_tasks())} tasks")
        
        suggested_dependencies = []
        warnings = []
        statistics = {}
        
        # Group tasks by brief
        task_groups = self._group_tasks_by_brief(briefs, task_collection)
        
        # Analyze within-brief dependencies
        within_brief_deps = self._analyze_within_brief_dependencies(task_groups)
        suggested_dependencies.extend(within_brief_deps)
        
        # Analyze cross-brief dependencies
        cross_brief_deps = self._analyze_cross_brief_dependencies(briefs, task_groups)
        suggested_dependencies.extend(cross_brief_deps)
        
        # Analyze content-based dependencies
        content_deps = self._analyze_content_dependencies(task_collection)
        suggested_dependencies.extend(content_deps)
        
        # Check for circular dependencies
        circular_warnings = self._detect_circular_dependencies(suggested_dependencies)
        warnings.extend(circular_warnings)
        
        # Generate statistics
        statistics = self._generate_dependency_statistics(suggested_dependencies, task_collection)
        
        logger.info(f"Dependency analysis complete: {len(suggested_dependencies)} suggestions, {len(warnings)} warnings")
        
        return DependencyAnalysis(
            suggested_dependencies=suggested_dependencies,
            warnings=warnings,
            statistics=statistics
        )
    
    def _group_tasks_by_brief(self, briefs: List[BriefContent], 
                             task_collection: TaskCollection) -> Dict[str, List[Task]]:
        """Group tasks by their originating brief"""
        task_groups = {}
        all_tasks = task_collection.get_all_tasks()
        
        for brief in briefs:
            brief_key = f"{brief.brief_type}_{brief.file_path.stem}"
            task_groups[brief_key] = []
            
            # Use heuristics to associate tasks with briefs
            # This is based on task content matching brief content
            for task in all_tasks:
                if self._task_belongs_to_brief(task, brief):
                    task_groups[brief_key].append(task)
        
        # Handle any unassigned tasks
        assigned_task_ids = set()
        for tasks in task_groups.values():
            assigned_task_ids.update(t.id for t in tasks)
        
        unassigned_tasks = [t for t in all_tasks if t.id not in assigned_task_ids]
        if unassigned_tasks:
            task_groups['_unassigned'] = unassigned_tasks
        
        return task_groups
    
    def _task_belongs_to_brief(self, task: Task, brief: BriefContent) -> bool:
        """Determine if a task likely belongs to a specific brief"""
        task_text = f"{task.title} {task.description}".lower()
        
        # Check for brief title keywords
        brief_title_words = set(re.findall(r'\w+', brief.title.lower()))
        task_words = set(re.findall(r'\w+', task_text))
        
        # Check for content overlap
        brief_content = f"{brief.description} {' '.join(brief.tasks)}".lower()
        brief_words = set(re.findall(r'\w+', brief_content))
        
        # Calculate similarity scores
        title_overlap = len(brief_title_words & task_words) / max(len(brief_title_words), 1)
        content_overlap = len(brief_words & task_words) / max(len(brief_words), 1)
        
        # Use brief type patterns
        type_patterns = self.implementation_patterns.get(brief.brief_type, [])
        type_matches = sum(1 for pattern in type_patterns if pattern in task_text)
        
        # Scoring heuristic
        score = (title_overlap * 0.4) + (content_overlap * 0.4) + (type_matches * 0.2)
        return score > 0.3  # Threshold for association
    
    def _analyze_within_brief_dependencies(self, task_groups: Dict[str, List[Task]]) -> List[DependencyRelationship]:
        """Analyze dependencies within each brief"""
        dependencies = []
        
        for brief_key, tasks in task_groups.items():
            if len(tasks) <= 1:
                continue
            
            # Sort tasks by ID (assuming they were created in order)
            sorted_tasks = sorted(tasks, key=lambda t: t.id)
            
            # Determine brief type from key
            brief_type = brief_key.split('_')[0] if '_' in brief_key else 'unknown'
            is_sequential = self.brief_type_rules.get(brief_type, {}).get('internal_sequential', True)
            
            if is_sequential:
                # Create sequential dependencies
                for i in range(1, len(sorted_tasks)):
                    prev_task = sorted_tasks[i-1]
                    curr_task = sorted_tasks[i]
                    
                    dependencies.append(DependencyRelationship(
                        from_task_id=curr_task.id,
                        to_task_id=prev_task.id,
                        relationship_type='sequential',
                        confidence=0.8,
                        reason=f"Sequential dependency within {brief_type} brief"
                    ))
            else:
                # Analyze for logical dependencies based on content
                content_deps = self._analyze_task_content_dependencies(sorted_tasks)
                dependencies.extend(content_deps)
        
        return dependencies
    
    def _analyze_cross_brief_dependencies(self, briefs: List[BriefContent], 
                                         task_groups: Dict[str, List[Task]]) -> List[DependencyRelationship]:
        """Analyze dependencies between different briefs"""
        dependencies = []
        
        # Sort briefs by type priority
        sorted_briefs = sorted(briefs, key=lambda b: self.brief_type_rules.get(b.brief_type, {}).get('priority', 999))
        
        for i, current_brief in enumerate(sorted_briefs):
            current_key = f"{current_brief.brief_type}_{current_brief.file_path.stem}"
            current_tasks = task_groups.get(current_key, [])
            
            if not current_tasks:
                continue
            
            # Check dependencies on previous briefs
            for j in range(i):
                prev_brief = sorted_briefs[j]
                prev_key = f"{prev_brief.brief_type}_{prev_brief.file_path.stem}"
                prev_tasks = task_groups.get(prev_key, [])
                
                if not prev_tasks:
                    continue
                
                # Create dependency from first task of current brief to last task of previous brief
                first_current = min(current_tasks, key=lambda t: t.id)
                last_prev = max(prev_tasks, key=lambda t: t.id)
                
                # Check if this dependency makes sense
                if self._should_create_cross_brief_dependency(current_brief, prev_brief):
                    dependencies.append(DependencyRelationship(
                        from_task_id=first_current.id,
                        to_task_id=last_prev.id,
                        relationship_type='prerequisite',
                        confidence=0.9,
                        reason=f"{current_brief.brief_type} depends on {prev_brief.brief_type} completion"
                    ))
        
        return dependencies
    
    def _should_create_cross_brief_dependency(self, current_brief: BriefContent, 
                                            prev_brief: BriefContent) -> bool:
        """Determine if a cross-brief dependency should be created"""
        current_type = current_brief.brief_type
        prev_type = prev_brief.brief_type
        
        # Use brief type rules
        depends_on = self.brief_type_rules.get(current_type, {}).get('depends_on', [])
        if prev_type in depends_on:
            return True
        
        # Check content for explicit dependencies
        current_content = f"{current_brief.description} {' '.join(current_brief.tasks)}".lower()
        
        # Look for mentions of the previous brief's concepts
        prev_keywords = set(re.findall(r'\w+', prev_brief.title.lower()))
        if any(keyword in current_content for keyword in prev_keywords):
            return True
        
        return False
    
    def _analyze_content_dependencies(self, task_collection: TaskCollection) -> List[DependencyRelationship]:
        """Analyze dependencies based on task content"""
        dependencies = []
        all_tasks = task_collection.get_all_tasks()
        
        for task in all_tasks:
            content = f"{task.title} {task.description}".lower()
            
            # Look for explicit dependency keywords
            for dep_type, keywords in self.dependency_keywords.items():
                for keyword in keywords:
                    if keyword in content:
                        # Try to find referenced tasks
                        referenced_tasks = self._find_referenced_tasks(task, all_tasks, keyword)
                        
                        for ref_task, confidence in referenced_tasks:
                            dependencies.append(DependencyRelationship(
                                from_task_id=task.id,
                                to_task_id=ref_task.id,
                                relationship_type=dep_type,
                                confidence=confidence,
                                reason=f"Content mentions '{keyword}'"
                            ))
        
        return dependencies
    
    def _analyze_task_content_dependencies(self, tasks: List[Task]) -> List[DependencyRelationship]:
        """Analyze dependencies between tasks based on their content"""
        dependencies = []
        
        for i, task in enumerate(tasks):
            task_content = f"{task.title} {task.description}".lower()
            
            # Look for implementation patterns
            for pattern_type, patterns in self.implementation_patterns.items():
                if any(pattern in task_content for pattern in patterns):
                    # Find tasks that should come before this pattern
                    for j, other_task in enumerate(tasks):
                        if i == j:
                            continue
                        
                        other_content = f"{other_task.title} {other_task.description}".lower()
                        
                        # Check for prerequisite patterns
                        if self._is_prerequisite_pattern(other_content, pattern_type):
                            dependencies.append(DependencyRelationship(
                                from_task_id=task.id,
                                to_task_id=other_task.id,
                                relationship_type='prerequisite',
                                confidence=0.7,
                                reason=f"{pattern_type} requires foundation from other task"
                            ))
        
        return dependencies
    
    def _is_prerequisite_pattern(self, task_content: str, target_pattern: str) -> bool:
        """Check if task content represents a prerequisite for target pattern"""
        prerequisite_map = {
            'implementation': ['foundation', 'setup'],
            'integration': ['implementation', 'foundation'],
            'testing': ['implementation', 'integration'],
            'documentation': ['implementation', 'testing'],
            'deployment': ['testing', 'documentation']
        }
        
        prerequisites = prerequisite_map.get(target_pattern, [])
        return any(prereq in task_content for prereq in prerequisites)
    
    def _find_referenced_tasks(self, current_task: Task, all_tasks: List[Task], 
                              keyword: str) -> List[Tuple[Task, float]]:
        """Find tasks that might be referenced by dependency keywords"""
        referenced = []
        current_content = f"{current_task.title} {current_task.description}".lower()
        
        # Look for task references near the keyword
        keyword_context = self._extract_keyword_context(current_content, keyword)
        
        for task in all_tasks:
            if task.id == current_task.id:
                continue
            
            # Check if this task is mentioned in the context
            task_words = set(re.findall(r'\w+', f"{task.title} {task.description}".lower()))
            context_words = set(re.findall(r'\w+', keyword_context))
            
            overlap = len(task_words & context_words)
            if overlap >= 2:  # At least 2 word overlap
                confidence = min(0.9, overlap / len(task_words))
                referenced.append((task, confidence))
        
        return referenced
    
    def _extract_keyword_context(self, content: str, keyword: str, window: int = 10) -> str:
        """Extract context around a keyword"""
        words = content.split()
        try:
            keyword_index = words.index(keyword)
            start = max(0, keyword_index - window)
            end = min(len(words), keyword_index + window + 1)
            return ' '.join(words[start:end])
        except ValueError:
            return ''
    
    def _detect_circular_dependencies(self, dependencies: List[DependencyRelationship]) -> List[str]:
        """Detect circular dependencies in the suggested relationships"""
        warnings = []
        
        # Build dependency graph
        graph = {}
        for dep in dependencies:
            if dep.from_task_id not in graph:
                graph[dep.from_task_id] = []
            graph[dep.from_task_id].append(dep.to_task_id)
        
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if has_cycle(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    warnings.append(f"Circular dependency detected involving task {node}")
        
        return warnings
    
    def _generate_dependency_statistics(self, dependencies: List[DependencyRelationship], 
                                       task_collection: TaskCollection) -> Dict[str, Any]:
        """Generate statistics about the dependency analysis"""
        total_tasks = len(task_collection.get_all_tasks())
        
        # Count by relationship type
        type_counts = {}
        for dep in dependencies:
            type_counts[dep.relationship_type] = type_counts.get(dep.relationship_type, 0) + 1
        
        # Count by confidence level
        confidence_buckets = {'high': 0, 'medium': 0, 'low': 0}
        for dep in dependencies:
            if dep.confidence >= 0.8:
                confidence_buckets['high'] += 1
            elif dep.confidence >= 0.5:
                confidence_buckets['medium'] += 1
            else:
                confidence_buckets['low'] += 1
        
        # Tasks with dependencies
        tasks_with_deps = len(set(dep.from_task_id for dep in dependencies))
        
        return {
            'total_dependencies_suggested': len(dependencies),
            'dependency_types': type_counts,
            'confidence_distribution': confidence_buckets,
            'tasks_with_dependencies': tasks_with_deps,
            'dependency_density': len(dependencies) / max(total_tasks, 1),
            'average_confidence': sum(dep.confidence for dep in dependencies) / max(len(dependencies), 1)
        }
    
    def apply_dependencies(self, task_collection: TaskCollection, 
                          dependencies: List[DependencyRelationship],
                          confidence_threshold: float = 0.7) -> int:
        """
        Apply suggested dependencies to the task collection
        
        Args:
            task_collection: TaskCollection to modify
            dependencies: List of suggested dependencies
            confidence_threshold: Minimum confidence to apply dependency
            
        Returns:
            Number of dependencies applied
        """
        applied_count = 0
        
        for dep in dependencies:
            if dep.confidence < confidence_threshold:
                continue
            
            task = task_collection.get_task(dep.from_task_id)
            if task and dep.to_task_id not in task.dependencies and dep.from_task_id != dep.to_task_id:
                task.add_dependency(dep.to_task_id)
                applied_count += 1
                logger.debug(f"Applied dependency: Task {dep.from_task_id} -> {dep.to_task_id} ({dep.reason})")
        
        return applied_count