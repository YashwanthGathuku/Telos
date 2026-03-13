# TELOS — Known Limitations

## MVP Scope Constraints

This is a hackathon MVP. The following limitations are known and intentional.

### UIA Integration

- **Application compatibility varies.** Windows UI Automation support differs across applications. Some apps expose rich accessible trees; others (e.g., Electron-based, custom-rendered) expose minimal or no automation elements.
- **UIA tree depth and breadth are capped.** The UIGraph service limits traversal to depth 8 and 100 children per node to prevent hangs on deeply nested or virtualized controls.
- **SendKeys fallback.** When the target control doesn't support the UIA ValuePattern, the writer falls back to SendKeys. This is fragile if the target field doesn't have focus.
- **Single-monitor assumption.** The MVP has not been tested on multi-monitor setups.

### Cross-App Execution

- **Keyword-based element matching.** The reader agent matches UI elements by keyword overlap with the task detail string. This works for simple cases but may fail on complex or ambiguous UIs.
- **No retry on write failure.** If the writer fails to insert a value, the task completes without automatic retry.
- **No undo support.** Writes are permanent. There is no rollback mechanism.

### Provider Integration

- **Azure and Gemini only.** The MVP supports Azure OpenAI and Google Gemini. Other providers would require implementing `ProviderBase`.
- **No streaming responses.** Provider responses are received in full, not streamed.
- **No token budget management.** Tasks with very long UIA trees could exceed model context limits.

### Privacy

- **Regex-based PII detection.** SSN, email, phone, and credit card patterns are detected via regex. Novel formats or non-US patterns may not be caught.
- **No content-based PII classification.** The filter does not use NLP to identify semantic PII (e.g., names, addresses in free text).
- **Egress log is append-only.** There is no built-in rotation or size limit on `logs/egress.jsonl`.

### Scheduler

- **Cron evaluates purely locally.** The Go scheduler now auto-evaluates cron timing and triggers jobs via the API over localhost.
- **No distributed locking.** The scheduler is single-instance only.
- **SQLite concurrency.** Under heavy concurrent writes, SQLite may serialize requests.

### Desktop Shell

- **Windows only.** The UIA subsystem requires Windows. macOS/Linux are not supported.
- **Development mode tested.** The Tauri app has been tested primarily in `tauri dev` mode. Production builds (`.msi` packaging) are not validated.
- **No themes.** Dark mode only.
- **No i18n.** English only.

### Testing

- **UIGraph tests are mocked.** Real UIA tree walking requires a Windows desktop environment with target applications running. Integration tests mock the HTTP layer.
- **No browser-based frontend tests.** React components are not tested with a DOM testing library in this MVP.
- **Rust tests require GNU toolchain.** `cargo test` needs `dlltool.exe` which is part of the MinGW/GNU toolchain.

### Architecture

- **C# → Rust communication is HTTP, not named pipes.** The architecture specifies named pipes for C# → Rust delta engine communication, but the MVP uses HTTP for simplicity. The pipe interface is reserved for a future iteration.
- **Memory semantics are basic.** The SQLite memory store provides task history and key-value context. Advanced context-aware memory, RAG, or learning is deferred.
- **No agent-to-agent negotiation.** Agents execute in a fixed pipeline (planner → reader → writer → verifier). Dynamic agent collaboration is deferred.

## What Is Real

- Desktop app shell and mission-control dashboard
- Natural-language command intake and task routing
- UIA-first structured extraction with password masking
- Cross-app read → write → verify pipeline
- Pre-egress PII filtering with visible privacy metrics
- Dual-provider abstraction (Azure + Gemini) with env-var swap
- SQLite-backed scheduler with CRUD and manual trigger
- SSE event stream with live dashboard updates
- 80+ automated tests covering privacy, providers, routing, bus, memory, UIGraph extraction, and e2e hero flow
