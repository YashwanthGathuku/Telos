# TELOS architecture

TELOS is a Windows desktop agent with a cloud-capable Gemini control plane.

## Core components

### 1. Gemini control plane

- FastAPI orchestrator on port 8080
- Google ADK navigator
- Gemini provider through the official Google GenAI SDK
- Optional Firestore-backed task memory

### 2. Windows desktop companion

- C# UIGraph service on port 8083
- Go screenshot engine on port 8085
- Optional Go scheduler on port 8081
- Optional Tauri desktop dashboard

## Control loop

1. Capture the desktop screenshot
2. Ask Gemini what is visible and what action should happen next
3. Execute the chosen UI Automation tool inside the target Windows app
4. Capture again and verify the result

## Cloud usage

Google Cloud Run hosts the Gemini control plane. Cloud Build, Secret Manager, and Firestore support the deployment story. The Windows companion stays on the machine being controlled because it needs a live desktop session.
