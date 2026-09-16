# Software Design Description (SDD)
## SDLC-MCP: Agentic SDLC Automation Server

---

| Field | Value |
|---|---|
| **Document ID** | SDD-SDLC-MCP-001 |
| **Version** | 1.0 |
| **Status** | ✅ **Approved for Construction** |
| **Classification** | Internal — Engineering |
| **Related Artifacts** | SRS-SDLC-MCP-001, ADR-001…ADR-009 |
| **Framework Basis** | SWEBOK v4, ISO/IEC/IEEE 42010, C-DAD |

---

## 1. Introduction

### 1.1 Purpose
This Software Design Description specifies the design of **SDLC-MCP**, a Model Context Protocol (MCP) server that exposes a coordinated team of AI agents to automate the Software Development Life Cycle (SDLC). It translates the approved SRS into an implementable blueprint aligned with SWEBOK knowledge areas and Contract-Driven Agentic Development (C-DAD) principles.

### 1.2 Scope
The system provides MCP tools that drive SDLC phases — Inception, Elaboration, Construction, Transition, and Post-Transition — through specialized agents built on the **AG2 v1** framework (`autogen`) and served via **`fastmcp`**.

### 1.3 Definitions
| Term | Meaning |
|---|---|
| **MCP** | Model Context Protocol |
| **C-DAD** | Contract-Driven Agentic Development |
| **ADR** | Architecture Decision Record |
| **SRS** | Software Requirements Specification |
| **V-Model** | Verification pairing between producing and verifying roles |
| **Handoff Graph** | Deterministic agent-to-agent transition topology |

### 1.4 References
- SWEBOK Guide v4 (IEEE Computer Society)
- ISO/IEC/IEEE 42010:2022 — Architecture Description
- MCP Specification (Anthropic)
- AG2 v1 documentation (`autogen`)
- `fastmcp` documentation

---

## 2. Design Considerations

### 2.1 Assumptions
- Single-node, in-memory deployment for the reference implementation.
- MCP clients honor the session handshake (`initialize` → `Mcp-Session-Id` → `notifications/initialized`).
- LLM credentials supplied via `.env`.

### 2.2 Constraints
- Must use `autogen` (AG2 v1) for agent orchestration — **ADR-001**.
- Must use `fastmcp` for MCP transport — **ADR-002**.
- Contract lifecycle transitions **require human approval** — **ADR-005**.
- No containerization required for local execution — **ADR-008**.

### 2.3 Guiding Principles (C-DAD)
1. **Contracts as single source of truth** — REQ, ADR, SDD, and interface specs are versioned artifacts.
2. **Hybrid governance** — automation proposes; humans approve.
3. **Full traceability** — REQ → ADR → SDD → Code → Test → Deployment.
4. **Deterministic collaboration** — fixed handoff graph, not free-form chat.
5. **V-model verification pairing** — every producer has a verifier.

---

## 3. Architectural Design

### 3.1 System Context
```
┌────────────────┐   MCP/HTTP    ┌────────────────────────┐   LLM API   ┌─────────┐
│   MCP Client   │ ────────────► │   SDLC-MCP Server      │ ──────────► │   LLM   │
│ (IDE/CLI/Chat) │ ◄──────────── │  (fastmcp + autogen)   │ ◄────────── │Provider │
└────────────────┘               └──────────┬─────────────┘             └─────────┘
                                            │
                                            ▼
                                   ┌────────────────────┐
                                   │  ArtifactStore     │
                                   │  (in-memory)       │
                                   └────────────────────┘
```

### 3.2 Logical View — Agent Team

| Phase | Agent | SWEBOK KA | Verified By |
|---|---|---|---|
| Inception | **Requirements Analyst** | Software Requirements | Architect |
| Elaboration | **Architect** | Software Architecture | Designer |
| Elaboration | **Designer** | Software Design | QA |
| Construction | **Developer** | Software Construction | QA |
| Construction | **QA** | Software Testing | Orchestrator |
| Transition | **DevOps** | SE Operations | QA |
| Post-Transition | **Maintainer** | Software Maintenance | Orchestrator |
| Cross-cutting | **Orchestrator** | SE Management, SCM | Human |

### 3.3 Handoff Graph (Fixed)
```
Orchestrator ─► Requirements Analyst ─► Architect ─► Designer
                                                        │
                                                        ▼
Orchestrator ◄─ QA ◄─ Developer ◄────────────────── Designer
     │
     ├─► DevOps ─► QA (deployment verification)
     └─► Maintainer ─► Orchestrator (feedback loop)
```

### 3.4 Deployment View
- Single Python process launched via `python app.py` or `uvicorn app:mcp.app --host 0.0.0.0 --port 8000`.
- Stateless HTTP transport; state held in `ArtifactStore`.

### 3.5 Key Architectural Decisions
| ADR | Decision |
|---|---|
| **ADR-001** | Use AG2 v1 (`autogen`) for agent framework |
| **ADR-002** | Use `fastmcp` for MCP server transport |
| **ADR-003** | Fixed handoff graph over free-form group chat |
| **ADR-004** | In-memory `ArtifactStore` for reference impl |
| **ADR-005** | Human approval gate for contract lifecycle |
| **ADR-006** | V-model verification pairing enforced |
| **ADR-007** | SWEBOK KAs as agent role charter |
| **ADR-008** | Local execution without Docker |
| **ADR-009** | Session handshake per MCP spec |

---

## 4. Detailed Design

### 4.1 Project Structure
```
sdlc-mcp/
├── app.py                 # fastmcp server + tool registration
├── requirements.txt
├── .env                   # LLM keys, model config
├── agents/
│   ├── __init__.py
│   ├── prompts.py         # SWEBOK-aligned system prompts
│   ├── builders.py        # Agent factory functions
│   ├── analyst.py
│   ├── architect.py
│   ├── designer.py
│   ├── developer.py
│   ├── qa.py
│   ├── devops.py
│   ├── maintainer.py
│   └── orchestrator.py
├── workflow/
│   ├── __init__.py
│   ├── sdlc_team.py       # Team assembly + handoff graph
│   └── artifacts.py       # ArtifactStore, Contract, lifecycle
└── tests/
    ├── test_artifacts.py
    ├── test_workflow.py
    └── test_mcp_tools.py
```

### 4.2 Component: `workflow/artifacts.py`

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import uuid

class LifecycleState(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"

VALID_TRANSITIONS = {
    LifecycleState.DRAFT:      {LifecycleState.ACTIVE, LifecycleState.RETIRED},
    LifecycleState.ACTIVE:     {LifecycleState.DEPRECATED, LifecycleState.RETIRED},
    LifecycleState.DEPRECATED: {LifecycleState.RETIRED},
    LifecycleState.RETIRED:    set(),
}

@dataclass
class Contract:
    id: str
    kind: str                # 'REQ' | 'ADR' | 'SDD' | 'API' | 'TEST'
    content: dict
    state: LifecycleState = LifecycleState.DRAFT
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    proposed_transition: LifecycleState | None = None
    approvals: list[dict] = field(default_factory=list)

class ArtifactStore:
    def __init__(self) -> None:
        self.contracts: dict[str, Contract] = {}
        self.traceability: list[dict] = []   # {from_id, to_id, relation}
        self.approvals: list[dict] = []      # audit log

    def add(self, kind: str, content: dict) -> Contract:
        c = Contract(id=f"{kind}-{uuid.uuid4().hex[:8]}", kind=kind, content=content)
        self.contracts[c.id] = c
        return c

    def link(self, from_id: str, to_id: str, relation: str) -> None:
        self.traceability.append(
            {"from": from_id, "to": to_id, "relation": relation}
        )

    def propose_lifecycle_transition(
        self, contract_id: str, target: LifecycleState
    ) -> None:
        c = self.contracts[contract_id]
        if target not in VALID_TRANSITIONS[c.state]:
            raise ValueError(f"Invalid transition {c.state} → {target}")
        c.proposed_transition = target

    def approve(self, contract_id: str, approver: str, note: str = "") -> Contract:
        c = self.contracts[contract_id]
        if c.proposed_transition is None:
            raise ValueError("No pending transition")
        record = {
            "contract_id": contract_id,
            "from": c.state,
            "to": c.proposed_transition,
            "approver": approver,
            "note": note,
            "at": datetime.utcnow(),
        }
        c.state = c.proposed_transition
        c.proposed_transition = None
        c.version += 1
        c.approvals.append(record)
        self.approvals.append(record)
        return c

    def dump(self) -> dict[str, Any]:
        return {
            "contracts": {k: v.__dict__ for k, v in self.contracts.items()},
            "traceability": self.traceability,
            "approvals": self.approvals,
        }
```

### 4.3 Component: `agents/builders.py`
Factory functions instantiate `autogen.ConversableAgent` (or `AssistantAgent`) per role, injecting SWEBOK-aligned system prompts from `agents/prompts.py` and LLM config from `.env`.

### 4.4 Component: `workflow/sdlc_team.py`
- Assembles agents.
- Registers the handoff graph (allowed transitions per role).
- Exposes phase-level entry points invoked by MCP tools.
- Enforces V-model pairing: producer output cannot be finalized without verifier sign-off.

### 4.5 Component: `app.py`
- Instantiates `FastMCP("sdlc-mcp")`.
- Instantiates shared `ArtifactStore`.
- Registers MCP tools (Section 6.2).
- Runs via `mcp.run()` or ASGI mount for `uvicorn`.

---

## 5. Key Scenarios

### 5.1 Requirements Elicitation
```
Client ─► sdlc_elicit_requirements(goal)
       ─► Orchestrator ─► Requirements Analyst
       ─► Architect verifies acceptance criteria
       ─► ArtifactStore.add(kind='REQ', ...)
       ─► returns REQ-xxxxxxxx (state=draft)
       ─► Human approves via approve() → state=active
```

### 5.2 End-to-End Feature Implementation
```
sdlc_implement_feature(req_id)
  → Designer (SDD)  → link SDD→REQ
  → Developer (code) → link Code→SDD
  → QA (tests)       → link Test→REQ  (V-model)
  → Orchestrator packages result
  → Human approval gate before ACTIVE
```

### 5.3 Change Review
`sdlc_review_change(diff, contract_ids)` runs Architect + QA to assess impact, produce ADR-delta and test-impact report.

### 5.4 Operate & Maintain
`sdlc_operate_and_maintain(incident)` engages DevOps then Maintainer; produces post-mortem contract linked to originating REQ/ADR.

---

## 6. Interface Design

### 6.1 MCP Session Handshake
1. `POST /mcp` with `initialize` → server returns `Mcp-Session-Id` header.
2. Client sends `notifications/initialized`.
3. Subsequent tool calls include `Mcp-Session-Id`.

### 6.2 Exposed MCP Tools
| Tool | Purpose |
|---|---|
| `sdlc_elicit_requirements(goal)` | Produce SRS-level REQ contracts |
| `sdlc_design_architecture(req_ids)` | Produce ADRs + SDD skeleton |
| `sdlc_implement_feature(req_id)` | E2E: Design → Code → Test |
| `sdlc_review_change(diff, contract_ids)` | Impact analysis |
| `sdlc_operate_and_maintain(incident)` | DevOps + Maintainer flow |
| `sdlc_dump_artifacts()` | Full ArtifactStore snapshot |

### 6.3 Contract Governance API (internal)
`propose_lifecycle_transition(contract_id, target)` → `approve(contract_id, approver, note)`.

---

## 7. Data Design

### 7.1 In-Memory Schema
- `contracts: dict[str, Contract]`
- `traceability: list[{from, to, relation}]`
- `approvals: list[{contract_id, from, to, approver, note, at}]`

### 7.2 Contract Kinds & Relations
- Kinds: `REQ`, `ADR`, `SDD`, `API`, `CODE`, `TEST`, `DEPLOY`, `INCIDENT`.
- Relations: `derives_from`, `implements`, `verifies`, `deploys`, `resolves`.

---

## 8. Deployment & Operations

### 8.1 Local Execution
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # add LLM keys
python app.py
# or:
uvicorn app:mcp.app --host 0.0.0.0 --port 8000
```

### 8.2 Configuration (`.env`)
- `OPENAI_API_KEY` (or provider equivalent)
- `MODEL_NAME`
- `MCP_HOST`, `MCP_PORT`

### 8.3 Observability
- Structured logs for each tool invocation, handoff, and approval.
- `sdlc_dump_artifacts` supports offline audit.

---

## 9. Verification & Validation

### 9.1 V-Model Pairing
| Producer | Verifier |
|---|---|
| Requirements Analyst | Architect |
| Architect / Designer | QA |
| Developer | QA |
| DevOps | QA |
| Maintainer | Orchestrator |

### 9.2 Test Strategy
- **Unit**: `ArtifactStore` transitions, invalid lifecycle rejection.
- **Integration**: MCP handshake, tool round-trips.
- **Workflow**: End-to-end feature scenario asserts traceability chain.

---

## 10. Traceability Matrix (excerpt)

| REQ | ADR | SDD Section | Component | Test |
|---|---|---|---|---|
| REQ-agent-team | ADR-001, ADR-007 | §3.2 | `agents/*` | `test_workflow.py::test_team_roster` |
| REQ-mcp-transport | ADR-002, ADR-009 | §6.1 | `app.py` | `test_mcp_tools.py::test_handshake` |
| REQ-governance | ADR-005 | §4.2, §6.3 | `artifacts.py` | `test_artifacts.py::test_approval_required` |
| REQ-traceability | ADR-004 | §7 | `artifacts.py` | `test_artifacts.py::test_link` |
| REQ-deterministic-flow | ADR-003 | §3.3 | `sdlc_team.py` | `test_workflow.py::test_handoff_graph` |

---

## 11. Risks & Open Issues

| ID | Risk | Mitigation |
|---|---|---|
| R-01 | In-memory store lost on restart | Future: pluggable persistence adapter |
| R-02 | LLM non-determinism affects handoffs | Fixed graph + verifier gate |
| R-03 | Placeholder API drift (`ag2.*` vs `autogen`/`fastmcp`) | Mapping documented in ADR-001/002 |
| R-04 | Approval bottleneck | Batch approval endpoint (future) |
| R-05 | Prompt injection via requirements text | Input sanitization + role isolation |

---

## 12. Appendices

### A. Template-to-Real API Mapping
| Contest Template | Real Implementation |
|---|---|
| `ag2.Agent` | `autogen.ConversableAgent` / `AssistantAgent` |
| `ag2.mcp.MCPServer` | `fastmcp.FastMCP` |
| `ag2.tool` decorator | `@mcp.tool()` from `fastmcp` |

### B. `requirements.txt` (baseline)
```
autogen>=0.4          # AG2 v1
fastmcp>=0.2
python-dotenv
uvicorn
pytest
```

### C. Approval Record
| Role | Name | Date | Signature |
|---|---|---|---|
| Architect | — | — | ✅ |
| Designer | — | — | ✅ |
| QA Lead | — | — | ✅ |
| Product Owner | — | — | ✅ |

---

**End of Document — SDD-SDLC-MCP-001 v1.0 — Approved for Construction.**