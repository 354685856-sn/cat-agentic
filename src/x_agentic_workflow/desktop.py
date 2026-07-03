"""Clean-room local browser UI for x-agentic-workflow."""
# ruff: noqa: E501

import errno
import hashlib
import json
import os
import re
import socket
import subprocess
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

from .agent import Agent
from .config import ProviderConfig, RuntimeConfig
from .sessions import SessionStore
from .types import AgentEvent, Message

SECRET_PATTERN = re.compile(
    r"(?i)(sk-[a-z0-9][a-z0-9_\-]{8,}|"
    r"sk-ant-[a-z0-9_\-]{8,}|"
    r"(api[_-]?key|token|authorization)=([^&\s]+))"
)


def run_desktop(
    config: RuntimeConfig | None = None,
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = True,
) -> None:
    """Start the clean-room browser UI server."""

    runtime_config = config or RuntimeConfig.load(workdir=Path.cwd())
    app = DesktopApp(runtime_config)
    server = _create_server(host, port, _handler_for(app))
    url = f"http://{host}:{server.server_port}"
    if open_browser:
        threading.Timer(0.2, lambda: webbrowser.open(url)).start()
    print(f"x-agentic-workflow desktop UI running at {url}", flush=True)  # noqa: T201
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _create_server(
    host: str,
    port: int,
    handler: type[BaseHTTPRequestHandler],
) -> ThreadingHTTPServer:
    if port != 0 and _port_has_listener(host, port):
        return ThreadingHTTPServer((host, 0), handler)
    try:
        return ThreadingHTTPServer((host, port), handler)
    except OSError as exc:
        if exc.errno != errno.EADDRINUSE or port == 0:
            raise
        return ThreadingHTTPServer((host, 0), handler)


def _port_has_listener(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


class DesktopApp:
    """Small HTTP facade over the existing CLI agent runtime."""

    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config
        self.base_sessions_dir = config.sessions_dir
        self._scope_sessions_to_project(config.workdir)
        self.sessions = SessionStore(self.config.sessions_dir)
        self.agent = self._new_agent()
        self.messages: list[dict[str, str]] = []
        self.project_validation: dict[str, Any] | None = None
        self.file_changes: list[dict[str, Any]] = []

    def state(self) -> dict[str, Any]:
        return {
            "provider": self.config.provider.name,
            "model": self.config.provider.model,
            "baseUrl": self.config.provider.base_url,
            "apiKeyEnv": self.config.provider.api_key_env,
            "apiKeyPresent": bool(self.config.api_key),
            "workdir": str(self.config.workdir),
            "sessionId": self.agent.session_id,
            "sessions": list(reversed(self.sessions.list_sessions()[-8:])),
            "sessionsDir": str(self.config.sessions_dir),
            "messages": self.messages[-30:],
            "projectValidation": self.project_validation,
            "recentProjects": self._recent_project_entries(),
            "fileChanges": self.file_changes[-12:],
            "latestDiff": self.file_changes[-1] if self.file_changes else None,
        }

    def new_chat(self) -> dict[str, Any]:
        self.agent = self._new_agent()
        self.messages = []
        self.file_changes = []
        return self.state()

    def open_session(self, session_id: str) -> dict[str, Any]:
        self.agent = self._new_agent(session_id=session_id)
        self.messages = [
            {"role": message.role, "content": message.content}
            for message in self.agent.messages
            if message.role in {"user", "assistant"}
        ]
        return self.state()

    def ask(self, prompt: str) -> dict[str, Any]:
        text = prompt.strip()
        if not text:
            return self.state()
        self.messages.append({"role": "user", "content": text})
        try:
            answer = self.agent.run_once(text)
        except Exception as exc:  # noqa: BLE001 - API errors are rendered in the UI
            answer = f"{type(exc).__name__}: {exc}"
            self.messages.append({"role": "error", "content": answer})
            return self.state()
        if answer:
            self.messages.append({"role": "assistant", "content": answer})
        return self.state()

    def save_provider_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        provider_name = str(payload.get("provider", self.config.provider.name))
        if provider_name not in {"anthropic", "openai-compatible"}:
            return {
                **self.state(),
                "providerSave": {"ok": False, "message": f"Unsupported provider: {provider_name}"},
            }
        model = str(payload.get("model", self.config.provider.model)).strip()
        api_key_env = str(payload.get("apiKeyEnv", self.config.provider.api_key_env)).strip()
        base_url = str(payload.get("baseUrl", "")).strip() or None
        if not model:
            return {**self.state(), "providerSave": {"ok": False, "message": "Model is required."}}
        if not api_key_env:
            return {
                **self.state(),
                "providerSave": {"ok": False, "message": "API key environment variable is required."},
            }

        self.config.provider.name = cast(Any, provider_name)
        self.config.provider.model = model
        self.config.provider.base_url = base_url
        self.config.provider.api_key_env = api_key_env
        self.config.save()
        self.agent = self._new_agent(session_id=self.agent.session_id)
        return {
            **self.state(),
            "providerSave": {
                "ok": True,
                "message": f"Saved provider settings to {self.config.config_file}. Secret value was not stored.",
            },
        }

    def test_provider_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        provider_name = str(payload.get("provider", self.config.provider.name))
        if provider_name not in {"anthropic", "openai-compatible"}:
            return {
                **self.state(),
                "providerTest": {"ok": False, "message": f"Unsupported provider: {provider_name}"},
            }
        model = str(payload.get("model", self.config.provider.model)).strip()
        api_key_env = str(payload.get("apiKeyEnv", self.config.provider.api_key_env)).strip()
        base_url = str(payload.get("baseUrl", "")).strip() or None
        if not model:
            return {**self.state(), "providerTest": {"ok": False, "message": "Model is required."}}
        if not api_key_env:
            return {
                **self.state(),
                "providerTest": {
                    "ok": False,
                    "message": "API key environment variable is required.",
                },
            }

        probe = RuntimeConfig(
            provider=ProviderConfig(
                name=cast(Any, provider_name),
                model=model,
                base_url=base_url,
                api_key_env=api_key_env,
            ),
            max_tokens=32,
            temperature=0,
            workdir=self.config.workdir,
            config_file=self.config.config_file,
            sessions_dir=self.config.sessions_dir,
            skills_dir=self.config.skills_dir,
            hooks_dir=self.config.hooks_dir,
            mcp_config_file=self.config.mcp_config_file,
        )
        try:
            if not probe.api_key:
                raise ValueError(
                    f"{api_key_env} is not set. Export it in your shell or launch environment."
                )
            from .providers import build_provider

            response = build_provider(probe).complete(
                [
                    Message(role="system", content="Reply with exactly: ok"),
                    Message(role="user", content="connection test"),
                ],
                [],
            )
            del response
        except Exception as exc:  # noqa: BLE001 - surfaced as UI test result
            return {
                **self.state(),
                "providerTest": {"ok": False, "message": _redact_provider_error(str(exc), api_key_env)},
            }
        return {**self.state(), "providerTest": {"ok": True, "message": "Connection test passed."}}

    def validate_project(self) -> dict[str, Any]:
        self.project_validation = _validate_project(self.config.workdir)
        return self.state()

    def switch_project(self, payload: dict[str, Any]) -> dict[str, Any]:
        raw_path = str(payload.get("path", "")).strip()
        if not raw_path:
            return {
                **self.state(),
                "projectSwitch": {"ok": False, "message": "Project path is required."},
            }
        target = Path(raw_path).expanduser().resolve()
        if not target.exists():
            return {
                **self.state(),
                "projectSwitch": {"ok": False, "message": f"Project path does not exist: {target}"},
            }
        if not target.is_dir():
            return {
                **self.state(),
                "projectSwitch": {"ok": False, "message": f"Project path is not a directory: {target}"},
            }

        self.config.workdir = target
        self._scope_sessions_to_project(target)
        self.sessions = SessionStore(self.config.sessions_dir)
        self._remember_project(target)
        self.config.save()
        self.agent = self._new_agent()
        self.messages = []
        self.file_changes = []
        self.project_validation = _validate_project(target)
        return {
            **self.state(),
            "projectSwitch": {"ok": True, "message": f"Switched to {target}."},
        }

    def _remember_project(self, path: Path) -> None:
        target = str(path.resolve())
        seen: set[str] = set()
        projects: list[str] = []
        for candidate in [target, *self.config.recent_projects]:
            if candidate in seen:
                continue
            seen.add(candidate)
            projects.append(candidate)
        self.config.recent_projects = projects[:8]

    def _recent_project_entries(self) -> list[dict[str, Any]]:
        current = str(self.config.workdir)
        seen: set[str] = set()
        entries: list[dict[str, Any]] = []
        for candidate in [current, *self.config.recent_projects]:
            if candidate in seen:
                continue
            seen.add(candidate)
            path = Path(candidate)
            entries.append(
                {
                    "name": path.name or candidate,
                    "path": candidate,
                    "active": candidate == current,
                }
            )
        return entries[:8]

    def _scope_sessions_to_project(self, workdir: Path) -> None:
        self.config.sessions_dir = _project_sessions_dir(self.base_sessions_dir, workdir)

    def _new_agent(self, session_id: str | None = None) -> Agent:
        return Agent(self.config, session_id=session_id, event_sink=self._record_agent_event)

    def _record_agent_event(self, event: AgentEvent) -> None:
        if event.kind != "tool_result" or event.metadata.get("operation") != "write_file":
            return
        path = str(event.metadata.get("path", ""))
        diff = str(event.metadata.get("diff", ""))
        if not path:
            return
        self.file_changes.append(
            {
                "path": path,
                "ok": bool(event.ok),
                "existed": bool(event.metadata.get("existed", False)),
                "summary": event.content,
                "diff": diff,
            }
        )
        self.file_changes = self.file_changes[-50:]


def _handler_for(app: DesktopApp) -> type[BaseHTTPRequestHandler]:
    class DesktopHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - stdlib callback name
            if self.path in {"/", "/index.html"}:
                self._send_html(render_desktop_html())
                return
            if self.path == "/api/state":
                self._send_json(app.state())
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802 - stdlib callback name
            payload = self._read_json()
            if self.path == "/api/new":
                self._send_json(app.new_chat())
                return
            if self.path == "/api/open":
                self._send_json(app.open_session(str(payload.get("sessionId", ""))))
                return
            if self.path == "/api/ask":
                self._send_json(app.ask(str(payload.get("prompt", ""))))
                return
            if self.path == "/api/provider":
                self._send_json(app.save_provider_settings(payload))
                return
            if self.path == "/api/test-provider":
                self._send_json(app.test_provider_settings(payload))
                return
            if self.path == "/api/project/validate":
                self._send_json(app.validate_project())
                return
            if self.path == "/api/project/switch":
                self._send_json(app.switch_project(payload))
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def log_message(self, format: str, *args: object) -> None:
            return

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("content-length", "0"))
            if length <= 0:
                return {}
            raw = self.rfile.read(length).decode("utf-8")
            return cast(dict[str, Any], json.loads(raw or "{}"))

        def _send_html(self, html: str) -> None:
            data = html.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_json(self, payload: dict[str, Any]) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("content-type", "application/json; charset=utf-8")
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return DesktopHandler


def _redact_provider_error(message: str, api_key_env: str) -> str:
    secret_value = os.environ.get(api_key_env, "").strip()
    redacted = message
    if secret_value:
        redacted = redacted.replace(secret_value, "[REDACTED]")
    return SECRET_PATTERN.sub(lambda match: _redact_secret_match(match), redacted)


def _redact_secret_match(match: re.Match[str]) -> str:
    text = match.group(0)
    if "=" in text:
        key, _, _value = text.partition("=")
        return f"{key}=[REDACTED]"
    return "[REDACTED]"


def _project_sessions_dir(base_dir: Path, workdir: Path) -> Path:
    resolved = str(workdir.resolve())
    digest = hashlib.sha256(resolved.encode("utf-8")).hexdigest()[:12]
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", workdir.name).strip(".-") or "project"
    return base_dir / "projects" / f"{slug}-{digest}"


def _validate_project(workdir: Path) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    recommendations: list[str] = []
    files: list[str] = []

    def add_check(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    if not workdir.exists():
        return {
            "ok": False,
            "path": str(workdir),
            "summary": "Project path does not exist.",
            "checks": [{"name": "Path", "status": "fail", "detail": str(workdir)}],
            "files": [],
            "recommendations": [],
            "git": "not checked",
        }
    if not workdir.is_dir():
        return {
            "ok": False,
            "path": str(workdir),
            "summary": "Project path is not a directory.",
            "checks": [{"name": "Path", "status": "fail", "detail": str(workdir)}],
            "files": [],
            "recommendations": [],
            "git": "not checked",
        }

    add_check("Path", "pass", str(workdir))

    key_files = [
        "AGENTS.md",
        "README.md",
        "pyproject.toml",
        "package.json",
        "app.json",
        "docs/product/clean-room-scope.md",
    ]
    for rel in key_files:
        if (workdir / rel).exists():
            files.append(rel)
    if files:
        add_check("Key files", "pass", ", ".join(files))
    else:
        add_check("Key files", "warn", "No AGENTS.md, README.md, pyproject.toml, or package.json found.")

    git_summary = _git_status_summary(workdir)
    add_check("Git", git_summary["status"], git_summary["detail"])

    if (workdir / "pyproject.toml").exists():
        recommendations.extend(
            [
                ".venv/bin/python -m pytest",
                ".venv/bin/python -m ruff check src tests",
                ".venv/bin/python -m mypy src/x_agentic_workflow",
            ]
        )
    if (workdir / "package.json").exists():
        recommendations.extend(["npm test", "npm run lint", "npm run build"])
    if not recommendations:
        recommendations.append("Inspect README.md or AGENTS.md for project-specific verification commands.")

    has_fail = any(check["status"] == "fail" for check in checks)
    has_warn = any(check["status"] == "warn" for check in checks)
    summary = "Project validation passed." if not has_warn else "Project validation passed with warnings."
    if has_fail:
        summary = "Project validation failed."
    return {
        "ok": not has_fail,
        "path": str(workdir),
        "summary": summary,
        "checks": checks,
        "files": files,
        "recommendations": recommendations,
        "git": git_summary["detail"],
    }


def _git_status_summary(workdir: Path) -> dict[str, str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(workdir), "status", "--short", "--branch"],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "warn", "detail": f"Git status unavailable: {exc}"}

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "Not a git repository.").strip()
        return {"status": "warn", "detail": detail}
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        return {"status": "pass", "detail": "Clean git repository."}
    branch = lines[0]
    changes = lines[1:]
    if changes:
        return {"status": "warn", "detail": f"{branch}; {len(changes)} uncommitted change(s)."}
    return {"status": "pass", "detail": branch}


def render_desktop_html() -> str:
    """Return the clean-room desktop UI shell."""

    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>x-agentic-workflow</title>
  <style>
    :root {
      --ink: #202633;
      --muted: #6f7b8b;
      --line: #dfe6ef;
      --soft: #f5f8fc;
      --panel: #ffffff;
      --side: #f3f7fb;
      --accent: #2d7df0;
      --warm: #e2b7a7;
      --shadow: 0 22px 60px rgba(33, 48, 75, .12);
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", system-ui, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body { margin: 0; color: var(--ink); background: #fefefe; overflow: hidden; }
    .app { height: 100vh; overflow: hidden; display: grid; grid-template-columns: 360px minmax(620px, 1fr) 360px; }
    .app.inspector-collapsed { grid-template-columns: 360px minmax(620px, 1fr) 56px; }
    aside {
      border-right: 1px solid var(--line);
      background: linear-gradient(180deg, #fdfdfc, #f7f8fa);
      padding: 18px 0 0;
      display: flex;
      flex-direction: column;
      gap: 0;
      min-width: 0;
      height: 100vh;
    }
    .sidebar-chrome { display: grid; grid-template-columns: 96px 1fr; align-items: center; padding: 0 18px 22px; }
    .traffic { display: flex; gap: 10px; align-items: center; height: 26px; }
    .dot { width: 13px; height: 13px; border-radius: 99px; display: inline-block; }
    .red { background: #ff5f57; } .yellow { background: #febc2e; } .green { background: #28c840; }
    .sidebar-arrows { display: flex; gap: 22px; justify-content: flex-end; color: #9c9c9a; font-size: 20px; padding-right: 14px; }
    .main-nav { display: grid; gap: 10px; padding: 0 22px 24px; }
    .main-nav button {
      border: 0; background: transparent; color: #3f4247; display: flex; align-items: center; gap: 16px;
      height: 32px; padding: 0; font-size: 15px; font-weight: 450; cursor: pointer;
    }
    .main-nav .badge-count { margin-left: auto; background: #ececeb; color: #686a6d; border-radius: 15px; padding: 2px 9px; font-weight: 450; font-size: 13px; }
    .side-scroll { flex: 1; overflow: auto; padding-bottom: 24px; }
    .side-heading { color: #aaa; font-size: 13px; font-weight: 450; margin: 18px 0 14px; padding: 0 0; }
    .project-block { display: grid; gap: 6px; margin-bottom: 22px; }
    .project-header { display: flex; align-items: center; gap: 12px; color: #3e4248; font-size: 15px; font-weight: 430; padding: 0 0; }
    .project-icon { color: #3e4248; font-size: 15px; width: 24px; text-align: center; }
    .conversation-row {
      display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 12px;
      min-height: 32px; margin-left: 36px; padding: 0 8px 0 0; color: #343840;
      font-size: 14px; font-weight: 420; border-radius: 10px;
    }
    .conversation-row.active { background: #e9e9e7; padding-left: 0; margin-left: 36px; font-weight: 520; }
    .conversation-row button {
      border: 0; background: transparent; color: inherit; font: inherit; text-align: left;
      overflow: hidden; white-space: nowrap; text-overflow: ellipsis; cursor: pointer; padding: 0;
    }
    .conversation-row.muted { color: #b7b7b5; }
    .conversation-title { overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
    .shortcut { background: #eeeeed; color: #858585; border-radius: 13px; padding: 2px 8px; font-size: 12px; font-weight: 430; }
    .relative-age { color: #8b8b89; font-size: 13px; font-weight: 400; }
    .sidebar-section { padding: 0 28px 0 0; }
    .sidebar-footer { margin: auto 0 0; border-top: 1px solid #e3e3e1; background: rgba(255,255,255,.74); padding: 12px 14px; }
    .account-card { border: 0; width: 100%; background: transparent; display: grid; grid-template-columns: 38px 1fr auto; align-items: center; gap: 10px; text-align: left; cursor: pointer; }
    .account-avatar { width: 38px; height: 38px; border-radius: 999px; background: #f0e7ff; display: grid; place-items: center; color: #8957ff; font-weight: 450; font-size: 14px; }
    .account-title { color: #222; font-size: 15px; font-weight: 450; }
    .account-sub { color: #858585; font-size: 13px; margin-top: 1px; }
    .account-chevron { color: #aaa; font-size: 18px; }
    .quick-icons { display: flex; gap: 16px; color: #737373; padding: 4px 18px 18px; font-size: 18px; }
    .brand { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 12px 14px; }
    .brand-left { display: flex; align-items: center; gap: 12px; min-width: 0; font-weight: 760; font-size: 20px; }
    .logo {
      width: 38px; height: 38px; border-radius: 12px; background: white; display: grid; place-items: center;
      color: var(--accent); box-shadow: 0 2px 10px rgba(39, 85, 145, .12); font-weight: 900;
    }
    .brand em { color: #d96c55; font-style: normal; }
    .icon-btn {
      border: 0; background: transparent; color: #7d8896; border-radius: 10px; font-size: 20px;
      width: 36px; height: 36px; cursor: pointer;
    }
    .icon-btn:hover { background: #e8eef6; }
    .segment { display: grid; grid-template-columns: repeat(3, 1fr); gap: 3px; margin: 0 12px 8px; padding: 3px; background: #f0f0ef; border-radius: 9px; }
    .seg { border: 0; background: transparent; border-radius: 7px; height: 36px; color: #878787; font-size: 16px; cursor: pointer; }
    .seg.active { background: white; color: #1f1f1f; box-shadow: 0 1px 6px rgba(0,0,0,.10); font-weight: 760; }
    nav { display: grid; gap: 8px; }
    .nav-item, .recent-item, .profile, .update {
      border: 0;
      width: 100%;
      text-align: left;
      background: transparent;
      color: #4d5968;
      border-radius: 12px;
      padding: 10px 14px;
      font-size: 16px;
      cursor: pointer;
    }
    .nav-item.active { background: #eeeeed; color: #202020; }
    .nav-item:hover, .recent-item:hover, .project:hover { background: #eeeeed; }
    .search-row { display: grid; grid-template-columns: 1fr 42px; gap: 8px; align-items: center; padding: 0 12px; }
    .search {
      height: 42px; border: 1px solid #e4e4e2; background: white; border-radius: 12px;
      display: flex; align-items: center; gap: 10px; padding: 0 16px; color: #8994a3;
      box-shadow: 0 1px 2px rgba(31, 54, 86, .04);
    }
    .search input { border: 0; outline: 0; background: transparent; width: 100%; font: inherit; color: var(--ink); }
    .square {
      width: 42px; height: 42px; border: 1px solid #e4e4e2; background: white; border-radius: 12px;
      color: #5e6a78; font-size: 20px; cursor: pointer;
    }
    .section-title { color: #8a8a88; font-size: 15px; margin: 22px 20px 8px; font-weight: 620; }
    .recents { flex: 1; overflow: auto; }
    .recent-item { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .project-group { display: grid; gap: 6px; margin-bottom: 14px; }
    .project {
      display: grid; grid-template-columns: 28px 1fr auto; align-items: center; gap: 10px;
      border-radius: 12px; padding: 8px 14px; color: #4d5968;
    }
    .project-title { font-weight: 720; color: #273142; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .project-sub { grid-column: 2 / 4; color: #788493; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .age { color: #8d98a7; font-size: 13px; }
    .old-sidebar-footer { margin: auto -10px 0; border-top: 1px solid var(--line); background: rgba(255,255,255,.70); padding: 12px 16px; }
    .update { background: white; border: 1px solid var(--line); box-shadow: 0 8px 25px rgba(51, 87, 133, .07); color: var(--muted); }
    .profile { border-radius: 12px; color: var(--muted); }
    main { position: relative; display: flex; flex-direction: column; min-width: 0; min-height: 0; height: 100vh; overflow: hidden; }
    .topbar { height: 54px; display: grid; grid-template-columns: 1fr auto; align-items: center; padding: 0 28px; color: var(--muted); border-bottom: 0; }
    .mode-tabs { display: flex; align-self: stretch; }
    .mode-tab {
      border: 0; border-bottom: 2px solid transparent; background: transparent; color: #536172;
      padding: 0 22px; font-size: 16px; font-weight: 720; cursor: pointer;
    }
    .mode-tab.active { color: #263141; border-bottom-color: #a55741; }
    .terminal { border: 1px solid var(--line); border-radius: 8px; width: 22px; height: 22px; display: grid; place-items: center; font-size: 13px; }
    .stage { flex: 1; min-height: 0; display: flex; align-items: stretch; justify-content: center; padding: 0 40px 8px; background: #fff; }
    .screen { width: 100%; height: 100%; min-height: 0; display: none; }
    .screen.active { display: flex; }
    #chatScreen.active { align-items: stretch; justify-content: center; }
    #settingsScreen.active { align-items: stretch; justify-content: stretch; padding: 0; }
    .hero { width: min(980px, 100%); height: 100%; min-height: 0; margin-top: 0; display: flex; flex-direction: column; }
    .hero-main { width: min(720px, 100%); margin: 28px auto 0; flex: 0 1 auto; }
    .hero-logo {
      display: inline-grid; place-items: center; margin-right: 12px; color: #dd6d4c; font-size: 32px; font-weight: 900;
    }
    .greeting { display: flex; align-items: center; justify-content: flex-start; font-size: clamp(26px, 2.8vw, 34px); line-height: 1.1; margin-bottom: 78px; color: #202020; font-weight: 560; letter-spacing: -.02em; }
    .subline { color: #777; font-size: 16px; line-height: 1.5; margin: -54px 0 28px 48px; max-width: 560px; }
    .usage-card { width: 100%; background: #f3f3f2; border: 1px solid #ededeb; border-radius: 12px; padding: 12px 16px 16px; color: #202020; }
    .usage-tabs { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; color: #515151; }
    .tab-group { display: flex; gap: 8px; }
    .mini-tab { border: 0; background: transparent; border-radius: 7px; padding: 6px 12px; color: #555; font-size: 15px; }
    .mini-tab.active { background: #e7e7e6; color: #222; }
    .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-bottom: 10px; }
    .stat { background: #e7e7e6; border-radius: 7px; padding: 8px; min-height: 56px; }
    .stat-label { color: #8c8c8a; font-size: 13px; }
    .stat-value { color: #242424; font-weight: 560; font-size: 17px; margin-top: 2px; }
    .heatmap { display: grid; grid-template-columns: repeat(28, 1fr); gap: 4px; margin-top: 6px; }
    .cell { aspect-ratio: 1 / 1; border-radius: 3px; background: #e6e6e4; }
    .cell.on { background: #7da8e8; }
    .cell.hot { background: #2f76df; }
    .usage-note { color: #8c8c8a; font-size: 14px; margin-top: 10px; }
    .composer {
      background: white;
      border: 1px solid #d5d5d3;
      border-radius: 18px;
      box-shadow: 0 16px 42px rgba(0,0,0,.08);
      overflow: hidden;
      width: 100%;
      min-width: 520px;
    }
    .composer-dock { width: min(1064px, 100%); margin: auto auto 0; padding-top: 24px; }
    .composer-context { display: flex; gap: 8px; margin-bottom: 10px; }
    .context-chip { border: 1px solid #dededc; border-radius: 9px; background: white; padding: 6px 10px; color: #555; font-size: 14px; }
    .notice { display: none; }
    .notice small { color: var(--muted); font-weight: 500; }
    textarea {
      width: 100%;
      min-height: 62px;
      resize: vertical;
      border: 0;
      outline: 0;
      padding: 18px 18px 10px;
      font: inherit;
      font-size: 17px;
      color: var(--ink);
    }
    textarea::placeholder { color: #9da7b4; }
    .composer-actions { display: flex; align-items: end; justify-content: space-between; padding: 10px 8px 0; }
    .left-tools, .right-tools { display: flex; align-items: center; gap: 12px; }
    .right-tools { margin-left: auto; justify-content: flex-end; }
    .round, .send, .pill {
      border: 1px solid var(--line);
      background: white;
      border-radius: 999px;
      min-width: 40px;
      height: 32px;
      padding: 0 14px;
      font-size: 14px;
      cursor: pointer;
    }
    .pill { color: #536172; background: #f8fafc; }
    .pill:disabled { color: #8b95a1; cursor: default; opacity: .72; }
    .send { background: #dd6d4c; color: white; border-color: #dd6d4c; padding: 0 16px; min-width: 86px; font-weight: 500; }
    .project-picker {
      display: grid; grid-template-columns: 1fr auto; gap: 8px; align-items: center;
      border-top: 1px solid #ececea; padding: 10px 12px 12px; background: #fbfbfa;
    }
    .project-picker input {
      min-width: 0; border: 1px solid #dededc; border-radius: 10px; height: 34px;
      padding: 0 10px; font: inherit; font-size: 13px; color: #333; background: white;
    }
    .project-picker button {
      border: 1px solid #dededc; border-radius: 10px; height: 34px; padding: 0 12px;
      background: white; color: #536172; font-size: 13px; cursor: pointer;
    }
    .project-picker button:disabled { color: #9ba4af; cursor: default; opacity: .75; }
    .model { display: flex; gap: 12px; align-items: center; color: var(--muted); }
    .chips { display: none; }
    .chip { border: 1px solid var(--line); background: white; border-radius: 13px; padding: 10px 16px; box-shadow: 0 3px 10px rgba(0,0,0,.05); font-size: 16px; }
    .messages { margin-top: 22px; display: grid; gap: 10px; max-height: 240px; overflow: auto; width: min(1064px, 100%); }
    .msg { border-radius: 16px; padding: 12px 14px; line-height: 1.45; white-space: pre-wrap; }
    .msg.user { background: var(--soft); justify-self: end; max-width: 78%; }
    .msg.assistant { background: white; border: 1px solid var(--line); }
    .msg.error { background: #fff1ef; color: #a23122; border: 1px solid #ffd4cc; }
    .inspector {
      border-left: 1px solid #efefed;
      background: #fff;
      padding: 18px 22px 26px;
      min-width: 0;
      height: 100vh;
      overflow: auto;
    }
    .inspector-toolbar {
      display: flex; justify-content: flex-end; align-items: center; gap: 24px;
      height: 54px; margin: -18px -22px 16px; padding: 0 22px; border-bottom: 1px solid #efefed;
    }
    .inspector-btn {
      width: 28px; height: 28px; border: 0; border-radius: 8px; background: transparent;
      color: #8b8d90; display: grid; place-items: center; cursor: pointer;
    }
    .inspector-btn:hover, .inspector-btn.active:hover { background: #f3f3f2; color: #606266; }
    .inspector-btn.active { background: transparent; color: #8b8d90; }
    .toolbar-icon { position: relative; display: block; width: 23px; height: 22px; color: currentColor; }
    .toolbar-list::before, .toolbar-list::after {
      content: ""; position: absolute; left: 1px; width: 5px; height: 5px; border: 2px solid currentColor; border-radius: 999px;
    }
    .toolbar-list::before { top: 2px; }
    .toolbar-list::after { bottom: 2px; }
    .toolbar-list span {
      position: absolute; left: 12px; width: 10px; height: 2px; background: currentColor; border-radius: 999px;
    }
    .toolbar-list span:first-child { top: 5px; }
    .toolbar-list span:last-child { bottom: 5px; }
    .toolbar-rect, .toolbar-side {
      width: 22px; height: 18px; border: 2.4px solid currentColor; border-radius: 6px;
    }
    .toolbar-rect::after {
      content: ""; position: absolute; left: 5px; right: 5px; bottom: 4px; height: 2px;
      background: currentColor; border-radius: 999px; opacity: .9;
    }
    .toolbar-side::after {
      content: ""; position: absolute; top: 3px; bottom: 3px; right: 4px; width: 2px;
      background: currentColor; border-radius: 999px; opacity: .9;
    }
    .app.inspector-collapsed .inspector { padding: 18px 10px; }
    .app.inspector-collapsed .inspector-card { display: none; }
    .app.inspector-collapsed .inspector-toolbar { flex-direction: column; align-items: center; gap: 12px; height: auto; margin: -18px -10px 0; padding: 16px 0; border-bottom: 0; }
    .app.inspector-collapsed .hide-when-collapsed { display: none; }
    .inspector-card {
      border: 1px solid #ededeb;
      border-radius: 22px;
      box-shadow: 0 14px 42px rgba(0,0,0,.08);
      padding: 22px;
      color: #2f3338;
    }
    .inspector-section { padding: 0 0 20px; margin-bottom: 20px; border-bottom: 1px solid #efefed; }
    .inspector-section:last-child { border-bottom: 0; margin-bottom: 0; padding-bottom: 0; }
    .inspector-title { color: #929292; font-size: 13px; font-weight: 450; margin-bottom: 14px; }
    .file-row, .task-row, .source-row {
      display: flex; align-items: center; gap: 10px; min-height: 34px; color: #30343a;
      font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .file-row span:last-child, .task-row span:last-child { overflow: hidden; text-overflow: ellipsis; }
    .more-link { color: #999; font-size: 14px; margin-top: 6px; }
    .diff-view {
      max-height: 220px; overflow: auto; border: 1px solid #ececea; border-radius: 8px;
      background: #fbfbfa; padding: 10px; color: #394150; font-size: 12px;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace; line-height: 1.42; white-space: pre;
    }
    .empty-note { color: #a4a4a1; font-size: 14px; line-height: 1.4; }
    .source-dots { display: flex; flex-wrap: wrap; gap: 10px; color: #717171; font-size: 16px; }
    .validation-box { display: grid; gap: 10px; }
    .validation-summary { font-size: 14px; color: #30343a; line-height: 1.4; }
    .validation-summary.ok { color: #0f7f58; }
    .validation-summary.warn { color: #9a5b0b; }
    .check-row {
      display: grid; grid-template-columns: 56px 1fr; gap: 8px; align-items: start;
      font-size: 13px; color: #4a5564; line-height: 1.35;
    }
    .check-status { font-weight: 760; text-transform: uppercase; font-size: 11px; color: #7d8794; }
    .check-status.pass { color: #0f9f6e; }
    .check-status.warn { color: #b76e00; }
    .check-status.fail { color: #b42318; }
    .command-list { display: grid; gap: 6px; margin-top: 4px; }
    .command-chip {
      display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
      border: 1px solid #e7ebf1; border-radius: 7px; padding: 6px 8px; color: #536172;
      background: #fbfcfe; font-size: 12px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    }
    .settings-layout { width: 100%; display: grid; grid-template-columns: 252px 1fr; min-height: calc(100vh - 64px); }
    .settings-nav { border-right: 1px solid var(--line); background: #f7faff; padding: 24px 14px; overflow: auto; }
    .settings-nav button {
      width: 100%; border: 0; background: transparent; color: #5c6877; border-radius: 0; text-align: left;
      padding: 12px 14px; font-size: 18px; display: flex; gap: 14px; align-items: center; cursor: pointer;
    }
    .settings-nav button.active { background: #e7edf5; color: #202633; font-weight: 780; }
    .settings-panel { padding: 34px 44px; max-width: 1060px; }
    .settings-head { display: flex; justify-content: space-between; align-items: center; gap: 20px; margin-bottom: 28px; }
    .settings-title { font-size: 28px; font-weight: 820; color: #1e2632; }
    .settings-subtitle { margin-top: 8px; color: #7a8798; font-size: 18px; }
    .primary-btn { border: 0; background: #ad6048; color: white; border-radius: 12px; padding: 12px 18px; font-size: 16px; font-weight: 760; cursor: pointer; }
    .provider-list { display: grid; gap: 14px; }
    .provider-form {
      display: grid; grid-template-columns: 180px 1fr 1fr; gap: 12px; margin-bottom: 20px;
      background: #fbfcfe; border: 1px solid #e2e8f0; border-radius: 14px; padding: 16px;
    }
    .field { display: grid; gap: 6px; }
    .field label { color: #697586; font-size: 13px; font-weight: 720; }
    .field input, .field select {
      height: 40px; border: 1px solid #d9e1ec; border-radius: 10px; padding: 0 12px;
      font: inherit; background: white; color: #202633;
    }
    .field.wide { grid-column: span 2; }
    .provider-actions { display: flex; gap: 10px; align-items: end; }
    .secondary-btn { border: 1px solid #d9e1ec; background: white; color: #536172; border-radius: 12px; padding: 10px 14px; font-size: 15px; font-weight: 720; cursor: pointer; }
    .settings-result { grid-column: 1 / -1; color: #697586; font-size: 14px; min-height: 20px; }
    .settings-result.ok { color: #0f9f6e; }
    .settings-result.bad { color: #b42318; }
    .provider-card {
      display: grid; grid-template-columns: 26px 22px 1fr auto; align-items: center; gap: 12px;
      border: 1px solid #dfe6ef; border-radius: 12px; padding: 18px 22px; min-height: 88px; background: white;
      cursor: pointer;
    }
    .provider-card.default { border-color: #b56049; box-shadow: 0 0 0 1px rgba(181, 96, 73, .1); }
    .drag { color: #9aa6b5; font-size: 22px; letter-spacing: -4px; }
    .status-dot { width: 13px; height: 13px; border-radius: 99px; background: #93a0ad; }
    .status-dot.on { background: #0f9f6e; }
    .provider-name { font-size: 20px; font-weight: 820; color: #202633; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .provider-meta { margin-top: 6px; color: #7c8797; font-size: 16px; }
    .badge { font-size: 13px; padding: 3px 8px; border-radius: 7px; background: #edf2f7; color: #7b8795; font-weight: 760; }
    .badge.hot { background: #fff0e9; color: #cf5f35; }
    .settings-note { margin-top: 28px; color: #728094; line-height: 1.55; font-size: 15px; }
    @media (max-width: 860px) {
      .app { grid-template-columns: 1fr; }
      aside { display: none; }
      .inspector { display: none; }
      .stage { padding: 18px; }
      .composer { min-width: 0; }
      .composer-dock { padding-top: 32px; }
      .subline { margin-bottom: 48px; }
      .settings-layout { grid-template-columns: 1fr; }
      .settings-nav { display: none; }
      .settings-panel { padding: 24px 18px; }
      .provider-form { grid-template-columns: 1fr; }
      .field.wide { grid-column: auto; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <div class="sidebar-chrome">
        <div class="traffic"><span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span></div>
        <div class="sidebar-arrows"><span>▯</span><span>‹</span><span>›</span></div>
      </div>
      <nav class="main-nav">
        <button id="newChat">✎ <span>新对话</span></button>
        <button>⌕ <span>搜索</span></button>
        <button>◷ <span>已安排</span><span class="badge-count">57</span></button>
        <button>◎ <span>插件</span></button>
      </nav>
      <div class="side-scroll">
        <div class="sidebar-section">
          <div class="side-heading">项目</div>
          <div class="project-block">
            <div class="project-header"><span class="project-icon">▱</span><span id="currentProjectName">x-agentic-workflow</span></div>
            <div class="conversation-row active"><span class="conversation-title" id="currentProjectPath">354685856-sn/x-agentic-workflow</span><span class="shortcut">当前</span></div>
          </div>
          <div class="project-block">
            <div class="project-header"><span class="project-icon">▱</span><span>最近项目</span></div>
            <div id="recentProjects"><div class="conversation-row muted"><span class="conversation-title">暂无最近项目</span></div></div>
          </div>
          <div class="side-heading">对话</div>
          <div id="recents"><div class="conversation-row muted"><span class="conversation-title">暂无聊天</span></div></div>
        </div>
      </div>
      <div class="sidebar-footer">
        <button class="account-card" id="settingsBtn">
          <span class="account-avatar">设</span>
          <span><span class="account-title">设置</span><span class="account-sub">账户</span></span>
          <span class="account-chevron">⌄</span>
        </button>
      </div>
    </aside>
    <main>
      <div class="topbar">
        <div class="mode-tabs">
          <button class="mode-tab active" id="chatTab">x-agentic-workflow</button>
          <button class="mode-tab" id="settingsTab">⚙ 设置</button>
        </div>
        <span class="terminal">›_</span>
      </div>
      <section class="stage">
        <div class="screen active" id="chatScreen">
          <div class="hero">
            <div class="hero-main">
              <div class="greeting"><span class="hero-logo">✳</span>What’s up next, sn?</div>
              <div class="subline">Code mode is ready for repo work, provider setup, tools, approvals, and clean-room product shipping.</div>
              <div class="usage-card">
                <div class="usage-tabs">
                  <div class="tab-group"><button class="mini-tab active">Overview</button><button class="mini-tab">Models</button></div>
                  <div class="tab-group"><button class="mini-tab active">All</button><button class="mini-tab">30d</button><button class="mini-tab">7d</button></div>
                </div>
                <div class="stats-grid">
                  <div class="stat"><div class="stat-label">Sessions</div><div class="stat-value">12</div></div>
                  <div class="stat"><div class="stat-label">Messages</div><div class="stat-value">1,091</div></div>
                  <div class="stat"><div class="stat-label">Total tokens</div><div class="stat-value">1.5M</div></div>
                  <div class="stat"><div class="stat-label">Active days</div><div class="stat-value">5</div></div>
                  <div class="stat"><div class="stat-label">Current streak</div><div class="stat-value">1d</div></div>
                  <div class="stat"><div class="stat-label">Longest streak</div><div class="stat-value">1d</div></div>
                  <div class="stat"><div class="stat-label">Peak hour</div><div class="stat-value">6 PM</div></div>
                  <div class="stat"><div class="stat-label">Favorite model</div><div class="stat-value">XAW Pro</div></div>
                </div>
                <div class="heatmap">
                  <span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span>
                  <span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell on"></span><span class="cell"></span><span class="cell"></span><span class="cell hot"></span><span class="cell"></span><span class="cell"></span><span class="cell on"></span>
                  <span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell on"></span><span class="cell"></span><span class="cell"></span>
                  <span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell hot"></span><span class="cell"></span><span class="cell"></span><span class="cell on"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span><span class="cell"></span>
                </div>
                <div class="usage-note">You’ve used local clean-room workflows across CLI, TUI, desktop, releases, and provider setup.</div>
              </div>
              <div class="messages" id="messages"></div>
            </div>
            <div class="composer-dock">
              <div class="composer-context"><span class="context-chip">▰ Local</span><span class="context-chip">▱ mac</span><span class="context-chip">▣</span></div>
              <div class="composer">
                <div class="notice"><span id="status">x-agentic-workflow is ready.</span><small id="workdir"></small></div>
                <textarea id="prompt" placeholder="Describe a task or ask a question"></textarea>
                <div class="project-picker">
                  <input id="projectPathInput" placeholder="/path/to/project" />
                  <button id="switchProject">切换项目</button>
                </div>
              </div>
              <div class="composer-actions">
                <div class="left-tools"><button class="pill" id="validateProject">验证项目</button><button class="pill">Accept edits</button><button class="round">＋</button><button class="round">⌄</button></div>
                <div class="right-tools"><span class="model" id="model">model</span><button class="pill">High</button><button class="send" id="send">↵</button></div>
              </div>
            </div>
          </div>
        </div>
        <div class="screen" id="settingsScreen">
          <div class="settings-layout">
            <div class="settings-nav">
              <button class="active">▤ 服务商</button>
              <button>☷ 通用</button>
              <button>▦ H5 访问</button>
              <button>▰ IM 接入</button>
              <button>▸ 终端</button>
              <button>▤ MCP</button>
              <button>▣ Agents</button>
              <button>✦ 技能</button>
              <button>▱ 记忆</button>
              <button>⌘ 插件</button>
              <button>◉ Computer Use</button>
              <button>▥ Token 用量</button>
              <button>⌬ Trace</button>
              <button>▧ 诊断</button>
            </div>
            <div class="settings-panel">
              <div class="settings-head">
                <div>
                  <div class="settings-title">服务商</div>
                  <div class="settings-subtitle">管理 API 服务商以访问模型。密钥只保存在本机环境变量或后续钥匙串方案中。</div>
                </div>
                <button class="primary-btn">＋ 添加服务商</button>
              </div>
              <div class="provider-form">
                <div class="field">
                  <label for="providerName">服务商协议</label>
                  <select id="providerName">
                    <option value="anthropic">Anthropic</option>
                    <option value="openai-compatible">OpenAI-compatible</option>
                  </select>
                </div>
                <div class="field">
                  <label for="providerModel">模型</label>
                  <input id="providerModel" placeholder="claude-3-5-sonnet-latest" />
                </div>
                <div class="field">
                  <label for="providerKeyEnv">API key 环境变量</label>
                  <input id="providerKeyEnv" placeholder="ANTHROPIC_API_KEY" />
                </div>
                <div class="field wide">
                  <label for="providerBaseUrl">Base URL（OpenAI-compatible 可选）</label>
                  <input id="providerBaseUrl" placeholder="https://api.openai.com/v1" />
                </div>
                <div class="provider-actions">
                  <button class="secondary-btn" id="testProvider">测试连接</button>
                  <button class="primary-btn" id="saveProvider">保存默认服务商</button>
                </div>
                <div class="settings-result" id="providerResult">密钥值不会写入配置文件；这里只保存环境变量名、模型和 base URL。</div>
              </div>
              <div class="provider-list">
                <div class="provider-card default">
                  <div class="drag">⋮⋮</div><div class="status-dot on"></div>
                  <div><div class="provider-name">DeepSeek <span class="badge">OpenAI-compatible</span><span class="badge hot">默认</span></div><div class="provider-meta">https://api.deepseek.com/v1 · deepseek-chat / deepseek-reasoner</div></div>
                  <span></span>
                </div>
                <div class="provider-card">
                  <div class="drag">⋮⋮</div><div class="status-dot"></div>
                  <div><div class="provider-name">OpenAI <span class="badge hot">Responses / Chat Completions</span></div><div class="provider-meta">https://api.openai.com/v1 · gpt-4.1 / o-series / compatible models</div></div>
                  <span></span>
                </div>
                <div class="provider-card">
                  <div class="drag">⋮⋮</div><div class="status-dot"></div>
                  <div><div class="provider-name">Anthropic 官方 <span class="badge">Messages API</span></div><div class="provider-meta">Claude 模型 · BYOK 环境变量 / 后续钥匙串方案</div></div>
                  <span></span>
                </div>
                <div class="provider-card">
                  <div class="drag">⋮⋮</div><div class="status-dot"></div>
                  <div><div class="provider-name">OpenRouter / DashScope / LM Studio <span class="badge">OpenAI-compatible</span></div><div class="provider-meta">自定义 base URL、模型名、请求头和本地模型入口</div></div>
                  <span></span>
                </div>
              </div>
              <div class="settings-note">Clean-room 交付原则：我们吸收公开产品体验与包交付结构，但 UI、代码、文案、图标、配置格式均由 XAW 自己实现。当前表单已接入 Provider Settings 保存和连接测试；后续补安全的 API key 存储。</div>
            </div>
          </div>
        </div>
      </section>
    </main>
    <aside class="inspector">
      <div class="inspector-toolbar">
        <button class="inspector-btn hide-when-collapsed" id="inspectorAdd" title="列表"><span class="toolbar-icon toolbar-list"><span></span><span></span></span></button>
        <button class="inspector-btn active" id="inspectorToggle" title="收起右侧栏"><span class="toolbar-icon toolbar-rect"></span></button>
        <button class="inspector-btn hide-when-collapsed" title="右侧视图"><span class="toolbar-icon toolbar-side"></span></button>
      </div>
      <div class="inspector-card">
        <div class="inspector-section">
          <div class="inspector-title">项目验证</div>
          <div class="validation-box" id="projectValidation">
            <div class="validation-summary">尚未验证当前项目。</div>
          </div>
        </div>
        <div class="inspector-section">
          <div class="inspector-title">文件变更</div>
          <div id="fileChanges"><div class="empty-note">暂无文件变更。</div></div>
        </div>
        <div class="inspector-section">
          <div class="inspector-title">Diff</div>
          <pre class="diff-view" id="latestDiff">暂无 diff。</pre>
        </div>
        <div class="inspector-section">
          <div class="inspector-title">任务</div>
          <div class="task-row"><span>▸</span><span>.venv/bin/xaw desktop --host 127.0.0.1</span></div>
        </div>
        <div class="inspector-section">
          <div class="inspector-title">浏览器</div>
          <div class="task-row"><span>◎</span><span>x-agentic-workflow 127.0.0.1</span></div>
        </div>
        <div class="inspector-section">
          <div class="inspector-title">来源</div>
          <div class="source-dots"><span>▣</span><span>◎</span><span>◎</span><span>◎</span><span>◎</span><span>◎</span><span>◎</span><span>◎</span></div>
        </div>
      </div>
    </aside>
  </div>
  <script>
    const $ = (id) => document.getElementById(id);
    async function api(path, body) {
      const res = await fetch(path, { method: body ? 'POST' : 'GET', headers: {'content-type': 'application/json'}, body: body ? JSON.stringify(body) : undefined });
      return await res.json();
    }
    function render(state) {
      const parts = state.workdir.split('/').filter(Boolean);
      const projectName = parts[parts.length - 1] || state.workdir;
      const projectPath = parts.slice(-2).join('/') || projectName;
      $('status').textContent = state.apiKeyPresent ? 'x-agentic-workflow is ready.' : 'API key missing. Set your BYOK environment variable to run prompts.';
      $('workdir').textContent = projectPath;
      $('currentProjectName').textContent = projectName;
      $('currentProjectPath').textContent = projectPath;
      $('projectPathInput').value = state.workdir;
      $('chatTab').textContent = projectName;
      $('model').textContent = state.model;
      $('providerName').value = state.provider;
      $('providerModel').value = state.model;
      $('providerBaseUrl').value = state.baseUrl || '';
      $('providerKeyEnv').value = state.apiKeyEnv;
      if (state.providerSave) showProviderResult(state.providerSave);
      if (state.providerTest) showProviderResult(state.providerTest);
      renderProjectValidation(state.projectValidation);
      if (state.projectSwitch && !state.projectSwitch.ok) {
        renderProjectValidation({ok: false, summary: state.projectSwitch.message, checks: [], recommendations: []});
      }
      renderRecentProjects(state.recentProjects || []);
      renderFileChanges(state.fileChanges || [], state.latestDiff);
      $('recents').innerHTML = state.sessions.map((s, i) => `<div class="conversation-row" data-session="${s}"><span class="conversation-title">${s}</span><span class="shortcut">⌘${i + 1}</span></div>`).join('') || '<div class="conversation-row muted"><span class="conversation-title">暂无聊天</span></div>';
      $('messages').innerHTML = state.messages.map(m => `<div class="msg ${m.role}">${escapeHtml(m.content)}</div>`).join('');
      document.querySelectorAll('[data-session]').forEach(btn => btn.onclick = async () => render(await api('/api/open', {sessionId: btn.dataset.session})));
      document.querySelectorAll('[data-project-path]').forEach(btn => btn.onclick = async () => switchProject(btn.dataset.projectPath));
    }
    function providerPayload() {
      return {
        provider: $('providerName').value,
        model: $('providerModel').value,
        baseUrl: $('providerBaseUrl').value,
        apiKeyEnv: $('providerKeyEnv').value
      };
    }
    function showProviderResult(result) {
      const box = $('providerResult');
      box.textContent = result.message;
      box.classList.toggle('ok', !!result.ok);
      box.classList.toggle('bad', !result.ok);
    }
    function renderProjectValidation(result) {
      const box = $('projectValidation');
      if (!result) {
        box.innerHTML = '<div class="validation-summary">尚未验证当前项目。</div>';
        return;
      }
      const tone = result.ok ? 'ok' : 'warn';
      const checks = result.checks.map(check => `<div class="check-row"><span class="check-status ${check.status}">${check.status}</span><span>${escapeHtml(check.name)}: ${escapeHtml(check.detail)}</span></div>`).join('');
      const commands = result.recommendations.map(cmd => `<span class="command-chip">${escapeHtml(cmd)}</span>`).join('');
      box.innerHTML = `<div class="validation-summary ${tone}">${escapeHtml(result.summary)}</div>${checks}<div class="command-list">${commands}</div>`;
    }
    function renderRecentProjects(projects) {
      const box = $('recentProjects');
      if (!projects.length) {
        box.innerHTML = '<div class="conversation-row muted"><span class="conversation-title">暂无最近项目</span></div>';
        return;
      }
      box.innerHTML = projects.map((project, i) => {
        const active = project.active ? ' active' : '';
        const badge = project.active ? '当前' : `⌘${i + 1}`;
        return `<div class="conversation-row${active}"><button data-project-path="${escapeHtml(project.path)}" title="${escapeHtml(project.path)}">${escapeHtml(project.name)}</button><span class="shortcut">${badge}</span></div>`;
      }).join('');
    }
    function renderFileChanges(changes, latest) {
      const box = $('fileChanges');
      if (!changes.length) {
        box.innerHTML = '<div class="empty-note">暂无文件变更。</div>';
      } else {
        box.innerHTML = changes.slice().reverse().map(change => {
          const marker = change.ok ? '▣' : '!';
          const state = change.existed ? 'updated' : 'created';
          return `<div class="file-row"><span>${marker}</span><span title="${escapeHtml(change.summary)}">${escapeHtml(change.path)} · ${state}</span></div>`;
        }).join('');
      }
      $('latestDiff').textContent = latest && latest.diff ? latest.diff : '暂无 diff。';
    }
    function escapeHtml(text) {
      return text.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
    }
    function showScreen(name) {
      const chat = name === 'chat';
      $('chatScreen').classList.toggle('active', chat);
      $('settingsScreen').classList.toggle('active', !chat);
      $('chatTab').classList.toggle('active', chat);
      $('settingsTab').classList.toggle('active', !chat);
    }
    async function send() {
      const prompt = $('prompt').value.trim();
      if (!prompt) return;
      $('prompt').value = '';
      $('status').textContent = 'Running...';
      render(await api('/api/ask', {prompt}));
    }
    $('send').onclick = send;
    $('prompt').addEventListener('keydown', e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) send(); });
    $('newChat').onclick = async () => { showScreen('chat'); render(await api('/api/new', {})); };
    $('settingsBtn').onclick = () => showScreen('settings');
    $('settingsTab').onclick = () => showScreen('settings');
    $('chatTab').onclick = () => showScreen('chat');
    $('inspectorToggle').onclick = () => {
      const app = document.querySelector('.app');
      const collapsed = app.classList.toggle('inspector-collapsed');
      $('inspectorToggle').title = collapsed ? '展开右侧栏' : '收起右侧栏';
    };
    $('saveProvider').onclick = async () => render(await api('/api/provider', providerPayload()));
    $('testProvider').onclick = async () => {
      showProviderResult({ok: true, message: 'Testing connection...'});
      render(await api('/api/test-provider', providerPayload()));
    };
    async function switchProject(path) {
      const target = (path || $('projectPathInput').value).trim();
      const button = $('switchProject');
      if (!target) return;
      button.disabled = true;
      button.textContent = '切换中...';
      renderProjectValidation({ok: true, summary: '正在切换并验证项目...', checks: [], recommendations: []});
      try {
        render(await api('/api/project/switch', {path: target}));
      } finally {
        button.disabled = false;
        button.textContent = '切换项目';
      }
    }
    $('switchProject').onclick = async () => switchProject();
    $('projectPathInput').addEventListener('keydown', e => { if (e.key === 'Enter') switchProject(); });
    $('validateProject').onclick = async () => {
      const button = $('validateProject');
      button.disabled = true;
      button.textContent = '验证中...';
      renderProjectValidation({ok: true, summary: '正在验证当前项目...', checks: [], recommendations: []});
      try {
        render(await api('/api/project/validate', {}));
      } finally {
        button.disabled = false;
        button.textContent = '验证项目';
      }
    };
    api('/api/state').then(render);
  </script>
</body>
</html>"""
