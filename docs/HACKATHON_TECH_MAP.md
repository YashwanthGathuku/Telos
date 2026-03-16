# TELOS Gemini challenge requirement map

This file maps the Gemini Live Agent Challenge requirements to concrete implementation evidence in the repo.

## Category fit

Primary category: `UI Navigator`

Why:
- The agent interprets screenshots of a Windows desktop.
- It outputs executable actions through Windows UI Automation.
- The flow is observe, decide, act, verify.

## Requirement mapping

| Requirement | Evidence |
|---|---|
| Gemini model is used | `services/orchestrator/agents/adk_navigator.py` uses `gemini-2.0-flash` and `services/orchestrator/providers/gemini_provider.py` uses the official Google GenAI SDK |
| Agent is built with Google ADK or GenAI SDK | `services/orchestrator/agents/adk_navigator.py`, `services/orchestrator/agents/adk_runner.py`, `services/orchestrator/requirements.txt` |
| Multimodal input | `services/capture_engine/main.go` captures screenshots and `capture_screen()` in `services/orchestrator/agents/adk_navigator.py` passes them into the Gemini decision loop |
| Output is executable UI actions | `click_element`, `type_text`, `launch_app`, `read_element`, `invoke_button`, `expand_element`, and `select_item` in `services/orchestrator/agents/adk_navigator.py`; Windows execution path in `uigraph/windows/Program.cs` and `uigraph/windows/Services/UIAutomationService.cs` |
| Google Cloud service is used | Cloud Run deployment files in `deploy/Dockerfile.cloudrun`, `deploy/cloudrun-service.yaml`, and `deploy/deploy-gcloud.sh`; Firestore backend in `services/orchestrator/memory/firestore_store.py` |
| Public repo explains how to run and deploy | `README.md`, `docs/SETUP.md`, `docs/demo/HERO_DEMO.md`, `walkthrough.md` |
| Submission copy is ready | `docs/devpost_submission.md` |

## Google Cloud usage story

- Cloud Run hosts the FastAPI orchestrator and Google ADK navigator.
- Cloud Build builds the deployment image.
- Secret Manager stores the Gemini API key.
- Firestore provides cloud-backed task memory.

## Honest architecture note

The Windows companion cannot run on Cloud Run because it must access a live Windows desktop session. The submission should describe Cloud Run as the hosted control plane and the Windows companion as the machine-local executor for UI automation.
