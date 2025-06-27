"""
File I/O utilities for Parsinator
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class FileIOError(Exception):
    """Custom exception for file I/O operations"""
    pass

class FileHandler:
    """Handles all file reading/writing operations for Parsinator"""
    
    def __init__(self, base_directory: str = "."):
        self.base_dir = Path(base_directory).resolve()
        
    def read_brief_file(self, filepath: str) -> str:
        """
        Read a .md brief file safely
        
        Args:
            filepath: Path to the brief file
            
        Returns:
            File content as string
            
        Raises:
            FileIOError: If file cannot be read
        """
        try:
            file_path = self._validate_path(filepath, [".md"])
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            logger.info(f"Successfully read brief file: {file_path}")
            return content
            
        except Exception as e:
            raise FileIOError(f"Failed to read brief file {filepath}: {str(e)}")
    
    def read_tasks_json(self, filepath: str) -> Dict[str, Any]:
        """
        Read existing tasks.json file
        
        Args:
            filepath: Path to tasks.json file
            
        Returns:
            Parsed JSON data
            
        Raises:
            FileIOError: If file cannot be read or parsed
        """
        try:
            file_path = self._validate_path(filepath, [".json"])
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            logger.info(f"Successfully read tasks file: {file_path}")
            return data
            
        except FileNotFoundError:
            logger.info(f"Tasks file not found: {filepath} (this is ok for new projects)")
            return {}
        except json.JSONDecodeError as e:
            raise FileIOError(f"Invalid JSON in tasks file {filepath}: {str(e)}")
        except Exception as e:
            raise FileIOError(f"Failed to read tasks file {filepath}: {str(e)}")
    
    def write_tasks_json(self, filepath: str, data: Dict[str, Any]) -> None:
        """
        Write tasks.json file safely
        
        Args:
            filepath: Path where to write tasks.json
            data: Task data to write
            
        Raises:
            FileIOError: If file cannot be written
        """
        try:
            file_path = self._validate_output_path(filepath, ".json")
            
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Successfully wrote tasks file: {file_path}")
            
        except Exception as e:
            raise FileIOError(f"Failed to write tasks file {filepath}: {str(e)}")
    
    def write_task_file(self, filepath: str, content: str) -> None:
        """
        Write individual task file
        
        Args:
            filepath: Path where to write task file
            content: Task file content
            
        Raises:
            FileIOError: If file cannot be written
        """
        try:
            # Allow both .txt and .md extensions for task files
            file_path = Path(filepath).resolve()
            if file_path.suffix.lower() not in ['.txt', '.md']:
                raise ValueError(f"Invalid file extension. Expected: .txt or .md, got: {file_path.suffix}")
            
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"Successfully wrote task file: {file_path}")
            
        except Exception as e:
            raise FileIOError(f"Failed to write task file {filepath}: {str(e)}")
    
    def find_brief_files(self, directory: str) -> List[Path]:
        """
        Find all .md brief files in directory
        
        Args:
            directory: Directory to search
            
        Returns:
            List of brief file paths, sorted by name
            
        Raises:
            FileIOError: If directory cannot be accessed
        """
        try:
            dir_path = self._validate_directory_path(directory)
            
            brief_files = sorted(dir_path.glob("*.md"))
            
            logger.info(f"Found {len(brief_files)} brief files in {dir_path}")
            return brief_files
            
        except Exception as e:
            raise FileIOError(f"Failed to find brief files in {directory}: {str(e)}")
    
    def _validate_path(self, filepath: str, allowed_extensions: List[str]) -> Path:
        """Validate input file path for security and existence"""
        file_path = Path(filepath).resolve()
        
        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
            
        # Check file extension
        if file_path.suffix.lower() not in allowed_extensions:
            raise ValueError(f"Invalid file extension. Allowed: {allowed_extensions}")
            
        # Basic security check - ensure it's under base directory or is absolute path we trust
        try:
            # This will raise an exception if file_path is not under base_dir
            file_path.relative_to(self.base_dir)
        except ValueError:
            # If it's not under base_dir, it should be an absolute path we explicitly allow
            if not file_path.is_absolute():
                raise ValueError(f"File path outside base directory: {filepath}")
                
        return file_path
    
    def _validate_output_path(self, filepath: str, expected_extension: str) -> Path:
        """Validate output file path"""
        file_path = Path(filepath).resolve()
        
        # Check file extension
        if not file_path.suffix.lower() == expected_extension:
            raise ValueError(f"Invalid file extension. Expected: {expected_extension}")
            
        return file_path
    
    def _validate_directory_path(self, directory: str) -> Path:
        """Validate directory path"""
        dir_path = Path(directory).resolve()
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
            
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")
            
        return dir_path
