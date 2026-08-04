<p align="center">
  <img src="assets/axiara-logo.svg" alt="Axiara" width="120" />
</p>

<h1 align="center">Axiara — 智能体报价核心</h1>

<p align="center">
  <strong>多智能体估值核心</strong> — 自动化成本核算与实时市场价格情报，基于 LangGraph 构建。
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/python-3.12-blue" alt="Python 3.12" /></a>
  <a href="#"><img src="https://img.shields.io/badge/framework-LangGraph-purple" alt="LangGraph" /></a>
  <a href="#"><img src="https://img.shields.io/badge/api-FastAPI-teal" alt="FastAPI" /></a>
  <a href="#"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT" /></a>
  <a href="README.md"><img src="https://img.shields.io/badge/lang-English-blue" alt="English" /></a>
</p>

---

**阅读语言：** [English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja-JP.md) · [한국어](README.ko-KR.md) · [Français](README.fr-FR.md) · [Deutsch](README.de-DE.md) · [Español](README.es-ES.md) · [Português](README.pt-BR.md) · [Русский](README.ru-RU.md)

---

Axiara 是一个**面向估值的 Agent 工作区**。它为 AI Agent 提供四项明确能力——*归档*、*查询*、*批量报价* 和 *复核*——并基于三层隔离、写权限严格受控的数据体系运行，确保自动化 Agent 永远不会污染官方价格基准。

> **设计理念：** Axiara 不是固定流程的应用。Agent 在工作区内自主工作，自行决定调用哪些数据与技能。四大模式是**能力与权限边界**，而非写死的界面流程。

## ✨ 核心特性

- **🔒 三层数据隔离** — 官方价格基准库（`main_db`）写保护：仅人工编辑可修改；爬虫与 AI 学习产出永远无法覆盖它。
- **🤖 自主 Agent 工作区** — 基于 LangGraph：Agent 按任务自主选择调用哪些数据与技能。
- **📦 归档（模式一）** — 人工录入官方价目表（带版本、可回滚）+ 从历史单据 AI 学习 + 按需抓取市场行情。
- **🔍 查询（模式二）** — 单品查询：官方成本 + 市场价区间 + 工艺备注。
- **📊 批量报价（模式三）** — Excel/物料清单回填并自动识别列位，附智能报价：约束协商（默认约束 + 项目约束），无约束时给出低/中/高三档方案。
- **✅ 复核（模式四）** — 用官方基准与市场数据交叉校验用户报价表，标记异常并给出调整建议。
- **🧩 模板自适应报价** — 内置默认报价单模板，遇到用户自有模板时动态适配（开源 / Fork 友好）。
- **💾 可插拔存储** — SQLite / PostgreSQL / MongoDB 后端，外加 CSV 导入导出。
- **🕐 按需爬取** — 行情在你需要时才刷新，不做盲目定时。

## 🏗️ 架构

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
         │  官方基准  │        │  学习参考  │        │  行情库   │
         │ （仅人工  │        │ （AI 训练）│        │（爬虫采集  │
         │  编辑可写）│        │           │        │  入库前需  │
         └───────────┘        └───────────┘        │  确认）   │
                                                   └───────────┘
```

## 🧰 技术栈

| 层 | 选型 |
| --- | --- |
| 语言 | Python 3.12 |
| API 框架 | FastAPI |
| Agent 框架 | LangGraph |
| 调度器 | APScheduler（预留） |
| 依赖管理 | [uv](https://docs.astral.sh/uv/) |
| 存储 | SQLite / PostgreSQL / MongoDB（可插拔）+ CSV |

## 🚀 快速开始

> 脚手架搭建中——以下命令为目标体验。

```bash
# 安装依赖
uv sync

# 启动工作区（交互式 Agent 壳）
uv run axiara

# 启动 REST API
uv run uvicorn axiara.api.main:app --reload
```

## 📁 仓库结构

```
Axiara/
├── agents/          # Agent 定义（LangGraph 图）
├── data/            # 数据层
│   ├── main/        #   官方价格基准（仅人工编辑可写）
│   ├── learn/       #   学习参考库
│   ├── market/      #   爬虫行情库
│   └── uploads/     #   用户上传的表格/单据
├── skills/          # Agent 技能包（归档/查询/报价/复核）
├── output/          # 产物输出（报价单、复核报告）
├── docs/            # 设计与架构文档
└── src/             # 核心库
```

## 📚 文档

- [业务模式与架构](docs/business-modes.md) — 数据权限模型、四大模式、LangGraph 映射
- [PLAN.md](PLAN.md) — 路线图的单一事实源

## 🗺️ 路线图

- [x] 工作区初始化与设计决策
- [ ] 包脚手架（`uv init`、`src/` 布局）
- [ ] 存储层（可插拔后端 + CSV）
- [ ] 成本核算引擎（多维成本模型）
- [ ] 价格抓取 Agent（LangGraph 爬取 + 规范化）
- [ ] 任务调度器（APScheduler，按需）
- [ ] 报价生成器（默认 + 用户模板）
- [ ] 复核引擎（异常检测）
- [ ] REST API
- [ ] 测试与 CI

## 🤝 贡献

欢迎贡献。请先阅读 [PLAN.md](PLAN.md)，并遵循 PR-only 工作流：**切勿直接推送 `main`**。

## 📄 许可证

MIT — 见 [LICENSE](LICENSE)。

---

*基于 LangGraph 构建。前端管理面板（`Axiara-Web`）规划为独立仓库。*
