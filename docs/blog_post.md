# Building a Gemini-Powered Desktop Agent That Actually Sees Your Screen

*I created this piece of content for the purposes of entering the Gemini Live Agent Challenge hackathon. #GeminiLiveAgentChallenge*

---

When I set out to build TELOS for the Gemini Live Agent Challenge, I had one question: **what if an AI agent could control your Windows desktop the same way a human does — by looking at the screen and clicking things?**

Not through brittle scripts or recorded macros, but by actually understanding what's on screen and deciding what to do next. That's what TELOS does, and here's how I built it with Google AI models and Google Cloud.

## The Problem: Desktop Automation is Stuck in 2005

Most desktop automation tools work like this: record mouse coordinates, replay them, hope nothing moved. If a button shifts 10 pixels, the script breaks. If the app updates its layout, start over.

I wanted something fundamentally different — an agent that *understands* the UI, not one that memorizes pixel positions.

## The Approach: Dual Perception with Gemini

TELOS uses two complementary ways to understand what's on screen:

**1. Structured perception** — Windows UI Automation gives access to the accessibility tree of desktop apps. Every button, text field, and checkbox has metadata: its name, control type, current value, and position. This is fast and precise.

**2. Visual perception** — When UI Automation can't reach an element (custom controls, canvas-based apps, or anything without proper accessibility markup), TELOS captures a screenshot and sends it to Gemini 2.0 Flash's multimodal endpoint. Gemini interprets the visual layout and identifies interactive elements.

The system automatically chooses the right approach based on what's available. This fallback mechanism is what makes it robust enough for real-world use.

## Multi-Agent Architecture with Google ADK

Rather than one monolithic agent, TELOS uses five specialized agents:

- The **Planner** takes a natural language command and breaks it into ordered steps using Gemini
- The **Reader** extracts data from app UI trees
- The **Writer** executes actions (clicks, keystrokes, value entry) with retry logic
- The **Verifier** confirms each action succeeded by re-reading the target
- The **Vision Agent** handles screenshot-based understanding when structured access fails

The ADK Navigator wraps this in a WebSocket-based live interaction mode using Google's Agent Development Kit, so users can interact in real-time.

## Privacy: The Part Nobody Talks About

Here's something most demo agents skip: a desktop agent sees *everything*. Passwords, bank statements, medical records, personal emails. If you're sending screenshots to a cloud API, you need to think about this.

TELOS has a privacy pipeline baked into its core:
- PII patterns (SSN, credit cards, emails, phone numbers) are detected and masked before any data leaves the machine
- Password fields are never read or transmitted
- Every outbound API call is logged with byte counts in a JSONL audit trail
- Privacy modes let you choose between strict (no image egress) and balanced (with logging)

## Deploying to Google Cloud

The control plane (orchestrator + scheduler) runs on **Cloud Run**, while the Windows desktop companion services stay on the local machine. This split makes sense: Gemini reasoning can happen anywhere, but actually clicking buttons in Notepad requires access to the Windows UI session.

Google Cloud services used:
- **Cloud Run** for the containerized orchestrator
- **Firestore** for persistent task memory
- **Secret Manager** for API key storage
- **Cloud Build** for automated Docker builds

The entire deployment is automated via `deploy-gcloud.sh` — a single script that enables APIs, creates secrets, builds the container, and deploys to Cloud Run.

## Key Technical Decisions

**Why FastAPI?** Async-first, built-in OpenAPI docs, and SSE support for real-time event streaming to the dashboard.

**Why a polyglot stack?** Each language plays to its strengths — Python for the AI/orchestration layer, Go for fast system services, Rust for performance-critical delta computation, C# for native Windows UI Automation access.

**Why google-genai SDK over raw REST?** The SDK handles auth, retries, and multimodal content construction cleanly. Combined with Google ADK for the agent framework, it made the wiring straightforward.

## What I'd Do Differently

If I had more time, I'd add browser automation alongside desktop automation — using Gemini's vision to interpret web pages the same way it handles desktop apps. The architecture already supports it; it's just another perception source feeding into the same agent pipeline.

I'd also explore Gemini's Live API for voice-based interaction — imagine telling your computer what to do by talking to it while it watches your screen.

## Try It Yourself

The full source is on GitHub with spin-up instructions. You'll need a Windows machine for the desktop companion services, but the orchestrator runs anywhere (including Cloud Run).

---

*Built with Gemini 2.0 Flash, Google ADK, and Google Cloud for the Gemini Live Agent Challenge. #GeminiLiveAgentChallenge*
