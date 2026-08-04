<p align="center">
  <img src="assets/axiara-logo.svg" alt="Axiara" width="120" />
</p>

<h1 align="center">Axiara — Agenten-Angebotskern</h1>

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

**Lesen Sie dies in:** [English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja-JP.md) · [한국어](README.ko-KR.md) · [Français](README.fr-FR.md) · [Deutsch](README.de-DE.md) · [Español](README.es-ES.md) · [Português](README.pt-BR.md) · [Русский](README.ru-RU.md)

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

## 🏗️ Architektur

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
         │  Offiz.   │        │  Gelernte │        │  Gecrawlte│
         │  Preisbasis│       │  Referenz │        │  Preise   │
         │ (nur man. │        │ (KI)      │        │ (Crawler, │
         │  Bearbeit.)│       │           │        │  Bestätig. │
         └───────────┘        └───────────┘        │  vor Insert│
                                                   └───────────┘
```

## 🧰 Tech-Stack

| Ebene | Wahl |
| --- | --- |
| Sprache | Python 3.12 |
| API-Framework | FastAPI |
| Agenten-Framework | LangGraph |
| Scheduler | APScheduler (reserviert) |
| Abhängigkeitsverwaltung | [uv](https://docs.astral.sh/uv/) |
| Speicherung | SQLite / PostgreSQL / MongoDB (plugable) + CSV |

## 🚀 Schnellstart

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
├── agents/          # Agenten-Definitionen (LangGraph-Graphen)
├── data/            # Datenebenen
│   ├── main/        #   offizielle Preisbasis (nur manuelle Bearbeitung)
│   ├── learn/       #   gelernte Referenz
│   ├── market/      #   gecrawlte Marktpreise
│   └── uploads/     #   vom Benutzer bereitgestellte Tabellen/Dokumente
├── skills/          # Agenten-Fähigkeitspakete (archivieren/abfragen/angebot/prüfen)
├── output/          # Generierte Ergebnisse (Angebote, Prüfberichte)
├── docs/            # Design- und Architekturdokumentation
└── src/             # Kernbibliothek
```

## 📚 Dokumentation

- [Geschäftsmodelle & Architektur](docs/business-modes.md) — Datenberechtigungsmodell, vier Modi, LangGraph-Mapping
- [PLAN.md](PLAN.md) — Single Source of Truth für die Roadmap

## 🗺️ Roadmap

- [x] Arbeitsbereich-Initialisierung und Designentscheidungen
- [ ] Paket-Gerüst (`uv init`, `src/`-Layout)
- [ ] Speicherebene (plugable Backends + CSV)
- [ ] Kostenberechnungs-Engine (mehrdimensionales Kostenmodell)
- [ ] Preisabruf-Agent (LangGraph-Crawl + Normalisierung)
- [ ] Aufgaben-Scheduler (APScheduler, On-Demand)
- [ ] Angebotsgenerator (Standard + Benutzervorlagen)
- [ ] Prüf-Engine (Anomalieerkennung)
- [ ] REST-API
- [ ] Tests & CI

## 🤝 Beiträge

Beiträge sind willkommen. Lesen Sie zuerst [PLAN.md](PLAN.md) und folgen Sie dem PR-only-Workflow: **niemals direkt auf `main` pushen**.

## 📄 Lizenz

MIT — siehe [LICENSE](LICENSE).

---

*Gebaut mit LangGraph. Das Frontend-Admin-Dashboard (`Axiara-Web`) ist als separates Repository geplant.*
