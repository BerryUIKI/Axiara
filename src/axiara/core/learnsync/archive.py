"""Inactive branch archiving for learn sync (D-SK11).

Implements branch lifecycle management:
- Detect inactive user branches (idle > 180 days)
- Admin confirmation gate
- Archive merge into archive/ branch
- Delete user branch
- Ledger recording
- Optional reactivation with seed from archive
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ArchiveCandidate:
    """A candidate for archiving."""
    
    user_id: str
    branch: str
    last_commit_date: datetime
    days_inactive: int
    commit_count: int
    reason: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "branch": self.branch,
            "last_commit_date": self.last_commit_date.isoformat(),
            "days_inactive": self.days_inactive,
            "commit_count": self.commit_count,
            "reason": self.reason,
        }


@dataclass
class ArchiveResult:
    """Result of an archive operation."""
    
    success: bool
    user_id: str
    source_branch: str
    archive_branch: str
    archive_path: str
    commit_hash: str | None = None
    message: str = ""
    error: str | None = None


class ArchiveManager:
    """Manages inactive branch archiving.
    
    Per learn-sync-text.md §3.5:
    - Feature gate: OFF by default
    - Detect branches idle > 180 days (configurable)
    - Admin confirmation required
    - Merge into archive/ branch
    - Delete user branch
    - Ledger entry for audit
    
    Branch naming:
    - Source: user/<user-id>
    - Archive: archive/<user-id>/<yyyymmdd>/
    """
    
    def __init__(
        self,
        store_dir: Path | None = None,
        idle_threshold_days: int = 180,
        enabled: bool = False,
    ) -> None:
        """Initialize archive manager.
        
        Args:
            store_dir: Store directory (default: .data/store/)
            idle_threshold_days: Days before branch is considered inactive
            enabled: Whether archiving is enabled (default: False)
        """
        self.store_dir = store_dir or Path(".data/store")
        self.idle_threshold_days = idle_threshold_days
        self.enabled = enabled
    
    def detect_inactive_branches(self) -> list[ArchiveCandidate]:
        """Detect user branches that are candidates for archiving.
        
        Returns:
            List of ArchiveCandidate instances
        """
        if not self.enabled:
            return []
        
        candidates: list[ArchiveCandidate] = []
        threshold_date = datetime.now(timezone.utc) - timedelta(days=self.idle_threshold_days)
        
        # Get list of user branches
        user_branches = self._list_user_branches()
        
        for branch in user_branches:
            # Get last commit date
            last_commit_date = self._get_last_commit_date(branch)
            
            if last_commit_date and last_commit_date < threshold_date:
                # Calculate days inactive
                days_inactive = (datetime.now(timezone.utc) - last_commit_date).days
                
                # Get commit count
                commit_count = self._get_commit_count(branch)
                
                # Extract user ID from branch name
                user_id = branch.replace("user/", "")
                
                candidate = ArchiveCandidate(
                    user_id=user_id,
                    branch=branch,
                    last_commit_date=last_commit_date,
                    days_inactive=days_inactive,
                    commit_count=commit_count,
                    reason=f"Branch inactive for {days_inactive} days (threshold: {self.idle_threshold_days})",
                )
                
                candidates.append(candidate)
        
        return candidates
    
    def _list_user_branches(self) -> list[str]:
        """List all user/* branches.
        
        Returns:
            List of branch names
        """
        try:
            result = subprocess.run(
                ["git", "branch", "--list", "user/*"],
                cwd=self.store_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            
            branches = []
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line.startswith("* "):
                    line = line[2:]
                if line and line.startswith("user/"):
                    branches.append(line)
            
            return branches
        
        except Exception:
            return []
    
    def _get_last_commit_date(self, branch: str) -> datetime | None:
        """Get the last commit date for a branch.
        
        Args:
            branch: Branch name
            
        Returns:
            Last commit datetime or None
        """
        try:
            result = subprocess.run(
                ["git", "log", branch, "-1", "--format=%aI"],
                cwd=self.store_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Parse ISO format timestamp
                date_str = result.stdout.strip()
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        
        except Exception:
            pass
        
        return None
    
    def _get_commit_count(self, branch: str) -> int:
        """Get the number of commits in a branch.
        
        Args:
            branch: Branch name
            
        Returns:
            Commit count
        """
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", branch],
                cwd=self.store_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            
            if result.returncode == 0:
                return int(result.stdout.strip())
        
        except Exception:
            pass
        
        return 0
    
    def archive_branch(
        self,
        candidate: ArchiveCandidate,
        admin_id: str,
        force: bool = False,
    ) -> ArchiveResult:
        """Archive a user branch after confirmation.
        
        Args:
            candidate: Archive candidate
            admin_id: ID of admin performing archive
            force: Force archive even if disabled
            
        Returns:
            ArchiveResult with status
        """
        if not self.enabled and not force:
            return ArchiveResult(
                success=False,
                user_id=candidate.user_id,
                source_branch=candidate.branch,
                archive_branch="",
                archive_path="",
                message="Archiving is disabled",
            )
        
        try:
            # Create archive path
            archive_date = datetime.now(timezone.utc).strftime("%Y%m%d")
            archive_branch = "archive"
            archive_path = f"archive/{candidate.user_id}/{archive_date}"
            
            # Ensure archive branch exists
            self._ensure_branch(archive_branch)
            
            # Checkout archive branch
            subprocess.run(
                ["git", "checkout", archive_branch],
                cwd=self.store_dir,
                capture_output=True,
                check=True,
            )
            
            # Copy user inbox to archive location
            source_inbox = f"learn_inbox/{candidate.user_id}"
            
            # Create archive directory
            archive_dir = self.store_dir / archive_path
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy files
            source_dir = self.store_dir / source_inbox
            if source_dir.exists():
                import shutil
                for item in source_dir.iterdir():
                    if item.is_dir():
                        dest = archive_dir / item.name
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(item, dest)
            
            # Commit
            commit_message = f"archive {candidate.user_id} - inactive {candidate.days_inactive} days - admin: {admin_id}"
            
            subprocess.run(
                ["git", "add", "-A"],
                cwd=self.store_dir,
                capture_output=True,
                check=True,
            )
            
            subprocess.run(
                ["git", "commit", "-m", commit_message],
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
            
            # Delete user branch
            subprocess.run(
                ["git", "branch", "-D", candidate.branch],
                cwd=self.store_dir,
                capture_output=True,
                check=True,
            )
            
            # Record in ledger
            self._record_archive_ledger(
                candidate=candidate,
                archive_path=archive_path,
                commit_hash=commit_hash,
                admin_id=admin_id,
            )
            
            return ArchiveResult(
                success=True,
                user_id=candidate.user_id,
                source_branch=candidate.branch,
                archive_branch=archive_branch,
                archive_path=archive_path,
                commit_hash=commit_hash,
                message=f"Archived {candidate.branch} to {archive_path}",
            )
        
        except Exception as e:
            return ArchiveResult(
                success=False,
                user_id=candidate.user_id,
                source_branch=candidate.branch,
                archive_branch="archive",
                archive_path="",
                error=str(e),
                message="Archive failed",
            )
    
    def _ensure_branch(self, branch: str) -> None:
        """Ensure a branch exists.
        
        Args:
            branch: Branch name
        """
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
    
    def _record_archive_ledger(
        self,
        candidate: ArchiveCandidate,
        archive_path: str,
        commit_hash: str,
        admin_id: str,
    ) -> None:
        """Record archive operation in ledger.
        
        Args:
            candidate: Archive candidate
            archive_path: Path in archive
            commit_hash: Commit hash
            admin_id: Admin who approved
        """
        ledger_dir = self.store_dir / ".ledger"
        ledger_dir.mkdir(parents=True, exist_ok=True)
        
        ledger_file = ledger_dir / "archive-log.yaml"
        
        # Load existing entries
        entries: list[dict[str, Any]] = []
        if ledger_file.exists():
            try:
                content = ledger_file.read_text(encoding="utf-8")
                data = yaml.safe_load(content) or {}
                entries = data.get("entries", [])
            except Exception:
                pass
        
        # Add new entry
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "archive_branch",
            "user_id": candidate.user_id,
            "source_branch": candidate.branch,
            "archive_path": archive_path,
            "commit_hash": commit_hash,
            "days_inactive": candidate.days_inactive,
            "admin_id": admin_id,
            "reason": candidate.reason,
        }
        
        entries.append(entry)
        
        # Save
        data = {
            "version": "1.0",
            "entries": entries,
        }
        
        content = yaml.dump(data, default_flow_style=False, sort_keys=False)
        ledger_file.write_text(content, encoding="utf-8")
    
    def reactivate_user(
        self,
        user_id: str,
        seed_from_archive: bool = False,
    ) -> dict[str, Any]:
        """Recreate a user branch after archiving.
        
        Args:
            user_id: User ID to reactivate
            seed_from_archive: Whether to seed from archive
            
        Returns:
            Dict with reactivation result
        """
        branch = f"user/{user_id}"
        
        # Check if branch already exists
        existing = subprocess.run(
            ["git", "branch", "--list", branch],
            cwd=self.store_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        
        if branch in existing.stdout:
            return {
                "success": False,
                "message": f"Branch {branch} already exists",
            }
        
        try:
            # Create new branch
            subprocess.run(
                ["git", "checkout", "-b", branch],
                cwd=self.store_dir,
                capture_output=True,
                check=True,
            )
            
            result = {
                "success": True,
                "user_id": user_id,
                "branch": branch,
                "seeded": False,
                "message": f"Created new branch {branch}",
            }
            
            # Optionally seed from archive
            if seed_from_archive:
                archive_dir = self.store_dir / "archive" / user_id
                if archive_dir.exists():
                    # Find latest archive
                    latest_archive = max(
                        archive_dir.iterdir(),
                        key=lambda d: d.name,
                    )
                    
                    if latest_archive:
                        # Copy to learn_inbox
                        import shutil
                        dest_inbox = self.store_dir / "learn_inbox" / user_id
                        if dest_inbox.exists():
                            shutil.rmtree(dest_inbox)
                        
                        shutil.copytree(latest_archive, dest_inbox)
                        
                        # Commit
                        subprocess.run(
                            ["git", "add", "-A"],
                            cwd=self.store_dir,
                            capture_output=True,
                            check=True,
                        )
                        
                        subprocess.run(
                            ["git", "commit", "-m", f"reactivate {user_id} - seeded from archive {latest_archive.name}"],
                            cwd=self.store_dir,
                            capture_output=True,
                            check=True,
                        )
                        
                        result["seeded"] = True
                        result["seed_source"] = latest_archive.name
                        result["message"] = f"Created and seeded {branch} from archive"
            
            return result
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Reactivation failed",
            }
    
    def get_archive_summary(self) -> dict[str, Any]:
        """Get summary of archived branches.
        
        Returns:
            Dict with archive summary
        """
        archive_dir = self.store_dir / "archive"
        
        if not archive_dir.exists():
            return {
                "total_archived": 0,
                "users": [],
            }
        
        users: list[dict[str, Any]] = []
        
        for user_dir in archive_dir.iterdir():
            if user_dir.is_dir():
                archive_dates = []
                
                for date_dir in user_dir.iterdir():
                    if date_dir.is_dir():
                        archive_dates.append({
                            "date": date_dir.name,
                            "file_count": len(list(date_dir.rglob("*"))),
                        })
                
                users.append({
                    "user_id": user_dir.name,
                    "archive_count": len(archive_dates),
                    "archives": archive_dates,
                })
        
        return {
            "total_archived": len(users),
            "users": users,
        }