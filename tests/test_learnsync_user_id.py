"""Tests for user identity management (learn sync).

Tests for:
- User-id generation and validation
- Config persistence
- Machine code fallback
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from axiara.core.learnsync.user_id import (
    UserIdError,
    UserIdInfo,
    UserIdManager,
    get_user_id_manager,
)


class TestUserIdManager:
    """Tests for UserIdManager."""
    
    def test_generate_user_id_format(self) -> None:
        """Test that generated user-id follows correct format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UserIdManager(config_dir=Path(tmpdir))
            user_id = manager.generate_user_id()
            
            # Should match pattern AX-xxxx-yyyy
            assert user_id.startswith("AX-")
            parts = user_id.split("-")
            assert len(parts) == 3
            assert len(parts[1]) == 4
            assert len(parts[2]) == 4
    
    def test_generate_unique_ids(self) -> None:
        """Test that generated IDs are unique."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UserIdManager(config_dir=Path(tmpdir))
            
            ids = set()
            for _ in range(100):
                user_id = manager.generate_user_id()
                ids.add(user_id)
            
            # All should be unique
            assert len(ids) == 100
    
    def test_get_user_id_creates_if_missing(self) -> None:
        """Test that get_user_id creates a new ID if none exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UserIdManager(config_dir=Path(tmpdir))
            
            info = manager.get_user_id()
            
            assert info.user_id.startswith("AX-")
            assert info.source == "generated"
            assert manager.validate_user_id(info.user_id)
    
    def test_get_user_id_returns_existing(self) -> None:
        """Test that get_user_id returns existing ID if present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UserIdManager(config_dir=Path(tmpdir))
            
            # First call creates
            info1 = manager.get_user_id()
            
            # Second call returns same ID
            info2 = manager.get_user_id()
            
            assert info1.user_id == info2.user_id
            assert info2.source == "config"
    
    def test_set_user_id_override(self) -> None:
        """Test that set_user_id can override existing ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UserIdManager(config_dir=Path(tmpdir))
            
            # Create initial ID
            info1 = manager.get_user_id()
            
            # Override
            new_id = "AX-1234-abcd"
            info2 = manager.set_user_id(new_id)
            
            assert info2.user_id == "AX-1234-abcd"
            
            # Next get returns the new ID
            info3 = manager.get_user_id()
            assert info3.user_id == "AX-1234-abcd"
    
    def test_validate_user_id_valid(self) -> None:
        """Test validation of valid user-ids."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UserIdManager(config_dir=Path(tmpdir))
            
            valid_ids = [
                "AX-1234-abcd",
                "AX-ffff-0000",
                "AX-a1b2-c3d4",
            ]
            
            for user_id in valid_ids:
                assert manager.validate_user_id(user_id)
    
    def test_validate_user_id_invalid(self) -> None:
        """Test validation of invalid user-ids."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UserIdManager(config_dir=Path(tmpdir))
            
            invalid_ids = [
                "AX-123-456",  # Too short
                "AX-12345-67890",  # Too long
                "user-1234",  # Wrong prefix
                "",  # Empty
                "AX-1234",  # Missing second part
            ]
            
            for user_id in invalid_ids:
                assert not manager.validate_user_id(user_id)
    
    def test_sanitize_id(self) -> None:
        """Test ID sanitization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UserIdManager(config_dir=Path(tmpdir))
            
            # Invalid characters should be replaced
            assert manager._sanitize_id("test@user!") == "test-user"
            # Underscores are valid characters, should be preserved
            assert manager._sanitize_id("user___name") == "user___name"
            assert manager._sanitize_id("") == "AX-unknown"
    
    def test_config_persistence(self) -> None:
        """Test that config is persisted correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            
            # Create manager and generate ID
            manager1 = UserIdManager(config_dir=config_dir)
            info1 = manager1.get_user_id()
            
            # Create new manager instance with same config_dir
            manager2 = UserIdManager(config_dir=config_dir)
            info2 = manager2.get_user_id()
            
            # Should return same ID from persisted config
            assert info1.user_id == info2.user_id
    
    def test_get_machine_code(self) -> None:
        """Test machine code generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UserIdManager(config_dir=Path(tmpdir))
            
            machine_code = manager.get_machine_code()
            
            # Should be sanitized
            assert "-" not in machine_code or machine_code.replace("-", "").isalnum() or machine_code.startswith("MC-")
            assert len(machine_code) > 0


class TestGetUserIdManager:
    """Tests for global manager."""
    
    def test_returns_same_instance(self) -> None:
        """Test that get_user_id_manager returns same instance."""
        manager1 = get_user_id_manager()
        manager2 = get_user_id_manager()
        
        assert manager1 is manager2