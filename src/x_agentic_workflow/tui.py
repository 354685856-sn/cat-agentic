"""Full-screen hybrid Textual interface for x-agentic-workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, RichLog, Static

from .agent import Agent
from .config import RuntimeConfig
from .tools import tool_specs
from .types import Message


@dataclass(frozen=True)
class TuiPanelState:
    """Snapshot rendered into the non-chat TUI panels."""

    provider: str
    model: str
    api_key_present: bool
    session_id: str
    workdir: Path
    sessions: tuple[str, ...]
    skills_count: int
    hooks_count: int
    mcp_servers_count: int
    tools: tuple[str, ...]
    approval_required: bool
    mode: str = "Chat"


class XawTuiApp(App[None]):
    """Hybrid terminal app with chat, status, tools, sessions, and approval panels."""

    TITLE = "x-agentic-workflow"
    SUB_TITLE = "hybrid terminal agent workspace"

    CSS = """
    Screen {
        layout: vertical;
        background: $background;
    }

    #workspace {
        height: 1fr;
    }

    #left-rail {
        width: 34;
        min-width: 28;
        padding: 1;
        background: $surface;
        border-right: solid $primary;
    }

    #center {
        width: 1fr;
    }

    #right-rail {
        width: 38;
        min-width: 30;
        padding: 1;
        background: $surface;
        border-left: solid $primary;
    }

    .panel {
        border: round $primary;
        padding: 1;
        margin-bottom: 1;
    }

    .panel-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #transcript {
        height: 1fr;
        padding: 1;
        border-bottom: solid $primary;
    }

    #composer {
        height: 3;
        padding: 0 1;
    }

    #prompt {
        width: 1fr;
    }

    #send {
        width: 10;
    }
    """

    BINDINGS = [
        Binding("ctrl+s", "submit", "Submit", show=True),
        Binding("ctrl+r", "reset", "Reset", show=True),
        Binding("ctrl+t", "focus_prompt", "Prompt", show=True),
        Binding("ctrl+a", "approval_panel", "Approval", show=True),
        Binding("ctrl+d", "doctor", "Doctor", show=True),
        Binding("ctrl+l", "clear", "Clear", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
    ]

    def __init__(
        self,
        config: RuntimeConfig | None = None,
        agent: Agent | None = None,
        session_id: str | None = None,
    ) -> None:
        super().__init__()
        self.config = config or RuntimeConfig.load(workdir=Path.cwd())
        self.agent = agent or Agent(self.config, session_id=session_id)
        self.mode = "Chat"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="workspace"):
            with Vertical(id="left-rail"):
                yield Static("", id="status-panel", classes="panel")
                yield Static("", id="sessions-panel", classes="panel")
                yield Static("", id="extensions-panel", classes="panel")
            with Vertical(id="center"):
                yield RichLog(id="transcript", wrap=True, markup=True)
                with Horizontal(id="composer"):
                    yield Input(placeholder="Ask x-agentic-workflow…", id="prompt")
                    yield Button("Send", id="send", variant="primary")
            with Vertical(id="right-rail"):
                yield Static("", id="tools-panel", classes="panel")
                yield Static("", id="approval-panel", classes="panel")
                yield Static("", id="help-panel", classes="panel")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_panels()
        transcript = self.query_one("#transcript", RichLog)
        transcript.write("[bold blue]x-agentic-workflow[/bold blue] hybrid TUI ready")
        transcript.write(f"[dim]session {self.agent.session_id} · mode {self.mode}[/dim]")
        self.query_one("#prompt", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._submit(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send":
            self._submit(self.query_one("#prompt", Input).value)

    def action_submit(self) -> None:
        self._submit(self.query_one("#prompt", Input).value)

    def action_reset(self) -> None:
        self.agent.messages = [Message(role="system", content=self.agent._system_prompt(""))]
        self.agent.sessions.save(self.agent.session_id, self.agent.messages)
        transcript = self.query_one("#transcript", RichLog)
        transcript.write("[bold yellow]session[/bold yellow] reset")
        self._refresh_panels()

    def action_focus_prompt(self) -> None:
        self.mode = "Chat"
        self.query_one("#prompt", Input).focus()
        self._refresh_panels()

    def action_approval_panel(self) -> None:
        self.mode = "Review"
        self._refresh_panels()
        self.query_one("#transcript", RichLog).write(
            "[bold yellow]approval[/bold yellow] command approvals are handled inline."
        )

    def action_doctor(self) -> None:
        self.mode = "Review"
        self._refresh_panels()
        key_status = "present" if self.config.api_key else "missing"
        self.query_one("#transcript", RichLog).write(
            "[bold cyan]doctor[/bold cyan] "
            f"provider={self.config.provider.name} model={self.config.provider.model} "
            f"api_key={key_status} workdir={self.config.workdir}"
        )

    def action_clear(self) -> None:
        self.query_one("#transcript", RichLog).clear()
        self._refresh_panels()

    def _submit(self, text: str) -> None:
        prompt = text.strip()
        if not prompt:
            return
        self.mode = "Run"
        self._refresh_panels()
        prompt_box = self.query_one("#prompt", Input)
        transcript = self.query_one("#transcript", RichLog)
        prompt_box.value = ""
        transcript.write(f"[bold green]you[/bold green] {prompt}")
        try:
            answer = self.agent.run_once(prompt)
        except Exception as exc:  # noqa: BLE001 - render provider/tool failures in UI
            transcript.write(f"[bold red]error[/bold red] {type(exc).__name__}: {exc}")
            self.mode = "Review"
            self._refresh_panels()
            return
        if answer:
            transcript.write(f"[bold blue]agent[/bold blue] {answer}")
        self.mode = "Chat"
        self._refresh_panels()

    def _state(self) -> TuiPanelState:
        sessions = tuple(self.agent.sessions.list_sessions()[-8:])
        hooks_count = sum(1 for path in self.config.hooks_dir.rglob("*") if path.is_file())
        return TuiPanelState(
            provider=self.config.provider.name,
            model=self.config.provider.model,
            api_key_present=bool(self.config.api_key),
            session_id=self.agent.session_id,
            workdir=self.config.workdir,
            sessions=sessions,
            skills_count=len(self.agent.skills.discover()),
            hooks_count=hooks_count,
            mcp_servers_count=len(self.agent.mcp.list_servers()),
            tools=tuple(spec.name for spec in tool_specs()),
            approval_required=self.config.require_command_approval,
            mode=self.mode,
        )

    def _refresh_panels(self) -> None:
        state = self._state()
        self.query_one("#status-panel", Static).update(_render_status(state))
        self.query_one("#sessions-panel", Static).update(_render_sessions(state))
        self.query_one("#extensions-panel", Static).update(_render_extensions(state))
        self.query_one("#tools-panel", Static).update(_render_tools(state))
        self.query_one("#approval-panel", Static).update(_render_approval(state))
        self.query_one("#help-panel", Static).update(_render_help())


def _render_status(state: TuiPanelState) -> str:
    key = "yes" if state.api_key_present else "no"
    base_url = "default" if state.provider == "anthropic" else "configured"
    return (
        "[bold cyan]Workspace[/bold cyan]\n"
        f"mode: [bold]{state.mode}[/bold]\n"
        f"provider: {state.provider}\n"
        f"model: {state.model}\n"
        f"api key: {key}\n"
        f"base url: {base_url}\n"
        f"workdir:\n{state.workdir}"
    )


def _render_sessions(state: TuiPanelState) -> str:
    lines = ["[bold cyan]Sessions[/bold cyan]", f"active: [bold]{state.session_id}[/bold]"]
    if state.sessions:
        lines.append("recent:")
        lines.extend(f"• {session}" for session in reversed(state.sessions))
    else:
        lines.append("recent: none")
    return "\n".join(lines)


def _render_extensions(state: TuiPanelState) -> str:
    return (
        "[bold cyan]Extensions[/bold cyan]\n"
        f"skills: {state.skills_count}\n"
        f"hooks: {state.hooks_count}\n"
        f"mcp servers: {state.mcp_servers_count}\n"
        "agents: role prompts"
    )


def _render_tools(state: TuiPanelState) -> str:
    lines = ["[bold cyan]Tools[/bold cyan]"]
    lines.extend(f"• {name}" for name in state.tools)
    return "\n".join(lines)


def _render_approval(state: TuiPanelState) -> str:
    status = "enabled" if state.approval_required else "disabled"
    return (
        "[bold cyan]Approval Queue[/bold cyan]\n"
        f"command approval: {status}\n"
        "pending: 0\n"
        "write guard: project sandbox\n"
        "path escape: blocked"
    )


def _render_help() -> str:
    return (
        "[bold cyan]Keys[/bold cyan]\n"
        "Ctrl+S submit\n"
        "Ctrl+R reset session\n"
        "Ctrl+T focus prompt\n"
        "Ctrl+A approval view\n"
        "Ctrl+D doctor\n"
        "Ctrl+L clear log\n"
        "Ctrl+Q quit"
    )
