# agents/maintainer.py - Defines the maintainer agent for the AG2 system.
from ag2 import Agent
from ag2.config import OpenAIConfig
from .prompts import MAINTAINER


def build(model: str) -> Agent:
    return Agent(
        name="maintainer",
        prompt=MAINTAINER,
        config=OpenAIConfig(model=model),
        tools=["artifact_store.write_adr",
               "artifact_store.publish_contract",
               "artifact_store.read_srs"],
        # TODO: Add any additional configuration or initialization for the maintainer agent here.
    )