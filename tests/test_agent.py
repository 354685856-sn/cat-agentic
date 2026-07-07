import json
from pathlib import Path

from x_agentic_workflow.agent import Agent
from x_agentic_workflow.config import RuntimeConfig
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
