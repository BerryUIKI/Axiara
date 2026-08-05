#!/usr/bin/env python3
"""
Validate CSV price list against template.

Checks that CSV file has correct headers, data types, and follows the template format.
Template: docs/templates/price-list.csv.example
"""

import csv
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple


# Expected header fields in exact order
EXPECTED_HEADERS = [
    "name",
    "spec",
    "unit",
    "unit_price",
    "currency",
    "effective_date",
    "note"
]

# ISO 4217 currency codes
VALID_CURRENCIES = {
    "CNY", "USD", "EUR", "JPY", "GBP", "KRW", "HKD", "TWD", "SGD",
    "AUD", "CAD", "CHF", "SEK", "NZD", "THB", "INR", "RUB", "ZAR"
}


def validate_header(row: List[str]) -> Tuple[bool, List[str]]:
    """Validate CSV header matches expected format."""
    errors = []

    if not row:
        errors.append("✗ Empty file - no header row found")
        return False, errors

    # Remove # comments if present
    header = [field.strip() for field in row if not field.strip().startswith('#')]

    # Check field count
    if len(header) != len(EXPECTED_HEADERS):
        errors.append(
            f"✗ Header field count mismatch: expected {len(EXPECTED_HEADERS)}, got {len(header)}"
        )

    # Check field names
    for i, (expected, actual) in enumerate(zip(EXPECTED_HEADERS, header)):
        if expected.lower() != actual.lower():
            errors.append(
                f"✗ Header field {i+1} mismatch: expected '{expected}', got '{actual}'"
            )

    if not errors:
        errors.append("✓ Header format correct")

    return len(errors) == 1, errors  # Only the success message


def validate_row(row_num: int, row: Dict[str, str]) -> Tuple[bool, List[str]]:
    """Validate a single CSV row."""
    errors = []

    # Check required fields
    required_fields = ["name", "unit", "unit_price", "currency", "effective_date"]
    for field in required_fields:
        if not row.get(field, "").strip():
            errors.append(f"  Row {row_num}: Missing required field '{field}'")

    # Check unit_price is numeric
    unit_price = row.get("unit_price", "").strip()
    if unit_price:
        try:
            # Remove thousands separators
            price_str = re.sub(r'[,，]', '', unit_price)
            price = float(price_str)
            if price <= 0:
                errors.append(f"  Row {row_num}: unit_price must be positive (got {price})")
        except ValueError:
            errors.append(f"  Row {row_num}: unit_price must be numeric (got '{unit_price}')")

    # Check currency is ISO code
    currency = row.get("currency", "").strip().upper()
    if currency and currency not in VALID_CURRENCIES:
        errors.append(
            f"  Row {row_num}: Invalid currency '{currency}' (must be ISO 4217 code)"
        )

    # Check effective_date format (YYYY-MM-DD or flexible)
    effective_date = row.get("effective_date", "").strip()
    if effective_date:
        if not re.match(r'\d{4}-\d{2}-\d{2}', effective_date):
            errors.append(
                f"  Row {row_num}: effective_date should be YYYY-MM-DD format (got '{effective_date}')"
            )

    return len(errors) == 0, errors


def validate_csv_file(csv_path: str) -> Tuple[bool, List[str]]:
    """Validate entire CSV file."""
    all_errors = []
    total_rows = 0
    valid_rows = 0

    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            # Validate header
            header_valid, header_errors = validate_header(reader.fieldnames or [])
            all_errors.extend(header_errors)

            if not header_valid:
                # Don't validate rows if header is wrong
                return False, all_errors

            # Validate data rows
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                total_rows += 1
                row_valid, row_errors = validate_row(row_num, row)

                if row_valid:
                    valid_rows += 1
                else:
                    all_errors.extend(row_errors)

    except FileNotFoundError:
        all_errors.append(f"✗ File not found: {csv_path}")
        return False, all_errors
    except Exception as e:
        all_errors.append(f"✗ Error reading file: {e}")
        return False, all_errors

    # Summary
    if valid_rows == total_rows:
        all_errors.append(f"✓ All {total_rows} data rows valid")
        return True, all_errors
    else:
        all_errors.append(
            f"✗ {total_rows - valid_rows}/{total_rows} rows have validation errors"
        )
        return False, all_errors


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate_csv.py <price-list.csv>")
        print()
        print("Validates CSV file against price list template.")
        print("Template: docs/templates/price-list.csv.example")
        print()
        print("Required fields: name, spec, unit, unit_price, currency, effective_date, note")
        print("Currency must be ISO 4217 code (CNY, USD, EUR, etc.)")
        print("effective_date format: YYYY-MM-DD")
        sys.exit(1)

    csv_path = sys.argv[1]

    print(f"Validating CSV: {csv_path}")
    print("=" * 60)
    print()

    valid, messages = validate_csv_file(csv_path)

    for message in messages:
        print(message)

    print()
    print("=" * 60)

    if valid:
        print("✓ Validation PASSED")
        print()
        print("Next steps:")
        print("  • Import to data/main/: 'axiara import <price-list.csv>'")
        return 0
    else:
        print("✗ Validation FAILED")
        print()
        print("Fix the errors above and re-validate before importing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())