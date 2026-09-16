# agents/security.py - Defines the security agent for the AG2 system.
from ._compat import build_agent
from .prompts import SECURITY_REVIEWER


def build(model: str):
    return build_agent(
        name="security",
        prompt=SECURITY_REVIEWER,
        tools=["artifact_store.write_adr",
               "artifact_store.publish_contract",
               "artifact_store.read_srs"],
        model=model,
        # TODO: Add any additional configuration or initialization for the security agent here.
    )
