# agents/architect.py
from ._compat import build_agent
from .prompts import ARCHITECT


def build(model: str):
    return build_agent(
        name="architect",
        prompt=ARCHITECT,
        tools=["artifact_store.write_adr",
               "artifact_store.publish_contract",
               "artifact_store.read_srs"],
        model=model,
    )
