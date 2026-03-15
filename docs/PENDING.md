# TELOS — Pending Items & Known Gaps

> Generated after the comprehensive remediation pass (Batches 1–4).
> Items below are NOT blockers for hackathon submission but should be
> addressed for production deployment.

---

## Not Yet Implemented (Requires New Code)

| Item | Severity | Notes |
|------|----------|-------|
| SSE token-in-query-string risk | Medium | SSE `/events?token=…` sends the API token in the URL. Consider switching to a short-lived session ticket or cookie-based auth for SSE streams. |
| Firestore composite indexes | Low | If Firestore is used at scale, document required composite indexes in `docs/FIRESTORE.md`. Current SQLite default does not need this. |
| Structured logging (JSON) | Low | Agents use Python `logging` with string formatting. Could be upgraded to `structlog` or `python-json-logger` for production log aggregation. |
| Coverage tooling | Low | `pytest-cov` is not configured. Add `[tool:pytest]` coverage options to `pytest.ini` for CI gating. |
| Delta Engine integration tests | Low | Rust delta engine has unit tests but no integration tests exercising the Python → Rust HTTP path end-to-end. |
| UIGraph C# health checks | Low | C# UIGraph service is assumed to have `/health` but this is not verified in Python tests. |
| Rate limiter persistence | Low | `rate_limit.py` uses in-memory counters that reset on restart. Consider Redis or SQLite backing for production. |

## Partially Implemented (Needs Hardening)

| Item | Status | Notes |
|------|--------|-------|
| Azure Container Apps deploy | Template ready | `deploy/azure-deploy.yaml` uses `${...}` variables. Needs actual CI pipeline to substitute and deploy. Not tested in real ACA. |
| Foundry provider | Wired, untested live | `foundry_provider.py` exists and is registered. No live Azure AI Foundry endpoint has been tested against. |
| Semantic Kernel provider | Wired, metrics limited | SK SDK does not expose per-request token counts. Byte-level tracking is implemented; see inline comment in `semantic_kernel_provider.py`. |
| Docker Compose | Functional for Orchestrator + Scheduler | Go capture engine and Rust delta engine run natively on Windows (screen capture requires desktop access). Not containerizable for CI. |

## Already Fixed (This Remediation Pass)

| Batch | Item | Fix |
|-------|------|-----|
| 1 | E2E test failures (7 tests) | Added `_await` parameter to `TaskRouter.submit()` |
| 1 | PII leakage in SSE payloads | Applied `mask_pii()` and `_sanitize_for_sse()` to all SSE event data |
| 2 | CORS too permissive (`*`) | Restricted to explicit methods and headers |
| 2 | Port conflict (Go + Rust both on 8084) | Go → 8085 (`SCREENSHOT_ENGINE_PORT`), Rust → 8084 (`DELTA_ENGINE_PORT`) |
| 2 | Writer retry was constant sleep | Changed to exponential backoff `min(1.0 * 2^attempt, 4.0)` |
| 2 | Frontend token in localStorage | Moved to `sessionStorage` |
| 3 | Azure deploy YAML had literal `<YOUR_...>` | Rewritten with `${...}` template vars, probes, resource limits |
| 3 | walkthrough.md overclaims | Corrected test count, delta pipeline, writer retry description |
| 3 | README missing hackathon info | Added tech map, Copilot usage, limitations sections |
| 4 | Env var naming collision (`CAPTURE_ENGINE_PORT`) | Renamed: Python uses `SCREENSHOT_ENGINE_*`, Rust uses `DELTA_ENGINE_*` |
| 4 | Vision test used wrong port (8084) | Fixed to 8085 with `SCREENSHOT_ENGINE_*` env vars |
| 4 | Reader/Writer had no egress logging | Added `egress.record()` for all UIGraph HTTP calls |
| 4 | SETUP.md was incomplete/wrong | Full rewrite with port map, startup order, troubleshooting |
| 4 | No startup script | Created `scripts/start-all.ps1` |

## Architecture Decisions Preserved

- **Windows-first**: Screenshot capture and UIAutomation require a Windows desktop session. These services cannot be containerized.
- **SQLite default**: Memory backend defaults to SQLite for zero-config local runs. Firestore is opt-in via `TELOS_MEMORY_BACKEND=firestore`.
- **Privacy-strict default**: `TELOS_PRIVACY_MODE=strict` blocks image egress by default. Vision features require explicit opt-in.
- **No cloud dependency for tests**: All 146 tests run offline with mocked providers.
