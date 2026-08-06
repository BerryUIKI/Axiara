# Contributing to Axiara

Thanks for your interest! Axiara follows a PR-only workflow — **never push
directly to `main` or `dev`**.

## Before you start

- Read [PLAN.md](PLAN.md) for the roadmap and current batch — fit your work into it.
- Read the **[developer documentation](docs/developer/README.md)** for the
  full picture: environment setup, repo layout, coding conventions, the
  visual identity (VI) spec for diagrams, and the recommended workflow.
- Check [CHANGELOG.md](CHANGELOG.md) — every PR into `dev` must add an entry
  under `[Unreleased]`.

## Quick rules

| Do | Don't |
| --- | --- |
| Cut a feature branch from `dev`, open a PR into `dev` | Never push directly to `main` / `dev` |
| Keep `pytest` green (`uv run pytest`) | Never merge with failing tests |
| Update docs before push (README + locales + CHANGELOG + affected `docs/*`) | Never push without syncing documentation |
| Follow the VI spec when touching diagrams (`docs/developer/VI-GUIDE.md`) | Never introduce new palette colors or font sizes |
| Update developer docs (`docs/developer/`) when behavior/VI changes | Never leave docs stale |

## Development quickstart

```bash
uv sync --dev
bash scripts/init-data.sh --language en --sync-mode none --backend sqlite --data-source none
uv run pytest          # full suite
uv run ruff check src/ tests/   # lint
```

See [docs/developer/README.md](docs/developer/README.md) for details and
Windows-specific troubleshooting.
