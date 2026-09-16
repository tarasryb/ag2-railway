# agents/qa.py - Defines the QA agent for the AG2 system.
from ._compat import build_agent
from .prompts import QA_ENGINEER


def build(model: str):
    return build_agent(
        name="qa",
        prompt=QA_ENGINEER,
        tools=["artifact_store.write_adr",
               "artifact_store.publish_contract",
               "artifact_store.read_srs"],
        model=model,
        # TODO: Add any additional configuration or initialization for the QA agent here.
    )
