"""Model provider abstraction.

This module uses public SDK contracts only: Anthropic Messages API and
OpenAI-compatible Chat Completions.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any, cast

import httpx
from anthropic import Anthropic
from openai import OpenAI

from .config import RuntimeConfig
from .types import Message, ModelResponse, ToolCall, ToolSpec


class ModelProvider(ABC):
    @abstractmethod
    def complete(self, messages: list[Message], tools: list[ToolSpec]) -> ModelResponse:
        raise NotImplementedError


def build_provider(config: RuntimeConfig) -> ModelProvider:
    config.validate_for_model_call()
    if config.provider.name == "anthropic":
        return AnthropicProvider(config)
    if config.provider.name == "openai-compatible":
        return OpenAICompatibleProvider(config)
    raise ValueError(f"Unsupported provider: {config.provider.name}")


class AnthropicProvider(ModelProvider):
    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config
        kwargs: dict[str, Any] = {
            "api_key": config.api_key,
            "timeout": config.ai_request_timeout_seconds,
        }
        http_client = _http_client_for_network_mode(config)
        if http_client is not None:
            kwargs["http_client"] = http_client
        self.client = Anthropic(**kwargs)

    def complete(self, messages: list[Message], tools: list[ToolSpec]) -> ModelResponse:
        system = "\n\n".join(m.content for m in messages if m.role == "system")
        convo = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in {"user", "assistant"}
        ]
        kwargs: dict[str, Any] = {
            "model": self.config.provider.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": convo,
            "tools": [
                {"name": t.name, "description": t.description, "input_schema": t.input_schema}
                for t in tools
            ],
        }
        if system:
            kwargs["system"] = system
        response = self.client.messages.create(**kwargs)
        text_parts: list[str] = []
        calls: list[ToolCall] = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                calls.append(ToolCall(id=block.id, name=block.name, arguments=dict(block.input)))
        return ModelResponse(text="\n".join(text_parts).strip(), tool_calls=calls)


class OpenAICompatibleProvider(ModelProvider):
    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config
        kwargs: dict[str, Any] = {
            "api_key": config.api_key,
            "timeout": config.ai_request_timeout_seconds,
        }
        if config.provider.base_url:
            kwargs["base_url"] = config.provider.base_url
        http_client = _http_client_for_network_mode(config)
        if http_client is not None:
            kwargs["http_client"] = http_client
        self.client = OpenAI(**kwargs)

    def complete(self, messages: list[Message], tools: list[ToolSpec]) -> ModelResponse:
        response = self.client.chat.completions.create(
            model=self.config.provider.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            messages=cast(Any, [_openai_message(m) for m in messages]),
            tools=cast(Any, [_openai_tool(t) for t in tools]),
        )
        msg = response.choices[0].message
        calls: list[ToolCall] = []
        for call in msg.tool_calls or []:
            function = getattr(call, "function", None)
            if function is None:
                continue
            args = json.loads(function.arguments or "{}")
            calls.append(ToolCall(id=call.id, name=function.name, arguments=args))
        return ModelResponse(text=msg.content or "", tool_calls=calls)


def _openai_message(message: Message) -> dict[str, Any]:
    data: dict[str, Any] = {"role": message.role, "content": message.content}
    if message.name:
        data["name"] = message.name
    if message.tool_call_id:
        data["tool_call_id"] = message.tool_call_id
    return data


def _openai_tool(tool: ToolSpec) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_schema,
        },
    }


def _http_client_for_network_mode(config: RuntimeConfig) -> httpx.Client | None:
    timeout = httpx.Timeout(config.ai_request_timeout_seconds)
    if config.desktop_network_mode == "direct":
        return httpx.Client(timeout=timeout, trust_env=False)
    if config.desktop_network_mode == "manual" and config.desktop_manual_proxy:
        return httpx.Client(timeout=timeout, proxy=config.desktop_manual_proxy, trust_env=False)
    return None


class FakeProvider(ModelProvider):
    """Deterministic provider for tests and dry runs."""

    def __init__(self, responses: Iterable[ModelResponse]) -> None:
        self.responses = list(responses)
        self.calls = 0

    def complete(self, messages: list[Message], tools: list[ToolSpec]) -> ModelResponse:
        del messages, tools
        result = self.responses[self.calls]
        self.calls += 1
        return result
