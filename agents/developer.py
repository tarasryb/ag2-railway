# agents/developer.py
from ag2 import Agent
from ag2.config import OpenAIConfig
from .prompts import DEVELOPER


def build(model: str) -> Agent:
    return Agent(
        name="developer",
        prompt=DEVELOPER,
        config=OpenAIConfig(model=model),
        tools=["artifact_store.read_sdd",
               "artifact_store.write_code",
               "artifact_store.write_unit_tests"],
    )
