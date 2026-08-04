<p align="center">
  <img src="assets/axiara-logo.svg" alt="Axiara" width="120" />
</p>

<h1 align="center">Axiara — Cœur de devis pour agents</h1>

<p align="center">
  <strong>Cœur d'évaluation multi-agents</strong> — calcul automatisé des coûts et intelligence de prix de marché en temps réel, construit avec LangGraph.
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/python-3.12-blue" alt="Python 3.12" /></a>
  <a href="#"><img src="https://img.shields.io/badge/framework-LangGraph-purple" alt="LangGraph" /></a>
  <a href="#"><img src="https://img.shields.io/badge/api-FastAPI-teal" alt="FastAPI" /></a>
  <a href="#"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT" /></a>
  <a href="README.md"><img src="https://img.shields.io/badge/lang-English-blue" alt="English" /></a>
</p>

---

**Lire ce document en :** [English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja-JP.md) · [한국어](README.ko-KR.md) · [Français](README.fr-FR.md) · [Deutsch](README.de-DE.md) · [Español](README.es-ES.md) · [Português](README.pt-BR.md) · [Русский](README.ru-RU.md)

---

Axiara est un **espace de travail à agents pour l'évaluation**. Il offre aux agents IA quatre capacités claires — *archivage*, *consultation*, *devis en lot* et *vérification* — s'appuyant sur trois couches de données isolées avec des permissions d'écriture strictes, afin que les agents automatisés ne puissent jamais corrompre la base de prix officielle.

> **Philosophie de conception :** Axiara n'est pas une application à flux fixe. Les agents travaillent de manière autonome dans l'espace de travail et décident quelles données et compétences appeler. Les quatre modes sont des *limites de capacités et de permissions*, pas des flux UI codés en dur.

## ✨ Fonctionnalités clés

- **🔒 Isolation des données en trois couches** — la base de prix officielle (`main_db`) est protégée en écriture : seules les modifications manuelles peuvent la changer ; les sorties du crawler et de l'IA ne peuvent jamais la remplacer.
- **🤖 Espace de travail à agents autonome** — basé sur LangGraph : les agents choisissent eux-mêmes quelles données et compétences invoquer.
- **📦 Archivage (mode 1)** — saisie manuelle des prix officiels (versionnée, rollback possible) + apprentissage IA à partir de documents historiques + crawling des prix de marché à la demande.
- **🔍 Consultation (mode 2)** — requête d'un article : coût officiel + fourchette de prix de marché + notes de processus.
- **📊 Devis en lot (mode 3)** — remplissage Excel/BOM avec détection automatique des colonnes, plus devis intelligent avec négociation de contraintes (défaut + projet ; trois options bas/moyen/haut si aucune).
- **✅ Vérification (mode 4)** — validation croisée des tableaux de devis utilisateur contre la base officielle et les données de marché ; signalement des anomalies et suggestions d'ajustement.
- **🧩 Devis adaptatif aux templates** — template de devis par défaut inclus, adaptation à la volée aux templates fournis par l'utilisateur (open source / fork-friendly).
- **💾 Stockage pluggable** — backends SQLite / PostgreSQL / MongoDB, plus import/export CSV.
- **🕐 Crawling à la demande** — les données de marché se rafraîchissent quand vous le demandez, pas selon un calendrier aveugle.

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
         │  Base de  │        │ Référence │        │ Prix      │
         │  prix off.│        │ apprise   │        │ crawlés   │
         │ (édition  │        │ (IA)      │        │ (confirme │
         │  manuelle │        │           │        │  avant    │
         │  UNIQUEMENT)       │           │        │  insert)  │
         └───────────┘        └───────────┘        └───────────┘
```

## 🧰 Pile technique

| Couche | Choix |
| --- | --- |
| Langage | Python 3.12 |
| Framework API | FastAPI |
| Framework agents | LangGraph |
| Planificateur | APScheduler (réservé) |
| Gestion de dépendances | [uv](https://docs.astral.sh/uv/) |
| Stockage | SQLite / PostgreSQL / MongoDB (pluggable) + CSV |

## 🚀 Démarrage rapide

> Scaffolding en cours — les commandes ci-dessous sont l'expérience cible.

```bash
# Installer les dépendances
uv sync

# Lancer l'espace de travail (shell agent interactif)
uv run axiara

# Lancer l'API REST
uv run uvicorn axiara.api.main:app --reload
```

## 📁 Structure du dépôt

```
Axiara/
├── agents/          # Définitions des agents (graphes LangGraph)
├── data/            # Couches de données
│   ├── main/        #   base de prix officielle (édition manuelle uniquement)
│   ├── learn/       #   référence apprise
│   ├── market/      #   prix de marché crawlés
│   └── uploads/     #   tableaux / documents fournis par l'utilisateur
├── skills/          # Packs de compétences (archivage/consultation/devis/vérification)
├── output/          # Livrables générés (devis, rapports de vérification)
├── docs/            # Documentation de conception et d'architecture
└── src/             # Bibliothèque cœur
```

## 📚 Documentation

- [Modes métier & architecture](docs/business-modes.md) — modèle de permissions de données, quatre modes, mapping LangGraph
- [PLAN.md](PLAN.md) — source unique de vérité pour la feuille de route

## 🗺️ Feuille de route

- [x] Initialisation de l'espace de travail et décisions de conception
- [ ] Scaffolding du package (`uv init`, layout `src/`)
- [ ] Couche de stockage (backends pluggables + CSV)
- [ ] Moteur de calcul des coûts (modèle de coûts multidimensionnel)
- [ ] Agent de récupération de prix (crawl LangGraph + normalisation)
- [ ] Planificateur de tâches (APScheduler, à la demande)
- [ ] Générateur de devis (templates par défaut + utilisateur)
- [ ] Moteur de vérification (détection d'anomalies)
- [ ] API REST
- [ ] Tests & CI

## 🤝 Contribution

Les contributions sont les bienvenues. Lisez d'abord [PLAN.md](PLAN.md) et suivez le workflow PR-only : **ne jamais pousser directement vers `main`**.

## 📄 Licence

MIT — voir [LICENSE](LICENSE).

---

*Construit avec LangGraph. Le tableau de bord front-end (`Axiara-Web`) est prévu dans un dépôt séparé.*
