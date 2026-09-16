# agents/designer.py - Defines the designer agent for the AG2 system.
from ag2 import Agent
from ag2.config import OpenAIConfig
from .prompts import DESIGNER


def build(model: str) -> Agent:
    return Agent(
        name="designer",
        prompt=DESIGNER,
        config=OpenAIConfig(model=model),
        tools=["artifact_store.write_adr",
               "artifact_store.publish_contract",
               "artifact_store.read_srs"],
        # TODO: Add any additional configuration or initialization for the designer agent here.
    )
