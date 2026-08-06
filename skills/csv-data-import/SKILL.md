---
name: csv-data-import
description: >
  Import price lists and historical invoices/order sheets into the Axiara
  valuation workspace with validation, versioning and tamper-evidence. Use when
  the user says "import price-list.csv into data/main/" or uploads historical
  invoices/orders for learning. Validates against the price-list template,
  writes to data/main/ only after diff + confirmation, refreshes the SHA-256
  manifest in db_dump/, and records the event in ledger/. Never overwrites the
  official baseline silently. Triggers: "import", "import price list",
  "upload price list", "learn from invoices", "import into data/main".
---

# CSV Data Import

Official price lists are the highest-weight baseline (`data/main/`, human-edit only).
Import must be reliable, versioned, and tamper-evident. This skill covers the
official-baseline path (Mode 1.1) and the learning path (Mode 1.2).

## When to use

- User: *"import price-list.csv into data/main/"* (official baseline).
- User uploads historical invoices / order sheets (learning into `data/learn/`).

## Examples

### Example 1: Validating a price list

```bash
# Validate CSV before import
python skills/csv-data-import/scripts/validate_csv.py price-list.csv

# Output:
# ✓ Header format correct
# ✓ All 12 data rows valid
# ✓ Validation PASSED
```

### Example 2: Import with diff

```bash
# Import to data/main/ (after validation)
axiara import price-list.csv

# Agent shows diff:
# + 3 new rows (copper-wire, aluminum, steel-rebar)
# ~ 2 changed rows (zinc: 23000 → 23500, nickel: 130000 → 135000)
# - 0 removed rows
#
# User confirms: yes
# ✓ Import complete
# ✓ Manifest updated in db_dump/
# ✓ Ledger entry created
```

### Example 3: Validation errors

```bash
# CSV with errors
python skills/csv-data-import/scripts/validate_csv.py bad-prices.csv

# Output:
# ✗ Row 3: unit_price must be numeric (got 'sixty-eight')
# ✗ Row 5: Invalid currency 'RMB' (must be ISO 4217 code)
# ✗ Row 8: Missing required field 'name'
# ✗ Validation FAILED
```

## Step 1 — Validate against the template

Template: `docs/templates/price-list.csv.example` (fields in exact order).

- Header row must match exactly: `name,spec,unit,unit_price,currency,effective_date,note`.
- Lines starting with `#` are comments — ignored.
- `unit_price` must be numeric; `currency` uses ISO codes (CNY / USD / EUR / JPY ...).
- Report validation errors to the user before any write.

**Validation script:**
```bash
python skills/csv-data-import/scripts/validate_csv.py <price-list.csv>
```

## Step 2 — Diff + confirm before writing `data/main/`

- Show the user what would change vs the current baseline (new rows / changed rows / removed rows).
- **Never overwrite silently.** Write only after explicit confirmation.
- Files land in `data/main/` (versioned; git tracks changes in team mode).

## Step 3 — Refresh manifest + record ledger

- Recompute the SHA-256 manifest of official-baseline files.
- Store manifest in **`db_dump/`** (NOT the wipeable `cache/`).
- Append a `ledger/` entry: time, file, hash before/after, action.

## Step 4 — Learning path (Mode 1.2)

- Historical invoices / order sheets → extract materials, processes, cost, note rules → `data/learn/`.
- **Never writes `data/main/`** — learned reference only.

## Validation Rules

### Field Constraints

| Field | Constraints |
| --- | --- |
| `name` | Required, non-empty |
| `spec` | Optional |
| `unit` | Required, non-empty |
| `unit_price` | Required, numeric, positive |
| `currency` | Required, ISO 4217 code (CNY/USD/EUR/...) |
| `effective_date` | Required, YYYY-MM-DD format |
| `note` | Optional |

### Currency Codes

Valid ISO 4217 codes: `CNY`, `USD`, `EUR`, `JPY`, `GBP`, `KRW`, `HKD`, `TWD`, `SGD`, `AUD`, `CAD`, `CHF`, `SEK`, `NZD`, etc.

See: `skills/csv-data-import/references/price_list_schema.md`

## Import Workflow

1. **Validate** - Check CSV against template schema
   ```bash
   python skills/csv-data-import/scripts/validate_csv.py <file.csv>
   ```

2. **Review diff** - Agent shows changes vs existing baseline

3. **Confirm** - User accepts/rejects/edits

4. **Import** - Write to `data/main/` (only after confirmation)

5. **Record** - Update SHA-256 manifest and ledger

## Anti-tampering reminder

- Detected unexpected change to `data/main/` → **review mode**: show diff, ask the user,
  restore from git history / `db_dump/` snapshot if needed. Never silently continue.

## See Also

- **Schema documentation**: `skills/csv-data-import/references/price_list_schema.md`
- **Validation script**: `skills/csv-data-import/scripts/validate_csv.py`
- **Example files**: `skills/csv-data-import/assets/valid_example.csv`, `invalid_example.csv`
- **Template**: `docs/templates/price-list.csv.example`