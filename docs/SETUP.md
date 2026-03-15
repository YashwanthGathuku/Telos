# TELOS Development Setup

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Orchestrator service |
| Node.js | 18+ | Desktop frontend (Tauri) |
| Rust | 1.75+ | Tauri shell + Delta Engine |
| Go | 1.22+ | Screenshot Capture Engine + Scheduler |
| .NET SDK | 8.0+ | UIGraph Windows service |

## Environment Configuration

Copy `.env.example` to `.env` and fill in provider credentials:

```powershell
Copy-Item .env.example .env
```

**Minimum required** — choose one provider block:

Azure AI Foundry (recommended for hackathon):
```
TELOS_PROVIDER=azure_foundry
AZURE_FOUNDRY_ENDPOINT=https://your-project.services.ai.azure.com
AZURE_FOUNDRY_API_KEY=your-foundry-api-key
AZURE_FOUNDRY_MODEL=gpt-4o
```

Azure OpenAI:
```
TELOS_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

Gemini:
```
TELOS_PROVIDER=gemini
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-2.0-flash
```

## Port Map

| Service | Port | Env Var | Language |
|---------|------|---------|----------|
| Orchestrator | 8080 | `ORCHESTRATOR_PORT` | Python |
| Scheduler | 8081 | `SCHEDULER_PORT` | Go |
| UIGraph | 8083 | `WINDOWS_MCP_PORT` | C# |
| Delta Engine | 8084 | `DELTA_ENGINE_PORT` | Rust |
| Screenshot Engine | 8085 | `SCREENSHOT_ENGINE_PORT` | Go |

## Service Startup Order

Start services in this order (each in a separate terminal):

1. **UIGraph** (port 8083) — no dependencies
2. **Delta Engine** (port 8084) — no dependencies
3. **Screenshot Engine** (port 8085) — no dependencies
4. **Scheduler** (port 8081) — no dependencies
5. **Orchestrator** (port 8080) — calls UIGraph, Screenshot Engine, and LLM provider
6. **Desktop** — calls Orchestrator, Scheduler

> **Tip:** Use `scripts/start-all.ps1` to start all services at once.

## Building Each Service

### Orchestrator (Python)
```powershell
cd services\orchestrator
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m services.orchestrator
```

### Scheduler (Go)
```powershell
cd services\scheduler
go build -o scheduler.exe .
.\scheduler.exe
```

### UIGraph (C#)
```powershell
cd uigraph\windows
dotnet build
dotnet run
```

### Delta Engine (Rust)
```powershell
cd uigraph\rust_engine
cargo build --release
# Binary outputs to target/release/
cargo run --release
```

### Screenshot Engine (Go)
```powershell
cd services\capture_engine
go build -o capture_engine.exe .
.\capture_engine.exe
```

### Desktop Shell (Tauri + React)
```powershell
cd apps\desktop
npm install
npm run tauri dev
```

## Running Tests

### Python Tests (from repo root)
```powershell
pip install -r tests\requirements-test.txt
python -m pytest tests\ -v
```

All 146 tests should pass. No external services or API keys are required — tests mock all external calls.

### Go Tests
```powershell
cd services\capture_engine
go test -v ./...

cd services\scheduler
go test -v ./...
```

### Rust Tests
```powershell
cd uigraph\rust_engine
cargo test
```

## Verifying Services Are Running

After starting all services, check health endpoints:

```powershell
# Orchestrator
Invoke-RestMethod http://localhost:8080/health

# Scheduler
Invoke-RestMethod http://localhost:8081/health

# UIGraph
Invoke-RestMethod http://localhost:8083/health

# Delta Engine
Invoke-RestMethod http://localhost:8084/health

# Screenshot Engine
Invoke-RestMethod http://localhost:8085/health
```

All should return `{"status": "healthy"}` or equivalent.

The orchestrator also provides a combined status endpoint:

```powershell
Invoke-RestMethod http://localhost:8080/api/status
```

This returns the health of all downstream services, active tasks, and egress metrics.

## Privacy Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `TELOS_PRIVACY_MODE` | `strict` | PII filter mode (`strict` blocks image egress) |
| `TELOS_ALLOW_IMAGE_EGRESS` | `false` | Allow VisionAgent to send screenshots to LLM |
| `TELOS_EGRESS_LOG` | `./logs/egress.jsonl` | Path for egress audit log |

In `strict` mode, the VisionAgent will refuse to capture/send screenshots.
Set `TELOS_PRIVACY_MODE=balanced` and `TELOS_ALLOW_IMAGE_EGRESS=true` to enable vision.

## Troubleshooting

**"Provider not configured"**: Check that `TELOS_PROVIDER` is set and the corresponding API key env var is populated.

**Orchestrator can't reach UIGraph**: Ensure UIGraph is running on port 8083 before starting the orchestrator. The orchestrator reports service health via `/api/status`.

**VisionAgent returns "blocked by privacy mode"**: Set `TELOS_PRIVACY_MODE=balanced` and `TELOS_ALLOW_IMAGE_EGRESS=true` in `.env`.

**Port already in use**: Check the port map above and ensure no other process is using the same port. Each service port is configurable via its respective env var.
