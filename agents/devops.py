# agents/devops.py - Defines the devops agent for the AG2 system.
from ag2 import Agent
from ag2.config import OpenAIConfig
from .prompts import DEVOPS


def build(model: str) -> Agent:
    return Agent(
        name="devops",
        prompt=DEVOPS,
        config=OpenAIConfig(model=model),
        tools=["artifact_store.write_adr",
               "artifact_store.publish_contract",
               "artifact_store.read_srs"],
        # TODO: Add any additional configuration or initialization for the devops agent here.
    )