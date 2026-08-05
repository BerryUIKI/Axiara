"""Tests for upload management (learn sync).

Tests for:
- Bundle preparation
- Upload confirmation
- Re-upload handling
- Git operations
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from axiara.core.learnsync.upload import (
    UploadManager,
    UploadResult,
    UploadStatus,
)


class TestUploadManager:
    """Tests for UploadManager."""
    
    def test_prepare_upload_empty(self) -> None:
        """Test preparing upload with no private data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            learn_dir = Path(tmpdir) / "learn"
            
            manager = UploadManager(store_dir=store_dir, learn_dir=learn_dir)
            
            bundle, user_id, bundle_path = manager.prepare_upload()
            
            assert user_id.startswith("AX-")
            assert "learn_inbox" in bundle_path
            assert bundle.metadata.user_id == user_id
            assert len(bundle.rules) == 0
    
    def test_prepare_upload_summary(self) -> None:
        """Test getting upload summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            learn_dir = Path(tmpdir) / "learn"
            
            manager = UploadManager(store_dir=store_dir, learn_dir=learn_dir)
            
            bundle, user_id, _ = manager.prepare_upload()
            
            summary = manager.get_upload_summary(bundle)
            
            assert summary["user_id"] == user_id
            assert "total_rules" in summary
            assert "kinds" in summary
    
    def test_confirm_upload_creates_bundle_file(self) -> None:
        """Test that confirm_upload creates bundle file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            learn_dir = Path(tmpdir) / "learn"
            
            manager = UploadManager(store_dir=store_dir, learn_dir=learn_dir)
            
            # Prepare
            bundle, user_id, bundle_path = manager.prepare_upload()
            
            # Mock git operations
            with patch.object(manager, "_ensure_branch"), \
                 patch.object(manager, "_commit_and_push", return_value="abc123"):
                
                result = manager.confirm_upload(
                    bundle=bundle,
                    user_id=user_id,
                    bundle_path=bundle_path,
                )
            
            assert result.status == UploadStatus.SUCCESS
            assert result.commit_hash == "abc123"
            
            # Check bundle file exists
            full_bundle_path = store_dir / bundle_path
            assert full_bundle_path.exists()
    
    def test_list_user_uploads_empty(self) -> None:
        """Test listing uploads when none exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            learn_dir = Path(tmpdir) / "learn"
            
            manager = UploadManager(store_dir=store_dir, learn_dir=learn_dir)
            
            uploads = manager.list_user_uploads("AX-test-1234")
            
            assert uploads == []
    
    def test_list_user_uploads_with_bundles(self) -> None:
        """Test listing existing uploads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            learn_dir = Path(tmpdir) / "learn"
            
            manager = UploadManager(store_dir=store_dir, learn_dir=learn_dir)
            
            # Create a bundle file manually
            inbox_dir = store_dir / "learn_inbox" / "AX-test-1234" / "20260805"
            inbox_dir.mkdir(parents=True)
            
            bundle_file = inbox_dir / "bundle.yaml"
            bundle_file.write_text("metadata:\n  user_id: AX-test-1234\n")
            
            uploads = manager.list_user_uploads("AX-test-1234")
            
            assert len(uploads) == 1
            assert uploads[0]["date"] == "20260805"
    
    def test_flag_stale_uploads(self) -> None:
        """Test flagging previous uploads as stale."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            learn_dir = Path(tmpdir) / "learn"
            
            manager = UploadManager(store_dir=store_dir, learn_dir=learn_dir)
            
            # Create old upload
            old_inbox = store_dir / "learn_inbox" / "AX-test-1234" / "20260801"
            old_inbox.mkdir(parents=True)
            (old_inbox / "bundle.yaml").write_text("metadata:\n  user_id: AX-test-1234\n")
            
            # Flag stale
            flagged = manager.flag_stale_uploads("AX-test-1234", "20260805")
            
            assert len(flagged) == 1
            
            # Check stale marker exists
            assert (old_inbox / ".stale").exists()


class TestUploadResult:
    """Tests for UploadResult."""
    
    def test_success_result(self) -> None:
        """Test creating success result."""
        result = UploadResult(
            status=UploadStatus.SUCCESS,
            user_id="AX-test-1234",
            bundle_path="learn_inbox/AX-test-1234/20260805/bundle.yaml",
            branch="user/AX-test-1234",
            commit_hash="abc123",
            message="Upload successful",
        )
        
        assert result.status == UploadStatus.SUCCESS
        assert result.error is None
    
    def test_error_result(self) -> None:
        """Test creating error result."""
        result = UploadResult(
            status=UploadStatus.ERROR,
            user_id="AX-test-1234",
            bundle_path="",
            branch="user/AX-test-1234",
            error="Git operation failed",
        )
        
        assert result.status == UploadStatus.ERROR
        assert result.error == "Git operation failed"