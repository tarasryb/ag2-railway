# app.py
import os
import uuid
from typing import Any

from dotenv import load_dotenv
from autogen import ConversableAgent
from fastmcp import FastMCP

from workflow.sdlc_team import (
    DEFAULT_COMPLETION_TOKEN,
    DEFAULT_MAX_ROUNDS,
    build_sdlc_team,
)

load_dotenv()

MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
API_KEY = os.environ["OPENAI_API_KEY"]      # KeyError раніше, ніж LLM-помилка
HOST    = os.getenv("HOST", "127.0.0.1")
PORT    = int(os.getenv("PORT", "8000"))
PATH    = os.getenv("MCP_PATH", "/mcp")

TEAM_REGISTRY: dict[str, Any] = {}

# ── AG2 agent ─────────────────────────────────────────────────────────────
llm_config = {
    "config_list": [
        {
            "model": MODEL,
            "api_key": API_KEY,
        }
    ]
}

agent = ConversableAgent(
    name="railway_assistant",
    system_message=(
        "You are a helpful AI assistant. "
        "Provide accurate, concise, and structured answers. "
        "Use tools when they are available."
    ),
    llm_config=llm_config,
    human_input_mode="NEVER",
)

# ── MCP server ────────────────────────────────────────────────────────────
app = FastMCP("ag2-railway")


def _agent_name(value: Any) -> str:
    if isinstance(value, str):
        return value
    return str(getattr(value, "name", value))


def _manager_chat(manager: Any) -> Any:
    return getattr(manager, "chat", None) or getattr(manager, "groupchat", None)


def _extract_handoffs(manager: Any) -> dict[str, list[str]]:
    chat = _manager_chat(manager)
    if chat is None:
        return {}

    raw_handoffs = getattr(chat, "handoffs", None)
    if isinstance(raw_handoffs, dict):
        return {
            _agent_name(source): [_agent_name(target) for target in targets]
            for source, targets in raw_handoffs.items()
        }

    raw_handoffs = getattr(chat, "allowed_or_disallowed_speaker_transitions", None)
    if not isinstance(raw_handoffs, dict):
        raw_handoffs = getattr(chat, "allowed_speaker_transitions_dict", None)
    if not isinstance(raw_handoffs, dict):
        return {}

    return {
        _agent_name(source): [_agent_name(target) for target in targets]
        for source, targets in raw_handoffs.items()
    }


def _extract_agent_names(manager: Any) -> list[str]:
    chat = _manager_chat(manager)
    if chat is None:
        return []
    return [_agent_name(agent) for agent in getattr(chat, "agents", [])]

@app.tool(
    name="ask_ag2",
    description="Ask the AG2 agent to analyze a question or complete a task.",
)
def ask_ag2(question: str) -> str:
    reply = agent.generate_reply(
        messages=[{"role": "user", "content": question}]
    )
    if isinstance(reply, dict):
        return reply.get("content", "")
    return str(reply)


@app.tool(
    name="create_sdlc_team",
    description=(
        "Create and register an SDLC multi-agent team manager "
        "built from workflow.sdlc_team.build_sdlc_team."
    ),
)
def create_sdlc_team(
    model: str = MODEL,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    completion_token: str = DEFAULT_COMPLETION_TOKEN,
) -> dict[str, Any]:
    manager = build_sdlc_team(
        model=model,
        max_rounds=max_rounds,
        completion_token=completion_token,
    )
    team_id = str(uuid.uuid4())
    TEAM_REGISTRY[team_id] = manager

    return {
        "team_id": team_id,
        "model": model,
        "max_rounds": max_rounds,
        "completion_token": completion_token,
        "agent_count": len(_extract_agent_names(manager)),
        "agents": _extract_agent_names(manager),
        "handoffs": _extract_handoffs(manager),
    }


@app.tool(
    name="list_sdlc_teams",
    description="List SDLC teams created during the current server process.",
)
def list_sdlc_teams() -> list[dict[str, Any]]:
    teams = []
    for team_id, manager in TEAM_REGISTRY.items():
        teams.append({
            "team_id": team_id,
            "agent_count": len(_extract_agent_names(manager)),
            "agents": _extract_agent_names(manager),
        })
    return teams

if __name__ == "__main__":
    host = os.getenv("HOST", HOST)
    port = int(os.getenv("PORT", str(PORT)))
    app.run(transport="http", host=host, port=port, path=PATH)
