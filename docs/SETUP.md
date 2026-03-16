# TELOS setup and deployment

This document is the operator guide for the Gemini Live Agent Challenge submission build.

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Orchestrator and Gemini provider |
| Node.js | 18+ | Desktop UI |
| Go | 1.22+ | Screenshot engine and scheduler |
| .NET SDK | 8.0+ | Windows UIGraph service |
| Google Cloud SDK | current | Cloud Run deployment |

Windows 10 or 11 is required for the desktop-control demo because UIGraph depends on Windows UI Automation.

## Local run

### 1. Configure environment

```powershell
Copy-Item .env.example .env
```

Minimum demo config:

```env
TELOS_PROVIDER=gemini
GOOGLE_API_KEY=your-google-ai-studio-key
GEMINI_MODEL=gemini-2.0-flash
TELOS_PRIVACY_MODE=balanced
TELOS_ALLOW_IMAGE_EGRESS=true
```

### 2. Install Python dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r services\orchestrator\requirements.txt
```

### 3. Install desktop dependencies

```powershell
cd apps\desktop
cmd /c npm install
cd ..\..
```

### 4. Start services

Start each in its own terminal.

UIGraph:

```powershell
cd uigraph\windows
dotnet run
```

Screenshot engine:

```powershell
cd services\capture_engine
go run main.go
```

Scheduler, optional:

```powershell
cd services\scheduler
go run main.go
```

Orchestrator:

```powershell
.\.venv\Scripts\python.exe -m services.orchestrator
```

Desktop UI, optional:

```powershell
cd apps\desktop
cmd /c npm run tauri -- dev
```

### 5. Verify health

```powershell
Invoke-RestMethod http://localhost:8080/health
Invoke-RestMethod http://localhost:8080/adk/health
Invoke-RestMethod http://localhost:8083/health
Invoke-RestMethod http://localhost:8085/health
```

### 6. Run the navigator

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8080/navigate `
  -ContentType application/json `
  -Body '{"task":"Open Calculator and compute 15 times 23"}'
```

### 7. Stream tool execution

```powershell
curl "http://localhost:8080/navigate/stream?message=Open+Notepad+and+type+Hello+Gemini"
```

## Cloud Run deployment

The submission's Google Cloud story is:

- Cloud Run hosts the Gemini orchestrator and ADK navigator.
- Cloud Build builds the deploy image.
- Secret Manager stores the Gemini API key.
- Firestore stores cloud task history.
- The Windows companion remains on the desktop being controlled.

### 1. Configure Google Cloud

```powershell
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com firestore.googleapis.com
```

Create Firestore once in the Google Cloud console.

### 2. Create the Gemini secret

```powershell
"YOUR_GOOGLE_API_KEY" | gcloud secrets create google-api-key --data-file=- 2>$null
"YOUR_GOOGLE_API_KEY" | gcloud secrets versions add google-api-key --data-file=-
```

### 3. Decide whether Cloud Run will drive a live desktop

If you only need cloud evidence, deploy without companion host overrides.

If you want the Cloud Run service to control a live Windows machine, expose the Windows companion and set:

```powershell
$env:WINDOWS_MCP_HOST="your-windows-host-or-tunnel"
$env:SCREENSHOT_ENGINE_HOST="your-windows-host-or-tunnel"
```

### 4. Deploy

```powershell
bash ./deploy/deploy-gcloud.sh YOUR_PROJECT_ID
```

### 5. Verify cloud deployment

```powershell
curl https://YOUR_CLOUD_RUN_URL/health
curl https://YOUR_CLOUD_RUN_URL/adk/health
```

## Troubleshooting

`navigate` returns screenshot errors:
- Check that `services/capture_engine` is running and reachable on port 8085.

UIGraph action fails:
- Check that `uigraph/windows` is running and that the target app is open and visible.

Vision is blocked:
- Set `TELOS_PRIVACY_MODE=balanced` and `TELOS_ALLOW_IMAGE_EGRESS=true`.

Cloud Run is healthy but cannot drive the desktop:
- Set `WINDOWS_MCP_HOST` and `SCREENSHOT_ENGINE_HOST` to reachable companion endpoints and redeploy.
