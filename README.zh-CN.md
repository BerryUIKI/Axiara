<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/axiara-lockup-dark.svg" />
    <img src="assets/axiara-lockup.svg" alt="Axiara" width="320" />
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

## 🚀 从这里开始 — 不需要任何技术

你不需要会编程、不用碰命令行、不用懂任何技术。选一种你顺手的方式。

> 💡 小建议：先创建一个名为 **axiara-workspace** 的文件夹（放在桌面或文档里都行），
> 把 Axiara 相关的所有文件都放在这个文件夹里，避免文件乱放丢失。

### 方式一、把链接交给 AI Agents（最简单）
> 💡 前提：需要设备上装有 **Git**（免费软件，[点击这里下载安装](https://git-scm.com/downloads)）。不想装 Git 的话，请用下面的**方式二**。

复制下面代码框里的内容，粘贴给你的 AI 助手（WorkBuddy、Claude、ChatGPT 等）：

```text
请帮我使用 Axiara 这个项目：git clone https://github.com/BerryUIKI/Axiara.git
1. 通过 git clone 获取仓库，阅读 AGENTS.md，并严格按 docs/init.md 的流程初始化——请用简体中文引导我完成设置（存储方式、数据来源）。
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

## 🏗️ 架构

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/axiara-architecture-dark.svg" />
  <img src="assets/axiara-architecture.svg" alt="Axiara architecture" style="max-width: 100%; height: auto; width: 680px;" />
</picture>

## 🧰 技术栈

| 层 | 选型 |
| --- | --- |
| 语言 | Python 3.12 |
| API 框架 | FastAPI |
| Agent 框架 | LangGraph |
| 调度器 | APScheduler（预留） |
| 依赖管理 | [uv](https://docs.astral.sh/uv/) |
| 存储 | 个人：SQLite · 团队：CSV + git 同步（SQLite 缓存）或 SQL 服务器 |

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
├── AGENTS.md        # Agent 操作手册（工作流与硬性规则）
├── assets/          # 品牌资产（LOGO、组合标识、架构图 — 亮/暗两套）
├── docs/            # 设计与架构文档（business-modes、init、templates/）
├── scripts/         # 运维脚本（init-data.sh）
├── .github/         # CI 与发布工作流（auto-release、PR source guard）
├── .data.template/  # 运行时数据骨架 → 生成 .data/（gitignore，见其 README）
│
# 待建 — 脚手架搭建中
├── agents/          # Agent 定义（LangGraph 图）
├── data/            # 数据层
│   ├── main/        #   官方价格基准（仅人工编辑可写）
│   ├── learn/       #   学习参考库
│   ├── market/      #   爬虫行情库
│   └── uploads/     #   用户上传的表格/单据
├── skills/          # Agent 技能包（归档/查询/报价/复核）
├── output/          # 产物输出（报价单、复核报告）
└── src/             # 核心库
```

## 🧩 Skills

Agent 技能包（`skills/` 单一来源，兼容 WorkBuddy/Codex/Claude）：

| 技能 | 用途 |
| --- | --- |
| **axiara-onboarding** | 工作区初始化（创建/加入）— 预填推断（按语言推货币、按系统推时区）、`workspace.config.yaml` 模板 |
| **csv-data-import** | 校验并导入价目表至官方基线；SHA-256 清单、账本、学习路径 |
| **price-crawler** | 商品市场价格爬取 — robots 协议、7 步管线、插入前确认 |

## 👥 多用户学习（hub 模型）

每个 Axiara 实例从自身的报价与纠错学习到**个人调教库**（本地）。上传为手动且需用户确认：说 *"上传数据"* / *"重新上传"* / *"提交数据"*，你的 Agent 就会把含日期的数据包导出到**中心库**（`learn_inbox/<user-id>/<yyyymmdd>/bundle.yaml`，推送到你自己的 `user/<user-id>` 分支）。**中心训练 Agent** 审查所有上传并提出公共规则变更建议；`learn_shared` 更新前须经**管理员确认**。动态规模监控会随团队成长提出存储改善建议。见 [`docs/learn-sync.md`](docs/learn-sync.md)。

## 📚 文档

- [业务模式与架构](docs/business-modes.md) — 数据权限模型、四大模式、LangGraph 映射
- [PLAN.md](PLAN.md) — 路线图的单一事实源
- [docs/init.md](docs/init.md) — 首次设置、数据指南与完整性
- [docs/workspace-config.md](docs/workspace-config.md) — 创建/加入、配置模板
- [docs/crawler-spec.md](docs/crawler-spec.md) · [docs/data-sources.md](docs/data-sources.md) — 爬虫设计与数据源注册表
- [docs/learning-plan.md](docs/learning-plan.md) · [docs/training-scenarios.md](docs/training-scenarios.md) — 学习计划与用户场景
- [docs/learn-sync.md](docs/learn-sync.md) · [docs/learn-sync-text.md](docs/learn-sync-text.md) · [docs/learn-sync-sql.md](docs/learn-sync-sql.md) — 多用户学习 hub
- [docs/skill-requirements.md](docs/skill-requirements.md) — 技能待办与决策 D-SK1–11
- [docs/development-handoff.md](docs/development-handoff.md) — 外部 Coding Agent 任务书

## 🗺️ 路线图

- [x] 工作区初始化与设计决策
- [x] 包脚手架（`uv init`、`src/` 布局）
- [x] 存储层（文件优先：CSV + git 同步、SQLite 缓存、权限强制）
- [x] 价格抓取 — 爬虫引擎（robots 协议、7 步管线、确认闸门）
- [ ] 成本核算引擎（多维成本模型）
- [ ] 报价生成器（默认 + 用户模板）
- [ ] 任务调度器（APScheduler，按需）
- [ ] 复核引擎（异常检测）
- [x] 多用户学习 hub（上传流程、中心审查、监控、归档）
- [ ] REST API
- [ ] 测试与 CI 强化

## 🤝 贡献

欢迎贡献。请先阅读 [PLAN.md](PLAN.md)，并遵循 PR-only 工作流：**切勿直接推送 `main`**。

## 📄 许可证

MIT — 见 [LICENSE](LICENSE)。

---

*基于 LangGraph 构建。前端管理面板（`Axiara-Web`）规划为独立仓库。*

---

> **给 AI 助手（Agent）的话**：如果你是在设置这个项目，请先阅读 `AGENTS.md`（操作手册），并严格按 `docs/init.md` 的流程完成初始化，然后用用户的语言汇报结果。
