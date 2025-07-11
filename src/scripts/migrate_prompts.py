#!/usr/bin/env python3
"""
Migration script to move file-based prompts to database.

This script scans the prompts directory for template files and migrates them
to the database while preserving functionality and adding proper categorization.
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from ..config.database import get_db_session
from ..models.prompt import Prompt, PromptCategory, PromptVersion
from ..models.analytics import PromptAnalytics
from ..models.user import User, SubscriptionTier
from ..services.prompt_service import PromptService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PromptMigrator:
    """Handles migration of file-based prompts to database."""
    
    def __init__(self, db_session: Session, prompts_directory: str):
        """
        Initialize the migrator.
        
        Args:
            db_session: Database session
            prompts_directory: Path to prompts directory
        """
        self.db = db_session
        self.prompts_dir = Path(prompts_directory)
        self.service = PromptService(db_session)
        
        # Category mapping based on filename patterns
        self.category_patterns = {
            PromptCategory.CODING: [
                r'coding', r'code', r'programming', r'development', r'dev'
            ],
            PromptCategory.ANALYSIS: [
                r'analysis', r'analyze', r'research', r'investigation'
            ],
            PromptCategory.DOCUMENTATION: [
                r'documentation', r'docs', r'readme', r'guide', r'manual'
            ],
            PromptCategory.DEBUGGING: [
                r'debug', r'troubleshoot', r'fix', r'error', r'bug'
            ],
            PromptCategory.TESTING: [
                r'test', r'testing', r'spec', r'validation'
            ],
            PromptCategory.REFACTORING: [
                r'refactor', r'improve', r'optimize', r'cleanup'
            ],
            PromptCategory.REVIEW: [
                r'review', r'audit', r'check', r'evaluate'
            ],
            PromptCategory.PLANNING: [
                r'planning', r'plan', r'design', r'architecture', r'brief'
            ]
        }
    
    def _get_or_create_system_user(self) -> User:
        """Get or create a system user for migrated prompts."""
        system_user = self.db.query(User).filter(
            User.email == "system@aihelpers.local"
        ).first()
        
        if not system_user:
            system_user = User(
                email="system@aihelpers.local",
                name="System Migration User",
                hashed_password="",  # No password for system user
                subscription_tier=SubscriptionTier.TEAM,
                is_active=True
            )
            self.db.add(system_user)
            self.db.commit()
            self.db.refresh(system_user)
            logger.info(f"Created system user with ID: {system_user.id}")
        
        return system_user
    
    def _extract_placeholders(self, content: str) -> List[str]:
        """Extract placeholder variables from template content."""
        placeholder_pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(placeholder_pattern, content)
        return [match.strip() for match in matches]
    
    def _categorize_prompt(self, filename: str, content: str) -> PromptCategory:
        """
        Determine the category of a prompt based on filename and content.
        
        Args:
            filename: Name of the prompt file
            content: Content of the prompt
            
        Returns:
            Appropriate PromptCategory
        """
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        # Check filename patterns first
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower):
                    return category
        
        # Check content patterns
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    return category
        
        # Default to GENERAL if no matches
        return PromptCategory.GENERAL
    
    def _generate_tags(self, filename: str, content: str, placeholders: List[str]) -> List[str]:
        """Generate tags for a prompt based on its content and metadata."""
        tags = set()
        
        # Add category-based tags
        category = self._categorize_prompt(filename, content)
        tags.add(category.value)
        
        # Add tags based on placeholders
        common_placeholder_tags = {
            'project': 'project-management',
            'task': 'task-oriented',
            'code': 'code-generation',
            'language': 'programming',
            'framework': 'framework-specific',
            'api': 'api-related',
            'database': 'database',
            'frontend': 'frontend',
            'backend': 'backend',
            'ui': 'user-interface',
            'ux': 'user-experience'
        }
        
        for placeholder in placeholders:
            placeholder_lower = placeholder.lower()
            for key, tag in common_placeholder_tags.items():
                if key in placeholder_lower:
                    tags.add(tag)
        
        # Add template tag
        tags.add('template')
        tags.add('migrated')
        
        return list(tags)[:10]  # Limit to 10 tags
    
    def _parse_template_metadata(self, content: str) -> Dict[str, str]:
        """
        Parse metadata from template content (if any).
        
        Look for metadata in comments or specific formats.
        """
        metadata = {}
        
        # Look for title in first lines or comments
        lines = content.split('\n')
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            line = line.strip()
            
            # Check for title patterns
            title_patterns = [
                r'^#\s*(.+)',  # Markdown heading
                r'^Title:\s*(.+)',  # Explicit title
                r'^/\*\s*(.+?)\s*\*/',  # Comment block
            ]
            
            for pattern in title_patterns:
                match = re.match(pattern, line)
                if match:
                    potential_title = match.group(1).strip()
                    if len(potential_title) > 5 and len(potential_title) < 100:
                        metadata['title'] = potential_title
                        break
            
            if 'title' in metadata:
                break
        
        return metadata
    
    def _scan_prompt_files(self) -> List[Path]:
        """Scan the prompts directory for template files."""
        if not self.prompts_dir.exists():
            logger.error(f"Prompts directory not found: {self.prompts_dir}")
            return []
        
        prompt_files = []
        
        # Find all .md files except meta_prompt.md
        for file_path in self.prompts_dir.rglob("*.md"):
            if file_path.name != "meta_prompt.md":
                prompt_files.append(file_path)
        
        logger.info(f"Found {len(prompt_files)} prompt template files")
        return prompt_files
    
    def migrate_file(self, file_path: Path, system_user: User) -> Optional[Prompt]:
        """
        Migrate a single prompt file to database.
        
        Args:
            file_path: Path to the prompt file
            system_user: System user to own the migrated prompt
            
        Returns:
            Created Prompt instance or None if failed
        """
        try:
            # Read file content
            content = file_path.read_text(encoding='utf-8')
            
            # Skip empty files
            if not content.strip():
                logger.warning(f"Skipping empty file: {file_path}")
                return None
            
            # Extract metadata
            metadata = self._parse_template_metadata(content)
            placeholders = self._extract_placeholders(content)
            category = self._categorize_prompt(file_path.name, content)
            tags = self._generate_tags(file_path.name, content, placeholders)
            
            # Generate title
            title = metadata.get('title')
            if not title:
                # Generate title from filename
                title = file_path.stem.replace('_', ' ').replace('-', ' ').title()
                if title.endswith(' Template'):
                    title = title[:-9]  # Remove ' Template' suffix
            
            # Generate description
            description = f"Migrated from file: {file_path.name}"
            if placeholders:
                description += f"\nPlaceholders: {', '.join(placeholders)}"
            
            # Check if prompt already exists (by title and owner)
            existing = self.db.query(Prompt).filter(
                Prompt.title == title,
                Prompt.owner_id == system_user.id
            ).first()
            
            if existing:
                logger.info(f"Prompt '{title}' already exists, skipping")
                return existing
            
            # Create the prompt
            prompt = self.service.create_prompt(
                title=title,
                content=content,
                owner_id=system_user.id,
                category=category,
                description=description,
                tags=tags,
                is_public=True  # Make migrated prompts public by default
            )
            
            logger.info(f"Migrated: {file_path.name} -> Prompt ID {prompt.id}")
            return prompt
            
        except Exception as e:
            logger.error(f"Failed to migrate {file_path}: {str(e)}")
            return None
    
    def run_migration(self, dry_run: bool = False) -> Dict[str, any]:
        """
        Run the full migration process.
        
        Args:
            dry_run: If True, only analyze files without creating database records
            
        Returns:
            Migration results summary
        """
        logger.info("Starting prompt migration process")
        
        # Get system user
        if not dry_run:
            system_user = self._get_or_create_system_user()
        else:
            system_user = None
        
        # Scan for files
        prompt_files = self._scan_prompt_files()
        
        if not prompt_files:
            logger.warning("No prompt files found to migrate")
            return {
                "total_files": 0,
                "migrated": 0,
                "skipped": 0,
                "errors": 0
            }
        
        # Migration stats
        stats = {
            "total_files": len(prompt_files),
            "migrated": 0,
            "skipped": 0,
            "errors": 0,
            "prompts": []
        }
        
        # Process each file
        for file_path in prompt_files:
            try:
                logger.info(f"Processing: {file_path}")
                
                if dry_run:
                    # Analyze file without creating records
                    content = file_path.read_text(encoding='utf-8')
                    if content.strip():
                        metadata = self._parse_template_metadata(content)
                        placeholders = self._extract_placeholders(content)
                        category = self._categorize_prompt(file_path.name, content)
                        tags = self._generate_tags(file_path.name, content, placeholders)
                        
                        title = metadata.get('title', file_path.stem.replace('_', ' ').title())
                        
                        stats["prompts"].append({
                            "file": str(file_path),
                            "title": title,
                            "category": category.value,
                            "tags": tags,
                            "placeholders": placeholders
                        })
                        stats["migrated"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    # Actually migrate
                    prompt = self.migrate_file(file_path, system_user)
                    if prompt:
                        stats["migrated"] += 1
                        stats["prompts"].append({
                            "file": str(file_path),
                            "prompt_id": prompt.id,
                            "title": prompt.title,
                            "category": prompt.category.value
                        })
                    else:
                        stats["skipped"] += 1
                        
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                stats["errors"] += 1
        
        if not dry_run:
            self.db.commit()
        
        logger.info(f"Migration complete: {stats['migrated']} migrated, "
                   f"{stats['skipped']} skipped, {stats['errors']} errors")
        
        return stats


def migrate_prompts_to_database(
    prompts_directory: str,
    dry_run: bool = False,
    db_session: Optional[Session] = None
) -> Dict[str, any]:
    """
    Main function to migrate file-based prompts to database.
    
    Args:
        prompts_directory: Path to the prompts directory
        dry_run: If True, analyze files without creating database records
        db_session: Optional database session (will create one if not provided)
        
    Returns:
        Migration results summary
    """
    if db_session is None:
        db_session = next(get_db_session())
    
    try:
        migrator = PromptMigrator(db_session, prompts_directory)
        return migrator.run_migration(dry_run)
    finally:
        if db_session:
            db_session.close()


def main():
    """CLI entry point for the migration script."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Migrate file-based prompts to database")
    parser.add_argument(
        "--prompts-dir",
        default="prompts",
        help="Path to prompts directory (default: prompts)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze files without creating database records"
    )
    parser.add_argument(
        "--output",
        help="Save results to JSON file"
    )
    
    args = parser.parse_args()
    
    # Run migration
    results = migrate_prompts_to_database(
        prompts_directory=args.prompts_dir,
        dry_run=args.dry_run
    )
    
    # Print results
    print(f"\nMigration Results:")
    print(f"Total files: {results['total_files']}")
    print(f"Migrated: {results['migrated']}")
    print(f"Skipped: {results['skipped']}")
    print(f"Errors: {results['errors']}")
    
    if args.dry_run:
        print("\nNote: This was a dry run. No database changes were made.")
    
    # Save results to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()