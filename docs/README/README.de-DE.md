<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/axiara-lockup-dark.svg" />
    <img src="assets/axiara-lockup.svg" alt="Axiara" width="320" />
  </picture>
</p>

<p align="center">
  <strong>Multi-Agenten-Bewertungskern</strong> — automatisierte Kostenberechnung und Echtzeit-Marktpreis-Intelligence, gebaut mit LangGraph.
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/python-3.12-blue" alt="Python 3.12" /></a>
  <a href="#"><img src="https://img.shields.io/badge/framework-LangGraph-purple" alt="LangGraph" /></a>
  <a href="#"><img src="https://img.shields.io/badge/api-FastAPI-teal" alt="FastAPI" /></a>
  <a href="#"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT" /></a>
  <a href="README.md"><img src="https://img.shields.io/badge/lang-English-blue" alt="English" /></a>
</p>

---

**Lesen Sie dies in:** [English](../README.md) · [简体中文](../README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja-JP.md) · [한국어](README.ko-KR.md) · [Français](README.fr-FR.md) · **Deutsch** · [Español](README.es-ES.md) · [Português](README.pt-BR.md) · [Русский](README.ru-RU.md)

---

Axiara ist ein **Agenten-Arbeitsbereich für Bewertungen**. Es gibt KI-Agenten vier klar definierte Fähigkeiten — *Archivieren*, *Abfragen*, *Massenangebote* und *Prüfen* — auf drei isolierten Datenebenen mit strengen Schreibrechten, sodass automatisierte Agenten die offizielle Preisbasis niemals korrumpieren können.

> **Designphilosophie:** Axiara ist keine App mit festem Ablauf. Agenten arbeiten autonom im Arbeitsbereich und entscheiden selbst, welche Daten und Fähigkeiten sie aufrufen. Die vier Modi sind *Fähigkeits- und Berechtigungsgrenzen*, keine fest codierten UI-Abläufe.

## ✨ Hauptfunktionen

- **🔒 Dreistufige Datenisolation** — die offizielle Preisbasis (`main_db`) ist schreibgeschützt: nur manuelle Bearbeitungen können sie ändern; Crawler- und KI-Ausgaben können sie niemals überschreiben.
- **🤖 Autonomer Agenten-Arbeitsbereich** — basierend auf LangGraph: Agenten wählen selbstständig, welche Daten und Fähigkeiten sie je nach Aufgabe aufrufen.
- **📦 Archivieren (Modus 1)** — manuelle Eingabe offizieller Preise (versioniert, rollbackfähig) + KI-Lernen aus historischen Dokumenten + On-Demand-Crawling von Marktpreisen.
- **🔍 Abfragen (Modus 2)** — Einzelartikel-Abfrage: offizielle Kosten + Marktpreisspanne + Prozessnotizen.
- **📊 Massenangebot (Modus 3)** — Excel/BOM-Befüllung mit automatischer Spaltenerkennung, plus intelligentes Angebot mit Constraint-Verhandlung (Standard + Projekt; drei Optionen niedrig/mittel/hoch, wenn keine angegeben).
- **✅ Prüfen (Modus 4)** — Kreuzvalidierung von Benutzer-Angebotstabellen gegen die offizielle Basis und Marktdaten; Anomalien markieren und Anpassungen vorschlagen.
- **🧩 Vorlagen-adaptives Angebot** — Standard-Angebotsvorlage enthalten, passt sich spontan an benutzerdefinierte Vorlagen an (Open-Source / Fork-freundlich).
- **💾 Plugable Speicherung** — SQLite / PostgreSQL / MongoDB-Backends, plus CSV-Import/-Export.
- **🕐 On-Demand-Crawling** — Marktdaten werden aktualisiert, wenn Sie es anfordern, nicht nach blindem Zeitplan.

## 🚀 Hier starten — keine technischen Kenntnisse nötig

Sie müssen keinen Code lesen, kein Terminal benutzen und nichts Technisches verstehen. Wählen Sie die Methode, die Ihnen leichter fällt.

> 💡 Tipp: Erstellen Sie zuerst einen Ordner namens **axiara-workspace** (auf dem Desktop oder in Dokumenten) und
> legen Sie alle Axiara-bezogenen Dateien in diesem Ordner ab, damit nichts verloren geht.

### Methode 1 — Den Link an Ihre AI Agents geben (am einfachsten)
> 💡 Voraussetzung: Für diese Methode muss **Git** installiert sein (kostenlos — [hier herunterladen](https://git-scm.com/downloads)). Wenn Sie Git nicht installieren möchten, nutzen Sie **Methode 2** unten.

Kopieren Sie den Text im Codeblock und fügen Sie ihn in Ihren KI-Assistenten ein (Claude, ChatGPT, ...) :

```text
Set up Axiara for me: git clone https://github.com/BerryUIKI/Axiara.git
1. Clone the repo via git clone, lesen Sie AGENTS.md und folgen Sie strikt der Einrichtung in docs/init.md — führen Sie mich auf Deutsch durch die Einrichtung (Speicherung, Datenquelle).
2. Wenn es fertig ist, sagen Sie mir, was ich Sie fragen kann.
```

Danach beantworten Sie einfach die Fragen. Das war's.

### Methode 2 — Dateien herunterladen und dann Ihre AI Agents nutzen
1. Laden Sie das neueste Archiv von der [Releases-Seite](https://github.com/BerryUIKI/Axiara/releases) herunter (oder klicken Sie auf den grünen **Code**-Button → **Download ZIP**) und entpacken Sie es in den oben vorgeschlagenen Ordner axiara-workspace.
2. Öffnen Sie den Ordner in Ihrem KI-Assistenten und sagen Sie: *"Richten Sie dieses Projekt ein und führen Sie mich durch die Einrichtung."*
3. Beantworten Sie die Fragen — fertig.

### Nach Updates suchen
Möchten Sie wissen, ob es eine neue Version gibt? Senden Sie dies an Ihren KI-Assistenten:

```text
Prüfen Sie, ob Axiara eine neue Version hat: https://github.com/BerryUIKI/Axiara
Wenn ja, aktualisieren Sie mich auf die neueste Version (behalten Sie meine vorhandenen Daten, löschen Sie nicht das .data-Verzeichnis).
```

Egal welche Methode: Sobald die Einrichtung abgeschlossen ist, können Sie z. B. sagen: *"Erstellen Sie mir ein Angebot für [Artikel]."* — den Rest erledigt der Agent.


## 🏗️ Architektur

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/axiara-architecture-de-DE-dark.svg" />
  <img src="assets/axiara-architecture-de-DE.svg" alt="Axiara architecture" style="max-width: 100%; height: auto; width: 1280px;" />
</picture>

## 🧩 Die vier Modi im Überblick

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/axiara-modes-de-DE-dark.svg" />
  <img src="assets/axiara-modes-de-DE.svg" alt="Axiara modes" style="max-width: 100%; height: auto; width: 1280px;" />
</picture>

## 🧭 Einrichtung — vier schnelle Entscheidungen

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/axiara-setup-decision-de-DE-dark.svg" />
  <img src="assets/axiara-setup-decision-de-DE.svg" alt="Axiara setup" style="max-width: 100%; height: auto; width: 1280px;" />
</picture>

### 💡 Brauchen Sie eine Python-Umgebung? (zuerst lesen)

**In den meisten Fällen nicht.** Axiara ist ein „Arbeitsbereich" für KI-Agenten — Sie geben den Repository-Ordner einfach an Ihren KI-Assistenten (WorkBuddy, Claude usw.) weiter, der Agent übernimmt die Abhängigkeiten automatisch.

Nur wenn Sie **selbst etwas ausführen** (statt es dem Agenten zu überlassen), brauchen Sie eine Python-Umgebung:

| Was Sie tun möchten | .venv nötig? | Vorgehen |
|------------|:---:|--------|
| Dem KI-Agenten überlassen (empfohlen) | ❌ nein | siehe Weg 1 / Weg 2 unten |
| REST-API-Server starten | ✅ ja | `uv sync` dann `uv run uvicorn axiara.api.main:app` |
| Interaktive CLI ausführen | ✅ ja | `uv sync` dann `uv run axiara` |
| Entwicklung / Tests | ✅ ja | `uv sync` dann `uv run pytest` |

## 🧰 Tech-Stack

| Ebene | Wahl |
| --- | --- |
| Sprache | Python 3.12 |
| API-Framework | FastAPI |
| Agenten-Framework | LangGraph |
| Scheduler | APScheduler (reserviert) |
| Abhängigkeitsverwaltung | [uv](https://docs.astral.sh/uv/) |
| Speicherung | Persönlich: SQLite · Team: CSV + git-Sync (SQLite-Cache) oder SQL-Server |

## 🧑‍💻 Schnellstart für Entwickler

> Gerüstbau im Gange — die folgenden Befehle sind die Zielerfahrung.

```bash
# Abhängigkeiten installieren
uv sync

# Arbeitsbereich starten (interaktive Agenten-Shell)
uv run axiara

# REST-API starten
uv run uvicorn axiara.api.main:app --reload
```

## 📁 Repository-Struktur

```
Axiara/
├── AGENTS.md        # Agenten-Betriebshandbuch — Workflow und harte Regeln
├── assets/          # Marken-Assets (Logo, Lockup, Architekturdiagramme — hell/dunkel)
├── docs/            # Design- und Architekturdokumentation (business-modes, init, templates/)
├── scripts/         # Betriebsskripte (init-data.sh)
├── .github/         # CI- und Release-Workflows (auto-release, PR source guard)
├── .data.template/  # Laufzeit-Datengerüst → .data/ (gitignoriert, siehe README)
│
# Geplant — Scaffolding in Arbeit
├── agents/          # Agenten-Definitionen (LangGraph-Graphen)
├── data/            # Datenebenen
│   ├── main/        #   offizielle Preisbasis (nur manuelle Bearbeitung)
│   ├── learn/       #   gelernte Referenz
│   ├── market/      #   gecrawlte Marktpreise
│   └── uploads/     #   vom Benutzer bereitgestellte Tabellen/Dokumente
├── skills/          # Agenten-Fähigkeitspakete (archivieren/abfragen/angebot/prüfen)
├── output/          # Generierte Ergebnisse (Angebote, Prüfberichte)
└── src/             # Kernbibliothek
```

## 🧩 Skills

Agent-Fähigkeitspakete (einzige Quelle in `skills/`, kompatibel mit WorkBuddy/Codex/Claude):

| Skill | Zweck |
| --- | --- |
| **axiara-onboarding** | Workspace-Init (Erstellen/Beitreten) — vorausgefüllte Inferenz (Währung nach Sprache, Zeitzone nach OS), `workspace.config.yaml`-Vorlagen |
| **csv-data-import** | Preislisten validieren + in die offizielle Basis importieren; SHA-256-Manifest, Ledger, Lernpfad |
| **price-crawler** | Rohstoff-Marktpreis-Crawling — Robots-Protokoll, 7-Schritte-Pipeline, Bestätigung vor dem Einfügen |

## 👥 Multi-User-Lernen (Hub-Modell)

Jede Axiara-Instanz lernt aus eigenen Angeboten und Korrekturen in eine **persönliche Bibliothek** (lokal). Das Hochladen erfolgt manuell und mit Benutzerbestätigung: Sage *"Daten hochladen"* / *"erneut hochladen"* / *"Daten einreichen"*, und dein Agent exportiert ein datiertes Bündel in die **zentrale Bibliothek** (`learn_inbox/<user-id>/<yyyymmdd>/bundle.yaml`, gepusht auf deinen eigenen `user/<user-id>`-Branch). Ein **zentraler Trainings-Agent** prüft alle Uploads und schlägt Änderungen an den öffentlichen Regeln vor; ein **Admin bestätigt**, bevor `learn_shared` aktualisiert wird. Dynamisches Skalierungs-Monitoring schlägt Speicher-Upgrades vor, wenn das Team wächst. Siehe [`docs/learn-sync.md`](docs/learn-sync.md).

## 📚 Dokumentation

- [Geschäftsmodelle & Architektur](docs/business-modes.md) — Datenberechtigungsmodell, vier Modi, LangGraph-Mapping
- [PLAN.md](PLAN.md) — Single Source of Truth für die Roadmap
- [docs/init.md](docs/init.md) — Ersteinrichtung, Datenratgeber & Datenintegrität
- [docs/workspace-config.md](docs/workspace-config.md) — Erstellen/Beitreten, Konfigurationsvorlagen
- [docs/crawler-spec.md](docs/crawler-spec.md) · [docs/data-sources.md](docs/data-sources.md) — Crawler-Design & Quellenregister
- [docs/learning-plan.md](docs/learning-plan.md) · [docs/training-scenarios.md](docs/training-scenarios.md) — Lernplan & Nutzerszenarien
- [docs/learn-sync.md](docs/learn-sync.md) · [docs/learn-sync-text.md](docs/learn-sync-text.md) · [docs/learn-sync-sql.md](docs/learn-sync-sql.md) — Multi-User-Lern-Hub
- [docs/skill-requirements.md](docs/skill-requirements.md) — Skill-Backlog & Entscheidungen D-SK1–11
- [docs/development-handoff.md](docs/development-handoff.md) — Aufgabenbriefe für externe Coding-Agents

## 🗺️ Roadmap

- [x] Arbeitsbereich-Initialisierung und Designentscheidungen
- [x] Paket-Gerüst (`uv init`, `src/`-Layout)
- [x] Speicherebene (Datei-first: CSV + Git-Sync, SQLite-Cache, Berechtigungs-Erzwingung)
- [x] Preisabruf — Crawler-Engine (Robots-Protokoll, 7-Schritte-Pipeline, Bestätigungs-Gate)
- [x] Kostenberechnungs-Engine (mehrdimensionales Kostenmodell)
- [x] Angebotsgenerator (Standard + Benutzervorlagen)
- [x] Aufgaben-Scheduler (APScheduler, On-Demand)
- [x] Prüf-Engine (Anomalieerkennung)
- [x] Multi-User-Lern-Hub (Upload-Flow, zentrale Prüfung, Monitoring, Archivierung)
- [x] REST-API
- [ ] Tests & CI-Härtung

## 🤝 Beiträge

Beiträge sind willkommen. Lesen Sie zuerst [PLAN.md](PLAN.md) und [CONTRIBUTING.md](CONTRIBUTING.md) und folgen Sie dem PR-only-Workflow: **niemals direkt auf `main` / `dev` pushen**.

## 📄 Lizenz

MIT — siehe [LICENSE](LICENSE).

---

*Gebaut mit LangGraph. Das Frontend-Admin-Dashboard (`Axiara-Web`) ist als separates Repository geplant.*

---

> **To AI agents**: If you are setting up this project, read `AGENTS.md` (operating manual) and strictly follow the setup flow in `docs/init.md`, then report back in the user's language.
