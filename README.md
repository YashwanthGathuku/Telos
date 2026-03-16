# TELOS — Gemini-Powered UI Navigator for Windows

> **Gemini Live Agent Challenge — UI Navigator Category**
>
> Multi-agent desktop automation system that uses Gemini 2.0 Flash with dual perception (UI Automation + multimodal vision) to understand, control, and verify actions across any Windows application.

[![Live on Cloud Run](https://img.shields.io/badge/Cloud%20Run-Live-4285F4?logo=google-cloud)](https://telos-orchestrator-777032186668.us-central1.run.app/health)
[![Gemini 2.0 Flash](https://img.shields.io/badge/Gemini-2.0%20Flash-8E24AA?logo=google)](https://ai.google.dev/)
[![Google ADK](https://img.shields.io/badge/Agent%20Framework-Google%20ADK-FB8C00)](https://google.github.io/adk-docs/)

## Architecture

![Architecture Diagram](docs/architecture_diagram.png)

TELOS has two runtime layers:

**☁️ Cloud Control Plane (Google Cloud Run)**
- FastAPI orchestrator with 5 specialized agents
- Google ADK Navigator (WebSocket live mode)
- Gemini 2.0 Flash via google-genai SDK
- Firestore for cloud-backed task memory
- Secret Manager for credential storage

**🖥️ Windows Desktop Companion (Local)**
- C# UIGraph service — Windows UI Automation bridge
- Go Capture Engine — screenshot service
- Rust Delta Engine — UI snapshot diffing
- Tauri 2 + React dashboard

This split is intentional: Gemini reasoning runs on Cloud Run, while desktop control stays on the Windows machine that owns the target UI session.

### Multi-Agent Pipeline

| Agent | Role | Perception |
|-------|------|------------|
| **Planner** | Decomposes NL tasks into ordered steps | Gemini LLM |
| **Reader** | Extracts data from app UI trees | Windows UIA |
| **Writer** | Executes clicks, keystrokes, value writes | UIGraph bridge |
| **Verifier** | Confirms actions by re-reading targets | Delegates to Reader |
| **Vision** | Screenshot + multimodal LLM interpretation | Gemini vision |
| **ADK Navigator** | WebSocket-based live interaction | Google ADK |

### Dual Perception (What Makes TELOS Different)

When UI Automation can't reach an element (custom controls, canvas apps), TELOS automatically falls back to capturing a screenshot and asking Gemini 2.0 Flash to interpret the visual layout. This makes the agent robust across all Windows applications.

### Privacy-First Design

- PII masking (SSN, email, phone, credit card) before any LLM call
- Password fields never read or transmitted
- Egress logging (JSONL audit trail) for every outbound API call
- Configurable privacy modes: `strict` | `balanced`

## Google Cloud Services Used

| Service | Purpose |
|---------|---------|
| **Cloud Run** | Orchestrator + scheduler containers |
| **Cloud Build** | Automated Docker image builds |
| **Secret Manager** | Gemini API key + API token storage |
| **Firestore** | Cloud-backed task memory |
| **Container Registry** | Docker image storage |
| **Gemini API** | LLM inference (text + multimodal) |

## Prerequisites

- **Windows 10/11** (for desktop companion services)
- **Python 3.12+**
- **Go 1.21+** (for capture engine and scheduler)
- **.NET 8.0+** (for Windows UI Automation service)
- **Node.js 18+** (for Tauri dashboard, optional)
- **Rust** (for delta engine, optional)
- **Google Cloud SDK** (for cloud deployment)

## Quick Start (Local)

### 1. Clone and configure

```powershell
git clone https://github.com/YOUR_USERNAME/Telos.git
cd Telos
Copy-Item .env.example .env
```

Edit `.env` with your values:

```env
TELOS_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.0-flash
TELOS_PRIVACY_MODE=balanced
TELOS_ALLOW_IMAGE_EGRESS=true
TELOS_MEMORY_BACKEND=sqlite
```

Get a Gemini API key at: https://aistudio.google.com/app/apikey

### 2. Install Python dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r services\orchestrator\requirements.txt
```

### 3. Start Windows companion services

**Terminal 1 — UI Automation bridge:**
```powershell
cd uigraph\windows
dotnet run
# Listening on http://localhost:8083
```

**Terminal 2 — Screenshot engine:**
```powershell
cd services\capture_engine
go run main.go
# Listening on http://localhost:8085
```

**Terminal 3 — Scheduler (optional):**
```powershell
cd services\scheduler
go run main.go
# Listening on http://localhost:8081
```

### 4. Start the orchestrator

```powershell
.\.venv\Scripts\python.exe -m services.orchestrator
# TELOS Orchestrator starting on 127.0.0.1:8080
```

### 5. Start the dashboard (optional)

```powershell
cd apps\desktop
npm install
npm run tauri -- dev
# Opens Tauri window on http://localhost:1420
```

## Verify Everything Works

```powershell
# Health checks
Invoke-RestMethod http://localhost:8080/health       # Orchestrator
Invoke-RestMethod http://localhost:8080/adk/health   # ADK Navigator
Invoke-RestMethod http://localhost:8083/health       # Windows MCP
Invoke-RestMethod http://localhost:8085/health       # Capture Engine
```

### Run the ADK Navigator

```powershell
# Single command execution
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8080/navigate `
  -ContentType application/json `
  -Body '{"task":"Open Notepad and type Hello Gemini"}'

# Stream tool activity in real-time
curl "http://localhost:8080/navigate/stream?message=Open+Calculator+and+compute+15*23"
```

### WebSocket Live Mode

Connect to `ws://localhost:8080/adk/live` and send:
```json
{"type": "text", "message": "Open Notepad and type Hello from TELOS"}
```

## Google Cloud Deployment

### Automated deployment (recommended)

```powershell
# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# One-command deploy
bash ./deploy/deploy-gcloud.sh YOUR_PROJECT_ID
```

The script automatically:
1. Enables required GCP APIs
2. Builds the Docker image via Cloud Build
3. Deploys to Cloud Run with secrets injection
4. Prints the live service URL

### Manual deployment

```powershell
# 1. Enable APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com `
  secretmanager.googleapis.com firestore.googleapis.com `
  artifactregistry.googleapis.com aiplatform.googleapis.com

# 2. Create Firestore database
gcloud firestore databases create --location=us-central1

# 3. Store secrets
echo "YOUR_GEMINI_KEY" | gcloud secrets create telos-gemini-api-key --data-file=-

# 4. Build container
gcloud builds submit --config cloudbuild.yaml --timeout=900s

# 5. Deploy to Cloud Run
gcloud run deploy telos-orchestrator `
  --image gcr.io/YOUR_PROJECT_ID/telos-orchestrator:latest `
  --platform managed --region us-central1 `
  --allow-unauthenticated `
  --set-secrets "GEMINI_API_KEY=telos-gemini-api-key:latest" `
  --set-env-vars "TELOS_PROVIDER=gemini,GEMINI_MODEL=gemini-2.0-flash,TELOS_MEMORY_BACKEND=firestore"
```

### Live deployment

- **Health**: https://telos-orchestrator-777032186668.us-central1.run.app/health
- **ADK Agent**: https://telos-orchestrator-777032186668.us-central1.run.app/adk/health

## Project Structure

```
Telos/
├── services/
│   ├── orchestrator/          # Python FastAPI orchestrator
│   │   ├── agents/            # Planner, Reader, Writer, Verifier, Vision, ADK
│   │   ├── providers/         # Gemini, Azure, GitHub Models adapters
│   │   ├── privacy/           # PII filter, egress logger
│   │   ├── memory/            # SQLite + Firestore stores
│   │   ├── bus/               # A2A async event bus
│   │   ├── middleware/        # Auth, rate limiting
│   │   └── app.py             # FastAPI application
│   ├── capture_engine/        # Go screenshot service
│   └── scheduler/             # Go cron scheduler
├── uigraph/
│   ├── windows/               # C# Windows UI Automation bridge
│   └── rust_engine/           # Rust delta engine (Axum)
├── apps/
│   └── desktop/               # Tauri 2 + React dashboard
├── deploy/
│   ├── Dockerfile.cloudrun    # Cloud Run container
│   ├── deploy-gcloud.sh       # Automated GCP deployment
│   └── docker-compose.yml     # Local multi-service setup
├── docs/
│   ├── architecture.md        # Mermaid diagram + data flow
│   ├── devpost_submission.md  # Devpost submission copy
│   └── blog_post.md           # Blog post for bonus points
└── cloudbuild.yaml            # Cloud Build configuration
```

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness check |
| `/ready` | GET | Readiness (memory + provider) |
| `/task` | POST | Submit natural language task |
| `/task/{id}` | GET | Get task status |
| `/tasks` | GET | List active tasks |
| `/navigate` | POST | Execute via ADK navigator |
| `/navigate/stream` | GET | SSE stream for navigator events |
| `/adk/live` | WS | WebSocket live agent session |
| `/adk/health` | GET | ADK agent health |
| `/events` | GET | SSE event stream (dashboard) |
| `/system/state` | GET | Full system health snapshot |
| `/models` | GET | Available Gemini models |
| `/privacy/summary` | GET | Privacy metrics |
| `/privacy/egress` | GET | Egress audit records |
| `/history` | GET | Task history |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Gemini 2.0 Flash (google-genai SDK) |
| Agent Framework | Google ADK |
| Backend | Python 3.12, FastAPI, uvicorn |
| Frontend | Tauri 2, React, Zustand, Vite |
| Desktop Services | Go, Rust (Axum), C# (.NET) |
| Cloud | Google Cloud Run, Firestore, Secret Manager, Cloud Build |
| Deployment | Docker, Infrastructure-as-Code |

## License

MIT

---

*Built for the [Gemini Live Agent Challenge](https://geminiliveagentchallenge.devpost.com/) — UI Navigator category*
