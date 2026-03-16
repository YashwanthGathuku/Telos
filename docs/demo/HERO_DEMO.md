# TELOS Hero Demo Guide

## Overview

The hero demo showcases TELOS's core differentiator: reading desktop applications via Windows UI Automation (not screenshots), coordinating specialist agents, and displaying live execution state in a privacy-visible mission control dashboard.

For the Microsoft AI Dev Days submission, record the final video as a public demo under 2 minutes and ensure the workflow shown matches the documented setup exactly.

## Demo Scenario

**Task:** "Copy the Q1 sales total from QuickBooks into Excel cell B4"

### Substitution for Demo

If QuickBooks is unavailable:
- Open **Notepad** → type `Q1 Sales Total: $142,587.00` → save as `sales.txt`
- Open **Excel** → create a blank workbook
- Modify task to: "Copy the Q1 sales total from Notepad into Excel cell B4"

## Pre-flight Checklist

1. `.env` configured with valid provider credentials
2. All core services running:
   - Orchestrator: `http://localhost:8080/health`
   - Scheduler: `http://localhost:8081/health`
   - UIGraph: `http://localhost:8083/health`
   - Delta Engine: `http://localhost:8084/health`
   - Screenshot Engine: `http://localhost:8085/health`
   - Desktop app: Tauri window open
3. Target applications (Notepad + Excel) open and visible
4. System Status panel shows all services green

## Demo Walkthrough

### Step 1: Show the Dashboard (10s)

Point out the mission-control layout:
- **Command Bar** at top — not a chatbot, it's a task operator
- **System Status** — green status for orchestrator, scheduler, UIGraph, screenshot, and delta services
- **Privacy Monitor** — shows 100% local, 0 bytes sent
- **Agent Grid** — all five agents idle
- **Task Timeline** — empty, ready for action

### Step 2: Submit the Task (5s)

Type in Command Bar:
```
Copy the Q1 sales total from Notepad into Excel cell B4
```

Click **Execute Mission** or press Enter.

### Step 3: Watch Live Execution (20s)

Observe in real time:
1. **Task Timeline** — new task card appears, status: `running`
2. **Agent Grid** — Planner Agent lights up, then Reader, Writer, Verifier
3. **UIGraph Panel** — shows UIA events as Notepad is read
4. **Privacy Monitor** — updates: 1 LLM call, bytes sent/received, fields masked count
5. **Task Timeline** — steps appear as they complete

### Step 4: Verify Results (5s)

- Switch to Excel — cell B4 should contain `$142,587.00`
- Back to TELOS — task status shows `completed`
- Privacy Monitor shows egress audit trail

### Step 5: Show Privacy (10s)

- Privacy Monitor: "No PII leaked" indicator
- Egress section: exact bytes sent to provider, destination logged
- Click through to see per-task privacy summary

## Key Demo Talking Points

1. **"We read applications, not screenshots"** — UIA extracts structured text, element types, and relationships. Password fields automatically masked.

2. **"Privacy is visible, not hidden"** — Every LLM call shows destination, bytes, PII status. Users can audit what left their machine.

3. **"Microsoft-first provider path"** — Switch between Azure OpenAI, Semantic Kernel, and Azure AI Foundry without changing the task pipeline.

4. **"Real cross-app actions"** — Data actually moved from Notepad to Excel. Not a mock, not a simulation.

5. **"Operations dashboard, not a chatbot"** — Dense, professional UI showing system state, agent status, execution timeline. Built for power users.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| System Status shows red dot | Check if the service is running on its port |
| "Connection lost" in TopBar | Orchestrator not responding, restart it |
| Task stays in `planning` | Check provider credentials in `.env` |
| UIGraph returns empty | Ensure target app is visible (not minimized) |
| Excel cell not updated | Run Excel as same user, ensure it's not in edit mode |

## Quick Start Commands

```bash
# Terminal 1: Orchestrator
cd services/orchestrator
python -m services.orchestrator

# Terminal 2: Scheduler
cd services/scheduler
go run main.go

# Terminal 3: UIGraph
cd uigraph/windows
dotnet run

# Terminal 4: Desktop
cd apps/desktop
npm run tauri dev
```
