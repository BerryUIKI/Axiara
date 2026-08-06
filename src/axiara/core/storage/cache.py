"""SQLite cache for fast queries on file-based data.

Provides a read-through cache layer that automatically syncs from
CSV/JSON files in store/ to a local SQLite database for fast queries.

Location: .data/cache/axiara_cache.db

The cache is:
- Always on (not a user choice per D20)
- Auto-synced from store/ files
- Wipeable (can be regenerated from source files)
- Token-efficient (querying SQLite is cheaper than reading large CSVs)
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from axiara.core.storage.permissions import DataLayer


class CacheError(Exception):
    """Raised when cache operations fail."""

    pass


class SQLiteCache:
    """SQLite cache for fast data queries.

    Tables:
    - main_prices: Official baseline prices (read from data/main/)
    - learn_prices: AI-learned reference prices (read from data/learn/)
    - market_prices: Crawled market prices (read from data/market/)
    - uploads: User-provided files (read from data/uploads/)
    - cache_metadata: Tracks file checksums for sync

    The cache uses a read-through pattern:
    1. Query checks cache first
    2. If not in cache or stale, loads from file
    3. Updates cache and returns result
    """

    # Schema for price data tables
    PRICE_TABLE_SCHEMA_CREATE = """
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            spec TEXT,
            unit TEXT NOT NULL,
            unit_price REAL NOT NULL,
            currency TEXT NOT NULL,
            effective_date TEXT NOT NULL,
            note TEXT,
            source TEXT,
            url TEXT,
            fetched_at TEXT,
            confidence TEXT,
            raw TEXT,
            file_path TEXT NOT NULL,
            row_hash TEXT NOT NULL,
            indexed_at TEXT NOT NULL
        );
    """

    PRICE_TABLE_SCHEMA_INDEXES = [
        "CREATE INDEX IF NOT EXISTS idx_{table_name}_name ON {table_name}(name);",
        "CREATE INDEX IF NOT EXISTS idx_{table_name}_effective_date ON {table_name}(effective_date);",
        "CREATE INDEX IF NOT EXISTS idx_{table_name}_source ON {table_name}(source);",
    ]

    METADATA_TABLE_SCHEMA = """
        CREATE TABLE IF NOT EXISTS cache_metadata (
            file_path TEXT PRIMARY KEY,
            file_checksum TEXT NOT NULL,
            file_mtime TEXT NOT NULL,
            last_synced TEXT NOT NULL,
            row_count INTEGER NOT NULL
        );
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialize the SQLite cache.

        Args:
            cache_dir: Directory for cache files (default: .data/cache/)
        """
        self.cache_dir = cache_dir or Path(".data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "axiara_cache.db"
        self._conn: sqlite3.Connection | None = None
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            # Create metadata table
            conn.execute(self.METADATA_TABLE_SCHEMA)

            # Create price tables for each layer
            for layer in [DataLayer.MAIN, DataLayer.LEARN, DataLayer.MARKET, DataLayer.UPLOADS]:
                table_name = self._get_table_name(layer)
                # Create table
                conn.execute(self.PRICE_TABLE_SCHEMA_CREATE.format(table_name=table_name))
                # Create indexes separately
                for index_sql in self.PRICE_TABLE_SCHEMA_INDEXES:
                    conn.execute(index_sql.format(table_name=table_name))

            conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection.

        Returns:
            SQLite connection with row factory
        """
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            # Note: WAL journal mode was considered for concurrent read safety
            # with FastAPI, but `PRAGMA journal_mode=WAL` permanently hangs on
            # some Windows + SQLite builds (blocking startup). The default
            # rollback journal is safe for the single-user/team-git use cases;
            # revisit WAL only behind a config flag if multi-process access
            # becomes a real requirement.
        return self._conn

    def _get_table_name(self, layer: DataLayer) -> str:
        """Get table name for a data layer.

        Args:
            layer: Data layer

        Returns:
            Table name (e.g., 'main_prices')
        """
        return f"{layer.value}_prices"

    def _compute_checksum(self, file_path: Path) -> str:
        """Compute SHA-256 checksum of a file.

        Args:
            file_path: Path to file

        Returns:
            Hexadecimal checksum string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _compute_row_hash(self, row: dict[str, Any]) -> str:
        """Compute hash for a data row.

        Args:
            row: Data row dictionary

        Returns:
            Hash string
        """
        # Create deterministic string representation
        row_str = json.dumps(row, sort_keys=True, default=str)
        return hashlib.sha256(row_str.encode()).hexdigest()[:16]

    def is_file_cached(self, file_path: Path) -> bool:
        """Check if a file is in cache and up-to-date.

        Args:
            file_path: Path to source file

        Returns:
            True if file is cached and current
        """
        if not file_path.exists():
            return False

        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT file_checksum, file_mtime FROM cache_metadata WHERE file_path = ?",
                (str(file_path),),
            )
            row = cursor.fetchone()

            if row is None:
                return False

            # Check if file has changed
            current_checksum = self._compute_checksum(file_path)
            current_mtime = str(file_path.stat().st_mtime)

            return row["file_checksum"] == current_checksum and row["file_mtime"] == current_mtime

    def sync_file(self, layer: DataLayer, file_path: Path) -> int:
        """Sync a file to the cache.

        Args:
            layer: Data layer
            file_path: Path to source file

        Returns:
            Number of rows synced

        Raises:
            CacheError: If file cannot be read
        """
        if not file_path.exists():
            raise CacheError(f"File not found: {file_path}")

        table_name = self._get_table_name(layer)
        file_checksum = self._compute_checksum(file_path)
        file_mtime = str(file_path.stat().st_mtime)

        # Read file based on extension
        ext = file_path.suffix.lower()
        try:
            if ext == ".csv":
                df = pd.read_csv(file_path)
            elif ext == ".json":
                df = pd.read_json(file_path)
            elif ext in [".yaml", ".yml"]:
                import yaml

                with open(file_path) as f:
                    data = yaml.safe_load(f)
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame([data])
            else:
                raise CacheError(f"Unsupported file format: {ext}")
        except Exception as e:
            raise CacheError(f"Failed to read {file_path}: {e}") from e

        if df.empty:
            return 0

        # Remove existing entries for this file
        with self._get_connection() as conn:
            conn.execute(f"DELETE FROM {table_name} WHERE file_path = ?", (str(file_path),))
            conn.execute("DELETE FROM cache_metadata WHERE file_path = ?", (str(file_path),))

            # Insert new rows
            now = datetime.now(timezone.utc).isoformat()
            row_count = 0

            for _, row in df.iterrows():
                row_dict = row.to_dict()
                row_hash = self._compute_row_hash(row_dict)

                conn.execute(
                    f"""
                    INSERT INTO {table_name}
                    (name, spec, unit, unit_price, currency, effective_date, note,
                     source, url, fetched_at, confidence, raw, file_path, row_hash, indexed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row_dict.get("name", ""),
                        row_dict.get("spec"),
                        row_dict.get("unit", ""),
                        float(row_dict.get("unit_price", 0)),
                        row_dict.get("currency", "CNY"),
                        row_dict.get("effective_date", ""),
                        row_dict.get("note"),
                        row_dict.get("source"),
                        row_dict.get("url"),
                        row_dict.get("fetched_at"),
                        row_dict.get("confidence"),
                        row_dict.get("raw"),
                        str(file_path),
                        row_hash,
                        now,
                    ),
                )
                row_count += 1

            # Update metadata
            conn.execute(
                """
                INSERT INTO cache_metadata
                (file_path, file_checksum, file_mtime, last_synced, row_count)
                VALUES (?, ?, ?, ?, ?)
                """,
                (str(file_path), file_checksum, file_mtime, now, row_count),
            )

            conn.commit()

        return row_count

    def sync_layer(self, layer: DataLayer, data_dir: Path | None = None) -> dict[str, int]:
        """Sync all files in a layer to cache.

        Args:
            layer: Data layer
            data_dir: Root data directory (default: data/)

        Returns:
            Dict mapping file paths to row counts
        """
        data_dir = data_dir or Path("data")
        layer_dir = data_dir / layer.value

        if not layer_dir.exists():
            return {}

        results = {}
        for file_path in layer_dir.glob("**/*"):
            if file_path.is_file() and file_path.suffix.lower() in [".csv", ".json", ".yaml", ".yml"]:
                if not self.is_file_cached(file_path):
                    row_count = self.sync_file(layer, file_path)
                    results[str(file_path)] = row_count

        return results

    def query(
        self,
        layer: DataLayer,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Query cached data.

        Args:
            layer: Data layer
            filters: Column filters (e.g., {"name": "copper-wire"})
            order_by: Column to order by
            limit: Maximum rows to return

        Returns:
            List of matching rows as dictionaries
        """
        table_name = self._get_table_name(layer)

        query = f"SELECT * FROM {table_name}"
        params: list[Any] = []

        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            query += " WHERE " + " AND ".join(conditions)

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit:
            query += f" LIMIT {limit}"

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def clear_cache(self) -> None:
        """Clear all cached data.

        Warning: This will remove all entries from cache tables.
        The cache can be regenerated by calling sync_layer().
        """
        with self._get_connection() as conn:
            for layer in [DataLayer.MAIN, DataLayer.LEARN, DataLayer.MARKET, DataLayer.UPLOADS]:
                table_name = self._get_table_name(layer)
                conn.execute(f"DELETE FROM {table_name}")
            conn.execute("DELETE FROM cache_metadata")
            conn.commit()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with table names and row counts
        """
        stats = {}
        with self._get_connection() as conn:
            for layer in [DataLayer.MAIN, DataLayer.LEARN, DataLayer.MARKET, DataLayer.UPLOADS]:
                table_name = self._get_table_name(layer)
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                stats[table_name] = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM cache_metadata")
            stats["cached_files"] = cursor.fetchone()[0]

        return stats

    def close(self) -> None:
        """Close database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "SQLiteCache":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()


# Global cache instance
_cache: SQLiteCache | None = None


def get_cache() -> SQLiteCache:
    """Get the global cache instance.

    Returns:
        Global SQLiteCache instance
    """
    global _cache
    if _cache is None:
        _cache = SQLiteCache()
    return _cache
