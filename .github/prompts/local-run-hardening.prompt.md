# Local Run Hardening Prompt

Inspect the current workspace and determine exactly how TELOS can be run and validated locally.

Your goals:
1. derive local setup instructions from actual files
2. identify blockers that currently prevent smooth local execution
3. propose the minimum repo changes needed to make local execution repeatable and judge-friendly

Review:
- README/docs
- manifests and lockfiles
- scripts and task runners
- env examples
- Docker / compose
- launch configs
- tests
- CI workflows
- service/binary dependencies
- language-specific build/run paths

Output structure:

1. Local Run Verdict
   - Locally Runnable / Partially Locally Runnable / Not Locally Runnable

2. Prerequisites
   - runtimes
   - CLIs
   - package managers
   - services/databases
   - Windows-specific dependencies

3. Required Environment Variables
   - variable
   - purpose
   - whether example/default exists
   - whether secret or non-secret
   - what is missing

4. Step-by-Step Local Setup
5. Step-by-Step Start Commands
6. Step-by-Step Test Commands
7. How to Verify the System Is Working
8. Local-Run Blockers
9. Repo Improvements Needed
10. Suggested README updates

Rules:
- Do not guess values that are not present.
- Prefer exact commands from the repo when available.
- If multiple subsystems have different startup paths, explain the dependency order clearly.
- Call out cloud-only dependencies that block true local execution.
