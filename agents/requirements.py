# agents/requirements.py
from ag2 import Agent
from ag2.config import OpenAIConfig
from .prompts import REQUIREMENTS_ANALYST


def build(model: str) -> Agent:
    return Agent(
        name="requirements_analyst",
        prompt=REQUIREMENTS_ANALYST,
        config=OpenAIConfig(model=model),
        tools=["artifact_store.write_srs",
               "artifact_store.trace_link"],
    )
