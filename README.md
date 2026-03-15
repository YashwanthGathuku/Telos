# TELOS — Your Machine's Purpose, Automated

> A native Windows desktop operations platform that reads open applications through Windows UI Automation as structured text, coordinates specialist agents, and executes cross-application tasks — all visible through a premium mission-control dashboard.

![Platform](https://img.shields.io/badge/platform-Windows-blue)
![Privacy](https://img.shields.io/badge/privacy-first-green)
![Provider](https://img.shields.io/badge/provider-Azure%20%7C%20Gemini-purple)

---

## What is TELOS?

TELOS is a **desktop operations layer** — not a chatbot, not a browser agent, not a macro recorder.

It understands your running Windows applications as **structured UI state** (via Windows UI Automation), then coordinates specialist agents to:
- **Read** data from source applications
- **Write** values into target applications
- **Verify** that actions completed correctly
- **Schedule** repeatable automation tasks

All of this is visible through a real-time **Mission Control dashboard** that shows task progress, agent status, privacy metrics, and application context.

## Key Differentiators

| Feature | TELOS | Generic Chatbot Wrappers |
|---------|-------|--------------------------|
| **Perception** | Structured UI Automation (not screenshots) | Screenshot/OCR first |
| **Privacy** | PII masked, egress tracked, local-first | Data sent freely to cloud |
| **Cross-app** | Real data movement between desktop apps | Single-app or browser only |
| **UX** | Mission-control dashboard | Chat bubble interface |
| **Providers** | Azure & Gemini via one env var | Single provider locked |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TELOS Mission Control (Tauri 2 + React)       │
│  ┌──────────┬────────────┬──────────┬───────────┬────────────┐  │
│  │ Command  │  Task      │  Agent   │  Privacy  │  UIGraph   │  │
│  │ Bar      │  Timeline  │  Grid    │  Monitor  │  Panel     │  │
│  └──────────┴────────────┴──────────┴───────────┴────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                    Tauri IPC Bridge                              │
├──────────┬────────────────┬─────────────────────────────────────┤
│          │                │                                      │
│  ┌───────▼────────┐  ┌───▼──────────┐  ┌────────────────────┐ │
│  │  Orchestrator   │  │  Scheduler   │  │  UIGraph Service   │ │
│  │  (FastAPI:8080) │  │  (Go:8081)   │  │  (C#:8083)         │ │
│  │                 │  │              │  │                     │ │
│  │  ┌─────────┐   │  │  SQLite      │  │  Win UI Automation  │ │
│  │  │ Planner │   │  │  Cron eval   │  │  Element extraction │ │
│  │  │ Reader  │   │  │  Job history  │  │  Action execution   │ │
│  │  │ Writer  │   │  └──────────────┘  │  Password masking   │ │
│  │  │ Verify  │   │                    │                     │ │
│  │  └─────────┘   │                    │  ┌───────────────┐  │ │
│  │                 │                    │  │ Rust Delta    │  │ │
│  │  ┌─────────┐   │                    │  │ Engine        │  │ │
│  │  │ Privacy │   │                    │  └───────────────┘  │ │
│  │  │ Filter  │   │                    └────────────────────┘ │
│  │  │ Egress  │   │                                           │
│  │  └─────────┘   │                                           │
│  │                 │           ┌───────────────┐               │
│  │  ┌─────────┐   │           │ Provider Layer │               │
│  │  │ A2A Bus │   │◄─────────►│ Azure │ Gemini │               │
│  │  └─────────┘   │           └───────────────┘               │
│  │                 │                                           │
│  │  ┌─────────┐   │                                           │
│  │  │ Memory  │   │                                           │
│  │  │ (SQLite)│   │                                           │
│  │  └─────────┘   │                                           │
│  └─────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘
```

## Hero Demo Path

```
User → "Copy the Q1 sales total from QuickBooks into Excel cell B4"
  ↓
Planner Agent → decomposes into: READ → WRITE → VERIFY
  ↓
Reader Agent → UIGraph reads QuickBooks via Windows UI Automation
  ↓
Writer Agent → UIGraph writes value into Excel cell B4
  ↓
Verifier Agent → Re-reads Excel to confirm write
  ↓
Dashboard → Shows live progress, privacy metrics, agent states
```

## Quick Start

### Prerequisites
- Windows 10/11
- Node.js 18+
- Python 3.11+
- Go 1.22+
- .NET 8 SDK
- Rust (MSVC target recommended for Tauri build)
- Visual Studio Build Tools with MSVC (`link.exe`)

### Setup

```bash
# 1. Clone and configure
git clone <repo-url> && cd telos
cp .env.example .env
# Edit .env with your provider credentials
# Optional: set TELOS_API_TOKEN for protected deployments

# 2. Start the orchestrator
cd services/orchestrator
pip install -r requirements.txt
python -m services.orchestrator

# 3. Start the scheduler
cd services/scheduler
go run main.go

# 4. Start the Capture Engine (Go — port 8085)
cd services/capture_engine
go run main.go

# 5. Start the UIGraph service (C#)
cd uigraph/windows
dotnet run

# 6. Start the desktop app
cd apps/desktop
npm install
npm run tauri dev
```

### Provider Switching

One environment variable controls which AI provider TELOS uses:

```bash
# Azure OpenAI
TELOS_PROVIDER=azure

# Azure OpenAI via Semantic Kernel
TELOS_PROVIDER=azure_sk

# Google Gemini
TELOS_PROVIDER=gemini
```

Both providers implement the same contract (`ProviderBase`). No code changes required.

### API Authentication

Set `TELOS_API_TOKEN` to require authentication on every route except `/health` and `/ready`.

```bash
TELOS_API_TOKEN=replace-me
```

Clients can authenticate with either:
- `Authorization: Bearer <token>`
- `X-Telos-Api-Token: <token>`
- `?access_token=<token>` for the SSE event stream

If the scheduler must call an orchestrator with a different token, set `ORCHESTRATOR_API_TOKEN` or `TELOS_INTERNAL_TOKEN`.

## Project Structure

```
telos/
├── apps/desktop/           # Tauri 2 + React Mission Control
│   ├── src/                # React TypeScript frontend
│   └── src-tauri/          # Rust Tauri backend
├── services/
│   ├── orchestrator/       # Python FastAPI (port 8080)
│   │   ├── agents/         # Planner, Reader, Writer, Verifier, Vision
│   │   ├── bus/            # A2A event bus
│   │   ├── memory/         # SQLite / Firestore memory
│   │   ├── privacy/        # PII filter + egress logger
│   │   └── providers/      # Azure, Gemini, SK, Foundry adapters
│   ├── scheduler/          # Go daemon (port 8081)
│   └── capture_engine/     # Go screenshot service (port 8085)
├── deploy/                 # Docker and Azure deployment artifacts
├── uigraph/
│   ├── windows/            # C# Windows UI Automation (port 8083)
│   └── rust_engine/        # Rust visual delta engine (port 8084)
├── tests/                  # Python test suite (146 tests)
├── docs/                   # Architecture, setup, and hackathon docs
├── .env.example            # Configuration template
├── ARCHITECTURE.md         # Detailed architecture document
└── README.md               # This file
```

## Privacy Architecture

TELOS is **privacy-first** by design:

- **Password fields** detected by UIA are always masked as `***MASKED***`
- **PII** (SSN, email, phone, credit card) is redacted before any LLM call
- **Vision uploads are opt-in in strict mode** — raw screenshots are blocked unless `TELOS_ALLOW_IMAGE_EGRESS=true`
- **Egress tracking** — every outbound API call logs destination, bytes, timestamp
- **Local/cloud split** — visible in the dashboard's Privacy Monitor panel
- **Audit trail** — JSONL egress log at `./logs/egress.jsonl`

## Testing

```bash
# Run Python tests
cd telos
pip install -r tests/requirements-test.txt
pytest

# Run Rust delta engine tests
cd uigraph/rust_engine
cargo test

# Run Go scheduler tests
cd ../../services/scheduler
go test ./...

# Run Go capture-engine tests
cd ../capture_engine
go test ./...

# Build the frontend
cd ../../apps/desktop
npm run build

# Check the Tauri backend with the Windows MSVC toolchain
cd src-tauri
cargo +stable-x86_64-pc-windows-msvc check --target x86_64-pc-windows-msvc

# Build the desktop installer bundle
cd ..
npm run tauri:build:msvc
```

## Production Readiness Checklist

- Set `TELOS_API_TOKEN` and store the same bearer token in the desktop Settings panel.
- Set `ORCHESTRATOR_API_TOKEN` for the scheduler when using a distinct internal token.
- Keep `TELOS_ALLOW_IMAGE_EGRESS=false` unless you have approved screenshot uploads.
- Verify `/health` and `/ready` for orchestrator, scheduler, and capture engine before demo or deployment.
- Run `pytest`, `go test ./...`, `npm run build`, `npm run tauri:check:msvc`, and `dotnet build` on a Windows machine with the full toolchain installed.
- Use the MSVC Rust toolchain for the Tauri app; the repo now pins `apps/desktop/src-tauri` to `x86_64-pc-windows-msvc`.

## Limitations (MVP)

- UIGraph integration requires target applications to have UIA support
- Hero demo path uses Notepad/Excel as substitutes when QuickBooks is unavailable
- Semantic Kernel provider does not yet surface token-level usage metrics (byte-level tracking is accurate)
- Firestore backend requires manual composite index creation (see docs/SETUP.md)

## Microsoft AI Dev Day Hackathon

TELOS targets the **AI Agent using Microsoft Agent Framework** category.

### Technologies Used

| Microsoft Technology | Where in Code |
|---------------------|---------------|
| **Semantic Kernel** (`semantic-kernel` SDK) | `services/orchestrator/providers/semantic_kernel_provider.py` |
| **Azure AI Foundry** | `services/orchestrator/providers/foundry_provider.py` |
| **Azure OpenAI** | `services/orchestrator/providers/azure_provider.py` |
| **Model Context Protocol (MCP)** | `services/orchestrator/mcp_server.py` |
| **Azure Container Apps** | `deploy/azure-deploy.yaml` |
| **GitHub Copilot Agent Mode** | `.github/copilot-instructions.md` |
| **VS Code** | Primary development environment |

See [docs/HACKATHON_TECH_MAP.md](docs/HACKATHON_TECH_MAP.md) for detailed requirement mapping with file-level evidence.

### How GitHub Copilot Agent Mode Was Used

TELOS was developed using GitHub Copilot Agent Mode in VS Code as the primary AI-assisted development workflow:
- **Code generation**: Agent mode generated the polyglot service implementations across Python, Go, Rust, C#, and TypeScript
- **Code review**: Agent mode performed deep security/privacy audits and identified PII leakage in SSE payloads
- **Test authoring**: E2E hero tests and privacy masking tests were co-authored with Copilot
- **Architecture hardening**: Agent mode identified port conflicts, CORS issues, and deployment misconfigurations
- **Documentation**: Hackathon tech mapping, architecture docs, and this README were reviewed/improved with Copilot

The `.github/copilot-instructions.md` file contains project-specific instructions that guide Copilot Agent Mode to maintain TELOS's privacy-first, Windows-first, polyglot engineering standards.

## License

MIT — see [LICENSE](LICENSE)
