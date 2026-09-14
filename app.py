import os

from ag2 import Agent
from ag2.config import OpenAIConfig
from ag2.mcp import MCPServer, SessionConfig


model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

agent = Agent(
    name="railway_assistant",
    prompt=(
        "You are a helpful AI assistant. "
        "Provide accurate, concise, and structured answers. "
        "Use tools when they are available."
    ),
    config=OpenAIConfig(model=model),
)

app = MCPServer(
    agent,
    path="/mcp",
    tool_name="ask_ag2",
    tool_description=(
        "Ask the AG2 agent to analyze a question or complete a task."
    ),
    sessions=SessionConfig(
        max_sessions=128,
        ttl=3600,
    ),
)
