#!/usr/bin/env python3
"""
Verify Axiara setup after onboarding.

Checks that .data/ directory structure is correct and configuration files exist.
Run after scripts/init-data.sh completes.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple


def check_directory_structure() -> List[Tuple[str, bool, str]]:
    """Check that required .data/ subdirectories exist."""
    checks = []

    required_dirs = [
        ".data",
        ".data/store",
        ".data/cache",
        ".data/ledger",
        ".data/db_dump",
        ".data/local_config",
    ]

    for dir_path in required_dirs:
        exists = Path(dir_path).exists()
        status = "✓" if exists else "✗"
        message = f"{status} {dir_path} {'exists' if exists else 'MISSING'}"
        checks.append((dir_path, exists, message))

    return checks


def check_config_files() -> List[Tuple[str, bool, str]]:
    """Check that required configuration files exist."""
    checks = []

    required_files = [
        ".data/local_config/config",
    ]

    for file_path in required_files:
        exists = Path(file_path).exists()
        status = "✓" if exists else "✗"
        message = f"{status} {file_path} {'exists' if exists else 'MISSING'}"
        checks.append((file_path, exists, message))

    return checks


def check_config_sections() -> List[Tuple[str, bool, str]]:
    """Check that config file has required sections."""
    checks = []

    config_path = Path(".data/local_config/config")
    if not config_path.exists():
        checks.append(("config_sections", False, "✗ Config file missing, cannot check sections"))
        return checks

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        required_sections = ['[data_repo]', '[git]', '[app]', '[storage]']

        for section in required_sections:
            exists = section in content
            status = "✓" if exists else "✗"
            message = f"{status} Section {section} {'found' if exists else 'MISSING'}"
            checks.append((section, exists, message))
    except Exception as e:
        checks.append(("config_sections", False, f"✗ Error reading config: {e}"))

    return checks


def check_store_sync() -> List[Tuple[str, bool, str]]:
    """Check if store/ directory has data (if sync was requested)."""
    checks = []

    store_path = Path(".data/store")
    if not store_path.exists():
        checks.append(("store", False, "✗ store/ directory missing"))
        return checks

    # Check if store has any files (excluding .git)
    has_files = any(
        True for item in store_path.iterdir()
        if item.name != '.git'
    )

    status = "✓" if has_files else "⚠"
    message = f"{status} store/ {'has data' if has_files else 'is empty (sync may not be configured)'}"
    checks.append(("store_content", has_files, message))

    return checks


def check_manifest() -> List[Tuple[str, bool, str]]:
    """Check for SHA-256 manifest in db_dump/."""
    checks = []

    db_dump_path = Path(".data/db_dump")
    if not db_dump_path.exists():
        checks.append(("manifest", False, "✗ db_dump/ directory missing"))
        return checks

    # Check for manifest files
    manifest_files = list(db_dump_path.glob("manifest-*.json"))

    status = "✓" if manifest_files else "⚠"
    message = f"{status} Manifest {'found' if manifest_files else 'not yet created'}"
    checks.append(("manifest", bool(manifest_files), message))

    return checks


def main():
    """Run all verification checks."""
    print("Axiara Setup Verification")
    print("=" * 60)
    print()

    all_passed = True

    # Check directory structure
    print("1. Directory Structure")
    print("-" * 40)
    for _, passed, message in check_directory_structure():
        print(f"  {message}")
        all_passed = all_passed and passed
    print()

    # Check config files
    print("2. Configuration Files")
    print("-" * 40)
    for _, passed, message in check_config_files():
        print(f"  {message}")
        all_passed = all_passed and passed
    print()

    # Check config sections
    print("3. Configuration Sections")
    print("-" * 40)
    for _, passed, message in check_config_sections():
        print(f"  {message}")
        all_passed = all_passed and passed
    print()

    # Check store sync
    print("4. Store Synchronization")
    print("-" * 40)
    for _, passed, message in check_store_sync():
        print(f"  {message}")
        # Don't fail on empty store, it's a warning
    print()

    # Check manifest
    print("5. Baseline Manifest")
    print("-" * 40)
    for _, passed, message in check_manifest():
        print(f"  {message}")
        # Don't fail on missing manifest, it's created on first import
    print()

    # Summary
    print("=" * 60)
    if all_passed:
        print("✓ Setup verification PASSED")
        print()
        print("Next steps:")
        print("  • Import price lists: 'axiara import <price-list.csv>'")
        print("  • Fetch market prices: 'axiara fetch <material>'")
        return 0
    else:
        print("✗ Setup verification FAILED")
        print()
        print("Troubleshooting:")
        print("  • Re-run: bash scripts/init-data.sh --language <lang> --sync-mode <mode> ...")
        print("  • Check docs/init.md for detailed setup guide")
        return 1


if __name__ == "__main__":
    sys.exit(main())