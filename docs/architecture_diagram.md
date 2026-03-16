# TELOS High-Level Architecture Diagram

The following Mermaid diagram illustrates the polyglot microservices architecture, the multi-agent orchestration pipeline, and the privacy boundary of the TELOS system.

> [!TIP]
> This diagram highlights the decoupling of the agent logic (Python Orchestrator) from performance-critical and platform-specific operations (Go Engines, C# Windows MCP), as well as the Provider Abstraction layer that supports seamless switching between LLMs.

```mermaid
flowchart TB
    classDef frontend fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#fff
    classDef python fill:#14532d,stroke:#22c55e,stroke-width:2px,color:#fff
    classDef golang fill:#075985,stroke:#0ea5e9,stroke-width:2px,color:#fff
    classDef csharp fill:#581c87,stroke:#a855f7,stroke-width:2px,color:#fff
    classDef cloud fill:#7f1d1d,stroke:#ef4444,stroke-width:2px,color:#fff
    classDef database fill:#451a03,stroke:#f59e0b,stroke-width:2px,color:#fff

    subgraph User Desktop Environment
        DesktopApp[("📱 TELOS Mission Control\n(React + Vite + Tauri)")]:::frontend
        DesktopApp --"SSE / HTTP"--> Orchestrator
    end

    subgraph TELOS Local Subsystem ["🛡️ Privacy Boundary (Local System)"]
        
        %% Core Orchestrator Segment
        subgraph OrchestratorLayer ["🐍 Python Orchestrator (:8080)"]
            Orchestrator["Task Router & Bus\n(FastAPI)"]:::python
            
            subgraph Specialist Agents
                direction LR
                Planner("🧠 Planner Agent"):::python
                Vision("👁️ Vision Agent"):::python
                Reader("📖 Reader Agent"):::python
                Writer("✍️ Writer Agent"):::python
                Verifier("✅ Verifier Agent"):::python
            end
            
            subgraph Provider Abstraction
                Registry["Provider Registry"]:::python
            end

            Orchestrator --> Planner
            Planner -->|Generates Steps| Orchestrator
            Orchestrator --> Vision & Reader & Writer & Verifier
            
            Planner & Vision --> Registry
            
            EgressLog["Egress Logger & PII Filter"]:::python
            Orchestrator -.-> EgressLog
        end

        %% Auxiliary Services written in other languages
        subgraph GoServices ["🐹 Go Microservices"]
            CaptureEngine("Capture Engine\n(:8085)"):::golang
            Scheduler("Cron Scheduler\n(:8081)"):::golang
            DeltaEngine("Delta Engine\n(:8084)"):::golang
        end

        subgraph CSharpServices ["🎯 Windows Services"]
            UIGraph("UIGraph / UI Automation\n(:8083)"):::csharp
            TargetApp["Any Windows Application\n(Excel, Notepad, Browser)"]
        end

        %% Database
        MemoryDB[("SQLite Memory DB")]:::database

        %% Internal Cross-Service Connections
        Vision --"HTTP POST (Capture)"--> CaptureEngine
        CaptureEngine --"Returns Base64 PNG"--> Vision
        
        Reader & Writer & Verifier --"HTTP (Snapshot/Focus/Action)"--> UIGraph
        UIGraph --"Windows UIA APIs"--> TargetApp
        UIGraph -.->|Fast Diff| DeltaEngine
        
        Scheduler --"Trigger Due Tasks"--> Orchestrator
        Orchestrator -->|State Persistence| MemoryDB
    end

    %% Cloud Boundaries
    subgraph Cloud Providers ["☁️ External LLM Environments"]
        direction LR
        GH[("GitHub Models\n(GPT-4o)")]:::cloud
        AZF[("Azure AI Foundry")]:::cloud
        AZO[("Azure OpenAI")]:::cloud
        GEM[("Google Gemini")]:::cloud
        SK[("Semantic Kernel")]:::cloud
    end

    %% Connections across privacy boundaries
    Registry --"Encrypted Payload & Images"--> GH & AZF & AZO & GEM & SK
    EgressLog -.->|Tracks bytes across boundary| Cloud Providers
    
    %% Style connections to denote type
    linkStyle default stroke:#64748b,stroke-width:2px,fill:none
```

### Component Details

1. **TELOS Mission Control (Frontend)**: The user interface built with React, Vite, and Tauri. It communicates with the Orchestrator via real-time Server-Sent Events (SSE) and strict HTTP endpoints.
2. **Task Router & Bus (Orchestrator)**: The central nervous system written in Python using FastAPI. It handles routing requests to the Planner, breaking down the steps, and executing them asynchronously while streaming updates back to the UI.
3. **Specialist Agents**:
   - **Planner**: Uses the LLM to decompose natural a language string into discrete steps involving the other agents.
   - **Vision**: Interfaces with the Go Capture Engine to read visual screen states, passing multimodal images back to the LLM.
   - **Reader/Writer/Verifier**: Interact exclusively via the UIGraph C# service to extract UI values and write inputs securely.
4. **Provider Abstraction Registry**: Abstracted interface standardizing requests (including multimodal capabilities) dynamically between backends such as GitHub Models, Azure OpenAI, Azure AI Foundry, Google Gemini, and Semantic Kernel.
5. **Polyglot Auxiliary Services**:
   - **Go Capture Engine**: Hyper-fast screen capturing utility binding specifically to performant system libraries.
   - **Go Scheduler**: Background task management utilizing proper posix/cron expressions.
   - **C# UIGraph**: Interacts with the Windows UI Automation (UIA) framework, walking the element tree for scraping or invoking programmatic control patterns.
6. **Privacy Boundary**: All PII scrubbing and egress logging takes place locally before any data (like images or search queries) traverses the local subsystem boundary to the cloud providers.
