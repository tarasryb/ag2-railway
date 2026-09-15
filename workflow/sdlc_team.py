# workflow/sdlc_team.py
from ag2 import GroupChat, GroupChatManager
from ag2.config import OpenAIConfig

from agents import (
    requirements, architect, designer, developer,
    qa, security, devops, maintainer, orchestrator,
)
from .artifacts import ArtifactStore


def build_sdlc_team(model: str) -> GroupChatManager:
    store = ArtifactStore()

    agents = [
        orchestrator.build(model),   # PM / router
        requirements.build(model),   # Inception
        architect.build(model),      # Elaboration
        designer.build(model),       # Elaboration
        security.build(model),       # cross-cutting reviewer
        developer.build(model),      # Construction
        qa.build(model),             # Construction / V-model right side
        devops.build(model),         # Transition
        maintainer.build(model),     # Post-Transition
    ]

    # Handoff graph — enforces V-model pairing (creator ↔ verifier)
    # and Unified Process phase ordering.
    handoffs = {
        "orchestrator":        ["requirements_analyst"],
        "requirements_analyst": ["architect", "orchestrator"],
        "architect":           ["designer", "security"],
        "designer":            ["developer", "qa"],
        "security":            ["architect", "designer", "developer"],
        "developer":           ["qa"],
        "qa":                  ["devops", "developer"],   # bounce back on fail
        "devops":              ["maintainer", "orchestrator"],
        "maintainer":          ["architect", "orchestrator"],
    }

    chat = GroupChat(
        agents=agents,
        handoffs=handoffs,
        shared_state={"artifacts": store},
        max_rounds=40,
        termination=lambda msg: "SDLC_COMPLETE" in (msg.content or ""),
    )

    return GroupChatManager(
        chat,
        config=OpenAIConfig(model=model),
        system_prompt=(
            "You coordinate an SDLC team of specialized AI agents. "
            "Route each message to the next appropriate role based on the "
            "handoff graph. Enforce: (1) V-model pairing — every "
            "creator role is followed by its verifier; (2) contract-driven "
            "governance — no lifecycle transition without human approval; "
            "(3) full traceability REQ → ADR → SDD → code → test → deploy."
        ),
    )
