"""Git-synced store management.

Manages the `store/` directory as a git repository for team sync:
- Pull on app startup
- Push only on explicit user action
- Conflict detection and reporting
- Integration with storage layer

Location: .data/store/ (git repo)

Per D20: store/ contains team-shared data (CSV files synced via git).
The Agent auto-maintains a local SQLite cache in .data/cache/ for fast queries.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class GitSyncError(Exception):
    """Raised when git sync operations fail."""

    pass


class SyncStatus(Enum):
    """Git sync status."""

    CLEAN = "clean"
    AHEAD = "ahead"
    BEHIND = "behind"
    DIVERGED = "diverged"
    CONFLICT = "conflict"
    ERROR = "error"


@dataclass
class GitStatus:
    """Git repository status."""

    branch: str
    status: SyncStatus
    ahead: int
    behind: int
    uncommitted: list[str]
    conflicts: list[str]
    last_sync: str | None


class GitSyncManager:
    """Manages git-synced store directory.

    Features:
    - Pull updates from remote on startup
    - Detect conflicts and uncommitted changes
    - Push only on explicit user action
    - Integration with storage layer

    The store/ directory contains:
    - Team-shared CSV files (official baseline)
    - Git-managed, never hand-edited
    - Synced via pull/push operations
    """

    def __init__(self, store_dir: Path | None = None) -> None:
        """Initialize git sync manager.

        Args:
            store_dir: Store directory (default: .data/store/)
        """
        self.store_dir = store_dir or Path(".data/store")
        self._ensure_git_repo()

    def _run_git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        """Run a git command.

        Args:
            *args: Git command arguments
            check: Whether to check return code

        Returns:
            CompletedProcess instance

        Raises:
            GitSyncError: If command fails
        """
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=self.store_dir,
                capture_output=True,
                text=True,
                check=check,
            )
            return result
        except subprocess.CalledProcessError as e:
            raise GitSyncError(f"Git command failed: {e.stderr}") from e

    def _ensure_git_repo(self) -> None:
        """Ensure store_dir is a git repository.

        Creates .git directory if needed.
        """
        self.store_dir.mkdir(parents=True, exist_ok=True)

        git_dir = self.store_dir / ".git"
        if not git_dir.exists():
            # Initialize new repo
            try:
                self._run_git("init")
            except GitSyncError:
                # Git not available, create placeholder
                pass

    def get_status(self) -> GitStatus:
        """Get current git repository status.

        Returns:
            GitStatus instance
        """
        # Get current branch
        try:
            branch_result = self._run_git("rev-parse", "--abbrev-ref", "HEAD")
            branch = branch_result.stdout.strip()
        except GitSyncError:
            branch = "main"

        # Get remote status
        ahead = 0
        behind = 0
        status = SyncStatus.CLEAN

        try:
            # Fetch remote info
            self._run_git("fetch", "--dry-run", check=False)

            # Count ahead/behind
            result = self._run_git("rev-list", "--left-right", "--count", f"{branch}...origin/{branch}", check=False)
            if result.returncode == 0:
                parts = result.stdout.strip().split()
                if len(parts) == 2:
                    ahead = int(parts[0])
                    behind = int(parts[1])

                # Determine status
                if ahead > 0 and behind > 0:
                    status = SyncStatus.DIVERGED
                elif ahead > 0:
                    status = SyncStatus.AHEAD
                elif behind > 0:
                    status = SyncStatus.BEHIND
                else:
                    status = SyncStatus.CLEAN
        except Exception:
            status = SyncStatus.ERROR

        # Get uncommitted changes
        uncommitted = []
        try:
            result = self._run_git("status", "--porcelain")
            for line in result.stdout.strip().split("\n"):
                if line:
                    # Format: XY path
                    uncommitted.append(line[3:])
        except Exception:
            pass

        # Get conflicts
        conflicts = []
        try:
            result = self._run_git("diff", "--name-only", "--diff-filter=U")
            conflicts = [line for line in result.stdout.strip().split("\n") if line]
        except Exception:
            pass

        # Get last sync time
        last_sync = None
        fetch_head = self.store_dir / ".git" / "FETCH_HEAD"
        if fetch_head.exists():
            mtime = fetch_head.stat().st_mtime
            last_sync = datetime.fromtimestamp(mtime).isoformat()

        return GitStatus(
            branch=branch,
            status=status,
            ahead=ahead,
            behind=behind,
            uncommitted=uncommitted,
            conflicts=conflicts,
            last_sync=last_sync,
        )

    def pull(self) -> dict[str, Any]:
        """Pull changes from remote.

        Returns:
            Dict with pull results

        Raises:
            GitSyncError: If pull fails
        """
        result: dict[str, Any] = {
            "success": False,
            "files_updated": [],
            "conflicts": [],
            "message": "",
        }

        try:
            # Check for remote
            remote_result = self._run_git("remote", "get-url", "origin", check=False)
            if remote_result.returncode != 0:
                result["message"] = "No remote configured"
                return result

            # Pull changes
            pull_result = self._run_git("pull", "--ff-only", check=False)

            if pull_result.returncode == 0:
                result["success"] = True
                result["message"] = pull_result.stdout.strip() or "Already up to date"

                # Parse updated files
                for line in pull_result.stdout.split("\n"):
                    if " -> " in line:
                        result["files_updated"].append(line.strip())
            else:
                # Check for conflicts
                status = self.get_status()
                if status.conflicts:
                    result["conflicts"] = status.conflicts
                    result["message"] = "Merge conflicts detected"
                else:
                    result["message"] = pull_result.stderr.strip()

        except Exception as e:
            result["message"] = str(e)

        return result

    def push(self, message: str | None = None) -> dict[str, Any]:
        """Push changes to remote.

        Only pushes on explicit user action, never automatic.

        Args:
            message: Commit message (if changes need committing)

        Returns:
            Dict with push results

        Raises:
            GitSyncError: If push fails
        """
        result: dict[str, Any] = {
            "success": False,
            "files_pushed": [],
            "message": "",
        }

        try:
            # Check for remote
            remote_result = self._run_git("remote", "get-url", "origin", check=False)
            if remote_result.returncode != 0:
                result["message"] = "No remote configured"
                return result

            # Check for uncommitted changes
            status = self.get_status()

            if status.uncommitted:
                # Commit changes first
                if message is None:
                    message = f"Update data: {datetime.utcnow().isoformat()}"

                self._run_git("add", "-A")
                self._run_git("commit", "-m", message)
                result["message"] = f"Committed {len(status.uncommitted)} files"

            # Push changes
            push_result = self._run_git("push", check=False)

            if push_result.returncode == 0:
                result["success"] = True
                result["message"] = push_result.stdout.strip() or "Push successful"
            else:
                result["message"] = push_result.stderr.strip()

        except Exception as e:
            result["message"] = str(e)

        return result

    def add_remote(self, url: str) -> None:
        """Add or update remote URL.

        Args:
            url: Remote repository URL

        Raises:
            GitSyncError: If operation fails
        """
        # Check if remote exists
        result = self._run_git("remote", "get-url", "origin", check=False)

        if result.returncode == 0:
            # Update existing remote
            self._run_git("remote", "set-url", "origin", url)
        else:
            # Add new remote
            self._run_git("remote", "add", "origin", url)

    def clone(self, url: str) -> dict[str, Any]:
        """Clone a remote repository.

        Args:
            url: Remote repository URL

        Returns:
            Dict with clone results

        Raises:
            GitSyncError: If clone fails
        """
        result: dict[str, Any] = {
            "success": False,
            "message": "",
        }

        try:
            # If .git exists, just add remote
            if (self.store_dir / ".git").exists():
                self.add_remote(url)
                result["success"] = True
                result["message"] = "Remote configured"
            else:
                # Clone repository
                clone_result = subprocess.run(
                    ["git", "clone", url, str(self.store_dir)],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if clone_result.returncode == 0:
                    result["success"] = True
                    result["message"] = "Repository cloned"
                else:
                    result["message"] = clone_result.stderr.strip()

        except Exception as e:
            result["message"] = str(e)

        return result

    def get_commit_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent commit history.

        Args:
            limit: Maximum commits to return

        Returns:
            List of commit info dicts
        """
        commits = []

        try:
            result = self._run_git("log", f"-{limit}", "--pretty=format:%H|%an|%ae|%aI|%s")

            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("|", 4)
                    if len(parts) == 5:
                        commits.append({
                            "hash": parts[0],
                            "author": parts[1],
                            "email": parts[2],
                            "date": parts[3],
                            "message": parts[4],
                        })

        except Exception:
            pass

        return commits

    def get_file_history(self, file_path: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get commit history for a specific file.

        Args:
            file_path: Path to file (relative to store/)
            limit: Maximum commits to return

        Returns:
            List of commit info dicts
        """
        commits = []

        try:
            result = self._run_git("log", f"-{limit}", "--pretty=format:%H|%an|%aI|%s", "--", file_path)

            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("|", 3)
                    if len(parts) == 4:
                        commits.append({
                            "hash": parts[0],
                            "author": parts[1],
                            "date": parts[2],
                            "message": parts[3],
                        })

        except Exception:
            pass

        return commits

    def resolve_conflict(self, file_path: str, strategy: str = "ours") -> bool:
        """Resolve a merge conflict.

        Args:
            file_path: Path to conflicted file
            strategy: Resolution strategy (ours, theirs, manual)

        Returns:
            True if conflict resolved
        """
        try:
            if strategy == "ours":
                self._run_git("checkout", "--ours", file_path)
            elif strategy == "theirs":
                self._run_git("checkout", "--theirs", file_path)
            else:
                # Manual resolution - just mark as resolved
                pass

            self._run_git("add", file_path)
            return True

        except Exception:
            return False

    def has_remote(self) -> bool:
        """Check if remote is configured.

        Returns:
            True if remote exists
        """
        result = self._run_git("remote", "get-url", "origin", check=False)
        return result.returncode == 0


# Global git sync manager instance
_git_sync_manager: GitSyncManager | None = None


def get_git_sync_manager() -> GitSyncManager:
    """Get the global git sync manager instance.

    Returns:
        Global GitSyncManager instance
    """
    global _git_sync_manager
    if _git_sync_manager is None:
        _git_sync_manager = GitSyncManager()
    return _git_sync_manager