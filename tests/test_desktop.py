import re
import socket
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

from x_agentic_workflow.config import RuntimeConfig
from x_agentic_workflow.desktop import (
    DesktopApp,
    _create_server,
    _project_sessions_dir,
    _validate_project,
    render_desktop_html,
)
from x_agentic_workflow.types import Message, ModelResponse, ToolSpec


def test_desktop_html_contains_clean_room_app_shell() -> None:
    html = render_desktop_html()

    assert "x-agentic-workflow" in html
    assert "新对话" in html
    assert "354685856-sn/x-agentic-workflow" in html
    assert "当前" in html
    assert "我的仓库位置" not in html
    assert "Claude-cc-haha" not in html
    assert "最近项目" in html
    assert "inspector-card" in html
    assert "inspectorToggle" in html
    assert "inspector-collapsed" in html
    assert "title=\"列表\"" in html
    assert "输出" in html
    assert "任务" in html
    assert "Describe a task or ask a question" in html
    assert "What’s up next, sn?" in html
    assert "Overview" in html
    assert "/api/ask" in html
    assert "验证项目" in html
    assert "验证中..." in html
    assert "切换项目" in html
    assert "切换中..." in html
    assert "/api/project/switch" in html
    assert "projectPathInput" in html
    assert "recentProjects" in html
    assert "button.disabled = true" in html
    assert "button.disabled = false" in html
    assert "/api/project/validate" in html
    assert "项目验证" in html
    assert "服务商" in html
    assert "DeepSeek" in html
    assert "MCP" in html
    assert "Token 用量" in html


def test_desktop_composer_actions_are_outside_prompt_box() -> None:
    html = render_desktop_html()

    composer_match = re.search(
        r'<div class="composer">(?P<body>.*?)</div>\s*<div class="composer-actions">',
        html,
        re.DOTALL,
    )

    assert composer_match is not None
    assert "composer-actions" not in composer_match.group("body")
    assert "right-tools" not in composer_match.group("body")


def test_desktop_composer_dock_is_bottom_aligned() -> None:
    html = render_desktop_html()

    assert "html, body { height: 100%; }" in html
    assert ".app { height: 100vh; overflow: hidden;" in html
    assert (
        "main { position: relative; display: flex; flex-direction: column; "
        "min-width: 0; min-height: 0; height: 100vh;"
    ) in html
    assert ".stage { flex: 1; min-height: 0; display: flex; align-items: stretch;" in html
    assert "padding: 0 40px 8px" in html
    assert ".hero { width: min(980px, 100%); height: 100%; min-height: 0;" in html
    assert ".composer-dock { width: min(1064px, 100%); margin: auto auto 0;" in html


def test_desktop_provider_settings_save_without_secret_value(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    state = app.save_provider_settings(
        {
            "provider": "openai-compatible",
            "model": "deepseek-chat",
            "baseUrl": "https://api.deepseek.com/v1",
            "apiKeyEnv": "DEEPSEEK_API_KEY",
        }
    )

    saved = (tmp_path / "config.json").read_text(encoding="utf-8")
    assert state["providerSave"]["ok"] is True
    assert '"api_key_env": "DEEPSEEK_API_KEY"' in saved
    assert "deepseek-chat" in saved
    assert "sk-" not in saved


def test_desktop_provider_connection_error_redacts_secret(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-testsecret123456789")

    class LeakyProvider:
        def complete(self, messages: list[Message], tools: list[ToolSpec]) -> ModelResponse:
            del messages, tools
            raise RuntimeError(
                "failed with sk-testsecret123456789 and api_key=sk-testsecret123456789"
            )

    def fake_build_provider(config: RuntimeConfig) -> LeakyProvider:
        del config
        return LeakyProvider()

    monkeypatch.setattr("x_agentic_workflow.providers.build_provider", fake_build_provider)
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    state = app.test_provider_settings(
        {
            "provider": "openai-compatible",
            "model": "deepseek-chat",
            "baseUrl": "https://api.deepseek.com/v1",
            "apiKeyEnv": "DEEPSEEK_API_KEY",
        }
    )

    message = state["providerTest"]["message"]
    assert state["providerTest"]["ok"] is False
    assert "sk-testsecret123456789" not in message
    assert "[REDACTED]" in message


def test_desktop_provider_connection_validates_payload(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    unsupported = app.test_provider_settings({"provider": "custom", "model": "m"})
    missing_model = app.test_provider_settings({"provider": "anthropic", "model": ""})
    missing_env = app.test_provider_settings(
        {"provider": "anthropic", "model": "claude-3-5-sonnet-latest", "apiKeyEnv": ""}
    )

    assert unsupported["providerTest"]["ok"] is False
    assert "Unsupported provider" in unsupported["providerTest"]["message"]
    assert missing_model["providerTest"]["message"] == "Model is required."
    assert missing_env["providerTest"]["message"] == "API key environment variable is required."


def test_desktop_project_validation_reports_key_files_and_commands(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")

    result = _validate_project(tmp_path)

    assert result["ok"] is True
    assert result["path"] == str(tmp_path)
    assert "AGENTS.md" in result["files"]
    assert "README.md" in result["files"]
    assert "pyproject.toml" in result["files"]
    assert any("pytest" in command for command in result["recommendations"])
    assert any(check["name"] == "Git" for check in result["checks"])


def test_desktop_validate_project_api_updates_state(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    state = app.validate_project()

    assert state["projectValidation"] is not None
    assert state["projectValidation"]["path"] == str(tmp_path)
    assert "README.md" in state["projectValidation"]["files"]


def test_desktop_switch_project_updates_workdir_and_recent_projects(tmp_path: Path) -> None:
    start = tmp_path / "start"
    target = tmp_path / "target"
    start.mkdir()
    target.mkdir()
    (target / "README.md").write_text("# Target\n", encoding="utf-8")
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=start,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    state = app.switch_project({"path": str(target)})

    assert state["projectSwitch"]["ok"] is True
    assert state["workdir"] == str(target)
    assert state["projectValidation"]["path"] == str(target)
    assert state["recentProjects"][0]["path"] == str(target)
    assert state["recentProjects"][0]["active"] is True
    saved = (tmp_path / "config.json").read_text(encoding="utf-8")
    assert str(target) in saved


def test_desktop_switch_project_rejects_invalid_path(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    state = app.switch_project({"path": str(tmp_path / "missing")})

    assert state["projectSwitch"]["ok"] is False
    assert state["workdir"] == str(tmp_path)
    assert not (tmp_path / "config.json").exists()


def test_desktop_sessions_are_scoped_to_active_project(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=first,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)
    app.sessions.save("first-session", [Message(role="user", content="first")])

    first_state = app.state()
    second_state = app.switch_project({"path": str(second)})
    app.sessions.save("second-session", [Message(role="user", content="second")])
    returned_state = app.switch_project({"path": str(first)})

    assert "first-session" in first_state["sessions"]
    assert "first-session" not in second_state["sessions"]
    assert "second-session" not in returned_state["sessions"]
    assert "first-session" in returned_state["sessions"]
    assert "/projects/" in returned_state["sessionsDir"]


def test_project_sessions_dir_is_stable_and_path_specific(tmp_path: Path) -> None:
    base = tmp_path / "sessions"
    first = tmp_path / "a" / "demo"
    second = tmp_path / "b" / "demo"
    first.mkdir(parents=True)
    second.mkdir(parents=True)

    assert _project_sessions_dir(base, first) == _project_sessions_dir(base, first)
    assert _project_sessions_dir(base, first) != _project_sessions_dir(base, second)
    assert _project_sessions_dir(base, first).parent == base / "projects"


def test_desktop_server_falls_back_when_preferred_port_is_busy() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self.send_response(200)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen()
        busy_port = sock.getsockname()[1]

        server = _create_server("127.0.0.1", busy_port, Handler)

    try:
        assert server.server_port != busy_port
        assert server.server_port > 0
    finally:
        server.server_close()
