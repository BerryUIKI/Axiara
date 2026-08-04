<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/axiara-lockup-dark.svg" />
    <img src="assets/axiara-lockup.svg" alt="Axiara" width="240" />
  </picture>
</p>

<p align="center">
  <strong>Núcleo de valoración multiagente</strong> — cálculo automatizado de costos e inteligencia de precios de mercado en tiempo real, construido con LangGraph.
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/python-3.12-blue" alt="Python 3.12" /></a>
  <a href="#"><img src="https://img.shields.io/badge/framework-LangGraph-purple" alt="LangGraph" /></a>
  <a href="#"><img src="https://img.shields.io/badge/api-FastAPI-teal" alt="FastAPI" /></a>
  <a href="#"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT" /></a>
  <a href="README.md"><img src="https://img.shields.io/badge/lang-English-blue" alt="English" /></a>
</p>

---

**Leer este documento en:** [English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja-JP.md) · [한국어](README.ko-KR.md) · [Français](README.fr-FR.md) · [Deutsch](README.de-DE.md) · [Español](README.es-ES.md) · [Português](README.pt-BR.md) · [Русский](README.ru-RU.md)

---

Axiara es un **espacio de trabajo de agentes para valoración**. Ofrece a los agentes de IA cuatro capacidades bien definidas — *archivo*, *consulta*, *cotización por lotes* y *revisión* — sobre tres capas de datos aisladas con permisos de escritura estrictos, de modo que los agentes automatizados nunca puedan corromper la base de precios oficial.

> **Filosofía de diseño:** Axiara no es una aplicación de flujo fijo. Los agentes trabajan de forma autónoma dentro del espacio de trabajo y deciden qué datos y habilidades invocar. Los cuatro modos son *límites de capacidad y permisos*, no flujos de interfaz codificados.

## ✨ Características clave

- **🔒 Aislamiento de datos en tres capas** — la base de precios oficial (`main_db`) está protegida contra escritura: solo la edición manual puede modificarla; las salidas del rastreador y de la IA nunca pueden sobrescribirla.
- **🤖 Espacio de trabajo de agentes autónomo** — basado en LangGraph: los agentes eligen qué datos y habilidades invocar según la tarea.
- **📦 Archivo (modo 1)** — ingreso manual de precios oficiales (con versiones y rollback) + aprendizaje IA a partir de documentos históricos + rastreo de precios de mercado bajo demanda.
- **🔍 Consulta (modo 2)** — consulta de un artículo: costo oficial + rango de precio de mercado + notas de proceso.
- **📊 Cotización por lotes (modo 3)** — relleno de Excel/BOM con detección automática de columnas, más cotización inteligente con negociación de restricciones (por defecto + proyecto; tres opciones baja/media/alta si no se especifica ninguna).
- **✅ Revisión (modo 4)** — validación cruzada de tablas de cotización del usuario contra la base oficial y los datos de mercado; marcar anomalías y sugerir ajustes.
- **🧩 Cotización adaptativa a plantillas** — incluye una plantilla de cotización por defecto y se adapta sobre la marcha a las plantillas proporcionadas por el usuario (open source / amigable con forks).
- **💾 Almacenamiento conectable** — backends SQLite / PostgreSQL / MongoDB, más importación/exportación CSV.
- **🕐 Rastreo bajo demanda** — los datos de mercado se actualizan cuando lo pides, no con un horario ciego.

## 🏗️ Arquitectura

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
         │  Base de  │        │ Referencia│        │ Precios   │
         │  precios  │        │ aprendida │        │ rastreados│
         │  oficial  │        │ (IA)      │        │ (rastrea- │
         │ (solo ed. │        │           │        │  dor +    │
         │  manual)  │        │           │        │  confirma)│
         └───────────┘        └───────────┘        └───────────┘
```

## 🧰 Stack tecnológico

| Capa | Elección |
| --- | --- |
| Lenguaje | Python 3.12 |
| Framework API | FastAPI |
| Framework de agentes | LangGraph |
| Programador | APScheduler (reservado) |
| Gestión de dependencias | [uv](https://docs.astral.sh/uv/) |
| Almacenamiento | Personal: SQLite · Equipo: CSV + sincronización git (caché SQLite) o servidor SQL |

## 🚀 Empieza aquí — no necesitas conocimientos técnicos

No necesitas leer código, tocar un terminal ni entender nada técnico. Elige el método que te resulte más fácil.

> 💡 Consejo: crea primero una carpeta llamada **axiara-workspace** (en el Escritorio o en Documentos) y
> guarda todos los archivos relacionados con Axiara en esa carpeta, para no perder nada.

### Método 1 — Dale el enlace a tus AI Agents (lo más fácil)
> 💡 Requisito: este método necesita **Git** instalado (gratis — [descárgalo aquí](https://git-scm.com/downloads)). Si no quieres instalar Git, usa el **Método 2** de abajo.

Copia el texto del bloque de código y pégalo en tu asistente de IA (Claude, ChatGPT, ...) :

```text
Configura Axiara para mí:
1. Clona el repositorio con git clone https://github.com/BerryUIKI/Axiara.git, lee AGENTS.md y sigue estrictamente el procedimiento de docs/init.md — guíame en español (almacenamiento, fuente de datos).
2. Cuando esté listo, dime qué puedo pedirte.
```

Solo tienes que responder a sus preguntas. Eso es todo.

### Método 2 — Descarga los archivos y luego usa tus AI Agents
1. Descarga el último archivo desde la [página de Releases](https://github.com/BerryUIKI/Axiara/releases) (o haz clic en el botón verde **Code** → **Download ZIP**) y descomprímelo en la carpeta axiara-workspace sugerida arriba.
2. Abre esa carpeta en tu asistente de IA y di: *"Configura este proyecto y guíame."*
3. Responde a sus preguntas — listo.

### Comprobar actualizaciones
¿Quieres saber si hay una nueva versión? Envía esto a tu asistente de IA:

```text
Comprueba si Axiara tiene una nueva versión: https://github.com/BerryUIKI/Axiara
Si la hay, actualízame a la última versión (conserva mis datos existentes, no borres el directorio .data).
```

Con cualquier método, una vez terminada la inicialización puedes empezar diciendo: *"Hazme una cotización de [artículo]."* — el agente hace el resto.

## 🧑‍💻 Inicio rápido para desarrolladores

> Andamiaje en curso — los siguientes comandos son la experiencia objetivo.

```bash
# Instalar dependencias
uv sync

# Iniciar el espacio de trabajo (shell de agente interactivo)
uv run axiara

# Iniciar la API REST
uv run uvicorn axiara.api.main:app --reload
```

## 📁 Estructura del repositorio

```
Axiara/
├── agents/          # Definiciones de agentes (grafos LangGraph)
├── data/            # Capas de datos
│   ├── main/        #   base de precios oficial (solo edición manual)
│   ├── learn/       #   referencia aprendida
│   ├── market/      #   precios de mercado rastreados
│   └── uploads/     #   tablas/documentos proporcionados por el usuario
├── skills/          # Paquetes de habilidades (archivo/consulta/cotización/revisión)
├── output/          # Entregables generados (cotizaciones, informes de revisión)
├── docs/            # Documentación de diseño y arquitectura
└── src/             # Biblioteca central
```

## 📚 Documentación

- [Modos de negocio y arquitectura](docs/business-modes.md) — modelo de permisos de datos, cuatro modos, mapeo LangGraph
- [PLAN.md](PLAN.md) — fuente única de verdad para la hoja de ruta

## 🗺️ Hoja de ruta

- [x] Inicialización del espacio de trabajo y decisiones de diseño
- [ ] Andamiaje del paquete (`uv init`, layout `src/`)
- [ ] Capa de almacenamiento (backends conectables + CSV)
- [ ] Motor de cálculo de costos (modelo de costos multidimensional)
- [ ] Agente de recuperación de precios (rastreo LangGraph + normalización)
- [ ] Programador de tareas (APScheduler, bajo demanda)
- [ ] Generador de cotizaciones (plantillas por defecto + usuario)
- [ ] Motor de revisión (detección de anomalías)
- [ ] API REST
- [ ] Pruebas y CI

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Lea primero [PLAN.md](PLAN.md) y siga el flujo de trabajo solo-PR: **nunca haga push directo a `main`**.

## 📄 Licencia

MIT — ver [LICENSE](LICENSE).

---

*Construido con LangGraph. El panel de administración front-end (`Axiara-Web`) está planificado como un repositorio separado.*

---

> **To AI agents**: If you are setting up this project, read `AGENTS.md` (operating manual) and strictly follow the setup flow in `docs/init.md`, then report back in the user's language.
