# Axiara — Multi-User Learning Data Sync (hub model)

Status: **v0.2** (2026-08-05) — redesigned per user decision (D-SK7): each user maintains their **own personalized library** (专属调教库), uploads it **weekly** to a central library, and the **central training Agent reviews** whether the core shared library should change. Supersedes the v0.1 direct-sync model. Pairs with `docs/learning-plan.md`, `docs/workspace-config.md`.

> **Two implementation variants, by user storage mode:**
> - Text format (team · text+git, no server): **`docs/learn-sync-text.md`**
> - Database format (team · SQL server: MySQL / MariaDB / PostgreSQL): **`docs/learn-sync-sql.md`**
> Both share this hub model; only the physical storage differs.
>
> **Format principle (D-SK8, 2026-08-05):** learned-data files are **AI-friendly first**. YAML is the preferred format for anything read or reviewed by humans/agents (comments, readable diffs); JSON is reserved for machine-only exchange and DB-query needs. Personal tuning libraries and upload bundles support both — **YAML recommended**.

## 1. The Model (hub-and-spoke with central review)

```
user A learn_private ─┐
user B learn_private ─┼── weekly upload (manual, user-triggered) ──▶ CENTRAL LIBRARY
user C learn_private ─┘                                                    │
                                                           central training Agent
                                                           reviews & proposes      ──▶ admin confirms ──▶ learn_shared (public) updated
                                                                                                          │
                                                                                    users pull updates (read-only merge)
```

- **Spokes**: every user's `learn_private` — their own tuned data (quotes, corrections, customer/personal rules). Lives locally, never auto-shared.
- **Weekly upload**: the user (or their Agent, on explicit request) uploads their library to the central library's inbox. **Manual, human-triggered** — nothing auto-pushes (OQ-LS2 resolved: manual).
- **Central training Agent**: examines uploaded data, compares against the public library, and produces **change proposals** (new rules / updates / rejections with reasons).
- **Admin confirmation**: proposals are confirmed before the **public library (`learn_shared`)** is updated. Public updates are then pulled back by users (read-only merge; personal overrides stay local).

## 2. Two Libraries

| Library | Content | Where | Written by |
| --- | --- | --- | --- |
| **`learn_private`** (personal) | User's tuned data: approved/corrected quotes, personal markup habits, customer-tier rules, notes | Local (`.data/learn/private/`) | The user's own Axiara (background learning) |
| **`learn_shared`** (public) | Core rules: material normalization, process-cost, cost-breakdown, pricing tiers | Central library (git `store/` or SQL) | **Only via central training Agent review + admin confirmation** |

Rule of thumb: personal/customer-specific → private; generic material/process/pricing facts → candidate for public (only after central review).

## 3. Weekly Upload Protocol

- Trigger: user says "upload my library" / scheduled reminder (weekly) — **always user-confirmed, never automatic**.
- Payload: incremental bundle of `learn_private` (YAML rules + provenance metadata: contributor, timestamps, observation counts). No credentials, no `local_config` items.
- Scope option: full private library, or only generic rules (customer-specific entries can be excluded — user choice).
- Destination: central library inbox (`<central>/inbox/<user>/<yyyy-mm-dd>/`).
- After upload: the user's library stays local; upload is a copy, not a move.

## 4. Central Training Agent Review Flow

1. **Ingest** — validate bundle, update ledger.
2. **Compare** — match against existing `learn_shared` (same rule_id → version/trust comparison; new keys → new-rule candidates).
3. **Propose** — output a change list: `ADD` / `UPDATE` (with diff) / `REJECT` (with reason, e.g. insufficient observations, contradicts official baseline).
4. **Confirm** — admin (or designated reviewer) approves/rejects each proposal.
5. **Apply** — approved changes update `learn_shared`; ledger + git history record everything.
6. **Pull back** — users get the public updates on their next pull (read-only merge; their private overrides remain untouched).

## 5. Rule Format, Versioning & Conflicts (unchanged core)

```yaml
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

- Same `rule_id` → higher `version` wins (at central review time).
- Different contributors, same material → both proposals kept, **pending team review** (S10 queue) — never silently dropped.
- `user_rule` trust wins over `stats`/`llm` regardless of version.
- Deletes are tombstones; stats are never merged — rebuilt from the merged authoritative `clean/` set.
- Conflicts surface in the **proposal list** (central review), not silently.

## 6. Security & Privacy

- `learn_private` never leaves the machine unless the user explicitly uploads it.
- Upload scope can exclude customer-specific entries (privacy of client relationships).
- `learn_shared` contains price tiers/cost rules only — no credentials, no `local_config`.
- Every review decision (accept/reject) and every apply is ledgered + in git history.

## 7. User Experience

- User sees: "weekly upload ready — N new rules since last upload?" → confirms → upload → later "2 of your rules accepted into the public library, 1 rejected (reason)".
- Public library changes arrive as pull updates; personal overrides always win locally.

## 8. Impact on Other Docs

- `learning-plan.md` §8 Phase 4: route new rules into `learn_private`; weekly upload is a separate scheduled-but-manual step; central review is a **new capability** (central training Agent — a distinct role, likely a coding-agent-built LangGraph flow + admin UI).
- `training-scenarios.md` S13: updated to the hub model (see update).
- `docs/workspace-config.md` §5: join flow pulls `learn_shared` (public), not personal data.

## 9. Open Questions

- **OQ-LS1** — Central library location: same git repo (`store/`) vs separate `axiara-learn` repo? Recommend inside `store/` (one clone) with `inbox/` + `learn_shared/` subdirs.
- **OQ-LS4** — Who is "admin" for proposal confirmation? Team owner / designated reviewer / the central training Agent's proposals auto-approved for `trust: user_rule`? Recommend: all proposals confirmed by a human reviewer.
- **OQ-LS5** — Upload cadence: strictly weekly, or on-demand anytime (weekly is the default reminder, manual anytime)? Recommend: on-demand allowed, weekly reminder default.
