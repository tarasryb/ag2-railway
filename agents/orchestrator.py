# agents/orchestrator.py - Defines the orchestrator agent for the AG2 system.
from ._compat import build_agent
from .prompts import ORCHESTRATOR


def build(model: str):
    return build_agent(
        name="orchestrator",
        prompt=ORCHESTRATOR,
        tools=["artifact_store.write_adr",
               "artifact_store.publish_contract",
               "artifact_store.read_srs"],
        model=model,
        # TODO: Add any additional configuration or initialization for the orchestrator agent here.
    )
