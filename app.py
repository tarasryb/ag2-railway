# app.py
import os
from dotenv import load_dotenv
from autogen import ConversableAgent
from fastmcp import FastMCP

load_dotenv()

MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
API_KEY = os.environ["OPENAI_API_KEY"]      # KeyError раніше, ніж LLM-помилка
HOST    = os.getenv("HOST", "127.0.0.1")
PORT    = int(os.getenv("PORT", "8000"))
PATH    = os.getenv("MCP_PATH", "/mcp")

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

if __name__ == "__main__":
    host = os.getenv("HOST", HOST)
    port = int(os.getenv("PORT", str(PORT)))
    app.run(transport="http", host=host, port=port, path=PATH)
