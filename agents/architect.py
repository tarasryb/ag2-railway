# agents/architect.py
from ag2 import Agent
from ag2.config import OpenAIConfig
from .prompts import ARCHITECT


def build(model: str) -> Agent:
    return Agent(
        name="architect",
        prompt=ARCHITECT,
        config=OpenAIConfig(model=model),
        tools=["artifact_store.write_adr",
               "artifact_store.publish_contract",
               "artifact_store.read_srs"],
    )
