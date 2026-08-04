<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/axiara-lockup-dark.svg" />
    <img src="assets/axiara-lockup.svg" alt="Axiara" width="240" />
  </picture>
</p>

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
- **💾 适配任何场景的存储——无需服务器** — 个人：SQLite；团队：CSV 文件 + git 同步（`store/`，Agent 自动维护本地 SQLite 缓存加速查询），或 SQL 服务器（MySQL / MariaDB / PostgreSQL）。
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
| 存储 | 个人：SQLite · 团队：CSV + git 同步（SQLite 缓存）或 SQL 服务器 |

## 🚀 从这里开始 — 不需要任何技术

你不需要会编程、不用碰命令行、不用懂任何技术。选一种你顺手的方式。

> 💡 小建议：先创建一个名为 **axiara-workspace** 的文件夹（放在桌面或文档里都行），
> 把 Axiara 相关的所有文件都放在这个文件夹里，避免文件乱放丢失。

### 方式一、把链接交给 AI Agents（最简单）
复制下面代码框里的内容，粘贴给你的 AI 助手（WorkBuddy、Claude、ChatGPT 等）：

```text
请帮我 'git clone https://github.com/BerryUIKI/Axiara.git' 这个项目：
1. 获取代码并完成初始化——请用简体中文引导我完成设置（语言、存储方式、数据来源）。
2. 初始化完成后，告诉我可以让你做什么。
```

然后按它的问题回答即可，就这么简单。

### 方式二、自己下载文件，再交给 AI Agents
1. 从 [Releases 页面](https://github.com/BerryUIKI/Axiara/releases) 下载最新压缩包（或点绿色 **Code** 按钮 → **Download ZIP**），解压到刚才建议的 axiara-workspace 文件夹里。
2. 在你的 AI 助手里打开这个文件夹，对它说："帮我初始化这个项目，并引导我完成设置"。
3. 回答它的问题——完成。

### 检查更新
想看看有没有新版本？把下面代码框里的内容发给你的 AI 助手：

```text
请检查 Axiara 有没有新版本：https://github.com/BerryUIKI/Axiara
如果有新版本，帮我更新到最新版（保留我现有的数据，不要清空 .data 目录）。
```

无论哪种方式，初始化完成后你都可以直接说："帮我对 XX 出一份报价"——剩下的交给 Agent。

## 🧑‍💻 开发者快速开始

> 脚手架搭建中——以下命令为目标体验。

```bash
# 安装依赖
uv sync

# 初始化运行时数据目录（.data/ — store、cache、ledger、db_dump、local_config）
bash scripts/init-data.sh

# 启动工作区（交互式 Agent 壳）
uv run axiara

# 启动 REST API
uv run uvicorn axiara.api.main:app --reload
```

### 首次使用（运行时数据目录）

`.data/` 已被 gitignore，clone 下来后不存在，先初始化一次即可——或者直接启动应用，启动时会自动补齐：

```bash
bash scripts/init-data.sh
```

该命令创建五个运行时目录并播种私有配置（`.data/local_config/config`，之后不再覆盖）；在该配置里填 `data_repo.url` 可同步团队数据仓库到 `store/`。完整指南见 [`docs/init.md`](docs/init.md)。

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
├── scripts/         # 运维脚本（init-data.sh）
├── .data.template/  # 运行时数据骨架 → 生成 .data/（gitignore，见其 README）
└── src/             # 核心库
```

## 📚 文档

- [业务模式与架构](docs/business-modes.md) — 数据权限模型、四大模式、LangGraph 映射
- [PLAN.md](PLAN.md) — 路线图的单一事实源

## 🗺️ 路线图

- [x] 工作区初始化与设计决策
- [ ] 包脚手架（`uv init`、`src/` 布局）
- [ ] 存储层（文件优先：CSV + git 同步、SQLite 缓存、SQL 选项）
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
