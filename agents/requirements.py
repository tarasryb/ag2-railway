# agents/requirements.py
from ._compat import build_agent
from .prompts import REQUIREMENTS_ANALYST


def build(model: str):
    return build_agent(
        name="requirements_analyst",
        prompt=REQUIREMENTS_ANALYST,
        tools=["artifact_store.write_srs",
               "artifact_store.trace_link"],
        model=model,
    )
