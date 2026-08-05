# Axiara — Multi-User Learning: Text Format (text + git)

Status: **v0.1** (2026-08-05) — implementation design for the **text+git storage mode** (`sync_mode: git`, `backend: csv`). Companion to `docs/learn-sync.md` (hub model overview) and `docs/learn-sync-sql.md` (the SQL-server variant). No server infrastructure — everything is plain-text files synced via git.

## 1. Model

```
user A data/learn/private/ ─┐
user B data/learn/private/ ─┼── weekly manual upload ──▶ central git repo (store/)
user C data/learn/private/ ─┘         │  learn_inbox/<user>/<date>/
                                      ▼
                          central training Agent reviews ──▶ admin confirms ──▶ learn_shared/ updated (+ manifest, git history)
                                                                                    │
                                                              users pull back (read-only merge)
```

Same hub-and-spoke logic as `docs/learn-sync.md`, implemented with **files + git** instead of tables.

## 2. Physical Structure

Central repo layout (recommended: inside the team store repo `store/`; a separate `axiara-learn` repo is the alternative — OQ-LS1):

```
store/
├── workspace.config.yaml        # team config template (workspace-config.md)
├── learn_shared/                # PUBLIC rules — only via review + admin confirm
│   ├── rules/
│   │   ├── material.yaml        # material normalization aliases
│   │   ├── process-cost.yaml    # process → unit_fee / loss_rate / yield
│   │   ├── cost-breakdown.yaml  # material+labor+loss+processing
│   │   └── pricing-tiers.yaml   # low/mid/high defaults
│   ├── stats/                   # rebuildable JSON aggregates (never hand-merged)
│   └── manifest.json            # SHA-256 of rules/ + stats/ (anti-tampering)
└── learn_inbox/                 # UPLOAD AREA — users never write learn_shared directly
    └── <user-id>/
        └── <yyyymmdd>/
            ├── bundle.yaml      # incremental rules with provenance
            └── README.md        # human note (optional)
```

> **Format note (D-SK8):** rules and upload bundles are **YAML** — AI/human-readable, commentable, clean diffs. JSON is used only where machines need it (`stats/` aggregates, `manifest.json` hash file). Personal tuning libraries support YAML or JSON (both), **YAML recommended**.

Personal library (never committed, never leaves the machine unless uploaded):

```
data/learn/private/
├── rules/                       # user's tuned rules (incl. customer-tier, personal habits)
└── stats/                       # user-local aggregates
```

## 3. Upload Trigger, Export & Branch Rules (text mode)

### 3.1 Trigger

User says **"上传数据" / "重新上传" / "提交数据"** (or English equivalents: *"upload my data" / "re-submit" / "submit my library"*) — or the weekly reminder fires. Always **manual, user-confirmed** (OQ-LS2): nothing auto-pushes.

### 3.2 Export — date + user ID

- **User identity**: a **unique machine code / user id** (唯一机器码), sanitized to `[a-zA-Z0-9_-]` (e.g. `AX-3f8a-c2d1`). This is the `contributor` everywhere.
- **Bundle location**: `learn_inbox/<machine-id>/<yyyymmdd>/bundle.yaml` — **date and user id are in the path**; provenance (contributor, timestamps, observation counts) is inside the bundle.
- **"重新上传" (re-upload)**: creates a *new* dated directory `.../<yyyymmdd>/` on the same user branch; the previous pending upload of that user is flagged stale during review (no silent overwrite).
- Post-upload: the personal library stays local (upload is a copy).

### 3.3 Branch rules (text data repo)

The data repo behind `store/` is **separate from the Axiara code repo**. It follows its own branch rules (protected, PR-only — mirrors AGENTS.md):

| Branch | Purpose | Writable by | Content |
| --- | --- | --- | --- |
| `main` | **Stable public library** — protected | Admin only (via PR, after review) | `learn_shared/` rules + manifest |
| `user/<machine-id>` | **Per-user upload branch** — one per user | That user only | `learn_inbox/<machine-id>/<yyyymmdd>/` bundles |
| `review/<yyyymmdd>` (optional) | Training-Agent proposals staging | Training Agent | proposals → PR into `main` |

Rules:
1. **Users never push to `main`** — it is protected; only admin merges after review (PR-only, same convention as the code repo).
2. **One branch per user**: `user/<machine-id>` — the user's only write point. Zero cross-user conflicts, natural isolation, full per-user audit.
3. Upload commit message convention: `upload <machine-id> <yyyymmdd> [re-upload]`.
4. Re-upload lands as a new dated directory on the same user branch; the review step marks the earlier pending dir stale.
5. `main` updates happen **only via review PR**: training Agent aggregates `user/*` → proposals → admin confirms → merge into `main`.
6. Users pull `main` read-only; their local overrides always win.

Flow:

```
user: "上传数据" ──▶ export bundle (machine-id + yyyymmdd)
      ──▶ commit+push → user/<machine-id>/learn_inbox/<machine-id>/<yyyymmdd>/bundle.yaml
      ──▶ training Agent aggregates user/* branches ──▶ proposals (review/<date>)
      ──▶ admin confirms ──▶ PR merge into main (learn_shared/ + manifest)
      ──▶ users pull main (read-only)
```

## 4. Central Review Flow (text mode)

1. **Ingest** — training Agent reads new `learn_inbox/<machine-id>/<date>/` bundles from all `user/*` branches, validates YAML + schema, ledger entry.
2. **Compare** — match bundle rules against `learn_shared/rules/*.yaml`:
   - same `rule_id` → version/trust comparison
   - new keys → new-rule candidates
   - contradicting official baseline (`data/main/`) → reject candidate
3. **Propose** — write a change list `learn_inbox/_reviews/<date>/proposals.yaml`:
   `ADD` / `UPDATE` (with diff) / `REJECT` (with reason).
4. **Confirm** — admin (designated reviewer) accepts/rejects each proposal (CLI or chat).
5. **Apply** — accepted proposals update `learn_shared/rules/*.yaml`; regenerate `stats/` (rebuildable, idempotent); update `manifest.json`; commit + push; ledger entry.
6. **Pull back** — users pull on next sync (read-only merge; personal overrides stay local).

## 5. Rule Format, Versioning & Conflicts (text mode)

```yaml
# store/learn_shared/rules/process-cost.yaml
- rule_id: pc-0042
  kind: process_cost
  key: { material: copper-wire, process: cutting }
  value: { unit_fee: 0.35, loss_rate: 0.03, yield: 0.97, unit: CNY }
  trust: stats            # user_rule > stats > llm
  contributor: alice
  version: 3
  updated_at: 2026-08-05T14:00:00Z
  supersedes: [pc-0038]
```

- Same `rule_id` → higher `version` wins (decided at review time, not by git).
- Different contributors, same material → **both kept** in the proposal list, flagged "pending team review" — never silently dropped.
- `user_rule` trust beats `stats`/`llm` regardless of version.
- Deletes are **tombstones** (`superseded_by: DELETED-<ts>`) — prevents stale replicas resurrecting removed rules.
- **Stats are never merged** — always rebuilt from the authoritative merged `clean/` set.
- Git conflict on `learn_shared` files is prevented by the review gate (only one writer: the reviewer step); if it happens anyway (e.g. two admins), resolve at review time keeping the higher-version rule.

## 6. Security & Privacy (text mode)

- `learn_private` never enters git; upload bundles are the only thing that leaves the machine.
- Upload scope excludes customer-specific entries by default.
- `learn_shared` contains price tiers / cost rules only — no credentials, no `local_config` items.
- Git history of the central repo IS the audit trail; every apply is a commit.
- No secrets in `bundle.yaml` (validation rejects any credential-like content).

## 7. Concurrency & Scale

- Uploads are isolated per user directory → few git conflicts in `learn_inbox`.
- `learn_shared` writes are serialized through the single review step → no concurrent writers.
- Works fine up to dozens of users; beyond that, teams should consider the SQL variant (`docs/learn-sync-sql.md`).

## 8. Reusable Assets

- `skills/csv-data-import/scripts/validate_csv.py` → basis for bundle schema validation.
- Storage layer (`development-handoff.md` Batch 1) provides CSV/JSON/YAML + manifest primitives.
- `skills/price-crawler/config/normalization.yaml` → shared alias dictionary.

## 9. Acceptance for Batch 4 (hub implementation)

- Weekly upload flow produces a valid `bundle.yaml` in `learn_inbox/<user>/<date>/` after user confirmation.
- Review gate: a proposal list is generated; a rejected proposal never reaches `learn_shared/`.
- Apply updates rules + manifest + git history; a pull-back merges read-only with local overrides winning.

## 10. Open Questions

- **OQ-LT1** — Inbox retention: keep upload bundles forever (audit) vs prune after review (keep summary)? Recommend: keep (cheap text, full audit).
- **OQ-LT2** — Manifest scope: SHA-256 over `learn_shared/` only, or also `learn_inbox/`? Recommend: shared only (inbox is git-versioned anyway).
