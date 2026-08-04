<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/axiara-lockup-dark.svg" />
    <img src="assets/axiara-lockup.svg" alt="Axiara" width="240" />
  </picture>
</p>

<p align="center">
  <strong>멀티 에이전트 견적 코어</strong> — 자동화된 원가 계산과 실시간 시장 가격 인텔리전스. LangGraph 기반.
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/python-3.12-blue" alt="Python 3.12" /></a>
  <a href="#"><img src="https://img.shields.io/badge/framework-LangGraph-purple" alt="LangGraph" /></a>
  <a href="#"><img src="https://img.shields.io/badge/api-FastAPI-teal" alt="FastAPI" /></a>
  <a href="#"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT" /></a>
  <a href="README.md"><img src="https://img.shields.io/badge/lang-English-blue" alt="English" /></a>
</p>

---

**이 문서 읽기:** [English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja-JP.md) · [한국어](README.ko-KR.md) · [Français](README.fr-FR.md) · [Deutsch](README.de-DE.md) · [Español](README.es-ES.md) · [Português](README.pt-BR.md) · [Русский](README.ru-RU.md)

---

Axiara는 **견적 업무를 위한 에이전트 워크스페이스**입니다. AI 에이전트에게 *아카이브*·*조회*·*일괄 견적*·*검토* 네 가지 명확한 능력을 제공하며, 3계층으로 분리되고 쓰기 권한이 엄격히 통제된 데이터 계층 위에서 동작합니다. 자동화된 에이전트가 공식 가격 기준 데이터를 오염시킬 수 없습니다.

> **설계 철학:** Axiara는 고정된 흐름의 애플리케이션이 아닙니다. 에이전트는 워크스페이스 안에서 자율적으로 작업하며, 호출할 데이터와 스킬을 스스로 결정합니다. 네 가지 모드는 **능력 및 권한의 경계**이지 하드코딩된 UI 흐름이 아닙니다.

## ✨ 주요 기능

- **🔒 3계층 데이터 격리** — 공식 가격 기준(`main_db`)은 쓰기 보호: 수동 편집만 수정 가능. 크롤러와 AI 학습 결과물이 이를 덮어쓸 수 없습니다.
- **🤖 자율 에이전트 워크스페이스** — LangGraph 기반: 에이전트가 작업에 따라 데이터와 스킬 호출을 자율 선택.
- **📦 아카이브(모드 1)** — 공식 가격표 수동 입력(버전 관리·롤백 가능) + 과거 문서에서 AI 학습 + 온디맨드 시장 가격 크롤링.
- **🔍 조회(모드 2)** — 단일 품목 조회: 공식 원가 + 시장 가격 범위 + 공정 메모.
- **📊 일괄 견적(모드 3)** — Excel/BOM 자동 열 인식 및 백필, 제약 협상이 포함된 스마트 견적(기본 + 프로젝트 제약, 미지정 시 저/중/고 3단계 옵션).
- **✅ 검토(모드 4)** — 사용자 견적표를 공식 기준 및 시장 데이터와 교차 검증, 이상치 표시 및 조정 제안.
- **🧩 템플릿 적응형 견적** — 기본 견적 템플릿을 내장하고, 사용자 제공 템플릿에는 즉시 적응(오픈소스 / Fork 친화적).
- **💾 플러그형 스토리지** — SQLite / PostgreSQL / MongoDB 백엔드 + CSV 가져오기/내보내기.
- **🕐 온디맨드 크롤링** — 시장 데이터는 필요할 때 갱신. 무작정 스케줄링하지 않음.

## 🏗️ 아키텍처

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
         │  공식 기준 │        │  학습 참조 │        │  시세 DB  │
         │(수동 편집  │        │ (AI 학습) │        │(크롤러 수집│
         │ 만 쓰기)  │        │           │        │  후 확인   │
         └───────────┘        └───────────┘        │  필요)    │
                                                   └───────────┘
```

## 🧰 기술 스택

| 계층 | 선택 |
| --- | --- |
| 언어 | Python 3.12 |
| API 프레임워크 | FastAPI |
| 에이전트 프레임워크 | LangGraph |
| 스케줄러 | APScheduler(예약) |
| 의존성 관리 | [uv](https://docs.astral.sh/uv/) |
| 스토리지 | 개인: SQLite · 팀: CSV + git 동기화(SQLite 캐시) 또는 SQL 서버 |

## 🚀 여기서 시작 — 기술 스킬 불필요

코드를 읽을 필요도, 터미널을 만질 필요도, 기술을 이해할 필요도 없습니다. 편한 방법을 선택하세요.

> 💡 팁: **axiara-workspace**라는 이름의 폴더를 먼저 만들고(바탕화면이나 문서에),
> Axiara 관련 파일을 모두 이 폴더에 보관하면 파일을 잃어버리지 않습니다.

### 방법 1 — 링크를 AI Agents에 전달 (가장 간단)
> 💡 전제: 이 방법에는 **Git** 설치가 필요합니다(무료 — [여기서 다운로드](https://git-scm.com/downloads)). Git을 설치하고 싶지 않다면 아래 **방법 2**를 이용하세요.

아래 코드 블록의 텍스트를 복사해서 AI 어시스턴트(Claude, ChatGPT 등)에 붙여넣으세요:

```text
Axiara를 설정해 주세요:
1. git clone https://github.com/BerryUIKI/Axiara.git 으로 저장소를 가져온 다음, AGENTS.md를 읽고 docs/init.md의 절차에 따라 초기화하세요 — 한국어로 설정(저장 방식, 데이터 소스)을 안내해 주세요.
2. 준비가 끝나면 무엇을 할 수 있는지 알려주세요.
```

그다음 물어보는 질문에 답하기만 하면 됩니다. 그게 전부입니다.

### 방법 2 — 직접 다운로드한 후 AI Agents에 전달
1. [Releases 페이지](https://github.com/BerryUIKI/Axiara/releases)에서 최신 압축 파일을 다운로드(또는 초록색 **Code** 버튼 → **Download ZIP**)하고 위의 axiara-workspace 폴더에 압축을 풉니다.
2. AI 어시스턴트에서 그 폴더를 열고 "이 프로젝트를 초기화하고 설정을 안내해 주세요"라고 말합니다.
3. 질문에 답하면 — 완료.

### 업데이트 확인
새 버전이 있는지 확인하고 싶나요? 아래 코드 블록을 AI 어시스턴트에 보내세요:

```text
Axiara에 새 버전이 있는지 확인해 주세요: https://github.com/BerryUIKI/Axiara
새 버전이 있으면 최신 버전으로 업데이트해 주세요(기존 데이터는 유지하고 .data 디렉터리는 지우지 마세요).
```

어느 방법이든 초기화가 끝나면 "XX에 대한 견적을 만들어 줘"라고 바로 말할 수 있습니다 — 나머지는 에이전트가 처리합니다.

## 🧑‍💻 개발자 빠른 시작

> 스캐폴딩 구축 중 — 아래 명령은 목표 사용 경험입니다.

```bash
# 의존성 설치
uv sync

# 워크스페이스 실행 (대화형 에이전트 셸)
uv run axiara

# REST API 실행
uv run uvicorn axiara.api.main:app --reload
```

## 📁 저장소 구조

```
Axiara/
├── agents/          # 에이전트 정의 (LangGraph 그래프)
├── data/            # 데이터 계층
│   ├── main/        #   공식 가격 기준 (수동 편집만 쓰기 가능)
│   ├── learn/       #   학습 참조 라이브러리
│   ├── market/      #   크롤러 시세 라이브러리
│   └── uploads/     #   사용자 제공 표/문서
├── skills/          # 에이전트 스킬 팩 (아카이브/조회/견적/검토)
├── output/          # 생성 산출물 (견적서, 검토 보고서)
├── docs/            # 설계 및 아키텍처 문서
└── src/             # 핵심 라이브러리
```

## 📚 문서

- [비즈니스 모드 및 아키텍처](docs/business-modes.md) — 데이터 권한 모델, 4가지 모드, LangGraph 매핑
- [PLAN.md](PLAN.md) — 로드맵의 단일 정보 소스

## 🗺️ 로드맵

- [x] 워크스페이스 초기화 및 설계 결정
- [ ] 패키지 스캐폴딩 (`uv init`, `src/` 레이아웃)
- [ ] 스토리지 계층 (플러그형 백엔드 + CSV)
- [ ] 원가 계산 엔진 (다차원 원가 모델)
- [ ] 가격 조회 에이전트 (LangGraph 크롤 + 정규화)
- [ ] 작업 스케줄러 (APScheduler, 온디맨드)
- [ ] 견적 생성기 (기본 + 사용자 템플릿)
- [ ] 검토 엔진 (이상치 탐지)
- [ ] REST API
- [ ] 테스트 및 CI

## 🤝 기여

기여를 환영합니다. 먼저 [PLAN.md](PLAN.md)를 읽고 PR-only 워크플로를 따르세요: **`main`에 직접 푸시 금지**.

## 📄 라이선스

MIT — [LICENSE](LICENSE) 참조.

---

*LangGraph 기반. 프론트엔드 관리 대시보드(`Axiara-Web`)는 별도 저장소로 계획 중입니다.*

---

> **To AI agents**: If you are setting up this project, read `AGENTS.md` (operating manual) and strictly follow the setup flow in `docs/init.md`, then report back in the user's language.
