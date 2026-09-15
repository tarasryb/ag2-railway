# workflow/artifacts.py
from __future__ import annotations
import json, time, uuid
from dataclasses import dataclass, field, asdict
from typing import Literal

Lifecycle = Literal["draft", "active", "deprecated", "retired"]


@dataclass
class Contract:
    id: str
    version: str = "0.1.0"
    lifecycle: Lifecycle = "draft"
    owners: list[str] = field(default_factory=list)
    artifacts: dict = field(default_factory=dict)   # openapi, tests, ...
    links: dict = field(default_factory=dict)       # adr, srs, ...
    provenance: dict = field(default_factory=dict)  # commit, author, sig


class ArtifactStore:
    """In-memory registry. Swap for Git/OCI in production."""

    def __init__(self) -> None:
        self._srs: dict[str, dict] = {}
        self._adr: dict[str, dict] = {}
        self._sdd: dict[str, dict] = {}
        self._contracts: dict[str, Contract] = {}
        self._traces: list[tuple[str, str]] = []   # (from_id, to_id)
        self._approvals: list[dict] = []           # human gates

    # --- SRS / ADR / SDD ------------------------------------------------
    def write_srs(self, req_id: str, spec: dict) -> str:
        self._srs[req_id] = spec
        return req_id

    def write_adr(self, adr_id: str, decision: dict) -> str:
        self._adr[adr_id] = decision
        return adr_id

    def write_sdd(self, sdd_id: str, design: dict) -> str:
        self._sdd[sdd_id] = design
        return sdd_id

    # --- Contracts (C-DAD) ---------------------------------------------
    def publish_contract(self, c: Contract) -> str:
        if c.id in self._contracts:
            raise ValueError(f"duplicate contract id: {c.id}")
        self._contracts[c.id] = c
        return c.id

    def propose_lifecycle_transition(
        self, contract_id: str, target: Lifecycle, reason: str
    ) -> dict:
        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "contract": contract_id,
            "target": target,
            "reason": reason,
            "ts": time.time(),
            "status": "pending_human_approval",
        }
        self._approvals.append(proposal)
        return proposal

    def approve(self, proposal_id: str, approver: str) -> None:
        for p in self._approvals:
            if p["proposal_id"] == proposal_id:
                p["status"] = "approved"
                p["approver"] = approver
                self._contracts[p["contract"]].lifecycle = p["target"]
                return
        raise KeyError(proposal_id)

    # --- Traceability graph --------------------------------------------
    def trace_link(self, from_id: str, to_id: str) -> None:
        self._traces.append((from_id, to_id))

    def dump(self) -> str:
        return json.dumps({
            "srs": self._srs,
            "adr": self._adr,
            "sdd": self._sdd,
            "contracts": {k: asdict(v) for k, v in self._contracts.items()},
            "traces": self._traces,
            "approvals": self._approvals,
        }, indent=2)
