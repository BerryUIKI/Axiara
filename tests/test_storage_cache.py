"""Tests for SQLite cache functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from axiara.core.storage import DataLayer
from axiara.core.storage.cache import SQLiteCache


def test_cache_init(tmp_path: Path) -> None:
    """Test cache initialization."""
    cache = SQLiteCache(cache_dir=tmp_path)
    assert cache is not None
    assert cache.db_path.exists()


def test_cache_compute_checksum(tmp_path: Path) -> None:
    """Test file checksum computation."""
    cache = SQLiteCache(cache_dir=tmp_path)

    # Create a test file
    test_file = tmp_path / "test.csv"
    test_file.write_text("name,price\ncopper,100\n")

    checksum = cache._compute_checksum(test_file)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA-256 hex length


def test_sync_csv_file(tmp_path: Path) -> None:
    """Test syncing a CSV file to cache."""
    cache = SQLiteCache(cache_dir=tmp_path)

    # Create a test CSV file
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("name,unit,unit_price,currency,effective_date\ncopper-wire,kg,100,CNY,2026-08-05\n")

    row_count = cache.sync_file(DataLayer.MARKET, csv_file)
    assert row_count == 1


def test_sync_json_file(tmp_path: Path) -> None:
    """Test syncing a JSON file to cache."""
    cache = SQLiteCache(cache_dir=tmp_path)

    # Create a test JSON file
    json_file = tmp_path / "test.json"
    data = [
        {
            "name": "copper-wire",
            "unit": "kg",
            "unit_price": 100.0,
            "currency": "CNY",
            "effective_date": "2026-08-05",
        }
    ]
    json_file.write_text(json.dumps(data))

    row_count = cache.sync_file(DataLayer.MARKET, json_file)
    assert row_count == 1


def test_query_cached_data(tmp_path: Path) -> None:
    """Test querying cached data."""
    cache = SQLiteCache(cache_dir=tmp_path)

    # Create and sync a test file
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("name,unit,unit_price,currency,effective_date\ncopper-wire,kg,100,CNY,2026-08-05\n")

    cache.sync_file(DataLayer.MARKET, csv_file)

    # Query the data
    results = cache.query(DataLayer.MARKET, filters={"name": "copper-wire"})
    assert len(results) == 1
    assert results[0]["name"] == "copper-wire"
    assert results[0]["unit_price"] == 100.0


def test_is_file_cached(tmp_path: Path) -> None:
    """Test checking if file is cached."""
    cache = SQLiteCache(cache_dir=tmp_path)

    # Create and sync a file
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("name,price\ncopper,100\n")

    # Before sync, not cached
    assert not cache.is_file_cached(csv_file)

    # After sync, cached
    cache.sync_file(DataLayer.MAIN, csv_file)
    assert cache.is_file_cached(csv_file)


def test_sync_layer(tmp_path: Path) -> None:
    """Test syncing an entire layer."""
    cache = SQLiteCache(cache_dir=tmp_path)

    # Create data directory structure
    data_dir = tmp_path / "data"
    market_dir = data_dir / "market"
    market_dir.mkdir(parents=True)

    # Create multiple files
    (market_dir / "prices1.csv").write_text("name,price\ncopper,100\n")
    (market_dir / "prices2.csv").write_text("name,price\naluminum,50\n")

    # Sync the layer
    results = cache.sync_layer(DataLayer.MARKET, data_dir=data_dir)

    # Should have synced files
    assert len(results) > 0


def test_clear_cache(tmp_path: Path) -> None:
    """Test clearing cache."""
    cache = SQLiteCache(cache_dir=tmp_path)

    # Create and sync a file
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("name,price\ncopper,100\n")
    cache.sync_file(DataLayer.MAIN, csv_file)

    # Clear cache
    cache.clear_cache()

    # Check stats
    stats = cache.get_cache_stats()
    assert stats["main_prices"] == 0


def test_get_cache_stats(tmp_path: Path) -> None:
    """Test getting cache statistics."""
    cache = SQLiteCache(cache_dir=tmp_path)

    # Initially empty
    stats = cache.get_cache_stats()
    assert stats["main_prices"] == 0
    assert stats["cached_files"] == 0

    # Add some data
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("name,price\ncopper,100\n")
    cache.sync_file(DataLayer.MAIN, csv_file)

    stats = cache.get_cache_stats()
    assert stats["main_prices"] == 1
    assert stats["cached_files"] == 1


def test_cache_context_manager(tmp_path: Path) -> None:
    """Test cache as context manager."""
    with SQLiteCache(cache_dir=tmp_path) as cache:
        assert cache is not None

        # Create a test file
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,price\ncopper,100\n")
        cache.sync_file(DataLayer.MAIN, csv_file)


def test_query_with_order_by(tmp_path: Path) -> None:
    """Test querying with order by."""
    cache = SQLiteCache(cache_dir=tmp_path)

    # Create file with multiple rows
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(
        "name,unit_price,effective_date\ncopper,100,2026-08-05\naluminum,50,2026-08-05\n"
    )

    cache.sync_file(DataLayer.MARKET, csv_file)

    # Query with order by
    results = cache.query(DataLayer.MARKET, order_by="name")
    assert len(results) == 2
    # Results should be ordered by name


def test_query_with_limit(tmp_path: Path) -> None:
    """Test querying with limit."""
    cache = SQLiteCache(cache_dir=tmp_path)

    # Create file with multiple rows
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(
        "name,unit_price\ncopper,100\naluminum,50\nsteel,80\n"
    )

    cache.sync_file(DataLayer.MARKET, csv_file)

    # Query with limit
    results = cache.query(DataLayer.MARKET, limit=2)
    assert len(results) == 2