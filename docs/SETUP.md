# TELOS Development Setup

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Orchestrator |
| Node.js | 18+ | Frontend tooling |
| Rust | 1.75+ | Tauri + Delta engine |
| Go | 1.22+ | Scheduler daemon |
| .NET SDK | 8.0+ | UIGraph Windows service |

## Environment Configuration

Copy `.env.example` to `.env` and fill in provider credentials:

```bash
cp .env.example .env
```

Required variables for Azure:
```
TELOS_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

Required variables for Gemini:
```
TELOS_PROVIDER=gemini
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-pro
```

## Service Startup Order

1. **UIGraph** (port 8083) — no dependencies
2. **Scheduler** (port 8081) — no dependencies
3. **Orchestrator** (port 8080) — calls UIGraph and uses provider
4. **Desktop** — calls all three services

## Building Each Service

### Orchestrator
```bash
cd services/orchestrator
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m services.orchestrator
```

### Scheduler
```bash
cd services/scheduler
go build -o scheduler.exe .
.\scheduler.exe
```

### UIGraph
```bash
cd uigraph\windows
dotnet build
dotnet run
```

### Rust Delta Engine
```bash
cd uigraph\rust_engine
cargo build --release
cargo test
```

### Desktop Shell
```bash
cd apps\desktop
npm install
npm run tauri dev
```

## Running Tests

### Python Tests
```bash
cd services/orchestrator
pip install -r ../tests/requirements-test.txt
pytest ../../tests/ -v
```

### Rust Tests
```bash
cd uigraph/rust_engine
cargo test
```

## Verifying Services

```bash
# Health checks
curl http://localhost:8080/health
curl http://localhost:8081/health
curl http://localhost:8083/health
```

All should return `{"status": "healthy"}` or equivalent.
