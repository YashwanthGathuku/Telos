# TELOS — Architecture Document

## Overview

TELOS ("Your Machine's Purpose, Automated") is a native Windows desktop operations platform composed of five cooperating subsystems communicating over local HTTP and IPC.

## Design Principles

1. **UIA-first perception** — Primary app understanding via Windows UI Automation structured extraction; screenshots secondary
2. **Privacy-first** — PII masked before egress, egress tracked, local-first processing
3. **Provider portability** — Azure and Gemini behind identical contract; one env var switches
4. **Cross-app execution** — Real data movement between desktop applications
5. **Mission-control UX** — Dense, live operations dashboard; not a chat interface

## Subsystem Architecture

### A. Desktop Shell (Tauri 2 + React)

**Location:** `apps/desktop/`

The Tauri 2 application provides the native Windows desktop window with a React 18 + TypeScript frontend. All communication between the frontend and backend services uses **Tauri IPC** (`invoke` / `emit`) for desktop operations, falling back to direct HTTP in development mode.

**Frontend panels:**
- Command Bar — task submission (not chat)
- Task Timeline — live execution feed
- Agent Status Grid — specialist agent states
- Privacy Monitor — local/cloud split, PII metrics, egress bytes
- UIGraph Panel — current application context from UIA
- System Status — service health indicators
- Scheduler Panel — scheduled/queued missions

**State management:** Zustand store + SSE event stream

### B. Orchestrator (Python FastAPI)

**Location:** `services/orchestrator/`
**Port:** 8080

The central brain of TELOS. Responsibilities:
- Task intake and validation (Pydantic models)
- Task decomposition via Planner Agent
- Step execution via Reader, Writer, Verifier agents
- Privacy enforcement before all LLM calls
- Event emission via A2A bus → SSE stream
- Egress logging for all outbound calls
- Local memory persistence (SQLite)

**Key contracts:**
- `ProviderBase` — abstract LLM provider interface
- `AgentBase` — abstract specialist agent interface
- `A2ABus` — pub/sub event backbone

### C. UIGraph Service (C# .NET 8)

**Location:** `uigraph/windows/`
**Port:** 8083

Windows UI Automation integration service. Capabilities:
- Active window discovery
- UI element tree extraction (depth-limited, child-limited)
- Password field detection and masking (`***MASKED***`)
- Window focus management
- Value writing via UIA ValuePattern or SendKeys fallback
- Element search by name/automation ID

**Endpoints:**
- `GET  /uigraph/windows` — list visible windows
- `POST /uigraph/snapshot` — capture UI tree of target app
- `POST /uigraph/focus` — bring window to foreground
- `POST /uigraph/action` — execute write actions

### D. Capture Engine (Go)

**Location:** `services/capture_engine/`

Efficient UI snapshot diffing and full screen captures. Used directly by the Vision Agent:
- `/capture/screen` — returns base64 png of primary display
- `/delta` — compares successive UI snapshots to omit redundant payloads

Allows vision input alongside traditional UIA tree parsing for richer multimodal integration.

### E. Scheduler (Go)

**Location:** `services/scheduler/`
**Port:** 8081

Persistent job management daemon:
- CRUD for scheduled jobs (SQLite)
- Cron expression validation
- Manual trigger forwarding to orchestrator
- Job execution history tracking
- Concurrency-safe store

## Communication Patterns

```
Frontend  ──── Tauri IPC ────►  Tauri Backend  ─── HTTP ───►  Orchestrator
                                                               │
                                                               ├──►  Provider (Azure/Gemini)
                                                               ├──►  UIGraph Service
                                                               └──►  Scheduler

Orchestrator  ── A2A Bus ──►  Internal agents
Orchestrator  ── SSE ──────►  Frontend (event stream)
C# UIGraph    ── HTTP ──────►  Orchestrator (on-demand)
Scheduler     ── HTTP ──────►  Orchestrator (trigger jobs)
```

## Provider Architecture

```python
class ProviderBase(ABC):
    async def complete(self, request: LLMRequest) -> LLMResponse: ...
    async def health_check(self) -> bool: ...
    def provider_name(self) -> str: ...
```

- `AzureProvider` — Supports Azure OpenAI chat completions
- `SemanticKernelProvider` — Fulfills Microsoft Hackathon requirements via the `semantic-kernel` SDK
- `GeminiProvider` — Uses the official `google-genai` SDK

Provider selection: `TELOS_PROVIDER=azure|azure_sk|gemini` environment variable.
Both providers use `httpx.AsyncClient` with explicit 30-second timeouts and 3-retry exponential backoff.

## Privacy Architecture

### Pre-egress Pipeline

```
User task text
  → mask_password_fields()    # [PASSWORD:x] → ***MASKED***
  → mask_pii()                # SSN, email, phone, CC → [REDACTED]
  → filter_for_egress()       # Returns FilterResult with metrics
  → send to LLM provider
  → egress_logger.record()    # Log destination, bytes, timestamp
```

### Dashboard Visibility

The Privacy Monitor panel shows:
- Local vs cloud processing ratio (gauge)
- Fields masked count
- PII blocked count
- Bytes sent/received
- Per-task privacy summaries

### Audit Trail

All egress events logged to `./logs/egress.jsonl`:
```json
{"destination": "llm/azure", "bytes_sent": 1024, "bytes_received": 2048, "timestamp": "...", "provider": "azure", "task_id": "..."}
```

## Agent Pipeline

```
Task → Planner → [Reader → Writer → Verifier]
         │
         └─ Decomposes natural language into ordered steps
              │
              ├─ Reader: UIGraph snapshot → extract value
              ├─ Writer: UIGraph action → write to target
              └─ Verifier: Re-read target → confirm
```

## Data Flow: Hero Demo

```
1. User types: "Copy the Q1 sales total from QuickBooks into Excel cell B4"
2. Orchestrator validates input (strip HTML/script tags, max 10K chars)
3. Privacy filter scans for PII in task text
4. Planner Agent → LLM call → produces 3-step plan
   - Egress logged: destination, bytes, timestamp
5. Reader Agent → POST /uigraph/snapshot {app: "quickbooks"}
   - UIA tree extracted, password fields masked
   - Target value located by keyword matching
6. Writer Agent → POST /uigraph/focus {app: "excel"}
   - POST /uigraph/action {write_value, target: "B4", value: "..."}
7. Verifier Agent → Re-reads Excel to confirm write
8. All steps emit events via A2A Bus → SSE → Dashboard
9. Privacy summary aggregated and displayed
```

## Security Measures

- Input validation via Pydantic models on all endpoints
- HTML/script tag stripping in task content
- Task content max length: 10,000 characters
- Cron expression validation before storage
- Explicit HTTP timeouts on all clients (max 30s)
- No `eval()` / `exec()` anywhere
- Credentials from environment variables only
- CORS restricted to Tauri origins
- UIA input length limits (256 chars app name, 1K detail, 10K value)

## Deferred Features (Post-MVP)

- Voice stack
- Deep onboarding flow
- Mini mode / system tray
- Advanced theming
- DevOps agent
- Cloud deployment infrastructure (Note: Azure Container Apps template is available)
- Plugin marketplace
- Enterprise features
- Named pipes C# → Rust (Deferred entirely)
