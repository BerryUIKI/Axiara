# Price List CSV Schema

Template: `docs/templates/price-list.csv.example`

## Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✓ | Material/commodity name (canonical form preferred) |
| `spec` | string | | Specification string (e.g., "1.5mm²", "Grade A") |
| `unit` | string | ✓ | Unit of measurement (e.g., "kg", "ton", "m") |
| `unit_price` | float | ✓ | Price per unit (numeric, positive) |
| `currency` | string | ✓ | ISO 4217 currency code (CNY, USD, EUR, etc.) |
| `effective_date` | date | ✓ | Date the price is valid (YYYY-MM-DD format) |
| `note` | string | | Additional notes (quality, region, tax status, etc.) |

## CSV Format Rules

### Header Row

The header row must match **exactly** (case-sensitive):

```csv
name,spec,unit,unit_price,currency,effective_date,note
```

### Comment Lines

Lines starting with `#` are treated as comments and ignored:

```csv
# This is a comment
name,spec,unit,unit_price,currency,effective_date,note
```

### Field Constraints

#### name
- Required field
- Should use canonical names when possible (see normalization dictionary)
- Examples: `copper-wire`, `aluminum`, `steel-rebar`

#### spec
- Optional field
- Free-form specification string
- Examples: `1.5mm²`, `Grade A`, `A00`

#### unit
- Required field
- Use canonical unit abbreviations when possible
- Examples: `kg`, `ton`, `m`, `sqm`, `l`

#### unit_price
- Required field
- Must be numeric (positive float or integer)
- Thousands separators (`,`, `，`) are automatically removed
- Examples: `12.50`, `1,250.00`, `5000`

#### currency
- Required field
- Must be ISO 4217 currency code (uppercase)
- Valid codes: `CNY`, `USD`, `EUR`, `JPY`, `GBP`, `KRW`, etc.

#### effective_date
- Required field
- Format: `YYYY-MM-DD` (ISO 8601 date)
- Example: `2026-08-05`

#### note
- Optional field
- Free-form text
- Example: `Premium grade, tax included`

## Example Files

### Valid Example

```csv
name,spec,unit,unit_price,currency,effective_date,note
copper-wire,1.5mm²,kg,68.50,CNY,2026-08-05,High conductivity
aluminum,A00,ton,18500.00,CNY,2026-08-05,Spot price
steel-rebar,HRB400,ton,4200,CNY,2026-08-05,Standard grade
zinc,0#,ton,23500,CNY,2026-08-05,
```

### Invalid Example (for testing)

```csv
name,spec,unit,unit_price,currency,effective_date,note
copper-wire,1.5mm²,kg,sixty-eight,CNY,2026-08-05,Invalid price
aluminum,,ton,-100,CNY,2026-08-05,Missing spec and negative price
steel-rebar,HRB400,ton,4200,RMB,08-05-2026,Wrong currency code and date format
,HRB400,ton,4200,CNY,2026-08-05,Missing name
```

## Validation

Run validation before importing:

```bash
python skills/csv-data-import/scripts/validate_csv.py <price-list.csv>
```

## Import Process

1. **Validate** - Check CSV against template
2. **Diff** - Compare with existing baseline (if any)
3. **Confirm** - Review changes with user
4. **Import** - Write to `data/main/` (official baseline)
5. **Record** - Update SHA-256 manifest and ledger

See: `skills/csv-data-import/SKILL.md` for full workflow.