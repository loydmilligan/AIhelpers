"""
Brief Parser Engine for Parsinator
Parses setup, feature, and deployment briefs into structured data
"""
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from parsinator.models import BriefContent, TaskPriority
from parsinator.utils import FileHandler, FileIOError

@dataclass
class ParsedTask:
    """Represents a parsed task from a brief"""
    title: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    details: str = ""
    is_optional: bool = False

class BriefParser:
    """Parses brief files and extracts structured data"""
    
    def __init__(self):
        self.file_handler = FileHandler()
        
        # Regex patterns for parsing different sections
        self.section_patterns = {
            'title': r'^#\s+(.+?)(?:\n|$)',
            'h2_section': r'^##\s+(.+?)(?:\n|$)', 
            'h3_section': r'^###\s+(.+?)(?:\n|$)',
            'task_list_item': r'^\d+\.\s+\*\*(.+?)\*\*:\s*(.+?)$',
            'bullet_item': r'^\*\s+(.+?)$',
            'dash_item': r'^-\s+(.+?)$'
        }
    
    def parse_brief_file(self, file_path: str) -> BriefContent:
        """
        Parse a brief file and extract structured content
        
        Args:
            file_path: Path to the brief file
            
        Returns:
            BriefContent object with parsed data
            
        Raises:
            FileIOError: If file cannot be read
            ValueError: If brief format is invalid
        """
        try:
            # Read the file
            content = self.file_handler.read_brief_file(file_path)
            path_obj = Path(file_path)
            
            # Detect brief type from filename or content
            brief_type = self._detect_brief_type(path_obj.name, content)
            
            # Extract title and description
            title = self._extract_title(content)
            description = self._extract_description(content, brief_type)
            
            # Parse tasks based on brief type
            parsed_tasks = self._parse_tasks_by_type(content, brief_type)
            
            # Extract metadata
            metadata = self._extract_metadata(content, brief_type)
            
            # Convert parsed tasks to simple string list for BriefContent
            task_descriptions = [f"{t.title}: {t.description}" for t in parsed_tasks]
            
            return BriefContent(
                file_path=path_obj,
                brief_type=brief_type,
                title=title,
                description=description,
                tasks=task_descriptions,
                metadata=metadata
            )
            
        except Exception as e:
            raise FileIOError(f"Failed to parse brief file {file_path}: {str(e)}")
    
    def _detect_brief_type(self, filename: str, content: str) -> str:
        """Detect brief type from filename and content"""
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        # Check filename patterns first
        if 'setup' in filename_lower or 'project' in filename_lower:
            return 'setup'
        elif 'deployment' in filename_lower or 'deploy' in filename_lower:
            return 'deployment'
        elif 'feature' in filename_lower:
            return 'feature'
        
        # Check content patterns
        setup_indicators = [
            'project setup', 'infrastructure', 'cli structure', 
            'technical requirements', 'setup scope'
        ]
        deployment_indicators = [
            'deployment', 'testing', 'documentation', 'release',
            'quality assurance', 'deployment goal'
        ]
        
        if any(indicator in content_lower for indicator in setup_indicators):
            return 'setup'
        elif any(indicator in content_lower for indicator in deployment_indicators):
            return 'deployment'
        else:
            return 'feature'  # Default fallback
    
    def _extract_title(self, content: str) -> str:
        """Extract the main title from the brief"""
        lines = content.split('\n')
        
        for line in lines:
            # Look for the first H1 heading
            title_match = re.match(self.section_patterns['title'], line.strip())
            if title_match:
                title = title_match.group(1).strip()
                # Remove common brief template words
                title = re.sub(r'\s*brief\s*template?\s*', '', title, flags=re.IGNORECASE)
                title = re.sub(r'\s*:\s*', ' - ', title)  # Convert colons to dashes
                return title.strip()
        
        return "Untitled Brief"
    
    def _extract_description(self, content: str, brief_type: str) -> str:
        """Extract description from Problem Statement or similar section"""
        lines = content.split('\n')
        description_sections = ['problem statement', 'deployment goal', 'project description']
        
        for i, line in enumerate(lines):
            if re.match(self.section_patterns['h2_section'], line.strip()):
                section_title = re.match(self.section_patterns['h2_section'], line.strip()).group(1).lower()
                
                if any(desc_section in section_title for desc_section in description_sections):
                    # Found a description section, extract content until next H2
                    description_lines = []
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].strip()
                        if re.match(self.section_patterns['h2_section'], next_line):
                            break
                        if next_line:  # Skip empty lines
                            description_lines.append(next_line)
                    
                    if description_lines:
                        return ' '.join(description_lines)
        
        return f"Brief for {brief_type} implementation"
    
    def _parse_tasks_by_type(self, content: str, brief_type: str) -> List[ParsedTask]:
        """Parse tasks based on brief type"""
        if brief_type == 'setup':
            return self._parse_setup_tasks(content)
        elif brief_type == 'feature':
            return self._parse_feature_tasks(content)
        elif brief_type == 'deployment':
            return self._parse_deployment_tasks(content)
        else:
            return self._parse_generic_tasks(content)
    
    def _parse_setup_tasks(self, content: str) -> List[ParsedTask]:
        """Parse setup brief tasks"""
        tasks = []
        
        # Look for "Core Setup Tasks" section
        core_tasks = self._extract_section_tasks(content, "core setup tasks", TaskPriority.HIGH)
        tasks.extend(core_tasks)
        
        # Look for "Optional Setup Tasks" section
        optional_tasks = self._extract_section_tasks(content, "optional setup tasks", TaskPriority.MEDIUM, is_optional=True)
        tasks.extend(optional_tasks)
        
        return tasks
    
    def _parse_feature_tasks(self, content: str) -> List[ParsedTask]:
        """Parse feature brief tasks"""
        tasks = []
        
        # Look for "Core Feature Tasks" section
        core_tasks = self._extract_section_tasks(content, "core feature tasks", TaskPriority.HIGH)
        tasks.extend(core_tasks)
        
        # Look for "Must-Have Implementation" subsection
        must_have_tasks = self._extract_section_tasks(content, "must-have implementation", TaskPriority.HIGH)
        tasks.extend(must_have_tasks)
        
        # Look for "Nice-to-Have Enhancements" section
        nice_to_have_tasks = self._extract_section_tasks(content, "nice-to-have", TaskPriority.MEDIUM, is_optional=True)
        tasks.extend(nice_to_have_tasks)
        
        return tasks
    
    def _parse_deployment_tasks(self, content: str) -> List[ParsedTask]:
        """Parse deployment brief tasks"""
        tasks = []
        
        # Look for "Core Deployment Tasks" section
        core_tasks = self._extract_section_tasks(content, "core deployment tasks", TaskPriority.HIGH)
        tasks.extend(core_tasks)
        
        # Look for "Must-Have for Release" subsection
        must_have_tasks = self._extract_section_tasks(content, "must-have for release", TaskPriority.HIGH)
        tasks.extend(must_have_tasks)
        
        # Look for "Quality Improvements" section
        quality_tasks = self._extract_section_tasks(content, "quality improvements", TaskPriority.MEDIUM)
        tasks.extend(quality_tasks)
        
        return tasks
    
    def _extract_section_tasks(self, content: str, section_name: str, 
                              priority: TaskPriority, is_optional: bool = False) -> List[ParsedTask]:
        """Extract tasks from a specific section"""
        tasks = []
        lines = content.split('\n')
        in_target_section = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check if we found the target section
            if re.match(self.section_patterns['h2_section'], line_stripped) or re.match(self.section_patterns['h3_section'], line_stripped):
                section_title = re.match(r'^#{2,3}\s+(.+?)(?:\n|$)', line_stripped)
                if section_title and section_name.lower() in section_title.group(1).lower():
                    in_target_section = True
                    continue
                elif in_target_section:
                    # We've moved to a new section
                    break
            
            # If we're in the target section, look for task list items
            if in_target_section:
                # Check for numbered list with bold task names
                task_match = re.match(self.section_patterns['task_list_item'], line_stripped)
                if task_match:
                    task_title = task_match.group(1).strip()
                    task_description = task_match.group(2).strip()
                    
                    tasks.append(ParsedTask(
                        title=task_title,
                        description=task_description,
                        priority=priority,
                        is_optional=is_optional
                    ))
                
                # Check for bullet points
                elif re.match(self.section_patterns['bullet_item'], line_stripped):
                    bullet_match = re.match(self.section_patterns['bullet_item'], line_stripped)
                    if bullet_match:
                        task_content = bullet_match.group(1).strip()
                        # Try to split into title and description
                        if ':' in task_content:
                            parts = task_content.split(':', 1)
                            task_title = parts[0].strip().rstrip('*').strip()
                            task_description = parts[1].strip()
                        else:
                            task_title = task_content
                            task_description = task_content
                        
                        tasks.append(ParsedTask(
                            title=task_title,
                            description=task_description,
                            priority=priority,
                            is_optional=is_optional
                        ))
        
        return tasks
    
    def _parse_generic_tasks(self, content: str) -> List[ParsedTask]:
        """Parse tasks from any section that looks like a task list"""
        tasks = []
        lines = content.split('\n')
        
        for line in lines:
            line_stripped = line.strip()
            
            # Look for numbered task items
            task_match = re.match(self.section_patterns['task_list_item'], line_stripped)
            if task_match:
                task_title = task_match.group(1).strip()
                task_description = task_match.group(2).strip()
                
                tasks.append(ParsedTask(
                    title=task_title,
                    description=task_description,
                    priority=TaskPriority.MEDIUM
                ))
        
        return tasks
    
    def _extract_metadata(self, content: str, brief_type: str) -> Dict[str, Any]:
        """Extract metadata from the brief"""
        metadata = {
            'brief_type': brief_type,
            'word_count': len(content.split()),
            'line_count': len(content.split('\n'))
        }
        
        # Extract specific metadata based on brief type
        if brief_type == 'setup':
            metadata.update(self._extract_setup_metadata(content))
        elif brief_type == 'feature':
            metadata.update(self._extract_feature_metadata(content))
        elif brief_type == 'deployment':
            metadata.update(self._extract_deployment_metadata(content))
        
        return metadata
    
    def _extract_setup_metadata(self, content: str) -> Dict[str, Any]:
        """Extract setup-specific metadata"""
        metadata = {}
        
        # Look for technical requirements
        tech_req_section = self._extract_section_content(content, "technical requirements")
        if tech_req_section:
            metadata['technical_requirements'] = tech_req_section
        
        return metadata
    
    def _extract_feature_metadata(self, content: str) -> Dict[str, Any]:
        """Extract feature-specific metadata"""
        metadata = {}
        
        # Look for target users
        target_users = self._extract_section_content(content, "target users")
        if target_users:
            metadata['target_users'] = target_users
        
        return metadata
    
    def _extract_deployment_metadata(self, content: str) -> Dict[str, Any]:
        """Extract deployment-specific metadata"""
        metadata = {}
        
        # Look for target environment
        target_env = self._extract_section_content(content, "target environment")
        if target_env:
            metadata['target_environment'] = target_env
        
        return metadata
    
    def _extract_section_content(self, content: str, section_name: str) -> Optional[str]:
        """Extract content from a named section"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if re.match(self.section_patterns['h2_section'], line.strip()):
                section_title = re.match(self.section_patterns['h2_section'], line.strip()).group(1).lower()
                
                if section_name.lower() in section_title:
                    # Extract content until next H2 section
                    section_lines = []
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].strip()
                        if re.match(self.section_patterns['h2_section'], next_line):
                            break
                        if next_line:
                            section_lines.append(next_line)
                    
                    return ' '.join(section_lines) if section_lines else None
        
        return None

class ParsingError(Exception):
    """Exception raised when brief parsing fails"""
    pass