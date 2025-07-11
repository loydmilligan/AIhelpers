"""
Prompt version control service.

Handles versioning, diffs, and history management for prompts.
"""

import difflib
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from ..models.prompt import Prompt, PromptVersion
from ..models.analytics import UserActivity


class PromptVersionService:
    """Service class for prompt version control operations."""
    
    def __init__(self, db_session: Session):
        """Initialize with database session."""
        self.db = db_session
    
    def create_version(
        self,
        prompt_id: int,
        content: str,
        user_id: int,
        change_description: Optional[str] = None
    ) -> Optional[PromptVersion]:
        """
        Create a new version of a prompt.
        
        Args:
            prompt_id: ID of the prompt to version
            content: New content for the version
            user_id: ID of user creating the version
            change_description: Optional description of changes
            
        Returns:
            Created version instance if successful, None if unauthorized
        """
        prompt = self.db.query(Prompt).filter(
            Prompt.id == prompt_id,
            Prompt.owner_id == user_id,  # Only owner can create versions
            Prompt.is_active == True
        ).first()
        
        if not prompt:
            return None
        
        # Check if content is actually different
        if prompt.content == content:
            return None  # No need to create a version for identical content
        
        # Create new version
        new_version_number = prompt.version + 1
        version = PromptVersion(
            prompt_id=prompt_id,
            content=content,
            version_number=new_version_number,
            created_by=user_id
        )
        
        # Update prompt with new version
        prompt.content = content
        prompt.version = new_version_number
        prompt.updated_at = datetime.utcnow()
        
        # Track activity
        activity = UserActivity.create_activity(
            user_id=user_id,
            activity_type="prompt_version_created",
            data={
                "prompt_id": prompt_id,
                "version_number": new_version_number,
                "change_description": change_description
            }
        )
        
        self.db.add_all([version, activity])
        self.db.commit()
        self.db.refresh(version)
        
        return version
    
    def get_version_history(
        self,
        prompt_id: int,
        user_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[PromptVersion], int]:
        """
        Get version history for a prompt.
        
        Args:
            prompt_id: Prompt ID
            user_id: Optional user ID for access control
            limit: Maximum number of versions to return
            offset: Offset for pagination
            
        Returns:
            Tuple of (versions list, total count)
        """
        # Check if user can access this prompt
        prompt = self.db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if not prompt:
            return [], 0
        
        # Access control
        if user_id:
            if not (prompt.owner_id == user_id or prompt.is_public):
                # TODO: Add team access check
                return [], 0
        else:
            if not prompt.is_public:
                return [], 0
        
        # Get versions
        query = self.db.query(PromptVersion).filter(
            PromptVersion.prompt_id == prompt_id
        ).order_by(desc(PromptVersion.version_number))
        
        total_count = query.count()
        versions = query.offset(offset).limit(limit).all()
        
        return versions, total_count
    
    def get_version(
        self,
        prompt_id: int,
        version_number: int,
        user_id: Optional[int] = None
    ) -> Optional[PromptVersion]:
        """
        Get a specific version of a prompt.
        
        Args:
            prompt_id: Prompt ID
            version_number: Version number to retrieve
            user_id: Optional user ID for access control
            
        Returns:
            Version instance if found and accessible, None otherwise
        """
        # Check prompt access first
        prompt = self.db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if not prompt:
            return None
        
        # Access control
        if user_id:
            if not (prompt.owner_id == user_id or prompt.is_public):
                return None
        else:
            if not prompt.is_public:
                return None
        
        # Get the specific version
        version = self.db.query(PromptVersion).filter(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.version_number == version_number
        ).first()
        
        return version
    
    def revert_to_version(
        self,
        prompt_id: int,
        version_number: int,
        user_id: int
    ) -> Optional[Prompt]:
        """
        Revert a prompt to a previous version.
        
        Args:
            prompt_id: Prompt ID
            version_number: Version number to revert to
            user_id: ID of user performing the revert
            
        Returns:
            Updated prompt if successful, None if unauthorized/not found
        """
        # Check if user owns the prompt
        prompt = self.db.query(Prompt).filter(
            Prompt.id == prompt_id,
            Prompt.owner_id == user_id,
            Prompt.is_active == True
        ).first()
        
        if not prompt:
            return None
        
        # Get the target version
        target_version = self.db.query(PromptVersion).filter(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.version_number == version_number
        ).first()
        
        if not target_version:
            return None
        
        # Don't revert to the current version
        if target_version.version_number == prompt.version:
            return prompt
        
        # Create a new version with the reverted content
        new_version_number = prompt.version + 1
        revert_version = PromptVersion(
            prompt_id=prompt_id,
            content=target_version.content,
            version_number=new_version_number,
            created_by=user_id
        )
        
        # Update prompt
        prompt.content = target_version.content
        prompt.version = new_version_number
        prompt.updated_at = datetime.utcnow()
        
        # Track activity
        activity = UserActivity.create_activity(
            user_id=user_id,
            activity_type="prompt_reverted",
            data={
                "prompt_id": prompt_id,
                "reverted_to_version": version_number,
                "new_version": new_version_number
            }
        )
        
        self.db.add_all([revert_version, activity])
        self.db.commit()
        self.db.refresh(prompt)
        
        return prompt
    
    def diff_versions(
        self,
        prompt_id: int,
        version1: int,
        version2: int,
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a diff between two versions of a prompt.
        
        Args:
            prompt_id: Prompt ID
            version1: First version number
            version2: Second version number
            user_id: Optional user ID for access control
            
        Returns:
            Diff data if successful, None if unauthorized/not found
        """
        # Check prompt access
        prompt = self.db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if not prompt:
            return None
        
        # Access control
        if user_id:
            if not (prompt.owner_id == user_id or prompt.is_public):
                return None
        else:
            if not prompt.is_public:
                return None
        
        # Get both versions
        v1 = self.db.query(PromptVersion).filter(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.version_number == version1
        ).first()
        
        v2 = self.db.query(PromptVersion).filter(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.version_number == version2
        ).first()
        
        if not v1 or not v2:
            return None
        
        # Generate diff
        diff_data = self._generate_diff(v1.content, v2.content)
        
        return {
            "prompt_id": prompt_id,
            "version1": {
                "number": version1,
                "created_at": v1.created_at.isoformat(),
                "created_by": v1.created_by
            },
            "version2": {
                "number": version2,
                "created_at": v2.created_at.isoformat(),
                "created_by": v2.created_by
            },
            "diff": diff_data
        }
    
    def get_latest_version(self, prompt_id: int) -> Optional[PromptVersion]:
        """
        Get the latest version of a prompt.
        
        Args:
            prompt_id: Prompt ID
            
        Returns:
            Latest version if found, None otherwise
        """
        return self.db.query(PromptVersion).filter(
            PromptVersion.prompt_id == prompt_id
        ).order_by(desc(PromptVersion.version_number)).first()
    
    def get_version_stats(self, prompt_id: int) -> Dict[str, Any]:
        """
        Get version statistics for a prompt.
        
        Args:
            prompt_id: Prompt ID
            
        Returns:
            Dictionary with version statistics
        """
        versions = self.db.query(PromptVersion).filter(
            PromptVersion.prompt_id == prompt_id
        ).all()
        
        if not versions:
            return {
                "total_versions": 0,
                "contributors": 0,
                "first_version": None,
                "latest_version": None
            }
        
        # Get unique contributors
        contributors = set(v.created_by for v in versions)
        
        # Sort versions by number
        versions.sort(key=lambda v: v.version_number)
        
        return {
            "total_versions": len(versions),
            "contributors": len(contributors),
            "first_version": {
                "number": versions[0].version_number,
                "created_at": versions[0].created_at.isoformat(),
                "created_by": versions[0].created_by
            },
            "latest_version": {
                "number": versions[-1].version_number,
                "created_at": versions[-1].created_at.isoformat(),
                "created_by": versions[-1].created_by
            }
        }
    
    def _generate_diff(self, content1: str, content2: str) -> Dict[str, Any]:
        """
        Generate a detailed diff between two text contents.
        
        Args:
            content1: First content
            content2: Second content
            
        Returns:
            Dictionary with diff data
        """
        lines1 = content1.splitlines(keepends=True)
        lines2 = content2.splitlines(keepends=True)
        
        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            lines1,
            lines2,
            fromfile='Version 1',
            tofile='Version 2',
            lineterm=''
        ))
        
        # Generate HTML diff for better visualization
        html_diff = difflib.HtmlDiff(wrapcolumn=80)
        html_table = html_diff.make_table(
            lines1,
            lines2,
            fromdesc='Version 1',
            todesc='Version 2'
        )
        
        # Calculate basic statistics
        additions = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))
        
        return {
            "unified_diff": ''.join(diff_lines),
            "html_diff": html_table,
            "statistics": {
                "additions": additions,
                "deletions": deletions,
                "changes": additions + deletions
            }
        }


# Convenience functions for direct use
def create_version(
    db: Session,
    prompt_id: int,
    content: str,
    user_id: int,
    change_description: Optional[str] = None
) -> Optional[PromptVersion]:
    """Create a new version using the service."""
    service = PromptVersionService(db)
    return service.create_version(prompt_id, content, user_id, change_description)


def revert_version(
    db: Session,
    prompt_id: int,
    version_number: int,
    user_id: int
) -> Optional[Prompt]:
    """Revert to a version using the service."""
    service = PromptVersionService(db)
    return service.revert_to_version(prompt_id, version_number, user_id)


def diff_versions(
    db: Session,
    prompt_id: int,
    version1: int,
    version2: int,
    user_id: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """Generate diff between versions using the service."""
    service = PromptVersionService(db)
    return service.diff_versions(prompt_id, version1, version2, user_id)