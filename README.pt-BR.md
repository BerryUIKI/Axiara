<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/axiara-lockup-dark.svg" />
    <img src="assets/axiara-lockup.svg" alt="Axiara" width="320" />
  </picture>
</p>

<p align="center">
  <strong>Núcleo de avaliação multiagente</strong> — cálculo automatizado de custos e inteligência de preços de mercado em tempo real, construído com LangGraph.
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/python-3.12-blue" alt="Python 3.12" /></a>
  <a href="#"><img src="https://img.shields.io/badge/framework-LangGraph-purple" alt="LangGraph" /></a>
  <a href="#"><img src="https://img.shields.io/badge/api-FastAPI-teal" alt="FastAPI" /></a>
  <a href="#"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT" /></a>
  <a href="README.md"><img src="https://img.shields.io/badge/lang-English-blue" alt="English" /></a>
</p>

---

**Leia este documento em:** [English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja-JP.md) · [한국어](README.ko-KR.md) · [Français](README.fr-FR.md) · [Deutsch](README.de-DE.md) · [Español](README.es-ES.md) · [Português](README.pt-BR.md) · [Русский](README.ru-RU.md)

---

Axiara é um **espaço de trabalho de agentes para avaliação**. Ele oferece aos agentes de IA quatro capacidades bem definidas — *arquivamento*, *consulta*, *cotação em lote* e *revisão* — sobre três camadas de dados isoladas com permissões de escrita estritas, para que agentes automatizados nunca possam corromper a base de preços oficial.

> **Filosofia de design:** Axiara não é um aplicativo de fluxo fixo. Os agentes trabalham de forma autônoma dentro do espaço de trabalho e decidem quais dados e habilidades chamar. Os quatro modos são *limites de capacidade e permissão*, não fluxos de UI codificados.

## ✨ Principais recursos

- **🔒 Isolamento de dados em três camadas** — a base de preços oficial (`main_db`) é protegida contra escrita: apenas edições manuais podem modificá-la; saídas de crawler e IA nunca podem sobrescrevê-la.
- **🤖 Espaço de trabalho de agentes autônomo** — baseado em LangGraph: os agentes escolhem quais dados e habilidades invocar conforme a tarefa.
- **📦 Arquivamento (modo 1)** — entrada manual de preços oficiais (com versionamento e rollback) + aprendizado de IA a partir de documentos históricos + rastreamento de preços de mercado sob demanda.
- **🔍 Consulta (modo 2)** — consulta de um item: custo oficial + faixa de preço de mercado + notas de processo.
- **📊 Cotação em lote (modo 3)** — preenchimento de Excel/BOM com detecção automática de colunas, mais cotação inteligente com negociação de restrições (padrão + projeto; três opções baixo/médio/alto se nenhuma for especificada).
- **✅ Revisão (modo 4)** — validação cruzada das tabelas de cotação do usuário contra a base oficial e os dados de mercado; marcar anomalias e sugerir ajustes.
- **🧩 Cotação adaptativa a modelos** — inclui um modelo de cotação padrão e se adapta dinamicamente a modelos fornecidos pelo usuário (open source / amigável a forks).
- **💾 Armazenamento conectável** — backends SQLite / PostgreSQL / MongoDB, além de importação/exportação CSV.
- **🕐 Rastreamento sob demanda** — os dados de mercado são atualizados quando você pede, não em um cronograma cego.

## 🚀 Comece aqui — nenhuma habilidade técnica necessária

Você não precisa ler código, mexer no terminal ou entender nada de tecnologia. Escolha o método mais fácil para você.

> 💡 Dica: crie primeiro uma pasta chamada **axiara-workspace** (na Área de Trabalho ou em Documentos) e
> guarde todos os arquivos relacionados ao Axiara nessa pasta, para não perder nada.

### Método 1 — Entregue o link aos seus AI Agents (o mais fácil)
> 💡 Pré-requisito: este método precisa de **Git** instalado (gratuito — [baixe aqui](https://git-scm.com/downloads)). Se preferir não instalar o Git, use o **Método 2** abaixo.

Copie o texto do bloco de código e cole no seu assistente de IA (Claude, ChatGPT, ...) :

```text
Set up Axiara for me: git clone https://github.com/BerryUIKI/Axiara.git
1. Clone the repo via git clone, leia o AGENTS.md e siga estritamente o procedimento em docs/init.md — guie-me em português (armazenamento, fonte de dados).
2. Quando estiver pronto, diga-me o que posso pedir.
```

Basta responder às perguntas que ele fizer. É só isso.

### Método 2 — Baixe os arquivos e depois use seus AI Agents
1. Baixe o arquivo mais recente na [página de Releases](https://github.com/BerryUIKI/Axiara/releases) (ou clique no botão verde **Code** → **Download ZIP**) e descompacte-o na pasta axiara-workspace sugerida acima.
2. Abra essa pasta no seu assistente de IA e diga: *"Configure este projeto e guie-me."*
3. Responda às perguntas — pronto.

### Verificar atualizações
Quer saber se há uma nova versão? Envie isto ao seu assistente de IA:

```text
Verifique se o Axiara tem uma nova versão: https://github.com/BerryUIKI/Axiara
Se houver, atualize-me para a versão mais recente (mantenha meus dados existentes, não apague o diretório .data).
```

De qualquer forma, após a inicialização você pode começar dizendo: *"Faça um orçamento de [item]."* — o agente faz o resto.

## 🏗️ Arquitetura

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/axiara-architecture-dark.svg" />
  <img src="assets/axiara-architecture.svg" alt="Axiara architecture" style="max-width: 100%; height: auto; width: 680px;" />
</picture>

## 🧰 Pilha tecnológica

| Camada | Escolha |
| --- | --- |
| Linguagem | Python 3.12 |
| Framework API | FastAPI |
| Framework de agentes | LangGraph |
| Agendador | APScheduler (reservado) |
| Gerenciamento de dependências | [uv](https://docs.astral.sh/uv/) |
| Armazenamento | Pessoal: SQLite · Equipe: CSV + sincronização git (cache SQLite) ou servidor SQL |

## 🧑‍💻 Início rápido para desenvolvedores

> Estrutura em construção — os comandos abaixo são a experiência alvo.

```bash
# Instalar dependências
uv sync

# Iniciar o espaço de trabalho (shell de agente interativo)
uv run axiara

# Iniciar a API REST
uv run uvicorn axiara.api.main:app --reload
```

## 📁 Estrutura do repositório

```
Axiara/
├── AGENTS.md        # Manual de operação de agentes — fluxo de trabalho e regras rígidas
├── assets/          # Ativos da marca (logo, lockup, diagramas de arquitetura — claro/escuro)
├── docs/            # Documentação de design e arquitetura (business-modes, init, templates/)
├── scripts/         # Scripts de operação (init-data.sh)
├── .github/         # Workflows de CI e release (auto-release, PR source guard)
├── .data.template/  # Esqueleto de dados de runtime → .data/ (ignorado pelo git, veja seu README)
│
# Planejado — scaffolding em andamento
├── agents/          # Definições de agentes (grafos LangGraph)
├── data/            # Camadas de dados
│   ├── main/        #   base de preços oficial (apenas edição manual)
│   ├── learn/       #   referência aprendida
│   ├── market/      #   preços de mercado rastreados
│   └── uploads/     #   tabelas/documentos fornecidos pelo usuário
├── skills/          # Pacotes de habilidades (arquivamento/consulta/cotação/revisão)
├── output/          # Entregáveis gerados (cotações, relatórios de revisão)
└── src/             # Biblioteca central
```

## 🧩 Skills

Pacotes de habilidades (fonte única em `skills/`, compatível com WorkBuddy/Codex/Claude):

| Skill | Propósito |
| --- | --- |
| **axiara-onboarding** | Inicialização do workspace (criar/entrar) — inferência pré-preenchida (moeda por idioma, fuso por SO), modelos `workspace.config.yaml` |
| **csv-data-import** | Validar e importar listas de preços para a base oficial; manifesto SHA-256, ledger, caminho de aprendizado |
| **price-crawler** | Crawling de preços de mercado de commodities — protocolo robots, pipeline de 7 etapas, confirmação antes da inserção |

## 👥 Aprendizado multiusuário (modelo hub)

Cada instância do Axiara aprende com suas próprias cotações e correções em uma **biblioteca pessoal** (local). O envio é manual e confirmado pelo usuário: diga *"enviar dados"* / *"reenviar"* / *"submeter dados"*, e seu agente exporta um pacote datado para a **biblioteca central** (`learn_inbox/<user-id>/<yyyymmdd>/bundle.yaml`, enviado para sua própria branch `user/<user-id>`). Um **agente de treinamento central** revisa todos os envios e propõe mudanças nas regras públicas; um **admin confirma** antes da atualização de `learn_shared`. O monitoramento dinâmico de escala sugere melhorias de armazenamento conforme a equipe cresce. Ver [`docs/learn-sync.md`](docs/learn-sync.md).

## 📚 Documentação

- [Modos de negócio e arquitetura](docs/business-modes.md) — modelo de permissões de dados, quatro modos, mapeamento LangGraph
- [PLAN.md](PLAN.md) — fonte única de verdade para o roteiro
- [docs/init.md](docs/init.md) — configuração inicial, guia de dados e integridade
- [docs/workspace-config.md](docs/workspace-config.md) — criar/entrar, modelos de configuração
- [docs/crawler-spec.md](docs/crawler-spec.md) · [docs/data-sources.md](docs/data-sources.md) — design do crawler e registro de fontes
- [docs/learning-plan.md](docs/learning-plan.md) · [docs/training-scenarios.md](docs/training-scenarios.md) — plano de aprendizado e cenários de usuário
- [docs/learn-sync.md](docs/learn-sync.md) · [docs/learn-sync-text.md](docs/learn-sync-text.md) · [docs/learn-sync-sql.md](docs/learn-sync-sql.md) — hub de aprendizado multiusuário
- [docs/skill-requirements.md](docs/skill-requirements.md) — backlog de skills e decisões D-SK1–11
- [docs/development-handoff.md](docs/development-handoff.md) — briefs de tarefas para agentes de codificação externos

## 🗺️ Roteiro

- [x] Inicialização do espaço de trabalho e decisões de design
- [x] Estruturação do pacote (`uv init`, layout `src/`)
- [x] Camada de armazenamento (arquivos primeiro: CSV + sync Git, cache SQLite, aplicação de permissões)
- [x] Agente de captura de preços — mecanismo crawler (protocolo robots, pipeline de 7 etapas, porta de confirmação)
- [ ] Mecanismo de cálculo de custos (modelo de custos multidimensional)
- [ ] Gerador de cotações (modelos padrão + usuário)
- [ ] Agendador de tarefas (APScheduler, sob demanda)
- [ ] Mecanismo de revisão (detecção de anomalias)
- [x] Hub de aprendizado multiusuário (fluxo de envio, revisão central, monitoramento, arquivamento)
- [ ] API REST
- [ ] Testes e reforço de CI

## 🤝 Contribuições

Contribuições são bem-vindas. Leia primeiro [PLAN.md](PLAN.md) e siga o fluxo de trabalho somente-PR: **nunca faça push direto para `main`**.

## 📄 Licença

MIT — veja [LICENSE](LICENSE).

---

*Construído com LangGraph. O painel de administração front-end (`Axiara-Web`) está planejado como um repositório separado.*

---

> **To AI agents**: If you are setting up this project, read `AGENTS.md` (operating manual) and strictly follow the setup flow in `docs/init.md`, then report back in the user's language.
