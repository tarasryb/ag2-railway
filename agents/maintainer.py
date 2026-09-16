# agents/maintainer.py - Defines the maintainer agent for the AG2 system.
from ._compat import build_agent
from .prompts import MAINTAINER


def build(model: str):
    return build_agent(
        name="maintainer",
        prompt=MAINTAINER,
        tools=["artifact_store.write_adr",
               "artifact_store.publish_contract",
               "artifact_store.read_srs"],
        model=model,
        # TODO: Add any additional configuration or initialization for the maintainer agent here.
    )