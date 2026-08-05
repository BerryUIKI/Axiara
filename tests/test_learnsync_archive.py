"""Tests for branch archiving (learn sync).

Tests for:
- Inactive branch detection
- Archive operations
- Reactivation
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from axiara.core.learnsync.archive import (
    ArchiveCandidate,
    ArchiveManager,
    ArchiveResult,
)


class TestArchiveManager:
    """Tests for ArchiveManager."""
    
    def test_detect_inactive_branches_disabled(self) -> None:
        """Test that detection returns empty when disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            manager = ArchiveManager(
                store_dir=store_dir,
                enabled=False,  # Disabled
            )
            
            candidates = manager.detect_inactive_branches()
            
            assert candidates == []
    
    def test_detect_inactive_branches_none(self) -> None:
        """Test detection when no branches exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            manager = ArchiveManager(
                store_dir=store_dir,
                enabled=True,
            )
            
            # Mock empty branch list
            with patch.object(manager, "_list_user_branches", return_value=[]):
                candidates = manager.detect_inactive_branches()
            
            assert candidates == []
    
    def test_detect_inactive_branches_with_old(self) -> None:
        """Test detecting branches older than threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            manager = ArchiveManager(
                store_dir=store_dir,
                idle_threshold_days=180,
                enabled=True,
            )
            
            # Mock old branch
            old_date = datetime.utcnow() - timedelta(days=200)
            
            with patch.object(manager, "_list_user_branches", return_value=["user/AX-old-1234"]), \
                 patch.object(manager, "_get_last_commit_date", return_value=old_date), \
                 patch.object(manager, "_get_commit_count", return_value=5):
                
                candidates = manager.detect_inactive_branches()
            
            assert len(candidates) == 1
            assert candidates[0].user_id == "AX-old-1234"
            assert candidates[0].days_inactive >= 180
    
    def test_detect_inactive_branches_skip_recent(self) -> None:
        """Test that recent branches are not detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            manager = ArchiveManager(
                store_dir=store_dir,
                idle_threshold_days=180,
                enabled=True,
            )
            
            # Mock recent branch
            recent_date = datetime.utcnow() - timedelta(days=30)
            
            with patch.object(manager, "_list_user_branches", return_value=["user/AX-new-1234"]), \
                 patch.object(manager, "_get_last_commit_date", return_value=recent_date), \
                 patch.object(manager, "_get_commit_count", return_value=3):
                
                candidates = manager.detect_inactive_branches()
            
            # Should be empty (branch is recent)
            assert candidates == []
    
    def test_archive_branch_disabled(self) -> None:
        """Test that archive fails when disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            manager = ArchiveManager(
                store_dir=store_dir,
                enabled=False,
            )
            
            candidate = ArchiveCandidate(
                user_id="AX-test-1234",
                branch="user/AX-test-1234",
                last_commit_date=datetime.utcnow(),
                days_inactive=200,
                commit_count=5,
            )
            
            result = manager.archive_branch(candidate, "admin-001")
            
            assert not result.success
            assert "disabled" in result.message.lower()
    
    def test_archive_branch_creates_archive(self) -> None:
        """Test that archive operation creates archive directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            manager = ArchiveManager(
                store_dir=store_dir,
                enabled=True,
            )
            
            candidate = ArchiveCandidate(
                user_id="AX-test-1234",
                branch="user/AX-test-1234",
                last_commit_date=datetime.utcnow() - timedelta(days=200),
                days_inactive=200,
                commit_count=5,
            )
            
            # Create source inbox
            inbox_dir = store_dir / "learn_inbox" / "AX-test-1234" / "20260101"
            inbox_dir.mkdir(parents=True)
            (inbox_dir / "bundle.yaml").write_text("test: data")
            
            # Mock git operations
            with patch.object(manager, "_ensure_branch"), \
                 patch("subprocess.run") as mock_run:
                
                # Setup mock for git commands
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="abc123",
                    stderr="",
                )
                
                result = manager.archive_branch(candidate, "admin-001", force=True)
            
            assert result.success
            assert "archive/AX-test-1234" in result.archive_path
    
    def test_get_archive_summary_empty(self) -> None:
        """Test getting summary when no archives."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            manager = ArchiveManager(store_dir=store_dir)
            
            summary = manager.get_archive_summary()
            
            assert summary["total_archived"] == 0
            assert summary["users"] == []
    
    def test_get_archive_summary_with_archives(self) -> None:
        """Test getting summary with archived branches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            # Create archive directory
            archive_dir = store_dir / "archive" / "AX-test-1234" / "20260805"
            archive_dir.mkdir(parents=True)
            (archive_dir / "bundle.yaml").write_text("test: data")
            
            manager = ArchiveManager(store_dir=store_dir)
            
            summary = manager.get_archive_summary()
            
            assert summary["total_archived"] == 1
            assert len(summary["users"]) == 1
            assert summary["users"][0]["user_id"] == "AX-test-1234"
    
    def test_reactivate_user_creates_branch(self) -> None:
        """Test reactivating a user creates new branch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            manager = ArchiveManager(store_dir=store_dir)
            
            # Mock git operations
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="",
                    stderr="",
                )
                
                result = manager.reactivate_user("AX-test-1234")
            
            assert result["success"]
            assert result["user_id"] == "AX-test-1234"
            assert result["branch"] == "user/AX-test-1234"
    
    def test_reactivate_user_seed_from_archive(self) -> None:
        """Test reactivating with seed from archive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            # Create archive
            archive_dir = store_dir / "archive" / "AX-test-1234" / "20260805"
            archive_dir.mkdir(parents=True)
            bundle_data = {"metadata": {"user_id": "AX-test-1234"}}
            (archive_dir / "bundle.yaml").write_text(yaml.dump(bundle_data))
            
            manager = ArchiveManager(store_dir=store_dir)
            
            # Mock git operations
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="",
                    stderr="",
                )
                
                result = manager.reactivate_user("AX-test-1234", seed_from_archive=True)
            
            assert result["success"]
            assert result["seeded"]


class TestArchiveCandidate:
    """Tests for ArchiveCandidate."""
    
    def test_creation(self) -> None:
        """Test creating archive candidate."""
        candidate = ArchiveCandidate(
            user_id="AX-test-1234",
            branch="user/AX-test-1234",
            last_commit_date=datetime(2026, 1, 1),
            days_inactive=200,
            commit_count=10,
            reason="Branch inactive for 200 days",
        )
        
        assert candidate.user_id == "AX-test-1234"
        assert candidate.days_inactive == 200
    
    def test_to_dict(self) -> None:
        """Test converting to dict."""
        candidate = ArchiveCandidate(
            user_id="AX-test-1234",
            branch="user/AX-test-1234",
            last_commit_date=datetime(2026, 1, 1),
            days_inactive=200,
            commit_count=10,
        )
        
        data = candidate.to_dict()
        
        assert data["user_id"] == "AX-test-1234"
        assert data["days_inactive"] == 200
        assert "last_commit_date" in data


class TestArchiveResult:
    """Tests for ArchiveResult."""
    
    def test_success_result(self) -> None:
        """Test successful archive result."""
        result = ArchiveResult(
            success=True,
            user_id="AX-test-1234",
            source_branch="user/AX-test-1234",
            archive_branch="archive",
            archive_path="archive/AX-test-1234/20260805",
            commit_hash="abc123",
            message="Archived successfully",
        )
        
        assert result.success
        assert result.error is None
    
    def test_failure_result(self) -> None:
        """Test failed archive result."""
        result = ArchiveResult(
            success=False,
            user_id="AX-test-1234",
            source_branch="user/AX-test-1234",
            archive_branch="",
            archive_path="",
            error="Git operation failed",
        )
        
        assert not result.success
        assert result.error == "Git operation failed"