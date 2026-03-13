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
- Rust (for Tauri build)

### Setup

```bash
# 1. Clone and configure
git clone <repo-url> && cd telos
cp .env.example .env
# Edit .env with your provider credentials

# 2. Start the orchestrator
cd services/orchestrator
pip install -r requirements.txt
python -m services.orchestrator

# 3. Start the scheduler
cd services/scheduler
go run main.go

# 4. Start the Capture Engine (Go)
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

# Google Gemini
TELOS_PROVIDER=gemini
```

Both providers implement the same contract (`ProviderBase`). No code changes required.

## Project Structure

```
telos/
├── apps/desktop/           # Tauri 2 + React Mission Control
│   ├── src/                # React TypeScript frontend
│   └── src-tauri/          # Rust Tauri backend
├── services/
│   ├── orchestrator/       # Python FastAPI (port 8080)
│   │   ├── agents/         # Planner, Reader, Writer, Verifier
│   │   ├── bus/            # A2A event bus
│   │   ├── memory/         # SQLite local memory
│   │   ├── privacy/        # PII filter + egress logger
│   │   └── providers/      # Azure + Gemini adapters
│   └── scheduler/          # Go daemon (port 8081)
├── uigraph/
│   ├── windows/            # C# Windows UI Automation (port 8083)
├── tests/                  # Python test suite
├── docs/                   # Architecture and demo docs
├── .env.example            # Configuration template
├── ARCHITECTURE.md         # Detailed architecture document
└── README.md               # This file
```

## Privacy Architecture

TELOS is **privacy-first** by design:

- **Password fields** detected by UIA are always masked as `***MASKED***`
- **PII** (SSN, email, phone, credit card) is redacted before any LLM call
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
```

## Limitations (MVP)

- UIGraph integration requires target applications to have UIA support
- Hero demo path uses Notepad/Excel as substitutes when QuickBooks is unavailable

## License

MIT — see [LICENSE](LICENSE)
