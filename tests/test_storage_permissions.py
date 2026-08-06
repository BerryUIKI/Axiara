"""Tests for storage layer permission enforcement."""

import pytest

from axiara.core.storage import DataLayer
from axiara.core.storage.permissions import PermissionError, PermissionManager


def test_permission_manager_init() -> None:
    """Test PermissionManager initialization."""
    manager = PermissionManager()
    assert manager is not None


def test_main_layer_write_rejected_for_crawler() -> None:
    """Test that crawler cannot write to MAIN layer."""
    manager = PermissionManager()

    with pytest.raises(PermissionError) as exc_info:
        manager.check_write_permission(DataLayer.MAIN, source="crawler")

    assert "crawler" in str(exc_info.value).lower()
    assert "main" in str(exc_info.value).lower()


def test_main_layer_write_rejected_for_learning() -> None:
    """Test that learning cannot write to MAIN layer."""
    manager = PermissionManager()

    with pytest.raises(PermissionError) as exc_info:
        manager.check_write_permission(DataLayer.MAIN, source="learning")

    assert "learning" in str(exc_info.value).lower()


def test_main_layer_write_allowed_for_manual() -> None:
    """Test that manual source can write to MAIN layer."""
    manager = PermissionManager()

    # Should not raise
    result = manager.check_write_permission(DataLayer.MAIN, source="manual")
    assert result is True


def test_learn_layer_write_allowed_for_learning() -> None:
    """Test that learning source can write to LEARN layer."""
    manager = PermissionManager()

    # Should not raise
    result = manager.check_write_permission(DataLayer.LEARN, source="learning")
    assert result is True


def test_market_layer_requires_confirmation_for_crawler() -> None:
    """Test that crawler writes to MARKET require confirmation."""
    manager = PermissionManager()

    # Without confirmation should raise
    with pytest.raises(PermissionError) as exc_info:
        manager.check_write_permission(DataLayer.MARKET, source="crawler", user_confirmed=False)

    assert "confirmation" in str(exc_info.value).lower()

    # With confirmation should pass
    result = manager.check_write_permission(DataLayer.MARKET, source="crawler", user_confirmed=True)
    assert result is True


def test_market_layer_allowed_for_crawler_with_confirmation() -> None:
    """Test that crawler can write to MARKET with user confirmation."""
    manager = PermissionManager()

    result = manager.check_write_permission(DataLayer.MARKET, source="crawler", user_confirmed=True)
    assert result is True


def test_uploads_layer_write_allowed_for_import() -> None:
    """Test that import source can write to UPLOADS layer."""
    manager = PermissionManager()

    result = manager.check_write_permission(DataLayer.UPLOADS, source="import")
    assert result is True


def test_get_allowed_sources() -> None:
    """Test getting allowed sources for each layer."""
    manager = PermissionManager()

    # MAIN layer should only allow manual
    main_sources = manager.get_allowed_sources(DataLayer.MAIN)
    assert "manual" in main_sources
    assert "crawler" not in main_sources

    # LEARN layer should allow manual and learning
    learn_sources = manager.get_allowed_sources(DataLayer.LEARN)
    assert "manual" in learn_sources
    assert "learning" in learn_sources

    # MARKET layer should allow manual and crawler
    market_sources = manager.get_allowed_sources(DataLayer.MARKET)
    assert "manual" in market_sources
    assert "crawler" in market_sources


def test_requires_confirmation() -> None:
    """Test checking if confirmation is required."""
    manager = PermissionManager()

    # Crawler to MARKET requires confirmation
    assert manager.requires_confirmation(DataLayer.MARKET, "crawler") is True

    # Crawler to LEARN does not require confirmation
    assert manager.requires_confirmation(DataLayer.LEARN, "crawler") is False

    # Manual never requires confirmation
    assert manager.requires_confirmation(DataLayer.MARKET, "manual") is False


def test_delete_permission_same_as_write() -> None:
    """Test that delete permissions follow same rules as write."""
    manager = PermissionManager()

    # Cannot delete from MAIN as crawler
    with pytest.raises(PermissionError):
        manager.check_delete_permission(DataLayer.MAIN, source="crawler")

    # Can delete from MARKET as manual
    result = manager.check_delete_permission(DataLayer.MARKET, source="manual")
    assert result is True


def test_all_layers_readable() -> None:
    """Test that all layers are readable."""
    manager = PermissionManager()

    for layer in [DataLayer.MAIN, DataLayer.LEARN, DataLayer.MARKET, DataLayer.UPLOADS]:
        assert manager.can_read(layer) is True


def test_unknown_layer_raises_error() -> None:
    """Test that unknown layer raises error."""
    manager = PermissionManager()

    # Create a fake layer value - this should be handled gracefully
    # Since we're using StrEnum, passing a non-enum value should fail
    # The test should check that the error handling works correctly
    with pytest.raises(AttributeError):
        # This will fail because "unknown_layer" doesn't have .value attribute
        manager.check_write_permission("unknown_layer", source="manual")  # type: ignore