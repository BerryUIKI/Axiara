<p align="center">
  <img src="assets/axiara-logo.svg" alt="Axiara" width="120" />
</p>

<h1 align="center">Axiara — Agent Quotation Core</h1>

<p align="center">
  <strong>Multi-agent valuation core</strong> — automated cost calculation and real-time market price intelligence, built on LangGraph.
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/python-3.12-blue" alt="Python 3.12" /></a>
  <a href="#"><img src="https://img.shields.io/badge/framework-LangGraph-purple" alt="LangGraph" /></a>
  <a href="#"><img src="https://img.shields.io/badge/api-FastAPI-teal" alt="FastAPI" /></a>
  <a href="#"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT" /></a>
</p>

---

**Read this in:** [English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja-JP.md) · [한국어](README.ko-KR.md) · [Français](README.fr-FR.md) · [Deutsch](README.de-DE.md) · [Español](README.es-ES.md) · [Português](README.pt-BR.md) · [Русский](README.ru-RU.md)

---

Axiara is an **agent workspace for valuation**. It gives AI agents four well-defined capabilities — *archive*, *query*, *batch quote*, and *review* — over three isolated data layers with strict write permissions, so automated agents can never corrupt the official price baseline.

> **Design philosophy:** Axiara is not a fixed workflow app. Agents work autonomously inside the workspace and decide which data and skills to call. The four modes are *capability and permission boundaries*, not hard-coded UI flows.

## ✨ Key Features

- **🔒 Three-layer data isolation** — official price baseline (`main_db`) is write-protected: only manual edits can modify it; crawler and AI-learned outputs can never overwrite it.
- **🤖 Autonomous agent workspace** — built on LangGraph: agents choose which data and skills to invoke per task.
- **📦 Archive (Mode 1)** — manual official price entry (versioned, rollback-able) + AI learning from historical documents + on-demand market price crawling.
- **🔍 Query (Mode 2)** — single-item lookup: official cost + market price range + process notes.
- **📊 Batch quote (Mode 3)** — Excel/BOM backfill with auto column detection, plus smart quotation with constraint negotiation (default + project constraints; three-tier low/mid/high options when none given).
- **✅ Review (Mode 4)** — cross-validate user quote tables against the official baseline and market data; flag anomalies and suggest adjustments.
- **🧩 Template-adaptive quoting** — ships a default quote template, adapts on the fly to user-provided templates (open-source / fork-friendly).
- **💾 Pluggable storage** — SQLite / PostgreSQL / MongoDB backends, plus CSV import/export.
- **🕐 On-demand crawling** — market data refreshes when you ask, not on a blind schedule.

## 🏗️ Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │                  Axiara                     │
                    │         AgentWorkspace (LangGraph)          │
                    └─────────────────────────────────────────────┘
                                     │
                ┌────────────────────┼────────────────────┐
                ▼                    ▼                    ▼
         ┌───────────┐        ┌───────────┐        ┌───────────┐
         │  main_db  │        │ learn_db  │        │ market_db │
         │  Official │        │  Learned  │        │  Crawled  │
         │  Baseline │        │ Reference │        │   Prices  │
         │ (manual   │        │ (AI       │        │ (crawler  │
         │  edit     │        │  training)│        │  + confirm│
         │  ONLY)    │        │           │        │   before  │
         └───────────┘        └───────────┘        │   insert) │
                                                   └───────────┘
```

## 🧰 Tech Stack

| Layer | Choice |
| --- | --- |
| Language | Python 3.12 |
| API Framework | FastAPI |
| Agent Framework | LangGraph |
| Scheduler | APScheduler (reserved) |
| Dependency Management | [uv](https://docs.astral.sh/uv/) |
| Storage | SQLite / PostgreSQL / MongoDB (pluggable) + CSV |

## 🚀 Quick Start

> Project scaffolding in progress — commands below are the target experience.

```bash
# Install dependencies
uv sync

# Run the workspace (interactive agent shell)
uv run axiara

# Start the REST API
uv run uvicorn axiara.api.main:app --reload
```

## 📁 Repository Layout

```
Axiara/
├── agents/          # Agent definitions (LangGraph graphs)
├── data/            # Data layers
│   ├── main/        #   official price baseline (manual-edit only)
│   ├── learn/       #   learned reference
│   ├── market/      #   crawled market prices
│   └── uploads/     #   user-provided tables / documents
├── skills/          # Agent skill packs (archive/query/quote/review)
├── output/          # Generated deliverables (quotes, review reports)
├── docs/            # Design & architecture docs
└── src/             # Core library
```

## 📚 Documentation

- [Business Modes & Architecture](docs/business-modes.md) — data permission model, four modes, LangGraph mapping
- [PLAN.md](PLAN.md) — single source of truth for the roadmap

## 🗺️ Roadmap

- [x] Workspace initialization & design decisions
- [ ] Package scaffolding (`uv init`, `src/` layout)
- [ ] Storage layer (pluggable backends + CSV)
- [ ] Costing engine (multi-dimensional cost model)
- [ ] Price fetch agent (LangGraph crawl + normalize)
- [ ] Task scheduler (APScheduler, on-demand)
- [ ] Quotation generator (default + user templates)
- [ ] Review engine (anomaly detection)
- [ ] REST API
- [ ] Tests & CI

## 🤝 Contributing

Contributions are welcome. Please read [PLAN.md](PLAN.md) first, and follow the PR-only workflow: **never push directly to `main`**.

## 📄 License

MIT — see [LICENSE](LICENSE).

---

*Built with LangGraph. Front-end dashboard (`Axiara-Web`) is planned as a separate repository.*
