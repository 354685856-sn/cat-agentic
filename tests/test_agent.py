import json
from pathlib import Path

from x_agentic_workflow.agent import Agent
from x_agentic_workflow.config import RuntimeConfig
from x_agentic_workflow.mcp import project_private_mcp_file, project_shared_mcp_file
from x_agentic_workflow.providers import FakeProvider
from x_agentic_workflow.types import AgentEvent, ModelResponse, ToolCall


def test_agent_resolves_tool_call_and_returns_final_text(tmp_path: Path) -> None:
    provider = FakeProvider(
        [
            ModelResponse(
                text="",
                tool_calls=[
                    ToolCall(
                        id="1",
                        name="write_file",
                        arguments={"path": "x.txt", "content": "ok"},
                    )
                ],
            ),
            ModelResponse(text="done"),
        ]
    )
    config = RuntimeConfig(
        workdir=tmp_path,
        sessions_dir=tmp_path / ".sessions",
        skills_dir=tmp_path / ".skills",
        hooks_dir=tmp_path / ".hooks",
        mcp_config_file=tmp_path / ".mcp.json",
    )
    agent = Agent(config, provider=provider, session_id="test")

    result = agent.run_once("write a file")

    assert result == "done"
    assert (tmp_path / "x.txt").read_text(encoding="utf-8") == "ok"


def test_agent_can_initialize_without_api_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    config = RuntimeConfig(
        workdir=tmp_path,
        sessions_dir=tmp_path / ".sessions",
        skills_dir=tmp_path / ".skills",
        hooks_dir=tmp_path / ".hooks",
        mcp_config_file=tmp_path / ".mcp.json",
    )

    agent = Agent(config, session_id="no-key")

    assert agent.session_id == "no-key"


def test_agent_mcp_context_summary_omits_disabled_servers(tmp_path: Path) -> None:
    mcp_config_file = tmp_path / ".mcp.json"
    mcp_config_file.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "enabled-server": {"command": "npx", "args": ["enabled-mcp"]},
                    "disabled-server": {
                        "command": "npx",
                        "args": ["disabled-mcp"],
                        "enabled": False,
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    config = RuntimeConfig(
        workdir=tmp_path,
        sessions_dir=tmp_path / ".sessions",
        skills_dir=tmp_path / ".skills",
        hooks_dir=tmp_path / ".hooks",
        mcp_config_file=mcp_config_file,
    )
    agent = Agent(config, session_id="mcp-disabled")

    summary = agent.mcp.context_summary()

    assert "enabled-server" in summary
    assert "disabled-server" not in summary


def test_agent_mcp_context_summary_reads_scoped_configs(tmp_path: Path) -> None:
    private_file = project_private_mcp_file(tmp_path, tmp_path)
    shared_file = project_shared_mcp_file(tmp_path)
    user_file = tmp_path / "user-mcp.json"
    private_file.parent.mkdir(parents=True)
    private_file.write_text(
        json.dumps({"mcpServers": {"private-server": {"command": "npx"}}}),
        encoding="utf-8",
    )
    shared_file.write_text(
        json.dumps({"mcpServers": {"shared-server": {"url": "https://example.com/mcp"}}}),
        encoding="utf-8",
    )
    user_file.write_text(
        json.dumps({"mcpServers": {"user-server": {"command": "uvx", "args": ["tool"]}}}),
        encoding="utf-8",
    )
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / ".sessions",
        skills_dir=tmp_path / ".skills",
        hooks_dir=tmp_path / ".hooks",
        mcp_config_file=user_file,
    )
    agent = Agent(config, session_id="mcp-scoped")

    summary = agent.mcp.context_summary()

    assert "private-server" in summary
    assert "shared-server" in summary
    assert "user-server" in summary


def test_agent_system_prompt_includes_desktop_preferences(tmp_path: Path) -> None:
    config = RuntimeConfig(
        workdir=tmp_path,
        sessions_dir=tmp_path / ".sessions",
        skills_dir=tmp_path / ".skills",
        hooks_dir=tmp_path / ".hooks",
        mcp_config_file=tmp_path / ".mcp.json",
        desktop_reply_language="zh-CN",
        desktop_output_style="review",
        desktop_thinking_enabled=False,
        desktop_web_search_provider="brave",
    )
    agent = Agent(config, session_id="preferences")

    prompt = agent._system_prompt("review this")  # noqa: SLF001 - verifies prompt assembly.

    assert "Reply language preference: Simplified Chinese." in prompt
    assert "review-oriented style" in prompt
    assert "Do not request or rely on extended thinking modes" in prompt
    assert "Preferred web search provider: brave." in prompt


def test_agent_emits_tool_timeline_events(tmp_path: Path) -> None:
    provider = FakeProvider(
        [
            ModelResponse(
                text="",
                tool_calls=[
                    ToolCall(
                        id="1",
                        name="write_file",
                        arguments={"path": "x.txt", "content": "ok"},
                    )
                ],
            ),
            ModelResponse(text="done"),
        ]
    )
    config = RuntimeConfig(
        workdir=tmp_path,
        sessions_dir=tmp_path / ".sessions",
        skills_dir=tmp_path / ".skills",
        hooks_dir=tmp_path / ".hooks",
        mcp_config_file=tmp_path / ".mcp.json",
    )
    events: list[AgentEvent] = []
    agent = Agent(config, provider=provider, session_id="events", event_sink=events.append)

    assert agent.run_once("write a file") == "done"

    assert [event.kind for event in events] == ["tool_call", "tool_result", "assistant"]
    assert events[0].name == "write_file"
    assert events[1].ok is True
    assert events[1].metadata["operation"] == "write_file"
    assert "b/x.txt" in str(events[1].metadata["diff"])
