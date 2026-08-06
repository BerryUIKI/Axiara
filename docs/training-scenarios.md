# Axiara — User Training Scenarios (learn_db)

Status: **v0.1** (2026-08-05) — product-side companion to `docs/learning-plan.md`. This document imagines how real users actually "train" Axiara, so the learning engine's features, interaction design and phase priorities follow from real situations — not from a data-science wishlist.

Core insight: **users rarely "train" on purpose.** Training happens inside everyday business actions — importing a price list, quoting, having the boss correct a price, winning/losing a deal. The system learns in the background; explicit training is just one mode. Every scenario below maps to: trigger → data involved → learning mechanism → user interaction → quality gate.

---

## 1. Scenario Dimensions

Four axes, one scenario per cell combination that matters:

| Axis | Values |
| --- | --- |
| **U — User profile** | Solo owner · Small team (salesperson + boss approves) · Larger org (procurement/sales/finance) |
| **D — Data maturity** | Zero-data (new install) · Bulk legacy (stored quotes/invoices) · Running operation (daily quotes) |
| **B — Business situation** | New product · Repeat product · Material price volatility · Customer bargaining · Bidding · Rush order |
| **I — Interaction** | Explicit import · Implicit feedback loop · Rule review · Training report · User teaches directly |

## 2. Scenario Catalog

### S1 — First launch, zero data — create vs join (U: any, D: zero, B: new, I: import)

New user installs Axiara, has no history. Onboarding now offers two paths (`docs/workspace-config.md`):

- **Create** — guided: everything pre-filled from inference (currency by language, timezone by OS, date/quote formats), user confirms or edits; core questions (sync mode / backend / data source) asked as today. `learn_db` starts empty and **says so**: quoting works off `data/main/` + market reference; learning begins after the first approved/corrected quote. No fake confidence, no empty-statistics tables.
- **Join** — user provides the team repo URL → team template applied → `learn_shared` pulled ("synced N shared rules, M pending review") → near-zero Q&A.

- Trigger: onboarding complete with `data_source: local_file|none` (create) or team repo URL (join).
- Interaction: review pre-filled settings list (keep/change) on create; one-line sync summary on join.
- Priority: P0 (sets expectations, prevents distrust).

### S2 — Bulk legacy training (U: any, D: bulk, B: any, I: import)

User has years of quotes/invoices/cost sheets. They hand files to the agent: "train from these". One flow: land → validate (SK-02) → clean → L1 stats → **training report** (n samples, n rules, holdout backtest MAE) → user confirms rules → `data/learn/` populated.

- Trigger: "train from these files".
- Interaction: review the training report; confirm/decline rule batches; see which materials get tiers.
- Priority: **P0** — the fastest way to make the workspace useful.

### S3 — Boss-corrects-salesperson (U: small team, D: running, B: repeat, I: implicit)

The highest-signal everyday loop. Salesperson drafts a quote → boss edits the price before approving → the diff is recorded as a `correction` (S2 in learning-plan) → **double-weight** into stats → periodically Axiara reports "you typically mark up material X by ~Y% — want this as a default tier?".

- Trigger: quote approved with edits vs. draft.
- Interaction: none at the moment of learning; surfaced later in training report / tier proposal.
- Priority: **P0** — no extra user effort, huge calibration value.

### S4 — New product, no history (U: any, D: any, B: new, I: implicit + review)

Quote request for a material with no stats entry. Axiara falls back to **L2 similar-material matching** + market reference, outputs a reference window with a visible "insufficient data" tag, and after the deal the final price becomes that material's first sample.

- Trigger: query with no `(material, process)` stats hit.
- Interaction: user sees reference range + confidence; accepts or overrides.
- Priority: P1.

### S5 — Repeat product, quick quote (U: any, D: running, B: repeat, I: implicit)

Stats hit + official price → instant low/mid/high tiers (Mode 3.2). User tweaks the final number → tweak is also a learning signal (small weight).

- Trigger: quoting a material with ≥N observations.
- Interaction: three-tier proposal, adjust, approve.
- Priority: P1.

### S6 — Material price volatility (U: any, D: running, B: volatility, I: report)

Crawler refreshes market prices; learned reference windows move but **rules never auto-change**. If a material's market window drifts > threshold from learned tiers, Axiara prompts: "market moved X% — re-evaluate tiers?" Re-evaluation still requires confirmation.

- Trigger: weekly refresh (D-SK2) detects drift vs learned tiers.
- Interaction: prompted review, no silent updates.
- Priority: P2.

### S7 — Customer/channel bargaining (U: small/large, D: running, B: bargaining, I: implicit)

Same material, different final prices per customer → Axiara learns **customer-tier markup elasticity** (rule dimension `customer_tier`). E.g. key accounts −3%, spot buyers +5%.

- Trigger: enough price observations grouped by customer.
- Interaction: proposed tier-per-customer in training report; user confirms.
- Priority: P2 (needs volume).

### S8 — Volume discounts & rush fees (U: any, D: running, B: bidding/rush, I: implicit)

From order history: quantity discounts and rush-order surcharges become process-cost rule extensions (`quantity_discount`, `rush_fee`).

- Trigger: invoice/order rows with quantity and due-date urgency.
- Interaction: rules proposed for review (S10 flow).
- Priority: P2.

### S9 — Bidding, fast tiers (U: any, D: running, B: bidding, I: implicit)

One-click low/mid/high + historical win-range for similar jobs. Default constraints are **proposed, never silently applied** (Mode 3.2 asks first).

- Trigger: user requests quote without constraints.
- Interaction: tier picker backed by learned defaults.
- Priority: P1.

### S10 — Rule review & correction (U: any, D: any, B: any, I: review)

LLM-proposed rules (aliases, process costs, markups) land in a review queue: **confirm / reject / modify**. A rejection reason is recorded and becomes a signal too ("alias wrong", "process outdated").

- Trigger: L3 extraction produced new rules; or S3/S8 proposals.
- Interaction: review list — this is the main human gate for learn_db.
- Priority: P1 (design the UI once, reuse everywhere).

### S11 — Drift alert & retrain (U: any, D: running, B: any, I: report)

Learned suggestions systematically deviate from newly approved quotes → "retrain suggested". One-click retrain (idempotent, rebuildable) → before/after report.

- Trigger: drift monitor (learning-plan §6).
- Interaction: alert + one-click retrain + comparison report.
- Priority: P2.

### S12 — User teaches directly (U: any, D: any, B: any, I: teach)

Power users edit rules by hand ("copper = LME + processing fee"). Accepted edits are marked `user_rule` (highest trust tier, wins over stats) and versioned.

- Trigger: user edits a rule file / says "teach Axiara that X costs Y".
- Interaction: rule editor with history.
- Priority: P1 — builds trust and correctness fast.

### S13 — Team shared learning (U: small team, D: running, B: any, I: implicit + review)

Multiple members learn in parallel. New rules pass through a **shared/private splitter** (`docs/learn-sync.md`): generic material/process/pricing rules → `learn_shared` (team, git/sql synced); customer/person-dimensioned insights → `learn_private` (local only). Conflicting team rules surface in the S10 review queue as "pending team review", never silently dropped. New joiners get a sync summary.

- Trigger: any ingestion while team sync is on (git/sql); a join/startup pull.
- Interaction: pending-review queue (S10); "synced N shared rules" on join.
- Priority: P1 — depends on the feedback loop (Phase 4) + shared/private splitter.

### S13 — Personal library → weekly upload → central review (U: small team, D: running, B: any, I: implicit + review)

Every user's Axiara tunes its own library (approved/corrected quotes, personal markup habits) during conversations. Weekly, the user uploads their library to the central library (manual, confirmed); the **central training Agent** reviews it and proposes changes to the shared public library (`learn_shared`); an admin confirms; public updates pull back to all users (personal overrides stay local). See `docs/learn-sync.md` (hub model).

- Trigger: weekly upload reminder (or on-demand); central review on arrival.
- Interaction: user sees upload confirmation + later "2 accepted / 1 rejected (reason)"; review queue (S10) carries proposals.
- Priority: P1 — ships with Phase 4 (feedback loop + upload flow).

## 3. Scenario → Feature Mapping

| Feature | Scenarios | Phase (learning-plan) | Owner |
| --- | --- | --- | --- |
| F1 Import + one-click bulk training + training report | S1, S2 | Phase 0–1 | WorkBuddy (flow) + coding agent (pipeline) |
| F2 Quote-approval feedback loop (incl. boss edits) | S3, S5 | Phase 4 (prioritize S3) | Coding agent |
| F3 Similar-material fallback + "insufficient data" tag | S4 | Phase 2 | Coding agent |
| F4 Three-tier defaults + constraint proposal | S5, S9 | quote generator | Coding agent |
| F5 Rule review queue (confirm/reject/modify + reasons) | S10, S8, S12 | Phase 3 | WorkBuddy (workflow) + coding agent (UI/helpers) |
| F6 Volatility prompt on market drift | S6 | Phase 5 | Coding agent |
| F7 Dimensioned rules (customer tier, volume, rush) | S7, S8 | Phase 3 | Coding agent |
| F8 Drift alert + one-click retrain + reports | S11 | Phase 5 | Coding agent |
| F9 Personal library + weekly upload + central review (hub) | S3, S10, S13 | Phase 4 (hub) | Coding agent |

## 4. Impact on the Learning Plan

- **Phase 4 (feedback loop) moves up in priority** — S3 (boss-corrects) is the cheapest, highest-value training signal; it should ship right after Phase 1, before L2/L3.
- **Phase 3 splits**: rule-review queue (F5) is a prerequisite for L3 extraction; dimensioned rules (F7) can ride on the same review flow.
- **S1 expectations banner** belongs in the SK-01 onboarding skill — empty learn_db should be explicit, not silent.
- Training report is a first-class deliverable in every phase (users confirm based on reports, not on trust).

## 5. Open Questions

- **OQ-S1** — Does the user's own business match the "small team, boss approves" profile (S3 as the anchor scenario), or solo (S1/S12 as anchors)? Determines what ships first.
- **OQ-S2** — Which customer/volume/rush dimensions exist in the user's real data (S7/S8)? Confirmed by a sample of their historical files.
- **OQ-S3 — RESOLVED (2026-08-05)**: training report appears **in chat AND as an `output/` file** (user decision).
