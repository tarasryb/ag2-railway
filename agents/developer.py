# agents/developer.py
from ._compat import build_agent
from .prompts import DEVELOPER


def build(model: str):
    return build_agent(
        name="developer",
        prompt=DEVELOPER,
        tools=["artifact_store.read_sdd",
               "artifact_store.write_code",
               "artifact_store.write_unit_tests"],
        model=model,
    )
