"""Compatibility helpers for constructing role agents across AG2 variants."""

from __future__ import annotations

from typing import Any

try:
    from ag2 import Agent as _AG2Agent  # type: ignore
    from ag2.config import OpenAIConfig as _OpenAIConfig  # type: ignore

    def build_agent(name: str, prompt: str, model: str, tools: list[str]) -> Any:
        return _AG2Agent(
            name=name,
            prompt=prompt,
            config=_OpenAIConfig(model=model),
            tools=tools,
        )

except ImportError:
    from autogen import AssistantAgent

    def build_agent(name: str, prompt: str, model: str, tools: list[str]) -> Any:
        # Legacy autogen agents do not accept the AG2 `tools` list directly.
        # We keep the role prompt and model configuration to preserve behavior.
        _ = tools
        return AssistantAgent(
            name=name,
            system_message=prompt,
            llm_config={"config_list": [{"model": model}]},
        )