import importlib
import sys
from types import ModuleType, SimpleNamespace


class FakeConversableAgent:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def generate_reply(self, messages):
        _ = messages
        return {"content": "ok"}


class FakeFastMCP:
    def __init__(self, name: str):
        self.name = name
        self.tools = {}

    def tool(self, name: str, description: str):
        _ = description

        def _decorator(func):
            self.tools[name] = func
            return func

        return _decorator

    def run(self, **kwargs):
        _ = kwargs


class FakeChat:
    def __init__(self):
        self.agents = [
            SimpleNamespace(name="orchestrator"),
            SimpleNamespace(name="requirements_analyst"),
        ]
        self.handoffs = {
            "orchestrator": ["requirements_analyst"],
            "requirements_analyst": ["orchestrator"],
        }


class FakeManager:
    def __init__(self):
        self.chat = FakeChat()


def _import_app(monkeypatch):
    build_calls = []

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")

    dotenv_module = ModuleType("dotenv")
    dotenv_module.load_dotenv = lambda: None

    autogen_module = ModuleType("autogen")
    autogen_module.ConversableAgent = FakeConversableAgent

    fastmcp_module = ModuleType("fastmcp")
    fastmcp_module.FastMCP = FakeFastMCP

    workflow_pkg = ModuleType("workflow")
    sdlc_team_module = ModuleType("workflow.sdlc_team")
    sdlc_team_module.DEFAULT_MAX_ROUNDS = 40
    sdlc_team_module.DEFAULT_COMPLETION_TOKEN = "SDLC_COMPLETE"

    def _fake_build(model: str, max_rounds: int, completion_token: str):
        build_calls.append((model, max_rounds, completion_token))
        return FakeManager()

    sdlc_team_module.build_sdlc_team = _fake_build

    monkeypatch.setitem(sys.modules, "dotenv", dotenv_module)
    monkeypatch.setitem(sys.modules, "autogen", autogen_module)
    monkeypatch.setitem(sys.modules, "fastmcp", fastmcp_module)
    monkeypatch.setitem(sys.modules, "workflow", workflow_pkg)
    monkeypatch.setitem(sys.modules, "workflow.sdlc_team", sdlc_team_module)

    sys.modules.pop("app", None)
    app_module = importlib.import_module("app")
    return app_module, build_calls


def test_create_sdlc_team_tool_builds_and_registers_team(monkeypatch):
    app_module, build_calls = _import_app(monkeypatch)

    payload = app_module.create_sdlc_team(
        model="gpt-4o-mini",
        max_rounds=25,
        completion_token="DONE",
    )

    assert build_calls == [("gpt-4o-mini", 25, "DONE")]
    assert payload["team_id"] in app_module.TEAM_REGISTRY
    assert payload["agent_count"] == 2
    assert payload["agents"] == ["orchestrator", "requirements_analyst"]


def test_list_sdlc_teams_returns_created_team(monkeypatch):
    app_module, _ = _import_app(monkeypatch)

    created = app_module.create_sdlc_team()
    teams = app_module.list_sdlc_teams()

    assert len(teams) == 1
    assert teams[0]["team_id"] == created["team_id"]
    assert teams[0]["agent_count"] == created["agent_count"]
