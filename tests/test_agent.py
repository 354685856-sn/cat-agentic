from pathlib import Path

from x_agentic_workflow.agent import Agent
from x_agentic_workflow.config import RuntimeConfig
from x_agentic_workflow.providers import FakeProvider
from x_agentic_workflow.types import ModelResponse, ToolCall


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
