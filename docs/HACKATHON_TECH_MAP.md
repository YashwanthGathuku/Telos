# TELOS — Microsoft AI Dev Days Hackathon Technology Mapping

This document maps TELOS features to the official Microsoft AI Dev Days Global Hackathon categories and hero technologies, with precise file locations so judges can verify each claim.

Official sources:

- https://github.com/Azure/AI-Dev-Days-Hackathon/blob/main/README.md
- https://github.com/Azure/AI-Dev-Days-Hackathon/blob/main/OFFICIAL_RULES.md

---

## Hero Technologies Used

### 1. Semantic Kernel-backed Microsoft Agent Path

| Claim | Evidence | File |
|-------|----------|------|
| Semantic Kernel provider is implemented | `SemanticKernelProvider` class wraps `AzureChatCompletion` | `services/orchestrator/providers/semantic_kernel_provider.py` |
| Uses official `semantic-kernel` Python SDK | `semantic-kernel>=1.39.0` in requirements | `services/orchestrator/requirements.txt` |
| Multimodal support (text + image) | `ImageContent` used when `image_data` present | `services/orchestrator/providers/semantic_kernel_provider.py:78-84` |
| Provider-switchable via env var | `TELOS_PROVIDER=azure_sk` activates SK path | `services/orchestrator/providers/registry.py` |
| Tests cover SK provider | Unit tests for registry and provider selection | `tests/test_providers.py` |

### 2. Azure AI Foundry

| Claim | Evidence | File |
|-------|----------|------|
| Foundry provider implemented | `FoundryProvider` class with Azure AI Foundry endpoint routing | `services/orchestrator/providers/foundry_provider.py` |
| Foundry env vars documented | `AZURE_FOUNDRY_ENDPOINT`, `AZURE_FOUNDRY_API_KEY`, `AZURE_FOUNDRY_MODEL` | `.env.example` |
| Default provider in deployment | `azure_foundry` is default in docker-compose | `deploy/docker-compose.yml` |

### 3. Multi-Agent Orchestration / Model Router

| Claim | Evidence | File |
|-------|----------|------|
| 5-agent pipeline | Planner → Reader → Writer → Verifier → Vision | `services/orchestrator/router.py` |
| Dynamic step decomposition | PlannerAgent uses LLM to produce ordered JSON steps | `services/orchestrator/agents/planner.py` |
| Agent-to-Agent event bus | `A2ABus` pub/sub with topic routing | `services/orchestrator/bus/a2a.py` |
| Provider registry with overrides | `get_provider()` + `provider_override()` context manager | `services/orchestrator/providers/registry.py` |
| Per-request provider switching | `X-Telos-Provider` header routes to different backends | `services/orchestrator/app.py` (submit_task endpoint) |

### 4. Local MCP-style Model Context Protocol Server

| Claim | Evidence | File |
|-------|----------|------|
| MCP tool server implemented | `MCPServer` with stdio transport | `services/orchestrator/mcp_server.py` |
| MCP tools exposed | `get_recent_tasks`, `get_task` tools | `services/orchestrator/providers/mcp_tools.py` |
| MCP server tests | Test coverage for tool invocations | `tests/test_mcp.py` |
| Copilot integration documented | `.github/copilot-instructions.md` | `.github/copilot-instructions.md` |

### 5. Azure Deployment / Container Apps

| Claim | Evidence | File |
|-------|----------|------|
| Container Apps YAML template | Proper secrets, probes, resource limits | `deploy/azure-deploy.yaml` |
| Docker Compose for local containers | Multi-service compose with env passthrough | `deploy/docker-compose.yml` |
| Dockerfiles for orchestrator & scheduler | Production-ready multi-stage builds | `deploy/Dockerfile.orchestrator`, `deploy/Dockerfile.scheduler` |

### 6. GitHub Copilot + VS Code Workflow Evidence

| Claim | Evidence | File |
|-------|----------|------|
| Copilot instructions configured | Detailed project-specific instructions | `.github/copilot-instructions.md` |
| VS Code workspace support | Python, Go, Rust, C#, TypeScript toolchain | `.github/workflows/ci.yml`, project root configs |
| Reusable Copilot prompts committed | Security-review, local-run, and judge-readiness prompt files | `.github/prompts/*.prompt.md` |
| Copilot-guided workflow documented | End-to-end coding standards and guardrails for Copilot | `.github/copilot-instructions.md` |
| Copilot-assisted hardening outcomes documented | SSE sanitization, CORS hardening, port consistency, docs truth-tightening | `walkthrough.md`, `README.md` |

---

## Official Category Strategy

### Primary: Best Multi-Agent System
- Real 5-agent pipeline: Planner, Reader, Writer, Verifier, Vision
- Internal A2A-style event bus for coordination
- Local MCP-style server for tool-based task inspection
- Strongest direct alignment to the official category wording

### Secondary: Best Enterprise Solution
- Privacy-first architecture with PII filtering
- Egress logging and audit trail
- Token-based authentication and rate limiting
- Hybrid Azure deployment story for enterprise operations

### Conditional: Best Azure Integration
- Azure provider paths and deployment template are implemented
- Should only be emphasized if live Azure proof is available in the submission package

### Conditional: Best Use of Microsoft Foundry
- Foundry-ready provider path exists
- Should only be emphasized if the Foundry path is demonstrated live in the video

---

## What is NOT implemented (honest disclosure)

| Item | Status |
|------|--------|
| Azure SRE Agent direct integration | Not implemented; SRE-readiness via health checks, structured logs, probes |
| Token-level usage metrics in SK provider | SK SDK does not surface these; byte-level tracking is accurate |
| Firestore composite indexes | Documented as manual step; not auto-provisioned |
| Demo video | Pending recording |
| Team information | Solo entrant metadata should be finalized in submission form |
