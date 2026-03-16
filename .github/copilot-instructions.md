# TELOS Copilot Instructions

You are operating inside the TELOS repository, a Windows-first multimodal agent project built around Gemini, Google ADK, and Google Cloud.

## Priorities

1. Preserve correctness across Python, Go, Rust, C#, and TypeScript boundaries.
2. Keep privacy and egress controls explicit.
3. Prefer maintainable, testable code over demo-only shortcuts.
4. Keep documentation aligned with what the repository actually implements.

## Project context

TELOS includes:
- Python orchestration and agent flows
- C# Windows UI automation surfaces
- Rust screenshot and delta services
- Go scheduling and support services
- TypeScript/React desktop UI

The hackathon submission path is Gemini-first:
- Gemini model usage through `google-genai`
- agent logic through Google ADK
- deployment on Google Cloud
- UI navigation driven by screenshots and executable actions

## Engineering rules

- Do not invent APIs or requirement claims.
- Do not hardcode secrets or endpoints.
- Keep request and response contracts explicit.
- Update tests and docs when behavior changes.
- Call out anything unverified instead of overclaiming.

## Language guidance

### Python
- Prefer FastAPI, Pydantic, `httpx`, `google-genai`, and Google ADK integrations already present in the repo.
- Add targeted `pytest` coverage for behavior changes.

### C#
- Preserve Windows UI Automation correctness and explicit error handling.

### Rust and Go
- Keep service boundaries clear and operational behavior predictable.

### TypeScript / React
- Prefer typed state and explicit backend contracts.

## Submission guidance

When updating hackathon-facing material, optimize for:
- a clear Gemini requirement mapping
- a credible Google Cloud deployment story
- fast local run instructions
- a demo path that can be recorded without hidden setup

Do not reintroduce outdated provider or hackathon framing.
