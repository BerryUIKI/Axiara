<p align="center">
  <img src="assets/axiara-logo.svg" alt="Axiara" width="120" />
</p>

<h1 align="center">Axiara — 智能體報價核心</h1>

<p align="center">
  <strong>多智能體估值核心</strong> — 自動化成本核算與即時市場價格情報，基於 LangGraph 建構。
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/python-3.12-blue" alt="Python 3.12" /></a>
  <a href="#"><img src="https://img.shields.io/badge/framework-LangGraph-purple" alt="LangGraph" /></a>
  <a href="#"><img src="https://img.shields.io/badge/api-FastAPI-teal" alt="FastAPI" /></a>
  <a href="#"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT" /></a>
  <a href="README.md"><img src="https://img.shields.io/badge/lang-English-blue" alt="English" /></a>
</p>

---

**閱讀語言：** [English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja-JP.md) · [한국어](README.ko-KR.md) · [Français](README.fr-FR.md) · [Deutsch](README.de-DE.md) · [Español](README.es-ES.md) · [Português](README.pt-BR.md) · [Русский](README.ru-RU.md)

---

Axiara 是一個**面向估值的 Agent 工作區**。它為 AI Agent 提供四項明確能力——*歸檔*、*查詢*、*批次報價* 與 *複核*——並在三層隔離、寫入權限嚴格受控的資料體系上運作，確保自動化 Agent 永遠不會污染官方價格基準。

> **設計理念：** Axiara 不是固定流程的應用。Agent 在工作區內自主工作，自行決定要呼叫哪些資料與技能。四大模式是**能力與權限邊界**，而非寫死的介面流程。

## ✨ 核心特性

- **🔒 三層資料隔離** — 官方價格基準庫（`main_db`）寫入保護：僅人工編輯可修改；爬蟲與 AI 學習產出永遠無法覆蓋它。
- **🤖 自主 Agent 工作區** — 基於 LangGraph：Agent 依任務自主選擇呼叫哪些資料與技能。
- **📦 歸檔（模式一）** — 人工輸入官方價目表（含版本、可回滾）+ 從歷史單據進行 AI 學習 + 按需抓取市場行情。
- **🔍 查詢（模式二）** — 單品查詢：官方成本 + 市場價區間 + 工藝備註。
- **📊 批次報價（模式三）** — Excel/物料清單回填並自動辨識欄位，附智慧報價：約束協商（預設約束 + 專案約束），無約束時提供低/中/高三檔方案。
- **✅ 複核（模式四）** — 以官方基準與市場資料交叉驗證使用者報價表，標記異常並提出調整建議。
- **🧩 模板自適應報價** — 內建預設報價單模板，遇到使用者自有模板時動態適配（開源 / Fork 友善）。
- **💾 可插拔儲存** — SQLite / PostgreSQL / MongoDB 後端，外加 CSV 匯入匯出。
- **🕐 按需爬取** — 行情在你需要時才更新，不做盲目排程。

## 🏗️ 架構

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
         │  官方基準  │        │  學習參考  │        │  行情庫   │
         │ （僅人工  │        │ （AI 訓練）│        │（爬蟲採集  │
         │  編輯可寫）│        │           │        │  入庫前需  │
         └───────────┘        └───────────┘        │  確認）   │
                                                   └───────────┘
```

## 🧰 技術棧

| 層 | 選型 |
| --- | --- |
| 語言 | Python 3.12 |
| API 框架 | FastAPI |
| Agent 框架 | LangGraph |
| 排程器 | APScheduler（預留） |
| 依賴管理 | [uv](https://docs.astral.sh/uv/) |
| 儲存 | SQLite / PostgreSQL / MongoDB（可插拔）+ CSV |

## 🚀 快速開始

> 脚手架搭建中——以下指令為目標體驗。

```bash
# 安裝依賴
uv sync

# 啟動工作區（互動式 Agent Shell）
uv run axiara

# 啟動 REST API
uv run uvicorn axiara.api.main:app --reload
```

## 📁 倉庫結構

```
Axiara/
├── agents/          # Agent 定義（LangGraph 圖）
├── data/            # 資料層
│   ├── main/        #   官方價格基準（僅人工編輯可寫）
│   ├── learn/       #   學習參考庫
│   ├── market/      #   爬蟲行情庫
│   └── uploads/     #   使用者上傳的表格/單據
├── skills/          # Agent 技能包（歸檔/查詢/報價/複核）
├── output/          # 產物輸出（報價單、複核報告）
├── docs/            # 設計與架構文件
└── src/             # 核心函式庫
```

## 📚 文件

- [業務模式與架構](docs/business-modes.md) — 資料權限模型、四大模式、LangGraph 對應
- [PLAN.md](PLAN.md) — 藍圖的單一事實來源

## 🗺️ 藍圖

- [x] 工作區初始化與設計決策
- [ ] 套件脚手架（`uv init`、`src/` 佈局）
- [ ] 儲存層（可插拔後端 + CSV）
- [ ] 成本核算引擎（多維成本模型）
- [ ] 價格抓取 Agent（LangGraph 爬取 + 正規化）
- [ ] 任務排程器（APScheduler，按需）
- [ ] 報價產生器（預設 + 使用者模板）
- [ ] 複核引擎（異常偵測）
- [ ] REST API
- [ ] 測試與 CI

## 🤝 貢獻

歡迎貢獻。請先閱讀 [PLAN.md](PLAN.md)，並遵循 PR-only 工作流：**切勿直接推送 `main`**。

## 📄 授權條款

MIT — 見 [LICENSE](LICENSE)。

---

*基於 LangGraph 建構。前端管理面板（`Axiara-Web`）規劃為獨立倉庫。*
