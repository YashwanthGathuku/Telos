# TELOS Hackathon Review Prompt

Use this prompt in Copilot Chat / Agent mode when you want a full deep audit of the current workspace.

---

Inspect the **entire current workspace** as the **source of truth**. Perform a deep, adversarial, production-grade review of this TELOS codebase and determine whether it is ready for serious engineering use **and** ready for Microsoft AI Dev Day Hackathon submission.

You are operating as an elite cross-functional review panel composed of:
- a Principal Software Engineer
- a Staff Software Architect
- a Senior Security Engineer
- a Senior SRE / Production Reliability Engineer
- a Senior Performance Engineer
- a Senior QA / Test Architect
- a Senior Hackathon Submission Reviewer

Treat this as both:
1. a formal engineering gate before production approval
2. a formal hackathon readiness and submission-quality review

Your standards must be extremely high. Do not give a shallow review. Do not optimize for politeness over truth. Optimize for correctness, risk discovery, evidence quality, and actionable next steps.

---

## Execution Rules

- Review the **actual files in the workspace**, not assumptions.
- Do **not** claim any hackathon requirement is satisfied unless there is direct repository evidence.
- Clearly separate:
  - **VERIFIED** findings supported by direct evidence
  - **INFERRED** risks based on patterns
  - **UNKNOWN / NOT VERIFIED** areas where evidence is missing
  - **MISSING** artifacts or files that should exist but do not
- Cite **file paths**, symbols, modules, or artifacts wherever possible.
- If possible, include **line-level references** or nearest symbol/function/class references.
- Distinguish:
  - production blockers
  - hackathon submission blockers
  - local-run blockers
  - documentation blockers
  - optional improvements
- Do not be fooled by code that merely compiles or looks polished. Look for hidden fragility, AI-generated sloppiness, weak integration, and unsupported claims.

---

## Workspace Traversal Order

Inspect as many relevant files as possible in this order:

1. repository structure and top-level docs
2. README, docs, architecture notes, demo assets, submission artifacts
3. package manifests, lockfiles, build files, dependency definitions
4. environment examples, config files, provider wiring, secrets handling
5. Dockerfiles, compose files, launch configs, scripts, task runners
6. CI/CD workflows, infra/deployment files, Azure-related config
7. tests, fixtures, mocks, coverage indicators
8. source code by subsystem:
   - Python orchestrator / agents / memory / APIs
   - Go capture engine / schedulers
   - Rust screenshot + diff engine
   - C# UIAutomation adapters
   - TypeScript/React dashboard
9. any repo metadata that supports hackathon evidence
10. any missing or suspicious gaps in the expected structure

---

## Review Objectives

### A. Functional correctness
Identify:
- bugs
- logic errors
- broken flows
- incorrect assumptions
- null / undefined handling problems
- race conditions
- concurrency hazards
- state management issues
- API contract mismatches
- serialization/deserialization risks
- validation failures
- partial implementations
- broken orchestration between Python, Go, Rust, C#, and frontend layers

### B. Code quality and maintainability
Identify:
- poor structure
- tight coupling
- weak abstractions
- low cohesion
- duplicated logic
- dead code
- inconsistent naming
- hidden complexity
- brittle modules
- poor extensibility
- poor separation of concerns
- weak typing
- poor error handling
- technical debt
- copy-paste patterns
- AI-generated code smells
- orphaned helpers
- TODO/FIXME risk areas
- fake abstractions that do not meaningfully reduce complexity

### C. Security, privacy, and egress safety
Identify:
- secret exposure
- raw PII logging
- missing masking/redaction
- missing `egress.record()` or equivalent required outbound tracking
- insecure external calls
- injection risks
- auth/authz issues
- unsafe file handling
- insecure defaults
- dependency vulnerability risks
- excessive permissions
- dangerous deserialization
- cloud egress without clear controls
- misconfigured transport/security behavior

### D. Performance, scalability, and algorithmic risk
Identify:
- inefficient algorithms
- poor data structure choices
- unnecessary recomputation
- repeated scans / nested loops
- blocking operations
- memory pressure risks
- N+1 patterns
- poor indexing assumptions
- weak caching strategy
- screenshot/diff throughput risks
- scheduler bottlenecks
- frontend rendering inefficiencies
- scale-breaking orchestration paths

For material hot paths:
- identify the algorithm/approach
- estimate time complexity
- estimate space complexity
- state assumptions behind the estimate
- explain whether the approach is acceptable for realistic workloads
- suggest better alternatives with tradeoffs

Do **not** assign Big-O to trivial helpers unless it matters.

### E. Architecture and reliability
Identify:
- poor boundaries
- fragile process coordination
- weak provider abstraction
- hidden shared state
- lack of idempotency
- weak retry/backoff strategy
- missing fault isolation
- missing graceful degradation
- weak startup/shutdown behavior
- observability gaps
- incomplete error surfaces between subsystems
- weak local/cloud boundary design

### F. Testing and validation
Identify:
- missing unit / integration / E2E coverage
- missing regression protection
- weak testability
- fragile mocks
- missing negative-path tests
- missing performance/security tests
- mismatch between claimed behavior and tested behavior
- lack of meaningful validation for Windows-specific or cross-language behavior

### G. Production readiness
Determine whether the project is:
- **Production Ready**
- **Conditionally Production Ready**
- **Not Production Ready**

Assess:
- observability
- structured logging
- health checks
- metrics/tracing
- configuration hygiene
- deployment safety
- rollback readiness
- local/cloud parity
- runbooks
- backup/recovery assumptions
- maintainability
- supportability

### H. Hackathon readiness and compliance
Determine whether the project is:
- **Submission Ready**
- **Conditionally Submission Ready**
- **Not Submission Ready**

Evaluate direct evidence for the Microsoft AI Dev Day Hackathon requirements, including:

#### Core requirements
1. **AI Technology**
   Evidence of one or more hero technologies:
   - Microsoft Foundry
   - Microsoft Agent Framework
   - Azure MCP
   - GitHub Copilot Agent Mode

2. **Azure Deployment**
   - deployable to Azure
   - Azure-compatible architecture
   - meaningful Azure service usage
   - deployment/config/infrastructure evidence where present

3. **GitHub Development**
   - public-repo readiness
   - evidence of GitHub-centered workflow
   - documentation showing use of VS Code or Visual Studio
   - documentation/evidence of GitHub Copilot usage
   - do not overclaim if evidence is absent

#### Category fit
Assess fit and competitiveness for:
- Best Use of Microsoft Foundry
- Best Enterprise Solution
- Best Multi-Agent System
- Best Azure Integration

#### Submission artifacts
Check for:
- working project
- clear project description
- demo video link or placeholder plan
- public GitHub repo readiness
- architecture diagram
- team info / Microsoft Learn usernames
- judge-friendly documentation

For each requirement/artifact, classify as:
- **VERIFIED**
- **PARTIALLY VERIFIED**
- **NOT VERIFIED**
- **MISSING**
- **NOT APPLICABLE**

### I. Local-run readiness
Determine whether the project is:
- **Locally Runnable**
- **Partially Locally Runnable**
- **Not Locally Runnable**

Based only on actual files, identify:
- prerequisites
- SDKs / runtimes / CLIs
- databases / containers / services
- required env vars
- missing secrets or configuration
- startup sequence
- test commands
- verification steps
- blockers that prevent successful local execution
- minimum changes needed to make local execution smooth and repeatable

### J. Documentation and judge clarity
Review README and docs for:
- requirement mapping
- Microsoft technology clarity
- GitHub Copilot + VS Code / Visual Studio documentation
- Azure story clarity
- architecture clarity
- local-run clarity
- evidence quality
- unsupported claims
- judge readability
- missing sections that could weaken scoring

---

## Output Requirements

Use this exact structure:

1. **Executive Summary**
2. **Production Readiness Verdict**
3. **Hackathon Submission Readiness Verdict**
4. **Local Run Readiness Verdict**
5. **Top Production Blockers**
6. **Top Hackathon Blockers**
7. **Top Local-Run Blockers**
8. **Critical Findings**
9. **High Severity Findings**
10. **Medium Severity Findings**
11. **Low Severity Findings**
12. **Security / Privacy / Egress Assessment**
13. **Architecture / Reliability Assessment**
14. **Performance, Scalability, and Algorithmic Complexity Assessment**
15. **Code Quality and Maintainability Assessment**
16. **Testing Assessment**
17. **DevOps / Deployment / SRE / Observability Assessment**
18. **Dependency and Configuration Assessment**
19. **Hackathon Compliance Assessment**
20. **Category Fit Assessment**
21. **Documentation / README / Judge Clarity Assessment**
22. **Sloppy Code / AI-Code Smell Assessment**
23. **Missing for Production Readiness**
24. **Missing for Hackathon Submission**
25. **Local Run Instructions and Gaps**
26. **Pending Items for Next Review**
27. **Prioritized Remediation Roadmap**
28. **Final Go / No-Go Recommendation**

---

## Issue Format

For each significant issue, include:

- **Issue title**
- **Severity**: Critical / High / Medium / Low
- **Domain**: Bug / Security / Privacy / Performance / Architecture / Maintainability / Testing / Operations / Documentation / Dependency / Algorithm / Hackathon Compliance / Local Run / Other
- **Evidence**: file path(s), symbol(s), and direct observation
- **Exact description**
- **Why it matters**
- **Production impact**
- **Hackathon impact**
- **Failure mode or exploit scenario**
- **Root cause**
- **Recommended fix**
- **Blocker type**:
  - production blocker?
  - hackathon blocker?
  - local-run blocker?
- **Priority**: Immediate / Soon / Later

---

## Special TELOS Checks

Pay special attention to:

- Windows-first assumptions and whether they are documented/testable
- Provider abstraction around `TELOS_PROVIDER`
- memory backend abstraction around `TELOS_MEMORY_BACKEND`
- adherence to `ProviderBase` or equivalent provider contract
- outbound call recording via `egress.record()`
- privacy-safe handling of forensic or user-sensitive artifacts
- cross-language contract safety between Python/Go/Rust/C#
- screenshot, diff, and capture pipeline stability/performance
- dashboard consistency with backend contracts
- judge-facing documentation quality for enterprise/agentic/Azure positioning

---

## Final Rules

- Be exhaustive, not superficial.
- Prefer evidence over impressions.
- Separate facts from assumptions.
- Do not assume a feature is complete because files exist.
- Do not assume hackathon compliance without proof.
- Do not assume the project is locally runnable unless startup requirements are evidenced.
- Call out both obvious and subtle risks.
- If something cannot be verified from the workspace, say exactly what is missing.
- Optimize for an answer that senior engineers and judges would both trust.
