"""Upload management for learn sync.

Handles the upload flow:
- Export bundle → confirm → push to user/<user-id> branch
- Re-upload handling (new dated dir, flag previous stale)
- Git operations on data repo
- CLI confirmation gate
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from axiara.core.learnsync.bundle import Bundle, BundleExporter
from axiara.core.learnsync.user_id import UserIdManager


class UploadStatus(Enum):
    """Status of an upload operation."""
    
    SUCCESS = "success"
    REJECTED = "rejected"  # User rejected confirmation
    ERROR = "error"
    CONFLICT = "conflict"


@dataclass
class UploadResult:
    """Result of an upload operation."""
    
    status: UploadStatus
    user_id: str
    bundle_path: str
    branch: str
    commit_hash: str | None = None
    timestamp: datetime | None = None
    message: str = ""
    error: str | None = None


class UploadManager:
    """Manages upload flow for learn sync.
    
    Per learn-sync-text.md §3:
    - Export learn_private → bundle.yaml
    - User confirmation required
    - Push to user/<user-id> branch
    - Re-upload creates new dated dir
    """
    
    def __init__(
        self,
        store_dir: Path | None = None,
        learn_dir: Path | None = None,
    ) -> None:
        """Initialize upload manager.
        
        Args:
            store_dir: Store directory (default: .data/store/)
            learn_dir: Learning data directory (default: data/learn/)
        """
        self.store_dir = store_dir or Path(".data/store")
        self.learn_dir = learn_dir or Path("data/learn")
        
        self.exporter = BundleExporter(learn_dir=self.learn_dir)
        self.user_id_manager = UserIdManager()
    
    def prepare_upload(
        self,
        exclude_customer_specific: bool = True,
    ) -> tuple[Bundle, str, str]:
        """Prepare an upload bundle for confirmation.
        
        Does NOT push - just prepares and returns info for user review.
        
        Args:
            exclude_customer_specific: Whether to exclude customer-specific entries
            
        Returns:
            Tuple of (Bundle, user_id, bundle_path)
        """
        # Get user ID
        user_id_info = self.user_id_manager.get_user_id()
        user_id = user_id_info.user_id
        
        # Get last upload time
        previous_upload = self.exporter.get_last_upload_time(user_id)
        
        # Export bundle
        bundle = self.exporter.export_bundle(
            user_id=user_id,
            exclude_customer_specific=exclude_customer_specific,
            previous_upload=previous_upload,
        )
        
        # Determine bundle path
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        bundle_filename = "bundle.yaml"
        bundle_path = f"learn_inbox/{user_id}/{date_str}/{bundle_filename}"
        
        return bundle, user_id, bundle_path
    
    def confirm_upload(
        self,
        bundle: Bundle,
        user_id: str,
        bundle_path: str,
        is_reupload: bool = False,
    ) -> UploadResult:
        """Execute upload after user confirmation.
        
        Args:
            bundle: Bundle to upload
            user_id: User ID
            bundle_path: Relative path in store
            is_reupload: Whether this is a re-upload
            
        Returns:
            UploadResult with status
        """
        try:
            # Ensure store directory exists
            self.store_dir.mkdir(parents=True, exist_ok=True)
            
            # Write bundle to store
            full_bundle_path = self.store_dir / bundle_path
            self.exporter.save_bundle(bundle, full_bundle_path)
            
            # Git operations
            branch = f"user/{user_id}"
            
            # Check/create branch
            self._ensure_branch(branch)
            
            # Add and commit
            commit_message = f"upload {user_id} {datetime.now(timezone.utc).strftime('%Y%m%d')}"
            if is_reupload:
                commit_message += " [re-upload]"
            
            commit_hash = self._commit_and_push(
                bundle_path,
                commit_message,
                branch,
            )
            
            # Record upload
            self.exporter.record_upload(
                user_id=user_id,
                timestamp=datetime.now(timezone.utc),
                bundle_path=bundle_path,
            )
            
            return UploadResult(
                status=UploadStatus.SUCCESS,
                user_id=user_id,
                bundle_path=bundle_path,
                branch=branch,
                commit_hash=commit_hash,
                timestamp=datetime.now(timezone.utc),
                message="Upload successful",
            )
        
        except Exception as e:
            return UploadResult(
                status=UploadStatus.ERROR,
                user_id=user_id,
                bundle_path=bundle_path,
                branch=f"user/{user_id}",
                error=str(e),
                message="Upload failed",
            )
    
    def _ensure_branch(self, branch: str) -> None:
        """Ensure a branch exists in the data repo.
        
        Args:
            branch: Branch name (e.g., user/AX-abcd-1234)
        """
        # Check if branch exists
        result = subprocess.run(
            ["git", "branch", "--list", branch],
            cwd=self.store_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        
        if branch not in result.stdout:
            # Create branch
            subprocess.run(
                ["git", "checkout", "-b", branch],
                cwd=self.store_dir,
                capture_output=True,
                check=True,
            )
        else:
            # Switch to branch
            subprocess.run(
                ["git", "checkout", branch],
                cwd=self.store_dir,
                capture_output=True,
                check=True,
            )
    
    def _commit_and_push(
        self,
        bundle_path: str,
        message: str,
        branch: str,
    ) -> str:
        """Commit and push bundle to remote.
        
        Args:
            bundle_path: Relative path to bundle
            message: Commit message
            branch: Branch name
            
        Returns:
            Commit hash
        """
        # Add file
        subprocess.run(
            ["git", "add", bundle_path],
            cwd=self.store_dir,
            capture_output=True,
            check=True,
        )
        
        # Commit
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.store_dir,
            capture_output=True,
            check=True,
        )
        
        # Get commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.store_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        commit_hash = result.stdout.strip()
        
        # Push (check if remote exists first)
        remote_result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=self.store_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        
        if remote_result.returncode == 0:
            # Remote exists, push
            subprocess.run(
                ["git", "push", "-u", "origin", branch],
                cwd=self.store_dir,
                capture_output=True,
                check=False,
            )
        
        return commit_hash
    
    def get_upload_summary(self, bundle: Bundle) -> dict[str, Any]:
        """Get a human-readable summary of upload for confirmation.
        
        Args:
            bundle: Bundle to summarize
            
        Returns:
            Dict with summary info
        """
        # Group rules by kind
        kind_counts: dict[str, int] = {}
        for rule in bundle.rules:
            kind_counts[rule.kind] = kind_counts.get(rule.kind, 0) + 1
        
        return {
            "user_id": bundle.metadata.user_id,
            "total_rules": bundle.metadata.rule_count,
            "total_observations": bundle.metadata.observation_count,
            "excluded_rules": bundle.metadata.excluded_count,
            "scope": bundle.metadata.scope,
            "kinds": kind_counts,
            "created_at": bundle.metadata.created_at.isoformat(),
            "previous_upload": (
                bundle.metadata.previous_upload.isoformat()
                if bundle.metadata.previous_upload
                else None
            ),
        }
    
    def list_user_uploads(self, user_id: str) -> list[dict[str, Any]]:
        """List all uploads for a user.
        
        Args:
            user_id: User ID to list uploads for
            
        Returns:
            List of upload info dicts
        """
        uploads: list[dict[str, Any]] = []
        inbox_dir = self.store_dir / "learn_inbox" / user_id
        
        if not inbox_dir.exists():
            return uploads
        
        for date_dir in sorted(inbox_dir.iterdir()):
            if date_dir.is_dir():
                bundle_file = date_dir / "bundle.yaml"
                if bundle_file.exists():
                    uploads.append({
                        "user_id": user_id,
                        "date": date_dir.name,
                        "path": str(bundle_file.relative_to(self.store_dir)),
                        "exists": True,
                    })
        
        return uploads
    
    def flag_stale_uploads(self, user_id: str, current_date: str) -> list[str]:
        """Flag previous pending uploads as stale.
        
        Called during re-upload to mark earlier pending uploads.
        
        Args:
            user_id: User ID
            current_date: Current upload date (YYYYMMDD)
            
        Returns:
            List of flagged paths
        """
        flagged: list[str] = []
        inbox_dir = self.store_dir / "learn_inbox" / user_id
        
        if not inbox_dir.exists():
            return flagged
        
        for date_dir in inbox_dir.iterdir():
            if date_dir.is_dir() and date_dir.name != current_date:
                # Create stale marker
                stale_marker = date_dir / ".stale"
                stale_marker.touch()
                flagged.append(str(date_dir.relative_to(self.store_dir)))
        
        return flagged