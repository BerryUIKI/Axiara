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

## Step 1 — Validate against the template

Template: `docs/templates/price-list.csv.example` (fields in exact order).

- Header row must match exactly: `name,spec,unit,unit_price,currency,effective_date,note`.
- Lines starting with `#` are comments — ignored.
- `unit_price` must be numeric; `currency` uses ISO codes (CNY / USD / EUR / JPY ...).
- Report validation errors to the user before any write.

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

## Anti-tampering reminder

- Detected unexpected change to `data/main/` → **review mode**: show diff, ask the user,
  restore from git history / `db_dump/` snapshot if needed. Never silently continue.
