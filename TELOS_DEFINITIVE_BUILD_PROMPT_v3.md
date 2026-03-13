# TELOS — DEFINITIVE ONE-SHOT BUILD PROMPT v3.0

> **Copy this entire prompt into Claude Code / Cursor / your AI coding tool.**
> **It contains EVERYTHING needed to build the complete TELOS project.**
> **Owner: Yashwanth Gathuku | DigitalSvarga LLC | All Rights Reserved**
> **Deadlines: March 15 (Microsoft) | March 16 (Gemini) | Windows-only MVP**

---

## 0. IDENTITY & IP

**TELOS** = "Your Machine's Purpose, Automated."
- Built by **DigitalSvarga LLC** (Yashwanth Gathuku, Founder & CEO)
- **IP Ownership**: DigitalSvarga retains 100% ownership. Microsoft gets royalty-free license for promotional use only. UIGraph Engine + Privacy Filter are proprietary IP.
- **License**: Apache 2.0 + Commons Clause on public repo. UIGraph core + Privacy Filter algo in private repo.
- **Public repo**: scaffold, dashboard, adapters, docs. **Private repo**: UIGraph core engine, privacy filter algorithms.

---

## 1. ONE-SENTENCE BUILD SCOPE

**TELOS is a native Windows desktop application (Tauri 2.0) that uses Windows UI Automation to read any open app as structured text — NOT screenshots — then coordinates 4 specialist AI agents via a local orchestrator to execute cross-app tasks privately, on schedule, with a live mission-control dashboard.**

### What We Are NOT Building (Hard Scope Cuts)
macOS port | Mobile app | Skill marketplace | Developer SDK | Multi-user/RBAC | Full Titans/MIRAS memory integration | 7 agents (cut to 4+1) | Always-on voice/wake-word | Enterprise SSO | Cloud tier | Always-on vision model | Full DevOps platform | OpenClaw-style chat bubble UI

### Critical Identity Rule
TELOS is a **NASA operations center crossed with a fintech trading terminal** — NOT a chatbot. No message bubbles. No chat history. No sidebar widget. A full standalone flight-control DASHBOARD with real-time data panels, agent status cards, and a live privacy counter.

---

## 2. DUAL HACKATHON REQUIREMENTS

### Hackathon 1: Microsoft AI Dev Days Global Hackathon
- **Deadline**: March 15, 2026 at 11:59 PM Pacific
- **Platform**: Microsoft Innovation Studio
- **MANDATORY TECH**: Azure AI Foundry (model routing), Azure Agent Framework / Semantic Kernel, Azure MCP (Model Context Protocol), GitHub Copilot Agent Mode, public GitHub repo, VS Code/Visual Studio
- **JUDGING (equally weighted Stage Two)**:
  1. **Technical Implementation** — code quality, documentation, use of hero technologies (Foundry, Agent Framework, Azure MCP, Copilot Agent Mode)
  2. **Innovation & Creativity** — Agentic AI patterns, agent orchestration sophistication, MCP integration, multi-agent collaboration
  3. **Real-World Impact** — meaningful problem, practical, usable
- **TARGET CATEGORIES**: Challenge 2 (Build AI Apps) — lead with UIGraph + Privacy Shield + cross-app demo. Challenge 1 (Agentic DevOps) — lead with DevOps Agent + Azure Monitor + GitHub integration. **Same codebase, two submissions. One project, maximum prize exposure.**
- **PRIZES**: Grand Prize $20K + Build 2026 ticket + 1:1 MS session. Category Prize $10K + Build ticket.
- **SUBMISSION**: Public GitHub repo, 2-min demo video (YouTube), architecture diagram, project description

### Hackathon 2: Gemini Live Agent Challenge (Google / Devpost)
- **Deadline**: March 16, 2026 at 5:00 PM Pacific (ONE EXTRA DAY)
- **Platform**: geminiliveagentchallenge.devpost.com
- **MANDATORY TECH**: Gemini model (Gemini 3 / 2.5-Flash), Google GenAI SDK or Agent Development Kit (ADK), at least one Google Cloud service (Cloud Run / Firestore / Vertex AI), multimodal inputs and outputs required
- **TARGET CATEGORY: "UI Navigator"** — "Build an agent that becomes the user's hands on screen. The agent observes the browser or device display, interprets visual elements, and performs actions based on user intent."
  - **Mandatory Tech**: Must use Gemini multimodal to interpret screenshots/screen recordings and output executable actions. Agents hosted on Google Cloud.
- **JUDGING**: Stage 1 pass/fail → Stage 2 equally weighted (innovation, technical execution, impact, UX) → Stage 3 bonus: blog/video content (+0.6 points, use #GeminiLiveAgentChallenge)
- **PRIZES**: Grand Prize $25K + $3K Google Cloud credits + 2 Cloud Next 2026 tickets (Las Vegas) + travel stipends + demo opportunity at Next. Best UI Navigator: $10K + $1K credits + 2 Next tickets.
- **SUBMISSION**: Devpost project page, demo video under 4 minutes (multimodal features in action, no mockups + pitch), architecture diagram (Gemini → backend → database → frontend), ~200 word Gemini integration write-up, public code repo URL, public demo link (no login required), NEW project, English. Optional blog post for bonus points.

### THE ADAPTER SWAP STRATEGY
`provider_azure.py` and `provider_gemini.py` implement the SAME interface (`ProviderBase`). To switch hackathons: change ONE environment variable `TELOS_PROVIDER=azure` → `TELOS_PROVIDER=gemini`. Zero other code changes. Enforced by abstract base class contract.

### CRITICAL: HYBRID UIGraph FOR GEMINI
TELOS's primary path is Windows UIA (zero screenshots, structured text). But the Gemini UI Navigator category **requires** Gemini multimodal to interpret screenshots. **Solution**: Add a Vision Verification layer — the UIGraph Engine's primary data comes from UIA, but a secondary Gemini multimodal path captures periodic screenshots for visual verification, fallback for apps with poor UIA support, and to satisfy the Gemini multimodal requirement. This makes TELOS the ONLY UI Navigator agent that does BOTH structured-text AND visual understanding — a massive differentiator.

---

## 3. FULL SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────┐
│         TELOS DESKTOP APP (Tauri 2.0 — Windows Native)              │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │    MISSION CONTROL UI (React 18 + TypeScript + Tailwind)     │   │
│  │    Rendered by: WebView2 (native OS renderer, NOT Chromium)  │   │
│  │                                                               │   │
│  │  [Agent Grid] [Task Timeline] [Privacy Meter] [Cron Board]   │   │
│  │  [MCP Status] [UIGraph View]  [DevOps Panel]  [Memory Log]   │   │
│  └────────────────────┬─────────────────────────────────────────┘   │
│                       │ Tauri IPC (invoke/emit — NOT HTTP)           │
│  ┌────────────────────▼─────────────────────────────────────────┐   │
│  │         TAURI RUST SHELL (src-tauri/src/main.rs)              │   │
│  │  Process Manager │ IPC Bridge │ System Tray │ Hotkeys         │   │
│  │  Spawns & monitors all sidecar processes                      │   │
│  └────────┬────────────────┬──────────────────┬─────────────────┘   │
└───────────│────────────────│──────────────────│─────────────────────┘
            │ spawn          │ spawn            │ COM/named pipe
  ┌─────────▼──────┐ ┌──────▼──────────┐ ┌────▼───────────────────┐
  │    PYTHON      │ │  GO SCHEDULER   │ │   UIGRAPH ENGINE       │
  │  ORCHESTRATOR  │ │    DAEMON       │ │   (C# + Rust)          │
  │  (FastAPI +    │ │  (Windows svc)  │ │                        │
  │   asyncio)     │ │  SQLite jobs    │ │  C#: UIA event hooks   │
  │                │ │  REST :8081     │ │  Rust: delta + privacy │
  │  Agent Router  │ │  Cron engine    │ │  Windows MCP :8083     │
  │  A2A bus       │ │  Retry logic    │ │                        │
  │  mem0 local    │ │  Job history    │ │  → Reads ALL open apps │
  │  REST :8080    │◄┤                 │ │    as structured text  │
  │                │ └─────────────────┘ │  No screenshots ever   │
  │  PROVIDER      │                     │  (+ Gemini vision      │
  │  ADAPTER FILE  │◄── Single swap:     │    fallback for        │
  └───────┬────────┘    provider_azure/   │    Devpost category)   │
          │             gemini.py         └────────────────────────┘
  ┌───────▼──────────────────────────────────────────────────────┐
  │        MCP MESH (3 servers — local + azure + web)            │
  │  Windows MCP :8083 │ Azure MCP :8084 │ Web MCP :8085        │
  └───────────────────────────────────────────────────────────────┘
          │                    │                    │
  Local Windows Apps     Azure AI Foundry     Playwright Browser
  (Excel, QuickBooks)    (Model routing)      (Web automation)
```

**Why Tauri 2.0 (not Electron/PyQt/Streamlit):**
~30MB RAM idle (WebView2) vs Electron's 150-400MB. ~8MB installer. Native Rust IPC. System tray. Hotkeys. Process management. Judges will be impressed — it's the smallest, fastest, most modern choice.

---

## 4. MONOREPO STRUCTURE

```
telos/                          ← Public GitHub repo (hackathon submission)
├── README.md                   ← Hero README: arch diagram + demo GIF + badges
├── ARCHITECTURE.md             ← Full architecture for judges
├── NOTICE.md                   ← IP notice: UIGraph + Privacy Filter proprietary
├── LICENSE                     ← Apache 2.0 + Commons Clause
├── .github/
│   ├── copilot-instructions.md ← GitHub Copilot context (MS requirement)
│   └── workflows/
│       └── ci.yml              ← CI/CD: pytest + go test + cargo test + vitest
│
├── apps/
│   └── desktop/                ← Tauri 2.0 desktop application root
│       ├── src-tauri/          ← Rust Tauri shell
│       │   ├── src/
│       │   │   ├── main.rs     ← Tauri entry + process spawner
│       │   │   ├── commands.rs ← IPC command handlers
│       │   │   └── tray.rs     ← System tray + hotkey logic
│       │   ├── Cargo.toml
│       │   └── tauri.conf.json ← App config + sidecar declarations
│       │
│       └── src/                ← React/TS frontend
│           ├── main.tsx
│           ├── App.tsx
│           ├── components/
│           │   ├── CommandBar.tsx       ← NL input (Ctrl+Space global hotkey)
│           │   ├── AgentGrid.tsx        ← Live agent status cards (4+1 agents)
│           │   ├── TaskTimeline.tsx     ← Task execution timeline
│           │   ├── PrivacyMeter.tsx     ← Live byte counter + egress chart
│           │   ├── CronBoard.tsx        ← Scheduled jobs management
│           │   ├── UIGraphView.tsx      ← Live element tree of active app
│           │   ├── DevOpsPanel.tsx      ← CI/CD monitoring (Challenge 1)
│           │   ├── MemoryLog.tsx        ← Memory store browser
│           │   ├── OnboardingWizard.tsx ← [NEW] 3-step first-run setup
│           │   ├── QuickActions.tsx     ← [NEW] Pinned frequent tasks
│           │   └── StatusBar.tsx        ← [NEW] Bottom bar: uptime, model, version
│           ├── hooks/
│           │   ├── useTelos.ts          ← Zustand store + Tauri IPC bridge
│           │   └── useTheme.ts          ← [NEW] Theme management
│           └── styles/
│               └── globals.css          ← Tailwind + glassmorphism tokens
│
├── services/
│   ├── orchestrator/           ← Python FastAPI orchestrator
│   │   ├── main.py             ← FastAPI app entry + lifespan
│   │   ├── config.py           ← TELOS_PROVIDER env var + all config
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py ← Main router agent (task decomposition)
│   │   │   ├── uigraph_agent.py← Windows UI agent (talks to MCP :8083)
│   │   │   ├── memory_agent.py ← mem0 local memory (store/recall)
│   │   │   └── scheduler_agent.py ← Cron interface agent (talks to Go :8081)
│   │   ├── bus/
│   │   │   └── a2a.py          ← A2A asyncio pub/sub message bus
│   │   ├── providers/
│   │   │   ├── __init__.py     ← get_provider() — reads TELOS_PROVIDER env
│   │   │   ├── provider_base.py← Abstract base class (THE CONTRACT)
│   │   │   ├── provider_azure.py ← ★ SWAP FILE: Azure AI Foundry adapter
│   │   │   └── provider_gemini.py← ★ SWAP FILE: Gemini GenAI SDK adapter
│   │   ├── privacy/
│   │   │   ├── filter.py       ← PII masking layer (regex + pattern match)
│   │   │   ├── byte_counter.py ← Egress byte tracking
│   │   │   └── audit_log.py    ← Privacy audit JSON logger
│   │   └── memory/
│   │       └── store.py        ← mem0 local vector store wrapper (ChromaDB)
│   │
│   ├── scheduler/              ← Go cron daemon
│   │   ├── main.go             ← Entry + Gin router
│   │   ├── jobs/jobs.go        ← Job CRUD + cron engine
│   │   ├── store/sqlite.go     ← SQLite persistence
│   │   └── api/rest.go         ← REST endpoints (:8081)
│   │
│   ├── devops_agent/           ← Python DevOps agent (Challenge 1: Agentic DevOps)
│   │   ├── watcher.py          ← GitHub Actions monitor (webhook/polling)
│   │   └── analyzer.py         ← LLM root cause analysis + issue creation
│   │
│   └── voice/                  ← [NEW] Voice input sidecar
│       └── whisper_sidecar.py  ← faster-whisper push-to-talk (P2)
│
├── uigraph/                    ← UIGraph ENGINE (public: interface only)
│   ├── windows/                ← C# UIA subscriber
│   │   ├── UIGraphSubscriber.cs← 3 UIA event types + named pipe writer
│   │   └── UIGraphSubscriber.csproj
│   ├── rust_engine/            ← Rust delta engine
│   │   ├── src/
│   │   │   ├── lib.rs
│   │   │   ├── delta.rs        ← DeltaEngine: graph HashMap + diff
│   │   │   ├── privacy.rs      ← PrivacyFilter: PII pattern scan
│   │   │   └── pipe.rs         ← Named pipe IPC reader
│   │   └── Cargo.toml
│   ├── bridge/
│   │   └── mcp_server.py       ← Windows MCP server (5 tools, :8083)
│   └── vision/                 ← [NEW] Gemini vision fallback
│       └── screenshot_agent.py ← Periodic screenshot → Gemini multimodal
│
├── tests/
│   ├── unit/
│   │   ├── test_provider_azure.py
│   │   ├── test_provider_gemini.py
│   │   ├── test_a2a_bus.py
│   │   ├── test_privacy_filter.py
│   │   ├── test_memory_store.py
│   │   └── test_orchestrator.py
│   ├── contracts/
│   │   └── test_provider_contract.py ← SAME suite runs against BOTH adapters
│   ├── integration/
│   │   └── test_cross_app.py
│   └── e2e/
│       └── test_full_demo.py
│
├── cloud/
│   ├── azure/                  ← Azure deployment (MS hackathon)
│   │   └── bicep/              ← Infrastructure as Code
│   └── gcloud/                 ← Google Cloud deployment (Gemini hackathon)
│       ├── cloudrun/           ← ADK agent wrapper on Cloud Run
│       └── firestore/          ← Optional cloud memory sync (OFF by default)
│
├── installer/
│   └── telos-setup.iss         ← Inno Setup script for Windows installer
│
└── docs/
    ├── architecture/           ← Architecture diagrams (draw.io exports)
    ├── api/                    ← API documentation
    └── demo/                   ← Demo script + video storyboard
```

---

## 5. PROVIDER ADAPTER CONTRACT (THE PLUG & PLAY PATTERN)

```python
# services/orchestrator/providers/provider_base.py
# ★ THE CONTRACT — both adapters MUST implement this exactly

from abc import ABC, abstractmethod
from typing import AsyncIterator

class ProviderBase(ABC):
    """Abstract base — swap Azure↔Gemini by changing one env var."""

    @abstractmethod
    async def complete(self, messages: list[dict], system: str = "") -> str:
        """Single completion."""

    @abstractmethod
    async def stream(self, messages: list[dict]) -> AsyncIterator[str]:
        """Streaming completion."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Text embedding for memory store."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns 'azure' | 'gemini'"""

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Active model identifier."""
```

```python
# services/orchestrator/providers/__init__.py — ONE LINE to swap providers
import os
from .provider_azure import AzureProvider
from .provider_gemini import GeminiProvider

PROVIDERS = {"azure": AzureProvider, "gemini": GeminiProvider}

def get_provider() -> ProviderBase:
    name = os.environ.get("TELOS_PROVIDER", "azure")  # ← ONLY CHANGE NEEDED
    return PROVIDERS[name]()
```

---

## 6. COMPONENT BUILD SPECS

### Component 1: UIGraph Engine (C# + Rust) — THE CORE MOAT

**C# UIA Event Subscriber** — subscribes to 3 Windows UIA event types:
1. `FocusChanged` — new app in foreground
2. `StructureChanged` — element added/removed
3. `PropertyChanged` — value/state changed (Value, Name, ToggleState)

Serializes elements to JSON, writes to named pipe → Rust delta engine. **NEVER exposes passwords** — checks `IsPassword` property before reading any value. Password fields always return `"***MASKED***"`.

**Rust Delta Engine** — maintains full UIGraph in HashMap. On each UIA event:
1. Receive UIANode from C# via named pipe
2. Run additional PII scan (SSN, email, phone, credit card patterns)
3. Compute delta (Added/Modified/Removed)
4. Emit DeltaPacket to Python orchestrator
5. Only send what CHANGED — not the full tree (massive token savings)

**Windows MCP Server** (Python, :8083) — 5 tools:
1. `read_active_apps` — list all open apps with element counts
2. `find_element` — find UI element by name/type/value
3. `execute_action` — click, type, select on a specific element
4. `get_app_graph` — full element tree for a specific app PID
5. `compose_cross_app` — read from App A, write to App B

### Component 2: Python Orchestrator (FastAPI + asyncio, :8080)

**Startup sequence** (lifespan):
1. Load provider (azure or gemini from env var)
2. Initialize A2A bus (asyncio pub/sub)
3. Initialize PrivacyFilter
4. Initialize MemoryStore (mem0 + ChromaDB local)
5. Boot 4 agents: Orchestrator, UIGraph, Memory, Scheduler
6. Each agent subscribes to A2A bus topics

**Key endpoints:**
- `POST /task` — submit NL task → orchestrator agent routes it
- `WS /ws` — real-time agent events → Tauri frontend
- `GET /agents` — agent status for dashboard
- `GET /privacy/stats` — byte counter data
- `GET /memory/search?q=` — search memory store

### Component 3: A2A Message Bus (asyncio pub/sub)

```python
# services/orchestrator/bus/a2a.py
import asyncio
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

@dataclass
class A2AMessage:
    topic: str
    sender: str
    payload: Any
    reply_to: str | None = None
    correlation_id: str = field(default_factory=lambda: uuid4().hex)

class A2ABus:
    """Agent-to-Agent asyncio pub/sub bus. Zero external dependencies."""
    
    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = {}
    
    async def publish(self, msg: A2AMessage):
        for q in self._subscribers.get(msg.topic, []):
            await q.put(msg)
    
    async def subscribe(self, topic: str) -> AsyncIterator[A2AMessage]:
        q = asyncio.Queue()
        self._subscribers.setdefault(topic, []).append(q)
        try:
            while True:
                yield await q.get()
        finally:
            self._subscribers[topic].remove(q)
```

### Component 4: Go Scheduler Daemon (:8081)

SQLite-backed cron engine. REST API for CRUD. Fires jobs by calling orchestrator `/task` endpoint. Survives reboots (loads jobs from DB on start). Retry logic with exponential backoff. Job history with run/fail counts.

**REST Routes:** `GET /jobs`, `POST /jobs`, `DELETE /jobs/:id`, `PUT /jobs/:id/pause`, `GET /jobs/:id/history`

### Component 5: Privacy Shield

Three layers:
1. **PII Filter** (Python) — regex patterns for SSN, email, phone, credit card, address. Strips before ANY API call.
2. **Byte Counter** (Python) — tracks every byte in/out with destination, timestamp, purpose. Visible in dashboard.
3. **UIA Password Masking** (C# + Rust) — IsPassword check at capture time + additional PII scan in Rust delta engine.

### Component 6: Memory Store (mem0 + ChromaDB local)

```python
# services/orchestrator/memory/store.py
from mem0 import Memory

class MemoryStore:
    def __init__(self):
        self.memory = Memory.from_config({
            "vector_store": {"provider": "chroma", "config": {"path": "./telos_memory_db"}}
        })
    
    def remember(self, content: str, metadata: dict = None):
        self.memory.add(content, user_id="default", metadata=metadata or {})
    
    def recall(self, query: str, limit: int = 5) -> list:
        return self.memory.search(query, user_id="default", limit=limit)
```

### Component 7: DevOps Agent (Challenge 1: Agentic DevOps)

Python, ~200 lines. Monitors GitHub Actions via API polling. On failure: fetches logs → sends to LLM for root cause analysis → creates GitHub issue with analysis + suggested fix. Shows in DevOps Panel on dashboard.

### Component 8: Vision Fallback for Gemini (NEW — Devpost requirement)

```python
# uigraph/vision/screenshot_agent.py
# Periodic screenshot → Gemini multimodal for visual verification
# This satisfies the Gemini UI Navigator "must use Gemini multimodal
# to interpret screenshots" requirement while keeping UIA as primary

import mss, base64, io
from PIL import Image

class VisionFallbackAgent:
    """Secondary path: screenshots → Gemini multimodal.
    Used for: apps with poor UIA, visual verification, Gemini requirement."""
    
    async def capture_and_analyze(self, task_context: str) -> dict:
        img_b64 = self._capture_screenshot()
        return await self._analyze_with_gemini(img_b64, task_context)
    
    def _capture_screenshot(self) -> str:
        with mss.mss() as sct:
            screenshot = sct.grab(sct.monitors[1])
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            buffer = io.BytesIO()
            img.save(buffer, format="PNG", optimize=True)
            return base64.b64encode(buffer.getvalue()).decode()
```

---

## 7. DESIGN SYSTEM — MISSION CONTROL UI

### Design Philosophy
NASA operations center × fintech trading terminal. Dark glassmorphism, real-time data panels, agent status cards, live privacy counter. **NO message bubbles. NO chat history. Pure operational intelligence.**

### Color Tokens
| Token | Value | Usage |
|-------|-------|-------|
| --telos-bg | #0A0A1A | Main background — deep space dark |
| --telos-surface | #13131F | Panel surface — slightly lighter |
| --telos-border | #1E1E35 | Glassmorphism border |
| --telos-purple | #7C3AED | Primary — agent active, headings |
| --telos-teal | #0D9488 | Secondary — success, local ops |
| --telos-amber | #F59E0B | Warning — cloud bytes (should stay low) |
| --telos-red | #EF4444 | Error — agent failed, security alert |
| --telos-text | #E2E8F0 | Primary text |
| --telos-muted | #64748B | Muted labels, metadata |

### Tech Stack
| Layer | Technology | Why |
|-------|-----------|-----|
| Desktop Shell | Tauri 2.0 (Rust) | Native WebView2, ~8MB installer, system tray, hotkeys |
| Frontend | React 18 + TypeScript | Type-safe, fast re-renders via Tauri events |
| Styling | Tailwind CSS + glassmorphism | Fast iteration, dark theme, no CSS files |
| State | Zustand (lightweight) | No Redux overhead, works with Tauri IPC |
| Real-time | Tauri event emit | Lower latency than WebSocket for local IPC |
| Charts | Recharts + D3 | Privacy byte counter chart, agent timeline |
| Icons | Lucide-React | Consistent, tree-shakeable |

### 6-Panel Layout
```
╔══════════════════════════════════════════════════════════════════════╗
║  ⬡ TELOS by DigitalSvarga   [●LIVE]   Privacy: ████░░ 2.4MB local ║
║  Mission Control v0.1.0                         0 bytes to cloud    ║
╠══════════════════╦═══════════════════════════╦═══════════════════════╣
║                  ║                           ║                       ║
║  AGENT STATUS    ║  TASK TIMELINE            ║  PRIVACY SHIELD       ║
║  ─────────────   ║  ────────────             ║  ─────────────        ║
║  ◉ Orchestrator  ║  ✓ Excel read (87ms)      ║  ████████░░ LOCAL     ║
║    [ROUTING]     ║  ✓ QB total found         ║  2.4 MB processed     ║
║                  ║  ► Writing to Excel...    ║                       ║
║  ◉ UIGraph       ║  ○ Scheduler notified     ║  ░░░░░░░░░░ CLOUD     ║
║    [ACTIVE]      ║                           ║  0 bytes sent         ║
║                  ║  [CROSS-APP COMPOSE]      ║                       ║
║  ◎ Memory        ║  QuickBooks ──► Excel     ║  Fields masked: 3     ║
║    [READY]       ║  Status: EXECUTING        ║  Audit events: 12     ║
║                  ║                           ║                       ║
║  ◎ Scheduler     ║  Duration: 1.2s total     ║  [VIEW AUDIT LOG]     ║
║    [STANDBY]     ║  Cloud bytes: 0           ║                       ║
╠══════════════════╩═══════════════════════════╩═══════════════════════╣
║                                                                      ║
║  NATURAL LANGUAGE INPUT                                              ║
║  ┌─────────────────────────────────────────────────────────────┐    ║
║  │  🎙 "Copy Q1 sales total from QuickBooks into Excel B4"  ▶ │    ║
║  └─────────────────────────────────────────────────────────────┘    ║
╠══════════════════════════════╦═══════════════════════════════════════╣
║  CRON BOARD                  ║  UIGRAPH LIVE VIEW                    ║
║  ──────────                  ║  ──────────────                       ║
║  ● Mon 8am Morning Brief    ║  App: EXCEL.EXE [14 elements]         ║
║  ● Daily 7pm Report Export   ║  ├─ Workbook: Q1_Report               ║
║  ○ Fri 5pm DevOps Summary   ║  │  ├─ Sheet: Summary                 ║
║  [+ Add Schedule]            ║  │  │  ├─ Cell B4: [editable] 42.50  ║
║                              ║  │  │  └─ Cell B5: [masked] ***      ║
╚══════════════════════════════╩═══════════════════════════════════════╝
```

---

## 8. UI UPGRADES & SUGGESTIONS (NEW — NOT IN ORIGINAL SCOPE)

### 8A. Onboarding Wizard (First-Run Experience)
**Problem**: Non-technical users need guided setup. Judges need instant "wow."
**Solution**: 3-step onboarding wizard on first launch:
1. **Welcome** — "I'm TELOS. I automate your desktop. Let me show you." + animated logo
2. **Quick Test** — "I'll open Notepad and type 'Hello from TELOS' — watch." (live demo of UIGraph in action, takes 3 seconds)
3. **Privacy Promise** — Show the Privacy Meter at 0 bytes. "Nothing left your machine. That's how TELOS always works."

### 8B. Quick Actions Bar (Pinned Tasks)
**Problem**: Frequent tasks require retyping.
**Solution**: Pinnable task buttons below the command bar. Pre-loaded with 3 defaults:
- "Organize my Downloads folder"
- "Export today's calendar to Excel"
- "Check my GitHub Actions status"
Users can pin their own. Stored in local memory.

### 8C. Agent Activity Pulse Animation
**Problem**: Static status cards don't convey "alive" feeling.
**Solution**: Each agent card has a subtle pulse animation when active. Color shifts: standby (dim teal) → active (bright purple pulse) → complete (solid teal) → error (red pulse). Smooth transitions. Feels like a heartbeat monitor.

### 8D. Action Replay / Step-Through
**Problem**: Users can't verify what the agent did after the fact.
**Solution**: Every task execution is recorded as a step-by-step replay. Users can click any completed task in the Timeline and see each step: "Captured UIGraph → Found element 'Sales Total' → Read value $4,285 → Switched to Excel → Found cell B4 → Wrote value." Each step shows timestamp + duration.

### 8E. Floating Mini-Mode (Compact View)
**Problem**: Full Mission Control takes screen space during work.
**Solution**: A minimal floating widget (like a mini-player) — 200x80px — that shows: current agent status + privacy meter + active task progress. Click to expand back to full Mission Control. Triggered by minimize button or `Ctrl+Shift+M`.

### 8F. Smart Suggestions / Context-Aware Hints
**Problem**: Users don't know what TELOS can do.
**Solution**: When the command bar is focused but empty, show 3 contextual suggestions based on: (a) currently active app, (b) time of day, (c) memory of past tasks. Example: if Excel is open → "Summarize this spreadsheet" / "Create a chart from column B" / "Save as PDF". Updates in real-time as user switches apps.

### 8G. Toast Notifications for Background Tasks
**Problem**: Scheduled tasks complete while Mission Control is minimized.
**Solution**: Windows native toast notifications via Tauri. Show: task name, completion status, duration, privacy stat. Click to open Mission Control at that task's detail view.

### 8H. Keyboard-First Design
**Problem**: Power users need speed.
**Solution**: Global hotkeys:
- `Ctrl+Space` — Toggle command bar (from anywhere on desktop)
- `Ctrl+Shift+T` — Open TELOS Mission Control
- `Ctrl+Shift+M` — Toggle mini-mode
- `Esc` — Close/minimize
- Arrow keys navigate between panels when Mission Control is focused
- `Tab` cycles through agent cards

### 8I. Dark/Light Theme Toggle
**Problem**: Some users work in bright environments.
**Solution**: Ship dark-first (the NASA aesthetic) but include a light theme variant for accessibility. Toggle in settings. The dark theme is the default and demo theme.

---

## 9. TDD MANDATE

**Every feature starts with a failing test.** Tests are the specification.

| Layer | Framework | Coverage Target |
|-------|-----------|----------------|
| Python Orchestrator | pytest + pytest-asyncio + httpx | 90%+ |
| Provider Adapters | pytest + respx (mock HTTP) | 100% (contract tests) |
| Go Scheduler | go test + testify | 85%+ |
| Rust Delta Engine | cargo test + proptest | 95%+ |
| C# UIA Subscriber | xUnit + FluentAssertions | 80%+ |
| Tauri IPC | Rust unit tests | 85%+ |
| React Frontend | Vitest + React Testing Library | 80%+ |
| E2E Integration | Playwright (desktop mode) | Key flows |
| Contract Tests | Pact (provider adapter) | 100% — both adapters pass identical suite |

**Contract Test Rule**: `test_provider_contract.py` runs against BOTH AzureProvider AND GeminiProvider. Both must pass. This guarantees swap compatibility.

---

## 10. 6-DAY SPRINT PLAN

### Day 1 — Mar 10 — Foundation (5h)
- [00-01h] Tauri 2.0 scaffold: React 18 + TS. Verify builds on Windows. (GitHub Copilot)
- [01-02h] Python FastAPI orchestrator: main.py, provider_base.py, provider_azure.py stub, pytest fixtures. (Claude Code)
- [02-03h] Go scheduler: main.go, SQLite schema, REST API stubs, go test. (GitHub Copilot)
- [03-04h] Wire Tauri → Python IPC (submit_task command). Test: submit from UI, see log in Python. (Claude Code)
- [04-05h] Dashboard shell: AgentGrid, TaskTimeline, PrivacyMeter components (static data). Dark theme. (Gemini)
- **CHECKPOINT**: All services start. Task submitted from Tauri UI → appears in orchestrator log.

### Day 2 — Mar 11 — UIGraph Engine (6h)
- [00-90m] C# UIGraphSubscriber: 3 UIA event types, JSON serializer, named pipe writer. xUnit tests.
- [90m-3h] Rust delta engine: DeltaEngine struct, graph HashMap, PrivacyFilter PII scan. cargo test.
- [3-4h] Windows MCP server (Python): 5 tools.
- [4-5h] Wire: C# → Rust (named pipe) → Python MCP (HTTP). Integration test: open Notepad → read text.
- [5-6h] TDD: cross-app compose tests. UIGraph agent in Python. Privacy masking tests.
- **CHECKPOINT**: Open Notepad → TELOS reads "Hello World" as text. No screenshot. Privacy meter shows 0 cloud bytes.

### Day 3 — Mar 12 — MCP Mesh + Memory + A2A (5h)
- [0-1h] Azure provider: real API calls, error handling, retry. Contract test suite — both providers pass.
- [1-2h] mem0 local memory store: embed + store + retrieve. pytest async tests.
- [2-3h] A2A bus: asyncio pub/sub, message schema, reply-to routing. 10 unit tests.
- [3-4h] Web MCP: Playwright server, 4 tools (navigate, click, fill_form, extract_data).
- [4-5h] Memory Agent + Scheduler Agent in Python. Integration test: task → orchestrator → uigraph → memory.
- **CHECKPOINT**: Full A2A round trip works. Agent reads memory. Azure LLM call works. Web MCP opens GitHub.

### Day 4 — Mar 13 — Dashboard Polish + DevOps Agent (6h)
- [0-90m] React dashboard: all 6 panels wired to live data via Tauri events. Privacy meter animated.
- [90m-3h] Cron Board: add/pause/delete jobs via Go scheduler API. Real-time updates.
- [3-5h] DevOps Agent (~200 lines): GitHub Actions watcher, failure detect, LLM analysis, issue creation.
- [5-6h] UIGraph live view panel: shows element tree of frontmost Windows app in real time.
- [+NEW] Onboarding Wizard + Quick Actions Bar + Agent Pulse animations.
- **CHECKPOINT**: Dashboard fully live. DevOps agent detects mock CI failure, creates GitHub issue.

### Day 5 — Mar 14 — Hero Demo + Voice + Polish + Rehearsal (5h)
- [0-1h] QuickBooks → Excel cross-app compose: full end-to-end. THIS IS THE HERO DEMO.
- [1-2h] Voice: faster-whisper push-to-talk in Python sidecar. Wire to orchestrator. Test 5 commands.
- [2-3h] UI polish: animations, loading states, error handling, onboarding, mini-mode, smart suggestions.
- [3-4h] Full end-to-end rehearsal: speak command → agents execute → dashboard updates → privacy meter.
- [4-5h] Bug fixes. Performance: cross-app demo < 2 seconds.
- **CHECKPOINT**: Complete demo runs flawlessly 3 times in a row. Timer: 87 seconds for full hero sequence.

### Day 6 — Mar 15 — Record Video + Submit (4h + bonus Gemini day)
- [0-1h] Architecture diagram: draw.io or Excalidraw. Export PNG. Add to README.
- [1-3h] Record 2-min demo video (screen capture + narration). Upload YouTube.
- [3-3.5h] Final README: hero one-pager, badge row, video embed, architecture PNG.
- [3.5-4h] Submit Challenge 2 (Build AI Apps) + Challenge 1 (Agentic DevOps) — same project, two submissions.
- **DEADLINE**: March 15, 11:59pm PT. Both MS challenges submitted.

### Day 6.5 — Mar 16 — Gemini Devpost Submission (2h bonus)
- [0-30m] Switch `TELOS_PROVIDER=gemini`. Run contract tests. Verify Gemini adapter works.
- [30m-1h] Record/edit 4-min Gemini demo video emphasizing: multimodal screenshot analysis, Gemini UI Navigator features, Google Cloud service integration.
- [1-1.5h] Create Devpost project page. Upload: demo video, architecture diagram, write-up, code repo link.
- [1.5-2h] Write blog post for bonus points. Publish on dev.to with #GeminiLiveAgentChallenge.
- **DEADLINE**: March 16, 5:00pm PT. Gemini submission complete.

---

## 11. 2-MINUTE DEMO VIDEO SCRIPT (MICROSOFT)

| Time | Narration | On-Screen |
|------|-----------|-----------|
| 0:00-0:12 | "Every AI agent in 2026 takes a screenshot of your screen and uploads it to the cloud. TELOS doesn't. Watch." | System tray → click → Mission Control opens. Dark glassmorphism. |
| 0:12-0:28 | "I'll type a command: 'Copy the Q1 sales total from QuickBooks into Excel cell B4.'" | Type in input bar. Enter. Agent Grid lights up — Orchestrator → UIGraph activates. |
| 0:28-0:48 | "TELOS is reading QuickBooks — not as an image. As structured text. 47 tokens. Not 4,700." | UIGraph Live View shows QB element tree. Sales Total: $4,285.00 highlighted. |
| 0:48-1:05 | "It found the value. Now writing to Excel. Look at the Privacy Shield — zero bytes to cloud." | Excel opens, B4 fills with $4,285.00. Privacy Meter: 2.1MB local / 0 bytes cloud. |
| 1:05-1:20 | "Now I'll schedule this. 'Run this every Monday at 8am.' Voice command." | Push-to-talk. Cron Board adds: "Mon 8:00 AM — QuickBooks to Excel sync". |
| 1:20-1:38 | "DevOps layer. TELOS detected a failed GitHub Actions pipeline, analyzed the error, filed an issue — automatically." | DevOps panel: failure detected, root cause, GitHub issue #47 created. |
| 1:38-1:52 | "Four languages. One agent OS. Everything local. Nothing exposed." | Architecture diagram slides in. Python + Go + Rust + C#. UIGraph → Agents → MCP. |
| 1:52-2:00 | "TELOS. Your machine's purpose, automated." | Logo fade. "by DigitalSvarga LLC". GitHub URL. |

---

## 12. ENV VARS

```env
# Provider swap (THE one-line change)
TELOS_PROVIDER=azure   # azure | gemini

# Azure (Microsoft hackathon)
AZURE_FOUNDRY_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_FOUNDRY_KEY=your_key
AZURE_FOUNDRY_MODEL=gpt-4o
AZURE_DEPLOYMENT=gpt-4o

# Google (Gemini hackathon)
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.0-flash
GOOGLE_CLOUD_PROJECT=your_project_id

# TELOS config
TELOS_PRIVACY_LEVEL=strict          # strict | balanced
TELOS_MEMORY_PATH=./telos_memory_db
TELOS_LOG_PATH=./telos_logs
TELOS_VOICE_ENABLED=false           # true to enable push-to-talk
```

---

## 13. SUBMISSION CHECKLISTS

### Microsoft AI Dev Days (March 15)
- [ ] Public GitHub repo: clean, documented, tests passing, badges
- [ ] Uses Azure AI Foundry (model routing via MCP)
- [ ] Uses Azure Agent Framework / Semantic Kernel
- [ ] Uses Azure MCP (3 MCP servers)
- [ ] Built with VS Code, GitHub Copilot evidence in .github/copilot-instructions.md
- [ ] Demo video ≤ 2 min on YouTube (public)
- [ ] Architecture diagram in README + ARCHITECTURE.md
- [ ] Submit to Challenge 2 (Build AI Apps) — UIGraph + Privacy + Cross-app
- [ ] Submit to Challenge 1 (Agentic DevOps) — DevOps Agent + Azure Monitor
- [ ] Working demo: installer or clear run instructions

### Gemini Live Agent Challenge (March 16)
- [ ] Devpost project page, all team members added
- [ ] Category: UI Navigator
- [ ] Uses Gemini model (GenAI SDK) — multimodal screenshot analysis
- [ ] Uses ADK for agent orchestration wrapper
- [ ] Uses Google Cloud service (Cloud Run for agent wrapper)
- [ ] Demo video ≤ 4 min (multimodal features in action + pitch)
- [ ] Architecture diagram (Gemini → backend → database → frontend)
- [ ] ~200 word Gemini integration write-up
- [ ] Public code repo URL
- [ ] Public demo link (no login/paywall)
- [ ] NEW project created during contest period
- [ ] BONUS: Blog post on dev.to with #GeminiLiveAgentChallenge

---

## 14. CRITICAL RULES

1. **UIGraph is the moat.** Remove UIGraph → TELOS becomes a generic chatbot. Every feature passes the UIGraph litmus test.
2. **Zero screenshots is the PRIMARY path.** UIA structured text = 10x fewer tokens, deterministic actions, privacy-safe. Gemini vision is the FALLBACK/VERIFICATION layer only.
3. **Privacy is the foundation, not a feature.** Byte counter always visible. Nothing leaves the machine without the user knowing. Password fields NEVER exposed.
4. **The user watches.** Every action visible in Action Viewer. Agent pulse animations. Task timeline. The "alive" feeling is the wow factor.
5. **Both hackathons, one codebase.** Provider adapter swap = one env var change. Contract tests guarantee compatibility.
6. **TDD throughout.** Tests first. Tests are the specification. Both adapters pass the same contract test suite.
7. **Ship > perfect.** A flawless 3-feature demo beats a broken 10-feature demo. Get UIGraph + Cross-App + Privacy Shield working perfectly first.
8. **The video sells the product.** The first 12 seconds hook the judges. The Privacy Shield moment is the differentiator. Rehearse 10 times.

---

## NOW BUILD IT. GO.
