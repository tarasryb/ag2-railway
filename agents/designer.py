# agents/designer.py - Defines the designer agent for the AG2 system.
from ._compat import build_agent
from .prompts import DESIGNER


def build(model: str):
    return build_agent(
        name="designer",
        prompt=DESIGNER,
        tools=["artifact_store.write_adr",
               "artifact_store.publish_contract",
               "artifact_store.read_srs"],
        model=model,
        # TODO: Add any additional configuration or initialization for the designer agent here.
    )
