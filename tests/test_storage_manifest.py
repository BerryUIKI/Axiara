"""Tests for manifest management functionality."""

import json
from pathlib import Path

import pytest

from axiara.core.storage import DataLayer
from axiara.core.storage.manifest import ManifestEntry, ManifestManager


def test_manifest_manager_init(tmp_path: Path) -> None:
    """Test manifest manager initialization."""
    manager = ManifestManager(manifest_dir=tmp_path)
    assert manager is not None
    assert manager.manifest_path.exists()


def test_manifest_entry_creation() -> None:
    """Test creating a manifest entry."""
    entry = ManifestEntry(
        file_path=Path("data/main/test.csv"),
        checksum="abc123",
        size=100,
        mtime="2026-08-05T10:00:00",
        layer="main",
        recorded_at="2026-08-05T10:00:00",
    )

    assert entry.file_path == Path("data/main/test.csv")
    assert entry.checksum == "abc123"

    # Test serialization
    entry_dict = entry.to_dict()
    assert entry_dict["checksum"] == "abc123"

    # Test deserialization
    entry2 = ManifestEntry.from_dict(entry_dict)
    assert entry2.checksum == entry.checksum


def test_record_file(tmp_path: Path) -> None:
    """Test recording a file in manifest."""
    manager = ManifestManager(manifest_dir=tmp_path)

    # Create a test file
    test_file = tmp_path / "test.csv"
    test_file.write_text("name,price\ncopper,100\n")

    # Record the file
    entry = manager.record_file("main", test_file)

    assert entry.checksum is not None
    assert entry.size > 0
    assert entry.layer == "main"


def test_verify_file(tmp_path: Path) -> None:
    """Test verifying a file against manifest."""
    manager = ManifestManager(manifest_dir=tmp_path)

    # Create and record a file
    test_file = tmp_path / "test.csv"
    test_file.write_text("name,price\ncopper,100\n")
    manager.record_file("main", test_file)

    # Verify should pass
    assert manager.verify_file(test_file) is True

    # Modify the file
    test_file.write_text("name,price\ncopper,200\n")

    # Verify should fail
    assert manager.verify_file(test_file) is False


def test_verify_layer(tmp_path: Path) -> None:
    """Test verifying a whole layer."""
    manager = ManifestManager(manifest_dir=tmp_path)

    # Create data directory
    data_dir = tmp_path / "data"
    main_dir = data_dir / "main"
    main_dir.mkdir(parents=True)

    # Create files
    file1 = main_dir / "prices1.csv"
    file1.write_text("name,price\ncopper,100\n")

    file2 = main_dir / "prices2.csv"
    file2.write_text("name,price\naluminum,50\n")

    # Record files
    manager.record_file("main", file1)
    manager.record_file("main", file2)

    # Verify layer
    results = manager.verify_layer("main", data_dir=data_dir)

    assert len(results) == 2
    assert all(results.values())


def test_detect_changes(tmp_path: Path) -> None:
    """Test detecting changes in a layer."""
    manager = ManifestManager(manifest_dir=tmp_path)

    # Create data directory
    data_dir = tmp_path / "data"
    main_dir = data_dir / "main"
    main_dir.mkdir(parents=True)

    # Create initial file
    file1 = main_dir / "prices1.csv"
    file1.write_text("name,price\ncopper,100\n")
    manager.record_file("main", file1)

    # Add new file
    file2 = main_dir / "prices2.csv"
    file2.write_text("name,price\naluminum,50\n")

    # Modify existing file
    file1.write_text("name,price\ncopper,200\n")

    # Detect changes
    changes = manager.detect_changes("main", data_dir=data_dir)

    assert len(changes["added"]) == 1  # prices2.csv
    assert len(changes["modified"]) == 1  # prices1.csv
    assert len(changes["removed"]) == 0


def test_create_and_restore_snapshot(tmp_path: Path) -> None:
    """Test creating and restoring snapshots."""
    manager = ManifestManager(manifest_dir=tmp_path)

    # Create and record a file
    test_file = tmp_path / "test.csv"
    test_file.write_text("name,price\ncopper,100\n")
    manager.record_file("main", test_file)

    # Create snapshot
    snapshot_id = manager.create_snapshot("test-snapshot")
    assert snapshot_id == "test-snapshot"

    # List snapshots
    snapshots = manager.list_snapshots()
    assert len(snapshots) == 1
    assert snapshots[0]["id"] == "test-snapshot"

    # Modify manifest
    manager.clear_manifest()

    # Restore snapshot
    restored = manager.restore_snapshot("test-snapshot")
    assert restored is True

    # Check entry is back
    entry = manager.get_entry(test_file)
    assert entry is not None


def test_get_entry(tmp_path: Path) -> None:
    """Test getting a manifest entry."""
    manager = ManifestManager(manifest_dir=tmp_path)

    # Create and record a file
    test_file = tmp_path / "test.csv"
    test_file.write_text("name,price\ncopper,100\n")
    manager.record_file("main", test_file)

    # Get entry
    entry = manager.get_entry(test_file)
    assert entry is not None
    assert entry.checksum is not None

    # Get non-existent entry
    no_entry = manager.get_entry(Path("nonexistent.csv"))
    assert no_entry is None


def test_remove_entry(tmp_path: Path) -> None:
    """Test removing a manifest entry."""
    manager = ManifestManager(manifest_dir=tmp_path)

    # Create and record a file
    test_file = tmp_path / "test.csv"
    test_file.write_text("name,price\ncopper,100\n")
    manager.record_file("main", test_file)

    # Entry should exist
    assert manager.get_entry(test_file) is not None

    # Remove entry
    removed = manager.remove_entry(test_file)
    assert removed is True

    # Entry should not exist
    assert manager.get_entry(test_file) is None


def test_get_stats(tmp_path: Path) -> None:
    """Test getting manifest statistics."""
    manager = ManifestManager(manifest_dir=tmp_path)

    # Create some files
    for i in range(3):
        test_file = tmp_path / f"test{i}.csv"
        test_file.write_text(f"name,price\ncopper,{i * 100}\n")
        manager.record_file("main", test_file)

    stats = manager.get_stats()

    assert stats["total_files"] == 3
    assert stats["layers"].get("main", 0) == 3


def test_clear_manifest(tmp_path: Path) -> None:
    """Test clearing manifest."""
    manager = ManifestManager(manifest_dir=tmp_path)

    # Create and record a file
    test_file = tmp_path / "test.csv"
    test_file.write_text("name,price\ncopper,100\n")
    manager.record_file("main", test_file)

    # Clear
    manager.clear_manifest()

    # Check stats
    stats = manager.get_stats()
    assert stats["total_files"] == 0


def test_record_layer(tmp_path: Path) -> None:
    """Test recording an entire layer."""
    manager = ManifestManager(manifest_dir=tmp_path)

    # Create data directory
    data_dir = tmp_path / "data"
    market_dir = data_dir / "market"
    market_dir.mkdir(parents=True)

    # Create multiple files
    for i in range(3):
        test_file = market_dir / f"prices{i}.csv"
        test_file.write_text(f"name,price\ncopper,{i * 100}\n")

    # Record layer
    entries = manager.record_layer("market", data_dir=data_dir)

    assert len(entries) == 3


def test_manifest_persistence(tmp_path: Path) -> None:
    """Test that manifest persists across sessions."""
    # Create and record in first session
    manager1 = ManifestManager(manifest_dir=tmp_path)
    test_file = tmp_path / "test.csv"
    test_file.write_text("name,price\ncopper,100\n")
    manager1.record_file("main", test_file)

    # Create new manager (simulates new session)
    manager2 = ManifestManager(manifest_dir=tmp_path)

    # Should still have the entry
    entry = manager2.get_entry(test_file)
    assert entry is not None