import importlib
import sys
from dataclasses import dataclass
from types import ModuleType


@dataclass
class FakeAgent:
    name: str


def _make_builder(agent_name: str):
    def _build(_model: str) -> FakeAgent:
        return FakeAgent(name=agent_name)

    return _build


class FakeGroupChat:
    def __init__(self, agents, handoffs, shared_state, max_rounds, termination):
        self.agents = agents
        self.handoffs = handoffs
        self.shared_state = shared_state
        self.max_rounds = max_rounds
        self.termination = termination


class FakeGroupChatManager:
    def __init__(self, chat, config, system_prompt):
        self.chat = chat
        self.config = config
        self.system_prompt = system_prompt


class FakeOpenAIConfig:
    def __init__(self, model: str):
        self.model = model


def _install_ag2_stubs(monkeypatch):
    ag2_module = ModuleType("ag2")
    ag2_module.GroupChat = FakeGroupChat
    ag2_module.GroupChatManager = FakeGroupChatManager

    ag2_config_module = ModuleType("ag2.config")
    ag2_config_module.OpenAIConfig = FakeOpenAIConfig

    monkeypatch.setitem(sys.modules, "ag2", ag2_module)
    monkeypatch.setitem(sys.modules, "ag2.config", ag2_config_module)


def _install_agent_stubs(monkeypatch):
    role_names = {
        "orchestrator": "orchestrator",
        "requirements": "requirements_analyst",
        "architect": "architect",
        "designer": "designer",
        "security": "security",
        "developer": "developer",
        "qa": "qa",
        "devops": "devops",
        "maintainer": "maintainer",
    }

    agents_package = ModuleType("agents")
    monkeypatch.setitem(sys.modules, "agents", agents_package)

    for module_name, role_name in role_names.items():
        module = ModuleType(f"agents.{module_name}")
        module.build = _make_builder(role_name)
        setattr(agents_package, module_name, module)
        monkeypatch.setitem(sys.modules, f"agents.{module_name}", module)


def _import_sdlc_team(monkeypatch):
    _install_ag2_stubs(monkeypatch)
    _install_agent_stubs(monkeypatch)
    sys.modules.pop("workflow.sdlc_team", None)
    return importlib.import_module("workflow.sdlc_team")


def _is_reachable(handoffs, start: str, target: str, max_hops: int = 8) -> bool:
    if start == target:
        return True

    visited = {start}
    frontier = {start}

    for _ in range(max_hops):
        next_frontier = set()
        for node in frontier:
            for nxt in handoffs.get(node, []):
                if nxt == target:
                    return True
                if nxt not in visited:
                    visited.add(nxt)
                    next_frontier.add(nxt)
        if not next_frontier:
            return False
        frontier = next_frontier

    return False


def test_handoff_graph_matches_built_agents(monkeypatch):
    sdlc_team = _import_sdlc_team(monkeypatch)

    manager = sdlc_team.build_sdlc_team("gpt-4o-mini")
    chat = manager.chat

    built_agent_names = {agent.name for agent in chat.agents}
    handoff_sources = set(chat.handoffs.keys())
    handoff_targets = {target for targets in chat.handoffs.values() for target in targets}

    assert handoff_sources == built_agent_names
    assert handoff_targets.issubset(built_agent_names)


def test_expected_bounce_back_route_present(monkeypatch):
    sdlc_team = _import_sdlc_team(monkeypatch)

    manager = sdlc_team.build_sdlc_team("gpt-4o-mini")
    handoffs = manager.chat.handoffs

    assert "developer" in handoffs["qa"]
    assert "qa" in handoffs["developer"]


def test_key_routing_transitions_are_reachable(monkeypatch):
    sdlc_team = _import_sdlc_team(monkeypatch)

    manager = sdlc_team.build_sdlc_team("gpt-4o-mini")
    handoffs = manager.chat.handoffs

    assert _is_reachable(handoffs, "orchestrator", "devops")
    assert _is_reachable(handoffs, "maintainer", "architect", max_hops=1)
    assert _is_reachable(handoffs, "requirements_analyst", "orchestrator", max_hops=1)
