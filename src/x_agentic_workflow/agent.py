"""Core agent loop."""

from __future__ import annotations

from collections.abc import Callable

from .config import RuntimeConfig
from .hooks import HookRunner
from .mcp import McpRegistry, scoped_mcp_config_files
from .multi_agent import role_prompt
from .providers import ModelProvider, build_provider
from .sessions import SessionStore
from .skills import SkillRegistry
from .tools import ToolRegistry, tool_specs
from .types import AgentEvent, Message
from .ui import assistant, error, tool_call, tool_result, user_prompt

BASE_SYSTEM_PROMPT = """You are cat-agentic, a direct terminal coding assistant.
Work in small, verifiable steps. Use tools for file and command work. Respect the
project sandbox. Ask before risky external side effects. Keep responses concise."""


class Agent:
    def __init__(
        self,
        config: RuntimeConfig,
        provider: ModelProvider | None = None,
        session_id: str | None = None,
        event_sink: Callable[[AgentEvent], None] | None = None,
    ) -> None:
        self.config = config
        self.provider = provider
        self.event_sink = event_sink
        self.tools = ToolRegistry(config)
        self.sessions = SessionStore(config.sessions_dir)
        self.session_id = session_id or self.sessions.new_id()
        self.messages = self.sessions.load(self.session_id)
        self.skills = SkillRegistry(config.skills_dir)
        self.hooks = HookRunner(config.hooks_dir)
        self.mcp = McpRegistry(
            scoped_mcp_config_files(
                config.config_file.parent,
                config.workdir,
                config.mcp_config_file,
            )
        )
        if not self.messages:
            self.messages.append(Message(role="system", content=self._system_prompt("")))

    def run_interactive(self) -> int:
        assistant(f"cat-agentic ready. session={self.session_id}. Type /exit to quit.")
        for hook_output in self.hooks.run("session_start", self.config.workdir):
            tool_result(hook_output)
        while True:
            try:
                text = user_prompt()
            except (EOFError, KeyboardInterrupt):
                break
            if text.strip() in {"/exit", "exit", "quit", ":q"}:
                break
            if text.strip() == "/reset":
                self.messages = [Message(role="system", content=self._system_prompt(""))]
                self.sessions.save(self.session_id, self.messages)
                assistant("Session reset.")
                continue
            if not text.strip():
                continue
            self.handle_user_text(text)
        self.sessions.save(self.session_id, self.messages)
        return 0

    def run_once(self, prompt: str) -> str:
        return self.handle_user_text(prompt, print_output=False)

    def handle_user_text(self, text: str, print_output: bool = True) -> str:
        self.messages[0] = Message(role="system", content=self._system_prompt(text))
        self.messages.append(Message(role="user", content=text))
        final_text = ""
        for _ in range(12):
            response = self._provider().complete(self.messages, tool_specs())
            if response.text:
                final_text = response.text
                self._emit(AgentEvent(kind="assistant", content=response.text))
                if print_output:
                    assistant(response.text)
                self.messages.append(Message(role="assistant", content=response.text))
            if not response.tool_calls:
                self.sessions.save(self.session_id, self.messages)
                return final_text
            for call in response.tool_calls:
                self._emit(
                    AgentEvent(
                        kind="tool_call",
                        name=call.name,
                        arguments=call.arguments,
                        content=f"{call.name}({call.arguments})",
                    )
                )
                if print_output:
                    tool_call(call.name, call.arguments)
                result = self.tools.dispatch(call.name, call.arguments)
                self._emit(
                    AgentEvent(
                        kind="tool_result",
                        name=call.name,
                        content=result.content,
                        ok=result.ok,
                        metadata=result.metadata,
                    )
                )
                if print_output:
                    tool_result(result.content)
                self.messages.append(
                    Message(
                        role="tool",
                        name=call.name,
                        tool_call_id=call.id,
                        content=result.content,
                    )
                )
        message = "Tool loop limit reached."
        self._emit(AgentEvent(kind="error", content=message))
        error(message)
        self.sessions.save(self.session_id, self.messages)
        return final_text

    def _emit(self, event: AgentEvent) -> None:
        if self.event_sink is not None:
            self.event_sink(event)

    def _provider(self) -> ModelProvider:
        if self.provider is None:
            self.provider = build_provider(self.config)
        return self.provider

    def _system_prompt(self, user_text: str) -> str:
        parts = [BASE_SYSTEM_PROMPT, role_prompt(), self._desktop_preferences_prompt()]
        mcp_summary = self.mcp.context_summary()
        skill_prompt = self.skills.matching_prompt(user_text)
        if mcp_summary:
            parts.append(mcp_summary)
        if skill_prompt:
            parts.append(skill_prompt)
        return "\n\n".join(parts)

    def _desktop_preferences_prompt(self) -> str:
        lines: list[str] = []
        reply_language = self.config.desktop_reply_language
        if reply_language != "default":
            language_labels = {
                "en": "English",
                "zh-CN": "Simplified Chinese",
                "zh-TW": "Traditional Chinese",
                "ja": "Japanese",
                "ko": "Korean",
            }
            lines.append(f"Reply language preference: {language_labels[reply_language]}.")
        style_prompts = {
            "concise": "Use concise answers and keep progress reports brief.",
            "explanatory": "Include more context and explain the reasoning behind changes.",
            "review": (
                "Use a review-oriented style: call out risks, regressions, "
                "and verification gaps."
            ),
        }
        if self.config.desktop_output_style in style_prompts:
            lines.append(style_prompts[self.config.desktop_output_style])
        if not self.config.desktop_thinking_enabled:
            lines.append("Do not request or rely on extended thinking modes for this session.")
        if self.config.desktop_web_search_provider == "off":
            lines.append(
                "Web search is disabled by desktop settings unless the user explicitly asks."
            )
        elif self.config.desktop_web_search_provider != "auto":
            lines.append(
                f"Preferred web search provider: {self.config.desktop_web_search_provider}."
            )
        if not lines:
            return ""
        return "Desktop preferences:\n" + "\n".join(f"- {line}" for line in lines)
