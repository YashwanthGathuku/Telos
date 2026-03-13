# TELOS — Complete Build Prompt (One-Shot Full Project)

> **Use this prompt to build the entire TELOS project from scratch in a single session.**
> **Last updated: March 11, 2026 | Deadline: March 15 (Microsoft) / March 16 (Google)**

---

## WHO YOU ARE

You are an elite full-stack systems engineer. You are building TELOS — a production-grade, privacy-first, AI-powered desktop agent for Windows. This is not a chatbot. This is not a wrapper. TELOS is an autonomous desktop operating system agent that **sees, understands, plans, and executes** actions on the user's computer while the user watches in real-time.

**The founding principle:** "TeraCognix is what your computer KNOWS. TELOS is what your computer DOES."

TELOS is the body — execution, control, scheduling, observable — that gives AI hands on the user's desktop.

---

## THE VISION

Build a completely production-grade application that changes how humans use AI on the desktop. It acts as a personal assistant with persistent memory, capable of doing everything through instructions while the user watches. Users should feel like they are using something far more advanced than the current generation of AI tools.

**Core values (non-negotiable):**
1. **User privacy is the #1 priority** — nothing leaves the user's system unless explicitly allowed
2. **Plug & play** — anyone can use it, from developers to people who barely know how to use a computer
3. **Observable autonomy** — the user always sees what the agent is doing (no black-box execution)
4. **Production-grade quality** — this is not a prototype, it ships as a real product

---

## DUAL HACKATHON TARGETS

TELOS is being submitted to **two hackathons simultaneously**. The architecture must satisfy BOTH sets of requirements.

### Hackathon 1: Microsoft AI Dev Days Global Hackathon

**Deadline:** Sunday, March 15, 2026 at 11:59 PM Pacific Time
**Platform:** Microsoft Innovation Studio Hackathon platform

**MANDATORY TECHNOLOGY REQUIREMENTS:**
- Must deploy application to **Azure** (leverage Azure services)
- Must host project in a **public GitHub repository**
- Must be developed with **VS Code or Visual Studio**
- Must be enhanced with **GitHub Copilot**
- Must leverage the **AI Dev Days hero technologies**:
  - **Microsoft Foundry** (Azure AI Foundry)
  - **Agent Framework** (Azure AI Agent Service / Semantic Kernel)
  - **Azure MCP** (Model Context Protocol on Azure)
  - **GitHub Copilot Agent Mode**

**JUDGING CRITERIA (equally weighted, Stage Two):**
1. **Technical Implementation** — Does the project demonstrate quality software development practices? How effectively does it leverage the AI Dev Days hero technologies? Is the code well-structured, documented, and maintainable?
2. **Innovation & Creativity** — How creatively does the solution apply Agentic AI patterns? Does it demonstrate sophisticated agent orchestration, MCP integration, or multi-agent collaboration?
3. **Real-World Impact** — Does the project solve a meaningful problem? Is it practical and usable?

**PRIZE CATEGORIES TO TARGET:**
- **Grand Prize: Best Overall Solution** — $20,000 (up to 4 team members) + Microsoft Build 2026 ticket + mentoring session
- **Grand Prize: Agentic DevOps** — $20,000 + Build ticket + mentoring
- **Best Enterprise Solution** — $10,000 + Build ticket
- **Best Use of Microsoft Foundry** — $10,000 + Build ticket

**SUBMISSION REQUIREMENTS:**
- Public GitHub repo with clean, documented code
- Demo video (under 3 minutes) showing the project functioning
- Text description of the project
- Must identify which category/categories you are submitting to

---

### Hackathon 2: Gemini Live Agent Challenge (Google / Devpost)

**Deadline:** Monday, March 16, 2026 at 5:00 PM Pacific Time
**Platform:** Devpost (geminiliveagentchallenge.devpost.com)

**MANDATORY TECHNOLOGY REQUIREMENTS:**
- Must leverage a **Gemini model** (Gemini 3 or newer)
- Agents must be built using **Google GenAI SDK** or **Agent Development Kit (ADK)**
- Must use **at least one Google Cloud service** (Firestore, CloudSQL, Cloud Run, Vertex AI, etc.)
- Must move beyond simple text-in/text-out interactions — **multimodal inputs and outputs required**
- Must abide by Google Cloud Acceptable Use Policy

**THE CATEGORY TO TARGET: "UI Navigator"**
This is a PERFECT fit for TELOS. The official description:

> *"Build an agent that becomes the user's hands on screen. The agent observes the browser or device display, interprets visual elements with or without relying on APIs or DOM access, and performs actions based on user intent. Examples include a universal web navigator, a cross-application workflow automator, or a visual QA testing agent."*

**Mandatory Tech for UI Navigator:** Must use Gemini multimodal to interpret screenshots/screen recordings and output executable actions. Agents must be hosted on Google Cloud.

**JUDGING CRITERIA:**
- Stage 1: Pass/fail — does it fit the theme and use required technologies?
- Stage 2: Equally weighted criteria (innovation, technical execution, impact, UX)
- Stage 3 (Bonus): Publishing blog/podcast/video content about how the project was built using Google AI models and Google Cloud (up to +0.6 points). Use hashtag #GeminiLiveAgentChallenge

**PRIZES:**
- **Overall Grand Prize:** $25,000 + $3,000 Google Cloud credits + 2 Google Cloud Next 2026 tickets + travel stipends + opportunity to demo at Google Cloud Next
- **Best UI Navigator:** $10,000 + $1,000 Google Cloud credits + 2 Google Cloud Next 2026 tickets + social promotion
- Winners announced at Google Cloud Next 2026 (April 22-24, Las Vegas)

**SUBMISSION REQUIREMENTS:**
- Project on Devpost with all team members added
- Demo video (under 4 minutes) showing multimodal/agentic features in action (no mockups) + pitching the project
- Clear architecture diagram showing how Gemini connects to backend, database, and frontend
- Brief text write-up (~200 words) detailing Gemini integration
- Public code repository URL
- Public project link / working demo (no login/paywall required)
- Must be a NEW project created during the contest period
- Must be in English or provide English translation

---

## TELOS ARCHITECTURE — THE COMPLETE SYSTEM

### Core Identity & Differentiator: The UIGraph Engine

The UIGraph Engine is what makes TELOS unique. Without it, TELOS slides back into generic chatbot territory. **Every feature must pass the UIGraph litmus test** — if removing UIGraph makes the feature identical to what any chatbot can do, the feature needs rethinking.

**UIGraph Engine** = TELOS's proprietary system for:
- Capturing screenshots/screen state of the user's desktop
- Building a semantic graph of UI elements (windows, buttons, text fields, menus)
- Understanding spatial relationships between UI elements
- Planning multi-step action sequences across applications
- Executing actions (clicks, keystrokes, drags) while the user watches
- Cross-app composition: orchestrating workflows that span multiple desktop applications

### Technology Stack (Polyglot Architecture)

For the hackathon MVP, Python is the primary language. The full production architecture uses Python + Go + Rust (the "Polyglot Method") for performance, but the hackathon submission focuses on getting a working, impressive demo.

```
┌─────────────────────────────────────────────────────────┐
│                    TELOS ARCHITECTURE                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              MISSION CONTROL UI (Tauri v2)           │ │
│  │  - System tray agent (always-on, lightweight)        │ │
│  │  - Real-time action viewer (user watches agent act)  │ │
│  │  - Task queue & history dashboard                    │ │
│  │  - Settings / privacy controls                       │ │
│  │  - Rust backend + WebView frontend                   │ │
│  └──────────────────────┬──────────────────────────────┘ │
│                         │ WebSocket / IPC                  │
│  ┌──────────────────────▼──────────────────────────────┐ │
│  │              ORCHESTRATOR (Python)                    │ │
│  │  - FastAPI server (local, never exposed)             │ │
│  │  - Agent routing & task decomposition                │ │
│  │  - UIGraph Engine (screenshot → semantic graph)      │ │
│  │  - Action Executor (pyautogui / Windows APIs)        │ │
│  │  - Memory Manager (mem0 local)                       │ │
│  │  - Privacy Shield (byte counter, egress monitor)     │ │
│  └──────┬──────────┬───────────┬───────────────────────┘ │
│         │          │           │                           │
│  ┌──────▼────┐ ┌──▼────────┐ ┌▼──────────────────────┐  │
│  │ AZURE AI  │ │ GEMINI AI │ │  LOCAL MODELS          │  │
│  │ FOUNDRY   │ │ (GenAI    │ │  (Ollama / fallback)   │  │
│  │ + Agent   │ │  SDK/ADK) │ │                        │  │
│  │ Framework │ │ + GCloud  │ │                        │  │
│  │ + MCP     │ │  services │ │                        │  │
│  └───────────┘ └───────────┘ └────────────────────────┘  │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              SCHEDULER (Go cron daemon)               │ │
│  │  - Background task scheduling                        │ │
│  │  - Periodic health checks                            │ │
│  │  - Automated routine execution                       │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              PRIVACY SHIELD                           │ │
│  │  - Zero data egress by default                       │ │
│  │  - Byte counter (tracks every byte leaving system)   │ │
│  │  - All AI calls logged with payload size             │ │
│  │  - Local memory store (nothing in cloud by default)  │ │
│  │  - User approval required for any external call      │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Platform Target
- **Windows 10/11 only** for hackathon MVP
- Must work on standard consumer hardware (no GPU required for core features)
- Packaged as a single installer (.msi or .exe)

---

## FEATURE SPECIFICATION — HACKATHON MVP

Build these features in priority order. Every feature must be working and demo-able.

### FEATURE 1: UIGraph Engine (THE DIFFERENTIATOR)

**What it does:**
1. Captures a screenshot of the user's current desktop/active window
2. Sends the screenshot to the AI model (Azure OpenAI GPT-4o Vision OR Gemini multimodal)
3. AI returns a structured semantic understanding of all UI elements on screen
4. Builds a UIGraph — a JSON graph of elements with coordinates, types, labels, and relationships
5. Uses the UIGraph to plan and execute actions (click button at x,y — type text in field — navigate menu)

**Implementation:**
```python
# Core UIGraph data structure
class UIElement:
    element_id: str
    element_type: str  # button, text_field, menu, link, checkbox, etc.
    label: str  # visible text or inferred purpose
    bounding_box: dict  # {x, y, width, height}
    state: str  # enabled, disabled, focused, checked, etc.
    children: list[str]  # child element IDs
    parent: str  # parent element ID

class UIGraph:
    timestamp: datetime
    window_title: str
    application: str
    elements: dict[str, UIElement]
    relationships: list[dict]  # spatial and logical relationships
```

**Key capabilities to demonstrate:**
- Open any application by name ("Open Chrome", "Open Notepad")
- Navigate to a website and interact with web forms
- Switch between applications and perform cross-app workflows
- Read on-screen text and respond to dialog boxes
- Fill in forms across different applications
- File management (create, move, rename, organize files/folders)

### FEATURE 2: Natural Language Task Execution

**What it does:**
User types or speaks a natural language command → TELOS plans → executes → reports back.

**Examples to demo:**
- "Create a new folder on my Desktop called 'Project Files' and move all PDFs from Downloads into it"
- "Open Chrome, go to GitHub, and star the repository I was looking at yesterday"
- "Take a screenshot of this error message and save it to my Documents folder"
- "Open Excel, create a new spreadsheet with columns for Name, Email, and Phone, then save it as contacts.xlsx"
- "Find all files larger than 100MB on my Desktop and list them for me"

**Implementation:**
- Parse natural language → break into atomic UI actions
- Each action goes through UIGraph Engine for execution
- Real-time feedback shown in Mission Control UI
- Error recovery: if an action fails, re-capture screen and re-plan

### FEATURE 3: Persistent Memory (mem0 local)

**What it does:**
TELOS remembers user preferences, past interactions, commonly used applications, file locations, and workflow patterns — ALL stored locally.

**Implementation:**
- Use mem0 (open-source memory layer) with local SQLite/ChromaDB backend
- Memory categories: user preferences, app usage patterns, file locations, task history, workflow templates
- Auto-learn: track which apps user opens most, what files they access, their preferred workflows
- Memory never leaves the machine unless user explicitly exports

**Demo scenarios:**
- User asks TELOS to organize files → TELOS remembers the user's folder structure preferences from last time
- User asks to "do that email thing again" → TELOS recalls the specific workflow from memory

### FEATURE 4: Mission Control UI (Tauri)

**What it does:**
A sleek, modern desktop application that serves as the command center for TELOS.

**Key UI components:**
1. **System Tray Agent** — always running, lightweight, right-click menu for quick commands
2. **Command Bar** — clean text input (like Spotlight/Alfred) for natural language commands
3. **Action Viewer** — real-time visualization of what the agent is doing (highlighted UI elements, action progress)
4. **Task Queue** — list of pending, active, and completed tasks with status
5. **Privacy Dashboard** — shows data egress stats (bytes sent/received, API calls made, all local by default)
6. **Memory Browser** — view/edit/delete stored memories
7. **Settings** — model selection (Azure/Gemini/Local), privacy controls, hotkeys, startup behavior

**Tech stack for UI:**
- Tauri v2 (Rust backend, WebView frontend)
- React + TypeScript + Tailwind CSS for the frontend
- WebSocket connection to Python orchestrator
- System tray integration with Windows notification API

### FEATURE 5: Privacy Shield

**What it does:**
A transparent privacy monitoring system that gives users complete visibility into data flow.

**Implementation:**
- Intercept all outbound network calls from TELOS
- Log every API call with: timestamp, destination, payload size in bytes, purpose
- Real-time byte counter visible in Mission Control
- Default mode: NO external calls (use local models)
- "Cloud Assist" mode: allow Azure/Gemini calls with explicit user approval per-session
- All logs stored locally, exportable for audit
- Privacy report: daily/weekly summary of all data that left the machine

### FEATURE 6: Multi-Model Intelligence Layer

**What it does:**
TELOS can use multiple AI backends depending on the task and user preference.

**For Microsoft Hackathon compliance:**
- Azure AI Foundry integration (GPT-4o, GPT-4.1 for vision tasks)
- Azure AI Agent Service for agent orchestration
- Azure MCP (Model Context Protocol) for tool connectivity
- Semantic Kernel for agent framework

**For Google Hackathon compliance:**
- Gemini model integration via Google GenAI SDK
- Agent Development Kit (ADK) for agent orchestration
- At least one Google Cloud service (Cloud Run for hosting agent logic, Firestore for cloud memory sync option)
- Gemini multimodal for screenshot interpretation (UIGraph)

**Architecture pattern:**
```python
class ModelRouter:
    """Routes tasks to the optimal AI backend"""
    
    def route(self, task: Task) -> ModelBackend:
        if task.requires_vision:
            return self.vision_model  # GPT-4o or Gemini multimodal
        elif task.requires_fast_response:
            return self.local_model  # Ollama
        elif task.requires_reasoning:
            return self.reasoning_model  # GPT-4.1 or Gemini
        else:
            return self.default_model
    
    @property
    def available_backends(self):
        return {
            "azure": AzureFoundryBackend(),
            "gemini": GeminiADKBackend(), 
            "local": OllamaBackend(),
        }
```

### FEATURE 7: Agentic Workflow Orchestration

**What it does:**
Multi-agent system where specialized agents collaborate to complete complex tasks.

**Agent types:**
1. **Planner Agent** — breaks down natural language into step-by-step plans
2. **Vision Agent** — interprets screenshots, builds UIGraph
3. **Executor Agent** — performs mouse/keyboard actions on the desktop
4. **Memory Agent** — manages persistent memory, retrieves relevant context
5. **Safety Agent** — validates actions before execution (prevent destructive actions)

**For Microsoft compliance:** Use Semantic Kernel / Azure AI Agent Framework for orchestration
**For Google compliance:** Use ADK (Agent Development Kit) for agent orchestration

---

## DIRECTORY STRUCTURE

```
telos/
├── README.md                          # Project overview, setup instructions
├── ARCHITECTURE.md                    # Architecture diagram + design decisions
├── LICENSE                            # MIT or Apache 2.0
├── .github/
│   ├── copilot-instructions.md        # GitHub Copilot context (Microsoft requirement)
│   └── workflows/
│       └── ci.yml                     # CI/CD pipeline
├── pyproject.toml                     # Python project config
├── requirements.txt                   # Python dependencies
├── package.json                       # Node dependencies (for Tauri frontend)
│
├── src/
│   ├── orchestrator/                  # Python — Core brain
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI server entry point
│   │   ├── config.py                  # Configuration management
│   │   ├── router.py                  # API routes
│   │   │
│   │   ├── uigraph/                   # UIGraph Engine
│   │   │   ├── __init__.py
│   │   │   ├── capture.py             # Screenshot capture (mss / PIL)
│   │   │   ├── analyzer.py            # Send to AI, parse response
│   │   │   ├── graph.py               # UIGraph data structures
│   │   │   └── planner.py             # Action planning from graph
│   │   │
│   │   ├── executor/                  # Action execution
│   │   │   ├── __init__.py
│   │   │   ├── actions.py             # Mouse, keyboard, window management
│   │   │   ├── windows_api.py         # Windows-specific APIs (win32)
│   │   │   └── safety.py              # Action validation / safety checks
│   │   │
│   │   ├── agents/                    # Multi-agent system
│   │   │   ├── __init__.py
│   │   │   ├── planner.py             # Planner agent
│   │   │   ├── vision.py              # Vision/UIGraph agent
│   │   │   ├── executor.py            # Executor agent
│   │   │   ├── memory.py              # Memory agent
│   │   │   └── safety.py              # Safety agent
│   │   │
│   │   ├── models/                    # AI model backends
│   │   │   ├── __init__.py
│   │   │   ├── router.py              # Model routing logic
│   │   │   ├── azure_foundry.py       # Azure AI Foundry + Agent Service
│   │   │   ├── azure_mcp.py           # Azure MCP integration
│   │   │   ├── gemini_sdk.py          # Google GenAI SDK integration
│   │   │   ├── gemini_adk.py          # Google ADK agent integration
│   │   │   └── ollama_local.py        # Local model fallback
│   │   │
│   │   ├── memory/                    # Persistent memory
│   │   │   ├── __init__.py
│   │   │   ├── store.py               # mem0 local store
│   │   │   ├── embeddings.py          # Local embedding generation
│   │   │   └── retrieval.py           # Context-aware memory retrieval
│   │   │
│   │   └── privacy/                   # Privacy Shield
│   │       ├── __init__.py
│   │       ├── monitor.py             # Egress monitoring
│   │       ├── byte_counter.py        # Byte-level tracking
│   │       └── audit_log.py           # Privacy audit logging
│   │
│   ├── scheduler/                     # Go — Background scheduler
│   │   ├── main.go
│   │   ├── cron.go                    # Cron job management
│   │   └── health.go                  # Health check endpoints
│   │
│   └── ui/                            # Tauri v2 — Mission Control
│       ├── src-tauri/                  # Rust backend
│       │   ├── Cargo.toml
│       │   ├── src/
│       │   │   ├── main.rs            # Tauri entry point
│       │   │   ├── tray.rs            # System tray
│       │   │   └── commands.rs        # Tauri IPC commands
│       │   └── tauri.conf.json
│       │
│       └── src/                       # React frontend
│           ├── App.tsx
│           ├── main.tsx
│           ├── components/
│           │   ├── CommandBar.tsx      # Natural language input
│           │   ├── ActionViewer.tsx    # Real-time action visualization
│           │   ├── TaskQueue.tsx       # Task list & history
│           │   ├── PrivacyDashboard.tsx # Privacy stats
│           │   ├── MemoryBrowser.tsx   # View/edit memories
│           │   └── Settings.tsx        # Configuration
│           ├── hooks/
│           │   ├── useWebSocket.ts     # WS connection to orchestrator
│           │   └── useAgent.ts         # Agent state management
│           └── styles/
│               └── globals.css         # Tailwind + custom styles
│
├── cloud/                             # Cloud deployment configs
│   ├── azure/                         # Azure deployment
│   │   ├── bicep/                     # Infrastructure as Code
│   │   ├── agent-service/             # Azure AI Agent config
│   │   └── mcp-server/               # Azure MCP server config
│   │
│   └── gcloud/                        # Google Cloud deployment
│       ├── cloudrun/                   # Cloud Run service config
│       ├── firestore/                  # Firestore rules
│       └── adk-agent/                 # ADK agent definition
│
├── installer/                         # Windows installer
│   ├── telos-setup.iss               # Inno Setup script
│   └── assets/                        # Installer assets (icons, etc.)
│
├── tests/
│   ├── test_uigraph.py
│   ├── test_executor.py
│   ├── test_agents.py
│   ├── test_memory.py
│   └── test_privacy.py
│
└── docs/
    ├── SETUP.md                       # Installation guide
    ├── DEMO_SCRIPT.md                 # Demo walkthrough for judges
    └── PRIVACY_WHITEPAPER.md          # Privacy architecture document
```

---

## IMPLEMENTATION GUIDE — BUILD ORDER

### Phase 1: Core Foundation (Hours 1-4)

**1.1 Project Setup**
```bash
# Create repo structure
mkdir -p telos/src/{orchestrator/{uigraph,executor,agents,models,memory,privacy},scheduler,ui}
cd telos

# Python environment
python -m venv .venv
source .venv/Scripts/activate  # Windows
pip install fastapi uvicorn websockets pyautogui mss pillow pydantic
pip install openai google-genai mem0ai chromadb
pip install semantic-kernel  # Microsoft Agent Framework

# Initialize Tauri project
npm create tauri-app@latest ui -- --template react-ts
cd ui && npm install
```

**1.2 FastAPI Orchestrator Server**

Build `src/orchestrator/main.py` — the local API server that everything connects to.

Key endpoints:
- `POST /task` — submit a natural language task
- `GET /task/{id}/status` — get task execution status
- `GET /ws` — WebSocket for real-time updates to UI
- `GET /privacy/stats` — privacy dashboard data
- `GET /memory/search` — search persistent memory
- `POST /settings` — update configuration

**1.3 UIGraph Engine — Screenshot → Understanding → Action**

This is the heart. Build it first, test it thoroughly.

```python
# src/orchestrator/uigraph/capture.py
import mss
from PIL import Image
import base64
import io

def capture_screen(monitor_index: int = 1) -> tuple[Image.Image, str]:
    """Capture screenshot and return PIL Image + base64 string"""
    with mss.mss() as sct:
        screenshot = sct.grab(sct.monitors[monitor_index])
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64 = base64.b64encode(buffer.getvalue()).decode()
        return img, b64

# src/orchestrator/uigraph/analyzer.py
# Send screenshot to vision model, get structured UIGraph back
# Use structured output / JSON mode to get reliable element detection
```

**UIGraph prompt for the vision model (critical — this determines quality):**

```
You are a UI analysis engine. Analyze this screenshot and return a JSON object describing every interactive UI element visible on screen.

For each element, provide:
- id: unique identifier (e.g., "btn_1", "input_2")
- type: one of [button, text_field, checkbox, radio, dropdown, menu_item, link, tab, icon, label, window_title, scrollbar, slider, toggle, image]
- label: the visible text or inferred purpose
- bbox: {x, y, width, height} in pixels from top-left
- state: one of [enabled, disabled, focused, selected, checked, unchecked]
- confidence: 0.0 to 1.0

Also identify:
- The active/focused window
- The current application name
- Any modal dialogs or popups
- The overall screen context (what is the user looking at?)

Return ONLY valid JSON. No markdown, no explanation.
```

### Phase 2: Action Execution (Hours 4-8)

**2.1 Windows Action Executor**

```python
# src/orchestrator/executor/actions.py
import pyautogui
import win32gui
import win32con
import subprocess
import time

class ActionExecutor:
    def __init__(self):
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        pyautogui.PAUSE = 0.3  # Small delay between actions for visibility
    
    def click(self, x: int, y: int, button: str = "left"):
        """Click at coordinates with visual feedback"""
        pyautogui.moveTo(x, y, duration=0.3)  # Visible movement
        pyautogui.click(x, y, button=button)
    
    def type_text(self, text: str, interval: float = 0.02):
        """Type text with realistic speed"""
        pyautogui.typewrite(text, interval=interval)
    
    def hotkey(self, *keys):
        """Press keyboard shortcut"""
        pyautogui.hotkey(*keys)
    
    def open_application(self, app_name: str):
        """Open application by name using Windows search"""
        pyautogui.hotkey('win')
        time.sleep(0.5)
        pyautogui.typewrite(app_name, interval=0.05)
        time.sleep(1)
        pyautogui.press('enter')
    
    def scroll(self, clicks: int, x: int = None, y: int = None):
        """Scroll at position"""
        pyautogui.scroll(clicks, x=x, y=y)
    
    def drag(self, start_x, start_y, end_x, end_y, duration=0.5):
        """Drag from one point to another"""
        pyautogui.moveTo(start_x, start_y, duration=0.2)
        pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration)
    
    def get_active_window(self) -> dict:
        """Get info about the currently active window"""
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        return {"title": title, "rect": rect, "hwnd": hwnd}
```

**2.2 Safety Agent**

```python
# src/orchestrator/executor/safety.py
DANGEROUS_ACTIONS = [
    "format",
    "delete system",
    "rm -rf",
    "shutdown",
    "restart",
    "registry",
    "regedit",
    "uninstall",
]

SENSITIVE_AREAS = [
    "password",
    "credit card",
    "social security",
    "bank",
]

class SafetyAgent:
    def validate_action(self, action: dict) -> tuple[bool, str]:
        """Returns (is_safe, reason)"""
        # Check for dangerous system commands
        if any(d in str(action).lower() for d in DANGEROUS_ACTIONS):
            return False, "Action involves potentially dangerous system operation"
        
        # Check for sensitive data interaction
        if any(s in str(action).lower() for s in SENSITIVE_AREAS):
            return False, "Action involves sensitive personal data — requires user confirmation"
        
        return True, "Action validated as safe"
```

### Phase 3: Multi-Model Integration (Hours 8-12)

**3.1 Azure AI Foundry Backend**

```python
# src/orchestrator/models/azure_foundry.py
from openai import AzureOpenAI
import os

class AzureFoundryBackend:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-12-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
    
    async def analyze_screenshot(self, image_b64: str, task: str) -> dict:
        """Send screenshot to GPT-4o Vision for UIGraph analysis"""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": UIGRAPH_SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "text", "text": f"Task: {task}\nAnalyze this screenshot:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                ]}
            ],
            response_format={"type": "json_object"},
            max_tokens=4096
        )
        return json.loads(response.choices[0].message.content)
    
    async def plan_actions(self, task: str, uigraph: dict, memory_context: str) -> list:
        """Use GPT-4.1 to plan action sequence from UIGraph"""
        response = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": ACTION_PLANNER_PROMPT},
                {"role": "user", "content": json.dumps({
                    "task": task,
                    "screen_state": uigraph,
                    "user_context": memory_context
                })}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)["actions"]
```

**3.2 Azure MCP Integration**

```python
# src/orchestrator/models/azure_mcp.py
# Implement MCP (Model Context Protocol) server for tool connectivity
# This exposes TELOS's desktop actions as MCP tools that the agent can call

MCP_TOOLS = [
    {
        "name": "capture_screen",
        "description": "Capture current desktop screenshot",
        "input_schema": {"type": "object", "properties": {"monitor": {"type": "integer"}}}
    },
    {
        "name": "click_element",
        "description": "Click on a UI element at specific coordinates",
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "button": {"type": "string", "enum": ["left", "right", "middle"]}
            }
        }
    },
    {
        "name": "type_text",
        "description": "Type text at current cursor position",
        "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}}
    },
    {
        "name": "open_application",
        "description": "Open a Windows application by name",
        "input_schema": {"type": "object", "properties": {"name": {"type": "string"}}}
    },
    {
        "name": "file_operation",
        "description": "Perform file operations (create, move, copy, delete, list)",
        "input_schema": {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create", "move", "copy", "delete", "list"]},
                "source": {"type": "string"},
                "destination": {"type": "string"}
            }
        }
    }
]
```

**3.3 Google Gemini / ADK Backend**

```python
# src/orchestrator/models/gemini_sdk.py
from google import genai

class GeminiBackend:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    
    async def analyze_screenshot(self, image_b64: str, task: str) -> dict:
        """Use Gemini multimodal for UI understanding"""
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",  # or gemini-3 if available
            contents=[
                {"role": "user", "parts": [
                    {"text": f"{UIGRAPH_SYSTEM_PROMPT}\n\nTask: {task}\nAnalyze this screenshot:"},
                    {"inline_data": {"mime_type": "image/png", "data": image_b64}}
                ]}
            ],
            config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)

# src/orchestrator/models/gemini_adk.py
# Agent Development Kit integration for Google hackathon compliance
# ADK agent that wraps TELOS desktop actions as agent tools
```

### Phase 4: Memory System (Hours 12-14)

```python
# src/orchestrator/memory/store.py
from mem0 import Memory

class TelosMemory:
    def __init__(self):
        self.memory = Memory.from_config({
            "llm": {
                "provider": "openai",  # or local via ollama
                "config": {"model": "gpt-4o-mini"}
            },
            "embedder": {
                "provider": "openai",
                "config": {"model": "text-embedding-3-small"}
            },
            "vector_store": {
                "provider": "chroma",
                "config": {"path": "./telos_memory_db"}  # LOCAL storage
            }
        })
        self.user_id = "default_user"
    
    def remember(self, content: str, metadata: dict = None):
        """Store a memory locally"""
        self.memory.add(content, user_id=self.user_id, metadata=metadata or {})
    
    def recall(self, query: str, limit: int = 5) -> list:
        """Retrieve relevant memories"""
        return self.memory.search(query, user_id=self.user_id, limit=limit)
    
    def get_context(self, task: str) -> str:
        """Get formatted context from memory for a task"""
        memories = self.recall(task)
        if not memories:
            return "No relevant memories found."
        return "\n".join([f"- {m['memory']}" for m in memories])
```

### Phase 5: Mission Control UI (Hours 14-18)

Build with Tauri v2 + React + TypeScript + Tailwind.

**Key UI design principles:**
- Dark mode default (professional, reduces eye strain)
- Minimal, clean interface (think: Linear, Raycast, Arc browser)
- Real-time updates via WebSocket
- Keyboard-first (Ctrl+Space to open command bar from anywhere)
- Glassmorphism/blur effects for modern feel

**Core components to build:**
1. `CommandBar.tsx` — Spotlight-like input that appears with hotkey
2. `ActionViewer.tsx` — Shows annotated screenshots with highlighted UI elements and action indicators
3. `TaskQueue.tsx` — Kanban-style task status board
4. `PrivacyDashboard.tsx` — Real-time byte counter, API call log, egress stats
5. `MemoryBrowser.tsx` — Searchable memory store viewer

### Phase 6: Privacy Shield (Hours 18-20)

```python
# src/orchestrator/privacy/byte_counter.py
import threading
from datetime import datetime
from collections import defaultdict

class PrivacyShield:
    def __init__(self):
        self.egress_log = []
        self.total_bytes_out = 0
        self.total_bytes_in = 0
        self.call_count = defaultdict(int)
        self._lock = threading.Lock()
    
    def log_api_call(self, destination: str, bytes_sent: int, bytes_received: int, purpose: str):
        """Log every external API call"""
        with self._lock:
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "destination": destination,
                "bytes_sent": bytes_sent,
                "bytes_received": bytes_received,
                "purpose": purpose,
            }
            self.egress_log.append(entry)
            self.total_bytes_out += bytes_sent
            self.total_bytes_in += bytes_received
            self.call_count[destination] += 1
    
    def get_stats(self) -> dict:
        """Get privacy statistics for dashboard"""
        return {
            "total_bytes_out": self.total_bytes_out,
            "total_bytes_in": self.total_bytes_in,
            "total_api_calls": sum(self.call_count.values()),
            "calls_by_destination": dict(self.call_count),
            "recent_log": self.egress_log[-50:],  # Last 50 entries
        }
    
    def get_report(self) -> str:
        """Generate human-readable privacy report"""
        stats = self.get_stats()
        return f"""
TELOS Privacy Report
====================
Total data sent:     {stats['total_bytes_out']:,} bytes ({stats['total_bytes_out']/1024:.1f} KB)
Total data received: {stats['total_bytes_in']:,} bytes ({stats['total_bytes_in']/1024:.1f} KB)
Total API calls:     {stats['total_api_calls']}

Breakdown by destination:
{chr(10).join(f"  {dest}: {count} calls" for dest, count in stats['calls_by_destination'].items())}

All data is logged locally at: ./telos_privacy_audit.json
No data is stored externally. Your privacy is protected.
"""
```

### Phase 7: Cloud Deployment Configs (Hours 20-22)

**Azure deployment (for Microsoft hackathon):**
- Deploy the MCP server component to Azure
- Configure Azure AI Foundry models
- Set up Azure AI Agent Service
- Keep the core TELOS agent LOCAL — only the AI inference calls go to Azure

**Google Cloud deployment (for Google hackathon):**
- Deploy an ADK agent wrapper to Cloud Run
- Firestore for optional cloud memory sync (OFF by default, user opt-in)
- The Gemini API calls route through Google Cloud

### Phase 8: Demo & Submission (Hours 22-24)

**Demo script (3 minutes for Microsoft, 4 minutes for Google):**

**[0:00-0:30] Hook:**
"What if your computer could understand you the way a human assistant does? Meet TELOS — the first privacy-first AI agent that sees your screen, understands what you're doing, and takes action for you."

**[0:30-1:30] Core Demo:**
- Show TELOS system tray icon → open Mission Control
- Type: "Create a new folder on Desktop called 'Project TELOS', open Notepad, write a summary of what TELOS can do, and save it in the folder"
- Show real-time action viewer as TELOS: captures screen → identifies Desktop → right-clicks → creates folder → opens Notepad → types content → saves file → moves to folder
- Highlight the UIGraph visualization (bounding boxes around elements being interacted with)

**[1:30-2:15] Privacy Demo:**
- Open Privacy Dashboard
- Show the byte counter: "Every single byte that left your machine is logged right here"
- Show zero external data by default in local mode
- Toggle to Cloud Assist mode, show the API call log with full transparency

**[2:15-2:45] Memory Demo:**
- Say "Do that same file organization I did yesterday"
- Show TELOS recalling the workflow from memory and executing it
- Open Memory Browser, show what's stored and that it's all local

**[2:45-3:00] Closing:**
"TELOS turns your AI from a chatbot into a co-pilot. Privacy-first. Observable. Intelligent. This is the future of human-computer interaction."

**FOR GOOGLE (extra minute):**
**[3:00-3:45]** Show architecture diagram, explain Gemini multimodal screenshot analysis, ADK agent orchestration, Google Cloud service integration. Show the multimodal flow: screenshot → Gemini vision → UIGraph → action plan → execution.

**[3:45-4:00]** "Built with Gemini, powered by Google Cloud, designed for privacy. TELOS — your desktop, your rules."

---

## SUBMISSION CHECKLIST

### Microsoft AI Dev Days
- [ ] Public GitHub repo with clean code and README
- [ ] Deployed to Azure (AI Foundry + Agent Service + MCP)
- [ ] Demo video < 3 minutes on YouTube (public)
- [ ] Built with VS Code, evidence of GitHub Copilot usage
- [ ] Leverages: Microsoft Foundry, Agent Framework, Azure MCP, GitHub Copilot
- [ ] Submit to categories: Best Overall Solution + Best Enterprise Solution
- [ ] Project description on Innovation Studio platform

### Gemini Live Agent Challenge
- [ ] Devpost project page with all team members
- [ ] Category: UI Navigator
- [ ] Uses Gemini model (GenAI SDK or ADK)
- [ ] Uses at least one Google Cloud service
- [ ] Demo video < 4 minutes on YouTube (public) — showing multimodal features
- [ ] Architecture diagram (Gemini → backend → database → frontend)
- [ ] ~200 word Gemini integration write-up
- [ ] Public code repo URL
- [ ] Public demo link (no login required)
- [ ] New project created during contest period
- [ ] BONUS: Blog post with #GeminiLiveAgentChallenge hashtag (+0.6 points)

---

## ENVIRONMENT VARIABLES REQUIRED

```env
# Azure (Microsoft Hackathon)
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_AI_AGENT_ENDPOINT=your_agent_endpoint
AZURE_SUBSCRIPTION_ID=your_sub_id

# Google (Gemini Hackathon)  
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Local
TELOS_MODE=hybrid  # local | azure | gemini | hybrid
TELOS_PRIVACY_LEVEL=strict  # strict | balanced | permissive
TELOS_MEMORY_PATH=./telos_memory_db
TELOS_LOG_PATH=./telos_logs
```

---

## CRITICAL REMINDERS

1. **UIGraph is the moat.** If you remove UIGraph, TELOS becomes a generic chatbot. Every feature, every demo, every line of code should showcase UIGraph.

2. **Privacy is not a feature, it's the foundation.** Every data flow must be auditable. The byte counter is always visible. Nothing leaves the machine without the user knowing.

3. **The user watches.** TELOS is not a black box. Every action is visible in the Action Viewer. The mouse moves on screen. The user sees the agent working. This is the "wow factor."

4. **Both hackathons, one codebase.** The architecture supports both Azure and Gemini backends. The model router selects the appropriate backend. Submission materials are customized per hackathon, but the code is the same.

5. **Quality over quantity.** A perfectly working demo of 3 features beats a broken demo of 10 features. Get UIGraph + Action Execution + Mission Control UI working flawlessly first. Everything else is bonus.

6. **Time is up March 15.** Ship. Don't over-architect. The Polyglot method (Go + Rust optimization) is for post-hackathon. Right now, Python does everything.

---

## NOW BUILD IT. GO.
