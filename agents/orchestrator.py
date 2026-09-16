# agents/orchestrator.py - Defines the orchestrator agent for the AG2 system.
from ag2 import Agent
from ag2.config import OpenAIConfig
from .prompts import ORCHESTRATOR


def build(model: str) -> Agent:
    return Agent(
        name="orchestrator",
        prompt=ORCHESTRATOR,
        config=OpenAIConfig(model=model),
        tools=["artifact_store.write_adr",
               "artifact_store.publish_contract",
               "artifact_store.read_srs"],
        # TODO: Add any additional configuration or initialization for the orchestrator agent here.
    )
