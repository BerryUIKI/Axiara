<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/axiara-lockup-dark.svg" />
    <img src="assets/axiara-lockup.svg" alt="Axiara" width="320" />
  </picture>
</p>

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
- **💾 Storage for any setup — no servers needed** — personal: SQLite; team: CSV files synced via git (`store/`, with an auto local SQLite cache for fast queries), or SQL server (MySQL / MariaDB / PostgreSQL).
- **🕐 On-demand crawling** — market data refreshes when you ask, not on a blind schedule.

## 🚀 Start here — no tech skills needed

You don't need to read code, touch a terminal, or understand anything technical. Pick whichever way is easier.

> 💡 Tip: first create a folder named **axiara-workspace** (on your Desktop or in Documents) and keep all Axiara-related files inside it, so nothing gets misplaced.

### Way 1 — hand the link to your AI agents (easiest)
> 💡 Prerequisite: this way needs **Git** installed (free — [download it here](https://git-scm.com/downloads)). If you'd rather not install Git, use **Way 2** below.

Copy the text in the code block and paste it into your AI assistant (Claude, ChatGPT, Copilot, Gemini, ...):

```text
Set up Axiara for me:
1. Clone the repo via git clone https://github.com/BerryUIKI/Axiara.git, then read AGENTS.md and strictly follow the setup flow in docs/init.md — walk me through the setup in English (storage, data source).
2. When it's ready, tell me what I can ask you to do.
```

Then just answer the questions it asks — that's it.

### Way 2 — download the files, then use your AI agents
1. Download the latest archive from the [Releases page](https://github.com/BerryUIKI/Axiara/releases) (or click the green **Code** button → **Download ZIP**) and unzip it into the axiara-workspace folder suggested above.
2. Open that folder in your AI assistant and say: *"Set up this project and guide me through the setup."*
3. Answer its questions — done.

### Check for updates
Want to know if there's a new version? Send this to your AI assistant:

```text
Check if Axiara has a new version: https://github.com/BerryUIKI/Axiara
If there is one, update me to the latest version (keep my existing data, don't wipe the .data directory).
```

Either way, once setup finishes you can start with something like: *"Make me a quotation for [item]."* — the agent does the rest.

## 🏗️ Architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/axiara-architecture-dark.svg" />
  <img src="assets/axiara-architecture.svg" alt="Axiara architecture" width="680" />
</picture>

## 🧰 Tech Stack

| Layer | Choice |
| --- | --- |
| Language | Python 3.12 |
| API Framework | FastAPI |
| Agent Framework | LangGraph |
| Scheduler | APScheduler (reserved) |
| Dependency Management | [uv](https://docs.astral.sh/uv/) |
| Storage | Personal: SQLite · Team: CSV + git sync (SQLite cache) or SQL server |

## 🧑‍💻 Developer Quick Start

> Project scaffolding in progress — commands below are the target experience.

```bash
# Install dependencies
uv sync

# Bootstrap the runtime data dir (.data/ — store, cache, ledger, db_dump, local_config)
bash scripts/init-data.sh

# Run the workspace (interactive agent shell)
uv run axiara

# Start the REST API
uv run uvicorn axiara.api.main:app --reload
```

### First-time setup (runtime data)

`.data/` is gitignored, so it does not exist right after cloning. Bootstrap it once — or just start the app, which auto-creates it:

```bash
bash scripts/init-data.sh
```

Creates the five runtime dirs and seeds your private config (`.data/local_config/config`, never overwritten); set `data_repo.url` there to sync the team data repo into `store/`. Full guide: [`docs/init.md`](docs/init.md).

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
├── scripts/         # Ops scripts (init-data.sh)
├── .data.template/  # Runtime data skeleton → .data/ (gitignored, see its README)
└── src/             # Core library
```

## 📚 Documentation

- [Business Modes & Architecture](docs/business-modes.md) — data permission model, four modes, LangGraph mapping
- [PLAN.md](PLAN.md) — single source of truth for the roadmap

## 🗺️ Roadmap

- [x] Workspace initialization & design decisions
- [ ] Package scaffolding (`uv init`, `src/` layout)
- [ ] Storage layer (file-first: CSV + git sync, SQLite cache, SQL option)
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

---

> **To AI agents**: If you are setting up this project, read `AGENTS.md` (operating manual) and strictly follow the setup flow in `docs/init.md`, then report back in the user's language.
