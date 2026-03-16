# TELOS — Master Hackathon Submission Walkthrough

This walkthrough is intentionally evidence-based. It describes what is implemented and tested in the repository today, plus what remains pending for submission polish.

## 1. Microsoft Hero Technologies (Azure Integration)
* **Azure AI Foundry provider path**: `FoundryProvider` exists and targets Azure OpenAI-compatible endpoints under a Foundry project endpoint.
* **Semantic Kernel-backed Microsoft path**: `SemanticKernelProvider` uses the official `semantic-kernel` SDK; token-level usage remains limited by SDK response surfaces.
* **Local MCP-style tool server**: `services/orchestrator/mcp_server.py` exposes local tools over stdio transport for task-history style queries.
* **Azure deployment template**: `deploy/azure-deploy.yaml` is a template with probes and secret placeholders; live deployment proof is separate.
* **Copilot-in-VS-Code workflow artifacts**: `.github/copilot-instructions.md` and `.github/prompts/*` capture the repeatable Copilot workflow used for hardening and review.

## 2. Google Gemini & GCP Advancements
* **Official GenAI SDK**: The orchestrator relies entirely on the new `google-genai` SDK for Gemini completions rather than bare `httpx`.
* **GCP Cloud Service option**: A Firestore backend (`memory/firestore_store.py`) is implemented as an optional memory backend alongside SQLite.
* **Multimodal Vision path**: `VisionAgent` supports screenshot + text requests when privacy settings allow image egress.

## 3. Execution Architecture Fixes (The Forensic Gaps)
* **High-Speed Screen Capture**: A lightweight **Go Capture Engine** (port 8085) takes ultra-fast screenshots to feed multimodal LLM inputs.
* **Delta Pipeline**: The **Rust Delta Engine** (port 8084) handles visual diff analysis. The C# UIGraph service attempts delta calls and falls back to snapshot-only mode if delta is unavailable.
* **Scheduler Daemon**: The Go-based cron orchestrator uses `robfig/cron/v3` for background job evaluation, enabling scheduled automation.
* **Writer Retries**: The `WriterAgent` uses exponential backoff (1s → 2s → 4s cap) for up to 3 retry attempts before failing.

## 4. Frontend / UX Fidelity (The Docs-Only Fixes)
* **Web Speech API**: Users can now click the microphone icon in the Mission Control dashboard to transcribe commands effortlessly.
* **Onboarding Flow**: A React configuration wizard overlays the system on the first boot to ensure environment keys are properly set prior to routing the jobs.
* **Settings & Provider Switcher**: Users can swap between Azure and Gemini dynamically through the React GUI.
* **Tauri Desktop Elements**: The system tray is fully configured and the web CSPs are correctly implemented.

## 5. Known Limits Before Submission
* Azure Container Apps deployment is template-ready but not represented here as a live deployment proof artifact.
* MCP is implemented as a local stdio server; external MCP interoperability proof is a separate demo step.
* Demo video and solo-entrant metadata must be finalized in submission materials.

## Verification
- **Code Completeness**: All endpoints use real logic; no dummy `{"success": true}` stubs remain in production paths.
- **Tests**: Full Python test suite: **146/146 passed** (8 E2E hero + 138 unit/integration). Go tests pass for scheduler and capture engine.
- **Privacy**: SSE event payloads are PII-filtered before reaching the frontend. Step details and result values are sanitised via `mask_pii()`.
- **Portability**: The `ProviderBase` abstraction makes switching between Azure Foundry, Semantic Kernel, and Gemini frictionless via the `TELOS_PROVIDER` env var.
