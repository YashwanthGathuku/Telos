# TELOS demo recording guide

Target length: 3 to 4 minutes total.

The goal of the video is to prove three things quickly:

1. This is a Gemini-powered `UI Navigator`
2. It performs real Windows desktop actions
3. It uses Google Cloud in the deployed architecture

## Before you record

- Confirm the repo README is pushed publicly
- Confirm the Gemini key works
- Start the Windows companion services
- Start the orchestrator
- Open the target apps you want to use
- If you have Cloud Run deployed, have the service URL ready in a browser tab

## Recommended demo scenario

Primary command:

`Open Calculator and compute 15 times 23`

Follow-up command:

`Open Notepad and type the answer`

This is short, obvious, and easy for judges to verify visually.

## Shot list

### 0:00 to 0:20 - challenge framing

Show the README header or your slide with:

- Gemini Live Agent Challenge
- UI Navigator category
- Gemini + Google ADK + Cloud Run

### 0:20 to 0:45 - services running

Show:

- `http://localhost:8080/health`
- `http://localhost:8080/adk/health`
- `http://localhost:8083/health`
- `http://localhost:8085/health`

### 0:45 to 2:20 - real desktop action

Run:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8080/navigate `
  -ContentType application/json `
  -Body '{"task":"Open Calculator and compute 15 times 23"}'
```

Show Calculator opening and the result appearing.

Then run:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8080/navigate `
  -ContentType application/json `
  -Body '{"task":"Open Notepad and type the answer"}'
```

Show Notepad opening and the value being typed.

### 2:20 to 2:50 - tool streaming

Show:

```powershell
curl "http://localhost:8080/navigate/stream?message=Open+Notepad+and+type+Hello+Gemini"
```

This proves the ADK loop is calling tools live, not returning a fake final answer.

### 2:50 to 3:30 - Google Cloud evidence

Show:

- Cloud Run service URL responding to `/health`
- The deploy command or Cloud Run console
- Firestore collection or Cloud Run environment variables if available

State clearly:

"Cloud Run hosts the Gemini orchestrator and ADK navigator. The Windows companion stays on the controlled machine because it needs a live desktop session."

### 3:30 to 4:00 - close

Summarize in one sentence:

"TELOS gives Gemini multimodal desktop understanding plus executable UI actions, which is why it fits the UI Navigator category."

## Recording tips

- Record at 100 percent display scaling if possible
- Use large terminal fonts
- Avoid switching between too many windows
- Keep the demo in one take if you can
- Do not claim voice or audio streaming unless you implement it before recording
