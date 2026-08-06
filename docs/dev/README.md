# Axiara — Developer Documentation

> **Audience**: developer-facing documentation, distinct from the
> user-facing README/docs. It lives alongside the user docs in the repo and
> ships with both `dev` and `main` — developers read it, users never need to.

This is the single entry point for developers working on the Axiara codebase:
architecture, environment setup, coding conventions, the visual identity
(VI) system for diagrams, and the recommended workflow for shipping changes.

---

## Index

| Doc | Purpose |
| --- | --- |
| [`docs/dev/README.md`](README.md) | This index + dev environment setup, repo layout, workflow, conventions |
| [`docs/dev/VI-GUIDE.md`](VI-GUIDE.md) | Visual identity system: palette, diagram style, typography, SVG specs |
| [`docs/dev/DEV-AGENT.md`](DEV-AGENT.md) | Drop-in agent prompt for a *developer* agent working on this codebase |

---

## Tech stack (one line each)

| Layer | Choice | Where |
| --- | --- | --- |
| Language | Python 3.12 (>=3.12) | `src/axiara/` |
| Package / env | [uv](https://docs.astral.sh/uv/) (`uv sync`, `uv run`) | `pyproject.toml`, `uv.lock` |
| API | FastAPI | `src/axiara/api/` |
| Agents | LangGraph | `src/axiara/agents/` |
| Scheduler | APScheduler (on-demand) | `src/axiara/scheduler.py` |
| Storage | Personal SQLite · Team CSV+git (SQLite cache) · SQL server | `src/axiara/core/storage/` |
| Tests | pytest + pytest-asyncio | `tests/` |
| Lint | ruff | `pyproject.toml [tool.ruff]` |

## Dev environment setup

```bash
# 1. Install deps + dev group
uv sync --dev

# 2. Bootstrap runtime dirs & local config (safe for agents/CI, never prompts)
bash scripts/init-data.sh --language en --sync-mode none --backend sqlite --data-source none

# 3. Run tests
uv run pytest            # full suite (currently 206 tests)
uv run pytest -q         # quiet
```

> Note: `uv run` performs a build each time; `python -m pytest` against an
> already-`uv sync`-ed `.venv` is faster for iteration:
> `.venv/Scripts/python.exe -m pytest tests/ -q` (Windows) /
> `.venv/bin/python -m pytest tests/ -q` (POSIX).

### Environment troubleshooting (Windows)

- **pytest KeyboardInterrupt at startup** — the `langsmith` pytest plugin
  (entry point `langsmith_plugin`) probes the LangSmith service at load time.
  It is disabled project-wide via `addopts = "-p no:langsmith_plugin"` in
  `pyproject.toml`. If you ever re-enable it, use the *entry-point* name, not
  the package name.
- **SQLite WAL hangs** — `PRAGMA journal_mode=WAL` permanently blocks on some
  Windows builds; the code intentionally does not enable WAL. If you revisit
  it, gate it behind a config flag and test on Windows first.

## Repo layout (what's where)

```
src/axiara/
  api/            FastAPI app (main.py), routers, DTOs
  agents/         LangGraph graphs & nodes (archive/query/quote/review), state
  core/
    costing/      multi-dimensional cost model
    quote/        quotation generator (default + user templates)
    storage/      permissions (DataLayer), manifest/checksum, SQLite cache
    pricefetch/   crawler engine (robots protocol, confirm gate)
  scheduler.py    APScheduler wiring
tests/            pytest suite (mirrors src/axiara/ layout)
scripts/          init-data.sh, helper scripts
assets/           SVG diagrams & logo (see VI-GUIDE.md)
docs/dev/   THIS directory — developer docs (README.md, VI-GUIDE.md, DEV-AGENT.md)
```

## Workflow & conventions

1. **Branching**: cut a feature branch from `dev` — never `main`. Open a PR
   into `dev`. `main` receives releases only.
2. **Commit hygiene**: one logical change per commit; reference the PR scope
   in the message. Prefer conventional prefixes: `fix(scope):`, `feat:`,
   `docs:`, `ci:`, `refactor:`.
3. **Docs discipline (hard rule)**: any change that affects user-facing
   behavior must update `README.md` (+ the 9 locale files), `CHANGELOG.md`
   (`[Unreleased]` entry per PR), and any affected `docs/*.md` **before**
   push. Track pending sync work in `.workbuddy/doc-sync-todo.md`.
4. **Tests**: keep `pytest` green. CI runs ruff (advisory until a cleanup PR
   lands) and the full suite on every push/PR to `dev`.
5. **VI compliance**: any new/changed diagram must follow
   `docs/dev/VI-GUIDE.md` (palette, font scale, 1280px width, dark
   variants).

## Adding a diagram (quick checklist)

1. Draft the SVG with the palette + font scale from `VI-GUIDE.md`, width
   `1280px`.
2. Generate the dark variant from the light one (placeholder two-phase
   color swap — see VI-GUIDE §Dark variants).
3. Validate: XML parses, all `<text>` inside its container `<rect>`
   (programmatic check), no overlapping rects.
4. Reference it in the README(s) with `<picture>` + `prefers-color-scheme`
   (matching `assets/axiara-architecture.svg` pattern) — all locale READMEs
   reuse the English diagram.
5. Commit `assets/*.svg` (+ `-dark.svg`), sync docs, PR into `dev`.

## Related (user-facing)

- `AGENTS.md` — operating manual for the *workspace agent* (what agents
  working *inside* a user's Axiara workspace must do).
- `docs/init.md` — onboarding flow. `docs/business-modes.md` — the four
  modes & permission model. `PLAN.md` — roadmap & batches.
