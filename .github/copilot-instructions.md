# TELOS Copilot Agent Instructions

Welcome, GitHub Copilot! You are assisting with the TELOS project (Task Execution & Live Operation System).

## 1. Project Context
TELOS is a Windows desktop forensic audit and execution harness. It is a polyglot system containing:
- **Python**: Core orchestrator, specialist agents (Planner, Reader, Writer, Verifier, Vision), memory stores.
- **Go**: High-performance HTTP capture engine and schedulers.
- **Rust**: High-performance screenshot capture and delta/diff engine (`telos_delta_engine`).
- **C#**: UIAutomation API adapters.
- **TypeScript/React**: The Dashboard frontend.

## 2. Coding Standards
- **Python**: Use `pydantic` for models, `httpx` for requests, `FastAPI` for APIs. Never use raw `requests`. Prefer `google-genai` for Gemini. Prefer `semantic-kernel` for Azure/Microsoft. Always use absolute imports.
- **Go**: Use standard library `net/http` when possible. Follow standard idiomatic formatting (`gofmt`).
- **Rust**: Prefer `x86_64-pc-windows-msvc` target features. Use `axum` and `tokio`.

## 3. Privacy & Egress
TELOS has strict privacy requirements:
- Never log raw PII.
- Mask PII in Local -> Cloud flows.
- Always record external calls via `egress.record()`.

## 4. Environment
The required environment variables flip the cloud provider logic to make TELOS plug-and-play:
- `TELOS_PROVIDER`: `gemini` or `azure_sk`
- `TELOS_MEMORY_BACKEND`: `sqlite` or `firestore`

When proposing new code, ensure it adheres to the `ProviderBase` interface for language models. Always verify tests via `pytest` before finalizing.