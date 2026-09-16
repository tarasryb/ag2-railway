# workflow/sdlc_team.py
try:
    from ag2 import GroupChat, GroupChatManager  # type: ignore
    from ag2.config import OpenAIConfig  # type: ignore
except ImportError:
    from autogen import GroupChat, GroupChatManager

    OpenAIConfig = None

from agents import (
    requirements, architect, designer, developer,
    qa, security, devops, maintainer, orchestrator,
)
from .artifacts import ArtifactStore


DEFAULT_MAX_ROUNDS = 40
DEFAULT_COMPLETION_TOKEN = "SDLC_COMPLETE"


def _message_content(message: object) -> str:
    if isinstance(message, dict):
        return str(message.get("content") or "")
    return str(getattr(message, "content", "") or "")


def _build_group_chat(agents, handoffs, store, max_rounds: int, completion_token: str):
    try:
        # Newer AG2 API
        return GroupChat(
            agents=agents,
            handoffs=handoffs,
            shared_state={"artifacts": store},
            max_rounds=max_rounds,
            termination=lambda msg: completion_token in _message_content(msg),
        )
    except TypeError:
        # Legacy autogen API
        by_name = {agent.name: agent for agent in agents}
        allowed_transitions = {
            by_name[source]: [by_name[target] for target in targets]
            for source, targets in handoffs.items()
        }
        chat = GroupChat(
            agents=agents,
            messages=[],
            max_round=max_rounds,
            allowed_or_disallowed_speaker_transitions=allowed_transitions,
            speaker_transitions_type="allowed",
            speaker_selection_method="auto",
        )
        setattr(chat, "shared_state", {"artifacts": store})
        setattr(chat, "termination", lambda msg: completion_token in _message_content(msg))
        return chat


def _build_manager(chat, model: str, system_prompt: str):
    if OpenAIConfig is not None:
        try:
            return GroupChatManager(
                chat,
                config=OpenAIConfig(model=model),
                system_prompt=system_prompt,
            )
        except TypeError:
            pass

    llm_config = {"config_list": [{"model": model}]}
    try:
        return GroupChatManager(
            groupchat=chat,
            llm_config=llm_config,
            system_message=system_prompt,
        )
    except TypeError:
        return GroupChatManager(
            chat,
            llm_config=llm_config,
            system_message=system_prompt,
        )


def build_sdlc_team(
    model: str,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    completion_token: str = DEFAULT_COMPLETION_TOKEN,
) -> GroupChatManager:
    """Build and configure the SDLC multi-agent team manager.

    The resulting team includes orchestrator, requirements, architecture,
    design, security, development, QA, DevOps, and maintenance roles wired
    through a directed handoff graph.

    Args:
        model: Provider model identifier understood by ``OpenAIConfig``
            (for example, ``"gpt-4o-mini"``).
        max_rounds: Maximum GroupChat turns before forced stop.
        completion_token: Sentinel string that marks successful completion
            when found in a message body.

    Returns:
        A ``GroupChatManager`` configured with the SDLC handoff policy.

    Invariants:
        - Every handoff source/target must resolve to an existing agent name.
        - Termination occurs when ``completion_token`` appears in message
          content.
    """
    if max_rounds <= 0:
        raise ValueError("max_rounds must be greater than 0")
    if not completion_token:
        raise ValueError("completion_token must be a non-empty string")

    store = ArtifactStore()

    orchestrator_agent = orchestrator.build(model)   # PM / router
    requirements_agent = requirements.build(model)    # Inception
    architect_agent = architect.build(model)          # Elaboration
    designer_agent = designer.build(model)            # Elaboration
    security_agent = security.build(model)            # cross-cutting reviewer
    developer_agent = developer.build(model)          # Construction
    qa_agent = qa.build(model)                        # Construction / V-model right side
    devops_agent = devops.build(model)                # Transition
    maintainer_agent = maintainer.build(model)        # Post-Transition

    agents = [
        orchestrator_agent,
        requirements_agent,
        architect_agent,
        designer_agent,
        security_agent,
        developer_agent,
        qa_agent,
        devops_agent,
        maintainer_agent,
    ]

    # Handoff graph — enforces V-model pairing (creator ↔ verifier)
    # and Unified Process phase ordering.
    handoffs = {
        orchestrator_agent.name: [requirements_agent.name],
        requirements_agent.name: [architect_agent.name, orchestrator_agent.name],
        architect_agent.name: [designer_agent.name, security_agent.name],
        designer_agent.name: [developer_agent.name, qa_agent.name],
        security_agent.name: [architect_agent.name, designer_agent.name, developer_agent.name],
        developer_agent.name: [qa_agent.name],
        qa_agent.name: [devops_agent.name, developer_agent.name],  # bounce back on fail
        devops_agent.name: [maintainer_agent.name, orchestrator_agent.name],
        maintainer_agent.name: [architect_agent.name, orchestrator_agent.name],
    }

    known_agents = {agent.name for agent in agents}
    for source, targets in handoffs.items():
        if source not in known_agents:
            raise ValueError(f"Unknown handoff source: {source}")
        missing_targets = [target for target in targets if target not in known_agents]
        if missing_targets:
            raise ValueError(
                f"Unknown handoff targets for {source}: {', '.join(missing_targets)}"
            )

    system_prompt = (
        "You coordinate an SDLC team of specialized AI agents. "
        "Route each message to the next appropriate role based on the "
        "handoff graph. Enforce: (1) V-model pairing - every "
        "creator role is followed by its verifier; (2) contract-driven "
        "governance - no lifecycle transition without human approval; "
        "(3) full traceability REQ -> ADR -> SDD -> code -> test -> deploy."
    )

    chat = _build_group_chat(
        agents=agents,
        handoffs=handoffs,
        store=store,
        max_rounds=max_rounds,
        completion_token=completion_token,
    )

    return _build_manager(chat=chat, model=model, system_prompt=system_prompt)
