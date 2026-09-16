# agents/qa.py - Defines the QA agent for the AG2 system.
from ag2 import Agent
from ag2.config import OpenAIConfig
from .prompts import QA_ENGINEER


def build(model: str) -> Agent:
    return Agent(
        name="qa",
        prompt=QA_ENGINEER,
        config=OpenAIConfig(model=model),
        tools=["artifact_store.write_adr",
               "artifact_store.publish_contract",
               "artifact_store.read_srs"],
        # TODO: Add any additional configuration or initialization for the QA agent here.
    )
