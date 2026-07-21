# Evidence-Routed Inference // Architecture Diagrams

> **Core Philosophy**: Deterministic scientific evidence rules and policy guardrails control method admissibility, computation, and abstention. Structured AI agents are subordinate to the deterministic core.

---

## 1. Conceptual Architecture Diagram

The conceptual flow illustrates how raw data are processed through diagnostic evidence testing and assumption routing to produce an auditable scientific verdict:

```mermaid
flowchart TD
    Q[Scientific Question] --> D[Observed Data y_t]
    D --> E[Deterministic Diagnostic Tests]
    E --> A[Supported vs Contradicted Assumptions]
    A --> M[Scientifically Admissible Methods Catalog]
    M --> R[Multi-Specification Robustness or Abstention Test]
    R --> V[Auditable Scientific Verdict]

    subgraph Scientific Governance
        E
        A
        M
        R
    end

    classDef coreFill fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
    class E,A,M,R coreFill;
```

---

## 2. Implementation Architecture Diagram

The technical implementation architecture demonstrates the offline presentation stack, highlighting how AI agents operate subordinated to the deterministic scientific core:

```mermaid
flowchart LR
    subgraph Frontend Presentation Layer [100% Offline Static Explorer]
        UI[Single-Screen HTML5/CSS3 UI] <--> JS[Vanilla JS Event State Machine]
    end

    subgraph Replay Data Layer [Tracked Replay Artifacts]
        JS <--> JSON[Deterministic Static JSON Payloads]
    end

    subgraph Scientific Core [Evidence-Routed Scientific Engine]
        JSON <--> Adapter[SharpeLab Presentation Adapter]
        Adapter <--> Engine[Deterministic Adjudicator & Router]
        Engine <--> Diag[Diagnostic Registry]
        Engine <--> Infer[Inference Math Engine]

        subgraph Subordinate AI Agent Layer [Planning & Explanation]
            Agent[Structured AI Agents] -.->|Requests Evidence & Explains| Engine
        end
    end

    classDef coreNode fill:#0f172a,stroke:#22c55e,stroke-width:2px,color:#f8fafc;
    classDef agentNode fill:#1e1e2e,stroke:#f59e0b,stroke-width:1px,stroke-dasharray: 5 5,color:#cbd5e1;
    class Engine,Diag,Infer coreNode;
    class Agent agentNode;
```

---

## Technical Summary
- **Deterministic Core**: Scientific calculations, diagnostic p-values, and eligibility decisions are 100% reproducible and governed by typed Pydantic models.
- **Subordinate AI Agents**: AI agents formulate diagnostic plans and draft explanation texts, but cannot bypass diagnostic evidence rules or force admissibility of invalid methods.
- **Presentation Isolation**: The visual UI renders pre-validated static JSON payloads, ensuring fast, 100% offline demonstration replay.
