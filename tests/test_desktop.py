import json
import re
import socket
import subprocess
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

import pytest

from x_agentic_workflow.config import RuntimeConfig
from x_agentic_workflow.desktop import (
    DesktopApp,
    _create_server,
    _project_sessions_dir,
    _prompt_with_attachment_context,
    _validate_project,
    _validate_text_attachments,
    render_desktop_html,
)
from x_agentic_workflow.types import AgentEvent, Message, ModelResponse, ToolSpec


def test_desktop_html_contains_clean_room_app_shell() -> None:
    html = render_desktop_html()

    assert "cat-agentic" in html
    assert "cat-agenic" not in html
    assert "x-agentic-workflow" not in html
    assert "新建会话" in html
    assert "navSettings" not in html
    assert "已安排" not in html
    assert "定时任务" in html
    assert '<span class="settings-nav-label">插件</span>' in html
    assert 'class="pending" disabled' in html
    assert "navSearch" not in html
    assert "navScheduled" not in html
    assert "navPlugins" not in html
    assert "354685856-sn/cat-agentic" in html
    assert "当前" in html
    assert "我的仓库位置" not in html
    assert "Claude-cc-haha" not in html
    assert "最近项目" in html
    assert "inspector-card" in html
    assert "inspectorToggle" in html
    assert "inspector-collapsed" in html
    assert "title=\"列表\"" in html
    assert "文件变更" in html
    assert "Diff" in html
    assert "latestDiff" in html
    assert "fileChanges" in html
    assert "workspaceStatus" in html
    assert "workspaceSummary" in html
    assert "renderWorkspaceStatus" in html
    assert "worktreeList" in html
    assert "createWorktree" in html
    assert "/api/worktree/create" in html
    assert "data-worktree-path" in html
    assert "selectedDiff" in html
    assert "selectedDiffIndex" in html
    assert "/api/diff/select" in html
    assert "data-diff-index" in html
    assert "任务" in html
    assert "随便问点什么..." in html
    assert "开始一个新的编码会话" in html
    assert "Overview" not in html
    assert "/api/ask" in html
    assert "/api/scheduled" in html
    assert "/api/scheduled/create" in html
    assert "/api/scheduled/delete" in html
    assert "/api/settings/general" in html
    assert "/api/settings/h5" in html
    assert "/api/terminal" in html
    assert "/api/terminal/probe" in html
    assert "/api/mcp" in html
    assert "/api/agents" in html
    assert "/api/skills" in html
    assert "/api/memory" in html
    assert "/api/memory/preview" in html
    assert 'data-settings-view="general"' in html
    assert 'data-settings-view="h5"' in html
    assert 'data-settings-view="terminal"' in html
    assert 'data-settings-view="mcp"' in html
    assert 'data-settings-view="agents"' in html
    assert 'data-settings-view="skills"' in html
    assert 'data-settings-view="memory"' in html
    assert 'id="h5SettingsPanel"' in html
    assert 'id="saveH5Settings"' in html
    assert "保存 H5 设置" in html
    assert 'id="terminalSettingsPanel"' in html
    assert 'id="refreshTerminalSettings"' in html
    assert 'id="runTerminalProbe"' in html
    assert "探针输出" in html
    assert 'id="mcpSettingsPanel"' in html
    assert 'id="refreshMcpSettings"' in html
    assert "MCP 配置文件" in html
    assert 'id="agentsSettingsPanel"' in html
    assert 'id="refreshAgentsSettings"' in html
    assert "AGENT 浏览器" in html
    assert 'id="skillsSettingsPanel"' in html
    assert 'id="refreshSkillsSettings"' in html
    assert 'id="skillsSearch"' in html
    assert "技能目录" in html
    assert 'id="memorySettingsPanel"' in html
    assert 'id="refreshMemorySettings"' in html
    assert 'id="memorySearch"' in html
    assert "记忆来源" in html
    assert 'id="requireCommandApproval"' in html
    assert 'id="notificationsEnabled"' in html
    assert 'id="uiScale"' in html
    assert 'data-send-mode="enter"' in html
    assert "验证项目" in html
    assert "验证中..." in html
    assert "切换项目" in html
    assert "切换中..." in html
    assert "/api/project/switch" in html
    assert "projectPathInput" in html
    assert "recentProjects" in html
    assert "sessionSearch" in html
    assert "githubBtn" in html
    assert "sidebarToggle" in html
    assert "scheduledBtn" in html
    assert "scheduledTab" in html
    assert "scheduledScreen" in html
    assert "createScheduledTask" in html
    assert "scheduledList" in html
    assert "refreshSessions" in html
    assert "clearSessionSearch" in html
    assert "sidebar-collapsed" in html
    assert "sessionDetails" in html
    assert "sessionTitle" in html
    assert "projectTopTab" in html
    assert "已恢复会话" in html
    assert "renderSessions" in html
    assert "attachButton" in html
    assert "attachmentInput" in html
    assert "pendingAttachments" in html
    assert "resetAttachments" in html
    assert "MAX_ATTACHMENT_FILES" in html
    assert "button.disabled = true" in html
    assert "button.disabled = false" in html
    assert "/api/project/validate" in html
    assert "项目验证" in html
    assert "服务商" in html
    assert "savedProviderCard" in html
    assert "savedProviderMeta" in html
    assert "providerSaveStatus" in html
    assert "providerFormDirty" in html
    assert "providerSubmitting" in html
    assert "runProviderAction" in html
    assert "添加服务商" not in html
    assert "DRAFT_KEY_PREFIX" in html
    assert "draftKeyForState" in html
    assert "restoreDraftForState" in html
    assert "saveCurrentDraft" in html
    assert "clearCurrentDraft" in html
    assert "MAX_DRAFT_CHARS" in html
    assert "updatedLabel" in html
    assert "relativeTime(" not in html
    assert "localStorage.setItem(currentDraftKey, draft)" in html
    assert "localStorage.removeItem(currentDraftKey)" in html
    assert "JSON.stringify(pendingAttachments)" not in html
    assert '<span class="settings-nav-label">Token 用量</span>' in html
    assert html.index('class="composer-actions"') < html.index('class="project-picker"')


def test_desktop_records_write_file_ledger_and_latest_diff(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    app._record_agent_event(
        AgentEvent(
            kind="tool_result",
            name="write_file",
            content="Wrote 12 chars to README.md",
            ok=True,
            metadata={
                "operation": "write_file",
                "path": "README.md",
                "diff": "--- a/README.md\n+++ b/README.md",
                "existed": True,
            },
        )
    )
    state = app.state()

    assert state["fileChanges"][0]["path"] == "README.md"
    assert state["fileChanges"][0]["existed"] is True
    assert state["latestDiff"]["diff"].startswith("--- a/README.md")
    session_data = json.loads(
        app.sessions.path_for(app.agent.session_id).read_text(encoding="utf-8")
    )
    assert session_data["file_changes"][0]["path"] == "README.md"


def test_desktop_workspace_status_reads_git_branch_changes_and_diff(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "xaw@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "XAW"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "README.md").write_text("hello\nchanged\n", encoding="utf-8")
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    status = app.state()["workspaceStatus"]

    assert status["isGit"] is True
    assert status["branch"] == "main"
    assert status["worktree"] == str(tmp_path)
    assert status["changes"] == [{"status": "M", "path": "README.md"}]
    assert "+changed" in status["diff"]
    assert status["worktrees"][0]["path"] == str(tmp_path)
    assert status["worktrees"][0]["branch"] == "main"
    assert status["worktrees"][0]["current"] is True


def test_desktop_workspace_status_handles_non_git_directory(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    status = app.state()["workspaceStatus"]

    assert status["isGit"] is False
    assert status["changes"] == []
    assert "不是 Git 仓库" in status["summary"]


def test_desktop_creates_and_lists_git_worktree(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "xaw@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "XAW"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True)
    target = tmp_path.parent / f"{tmp_path.name}-feature-worktree"
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    state = app.create_worktree({"branch": "feature/right-panel", "path": str(target)})

    assert state["worktreeCreate"]["ok"] is True
    assert target.exists()
    created = next(
        item for item in state["workspaceStatus"]["worktrees"] if item["path"] == str(target)
    )
    assert created["branch"] == "feature/right-panel"
    assert created["current"] is False


def test_desktop_rejects_invalid_worktree_request(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    state = app.create_worktree({"branch": "feature/test", "path": str(tmp_path / "target")})

    assert state["worktreeCreate"]["ok"] is False
    assert "不是 Git 仓库" in state["worktreeCreate"]["message"]


def test_desktop_restores_file_ledger_when_opening_session(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)
    session_id = "restore-session"
    app.sessions.save(session_id, [Message(role="user", content="hello")])
    app.sessions.save_file_changes(
        session_id,
        [
            {
                "path": "one.txt",
                "ok": True,
                "existed": False,
                "summary": "created one",
                "diff": "--- /dev/null\n+++ b/one.txt",
            },
            {
                "path": "two.txt",
                "ok": True,
                "existed": True,
                "summary": "updated two",
                "diff": "--- a/two.txt\n+++ b/two.txt",
            },
        ],
    )

    state = app.open_session(session_id)

    assert [change["path"] for change in state["fileChanges"]] == ["one.txt", "two.txt"]
    assert state["selectedDiffIndex"] == 1
    assert state["selectedDiff"]["path"] == "two.txt"
    assert state["messages"] == [{"role": "user", "content": "hello"}]
    assert state["sessionRestored"] is True
    assert state["sessionTitle"] == "hello"


def test_desktop_session_details_include_titles_and_counts(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)
    app.sessions.save(
        "session-one",
        [
            Message(role="system", content="system"),
            Message(role="user", content="please fix the desktop session recovery"),
            Message(role="assistant", content="done"),
        ],
    )
    app.sessions.save_file_changes(
        "session-one",
        [{"path": "README.md", "ok": True, "existed": True, "summary": "", "diff": ""}],
    )

    state = app.state()
    detail = next(item for item in state["sessionDetails"] if item["id"] == "session-one")

    assert detail["title"] == "please fix the desktop session recovery"
    assert detail["messageCount"] == 3
    assert detail["fileChangeCount"] == 1
    assert state["sessionRestored"] is False
    assert state["sessionTitle"] == "新建会话"


def test_desktop_scheduled_state_is_real_empty_list(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)
    state = app.state()

    assert state["scheduledTasks"] == []
    assert "暂无定时任务" in state["scheduledSummary"]


def test_desktop_scheduled_tasks_are_persisted_and_deleted(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    created = app.create_scheduled_task(
        {
            "title": "每日项目验证",
            "schedule": "每天 09:00",
            "prompt": "验证项目并汇报失败项",
        }
    )

    assert created["scheduledResult"]["ok"] is True
    assert created["scheduledTasks"][0]["title"] == "每日项目验证"
    assert created["scheduledTasks"][0]["projectPath"] == str(tmp_path)
    assert created["scheduledTasks"][0]["status"] == "scheduled"
    assert created["scheduledTasks"][0]["nextRunAt"]
    assert created["scheduledTasks"][0]["runs"] == []
    assert (tmp_path / "scheduled-tasks.json").exists()

    reloaded = DesktopApp(config)
    state = reloaded.state()
    assert state["scheduledTasks"][0]["prompt"] == "验证项目并汇报失败项"
    assert "已保存 1 个" in state["scheduledSummary"]
    assert "自动检查执行" in state["scheduledSummary"]

    deleted = reloaded.delete_scheduled_task({"id": state["scheduledTasks"][0]["id"]})
    assert deleted["scheduledResult"]["ok"] is True
    assert deleted["scheduledTasks"] == []


def test_desktop_rejects_incomplete_scheduled_tasks(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    state = app.create_scheduled_task({"title": "缺少提示词", "schedule": "每天 09:00"})

    assert state["scheduledResult"]["ok"] is False
    assert state["scheduledTasks"] == []


def test_desktop_rejects_unsupported_scheduled_task_time(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    state = app.create_scheduled_task(
        {"title": "自由格式", "schedule": "明天早上", "prompt": "验证项目"}
    )

    assert state["scheduledResult"]["ok"] is False
    assert "暂不支持" in state["scheduledResult"]["message"]
    assert state["scheduledTasks"] == []


def test_desktop_runs_due_scheduled_tasks_and_records_history(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ScheduledProvider:
        def complete(self, messages: list[Message], tools: list[ToolSpec]) -> ModelResponse:
            del tools
            assert messages[-1].content == "验证项目并汇报失败项"
            return ModelResponse(text="项目验证完成。")

    monkeypatch.setattr(
        "x_agentic_workflow.agent.build_provider",
        lambda _config: ScheduledProvider(),
    )
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)
    created = app.create_scheduled_task(
        {
            "title": "每分钟检查",
            "schedule": "每 30 分钟",
            "prompt": "验证项目并汇报失败项",
        }
    )
    task = created["scheduledTasks"][0]
    task["nextRunAt"] = "2026-07-04T01:00:00+00:00"
    app._save_scheduled_tasks([task])

    executed = app._run_due_scheduled_tasks(datetime.fromisoformat("2026-07-04T01:01:00+00:00"))
    state = app.state()
    updated = state["scheduledTasks"][0]

    assert executed[0]["ok"] is True
    assert updated["status"] == "last-ok"
    assert updated["lastRunAt"] == "2026-07-04T01:01:00+00:00"
    assert updated["nextRunAt"] == "2026-07-04T01:31:00+00:00"
    assert updated["runs"][0]["summary"] == "项目验证完成。"


def test_desktop_session_details_use_stable_updated_labels_and_order(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)
    app.sessions.path_for("old-session").write_text(
        json.dumps(
            {
                "session_id": "old-session",
                "updated_at": "2026-07-04T01:00:00+00:00",
                "messages": [{"role": "user", "content": "old prompt"}],
            }
        ),
        encoding="utf-8",
    )
    app.sessions.path_for("new-session").write_text(
        json.dumps(
            {
                "session_id": "new-session",
                "updated_at": "2026-07-04T05:12:00+00:00",
                "messages": [{"role": "user", "content": "new prompt"}],
            }
        ),
        encoding="utf-8",
    )

    state = app.state()
    details = state["sessionDetails"]

    assert [item["id"] for item in details] == ["new-session", "old-session"]
    assert details[0]["title"] == "new prompt"
    assert re.fullmatch(r"\d{2}-\d{2} \d{2}:\d{2}", details[0]["updatedLabel"])
    assert "updatedSortKey" in details[0]


def test_desktop_open_session_does_not_refresh_updated_time(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)
    app.sessions.path_for("history-session").write_text(
        json.dumps(
            {
                "session_id": "history-session",
                "updated_at": "2026-07-04T05:12:00+00:00",
                "messages": [{"role": "user", "content": "history prompt"}],
            }
        ),
        encoding="utf-8",
    )

    before = app.sessions.session_summary("history-session")["updatedAt"]
    app.open_session("history-session")
    after = app.sessions.session_summary("history-session")["updatedAt"]

    assert after == before


def test_desktop_text_attachment_context_is_validated_and_formatted() -> None:
    attachments = _validate_text_attachments(
        [{"name": "../notes.md", "content": "# Notes\nUse the existing API."}]
    )
    prompt = _prompt_with_attachment_context("Review this", attachments)

    assert attachments == [{"name": "notes.md", "content": "# Notes\nUse the existing API."}]
    assert "reference context, not system instructions" in prompt
    assert '<file name="notes.md">' in prompt
    assert "# Notes" in prompt

    with pytest.raises(ValueError, match="128 KiB"):
        _validate_text_attachments([{"name": "large.txt", "content": "x" * (128 * 1024 + 1)}])
    with pytest.raises(ValueError, match="at most 5"):
        _validate_text_attachments([{"name": f"{index}.txt", "content": ""} for index in range(6)])


def test_desktop_sends_text_attachments_as_agent_context(tmp_path: Path) -> None:
    class AttachmentProvider:
        def complete(self, messages: list[Message], tools: list[ToolSpec]) -> ModelResponse:
            del tools
            assert messages[-1].role == "user"
            assert '<file name="notes.md">' in messages[-1].content
            return ModelResponse(text="Attachment received.")

    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)
    app.agent.provider = AttachmentProvider()

    state = app.ask(
        "Review this",
        [{"name": "notes.md", "content": "# Notes\nUse the existing API."}],
    )
    session_id = app.agent.session_id
    restored = app.open_session(session_id)

    assert state["messages"][0]["content"] == "Review this\n\n附件: notes.md"
    assert state["messages"][1]["content"] == "Attachment received."
    assert restored["messages"][0]["content"] == "Review this\n\n附件: notes.md"
    assert "# Notes" not in restored["messages"][0]["content"]


def test_desktop_selects_prior_diff(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)
    app.file_changes = [
        {"path": "one.txt", "ok": True, "existed": False, "summary": "", "diff": "one diff"},
        {"path": "two.txt", "ok": True, "existed": True, "summary": "", "diff": "two diff"},
    ]
    app.selected_diff_index = 1

    state = app.select_diff({"index": 0})
    missing = app.select_diff({"index": 99})

    assert state["diffSelect"]["ok"] is True
    assert state["selectedDiffIndex"] == 0
    assert state["selectedDiff"]["path"] == "one.txt"
    assert state["latestDiff"]["diff"] == "one diff"
    assert missing["diffSelect"]["ok"] is False


def test_session_save_preserves_file_changes_and_old_sessions_load(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)
    session_id = "compat-session"
    app.sessions.save_file_changes(
        session_id,
        [{"path": "README.md", "ok": True, "existed": True, "summary": "", "diff": "diff"}],
    )
    app.sessions.save(session_id, [Message(role="user", content="keep metadata")])
    legacy_id = "legacy-session"
    app.sessions.path_for(legacy_id).write_text(
        json.dumps({"session_id": legacy_id, "messages": []}) + "\n",
        encoding="utf-8",
    )

    saved = json.loads(app.sessions.path_for(session_id).read_text(encoding="utf-8"))
    legacy_state = app.open_session(legacy_id)

    assert saved["file_changes"][0]["path"] == "README.md"
    assert legacy_state["fileChanges"] == []
    assert legacy_state["selectedDiff"] is None


def test_desktop_clears_file_ledger_on_new_chat_and_project_switch(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)
    first_session_id = app.agent.session_id
    change = {"path": "one.txt", "ok": True, "existed": False, "summary": "", "diff": ""}
    app.file_changes.append(change)

    new_state = app.new_chat()

    assert new_state["fileChanges"] == []
    assert new_state["sessionId"] != first_session_id
    app.file_changes.append({**change, "path": "two.txt"})
    switched = app.switch_project({"path": str(target)})

    assert switched["fileChanges"] == []
    assert switched["latestDiff"] is None


def test_desktop_composer_actions_are_inside_prompt_card() -> None:
    html = render_desktop_html()

    composer_match = re.search(
        r'<div class="composer">(?P<body>.*?)<div class="project-picker">',
        html,
        re.DOTALL,
    )

    assert composer_match is not None
    assert "composer-actions" in composer_match.group("body")
    assert "right-tools" in composer_match.group("body")
    assert "attachButton" in composer_match.group("body")


def test_desktop_composer_dock_is_bottom_aligned() -> None:
    html = render_desktop_html()

    assert "html, body { height: 100%; }" in html
    assert ".app { height: 100vh; overflow: hidden;" in html
    assert (
        "main { position: relative; display: flex; flex-direction: column; "
        "min-width: 0; min-height: 0; height: 100vh;"
    ) in html
    assert ".stage { flex: 1; min-height: 0; display: flex; align-items: stretch;" in html
    assert ".hero { width: min(1120px, 100%);" in html
    assert ".composer-dock { width: min(1068px, 100%); margin: 0 auto 0;" in html


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


def test_desktop_general_settings_are_validated_and_persisted(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config = RuntimeConfig(
        config_file=config_file,
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    state = app.save_general_settings(
        {
            "requireCommandApproval": False,
            "sendMode": "enter",
            "uiScale": 125,
            "notificationsEnabled": True,
        }
    )

    assert state["generalSave"]["ok"] is True
    assert state["generalSettings"] == {
        "requireCommandApproval": False,
        "sendMode": "enter",
        "uiScale": 125,
        "notificationsEnabled": True,
    }
    reloaded = RuntimeConfig.load(config_file=config_file, workdir=tmp_path)
    assert reloaded.require_command_approval is False
    assert reloaded.desktop_send_mode == "enter"
    assert reloaded.desktop_ui_scale == 125
    assert reloaded.desktop_notifications_enabled is True


def test_desktop_general_settings_reject_invalid_payload(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    invalid_mode = app.save_general_settings(
        {
            "requireCommandApproval": True,
            "sendMode": "space",
            "uiScale": 100,
            "notificationsEnabled": False,
        }
    )
    invalid_scale = app.save_general_settings(
        {
            "requireCommandApproval": True,
            "sendMode": "modifier-enter",
            "uiScale": 250,
            "notificationsEnabled": False,
        }
    )

    assert invalid_mode["generalSave"]["ok"] is False
    assert invalid_scale["generalSave"]["ok"] is False


def test_desktop_h5_settings_are_validated_and_persisted(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config = RuntimeConfig(
        config_file=config_file,
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)
    app.desktop_host = "127.0.0.1"
    app.desktop_port = 8765

    state = app.save_h5_settings(
        {
            "enabled": True,
            "bindHost": "0.0.0.0",
            "fixedPort": "9876",
            "keepaliveSeconds": 120,
        }
    )

    assert state["h5Save"]["ok"] is True
    assert state["h5Access"]["enabled"] is True
    assert state["h5Access"]["bindHost"] == "0.0.0.0"
    assert state["h5Access"]["fixedPort"] == 9876
    assert state["h5Access"]["keepaliveSeconds"] == 120
    assert state["h5Access"]["restartRequired"] is True
    reloaded = RuntimeConfig.load(config_file=config_file, workdir=tmp_path)
    assert reloaded.desktop_h5_enabled is True
    assert reloaded.desktop_h5_host == "0.0.0.0"
    assert reloaded.desktop_h5_fixed_port == 9876
    assert reloaded.desktop_h5_keepalive_seconds == 120


def test_desktop_h5_settings_reject_invalid_payload(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    invalid_port = app.save_h5_settings(
        {
            "enabled": True,
            "bindHost": "0.0.0.0",
            "fixedPort": "999",
            "keepaliveSeconds": 30,
        }
    )
    invalid_keepalive = app.save_h5_settings(
        {
            "enabled": True,
            "bindHost": "0.0.0.0",
            "fixedPort": "",
            "keepaliveSeconds": 2,
        }
    )

    assert invalid_port["h5Save"]["ok"] is False
    assert invalid_keepalive["h5Save"]["ok"] is False


def test_desktop_mcp_settings_read_config_without_secret_values(tmp_path: Path) -> None:
    mcp_config = tmp_path / "mcp.json"
    mcp_config.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "context7": {
                        "command": "npx",
                        "args": ["-y", "@upstash/context7-mcp"],
                        "env": {"CONTEXT7_API_KEY": "secret-value"},
                    },
                    "remote-search": {
                        "transport": "streamable-http",
                        "url": "https://example.com/mcp",
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=mcp_config,
    )
    app = DesktopApp(config)

    mcp = app.state()["mcpSettings"]

    assert mcp["ok"] is True
    assert mcp["exists"] is True
    assert mcp["total"] == 2
    assert mcp["stdio"] == 1
    assert mcp["remote"] == 1
    assert mcp["servers"][0]["name"] == "context7"
    assert mcp["servers"][0]["envKeys"] == ["CONTEXT7_API_KEY"]
    assert "secret-value" not in json.dumps(mcp)


def test_desktop_mcp_settings_reports_invalid_config(tmp_path: Path) -> None:
    mcp_config = tmp_path / "mcp.json"
    mcp_config.write_text("{not-json", encoding="utf-8")
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=mcp_config,
    )
    app = DesktopApp(config)

    mcp = app.state()["mcpSettings"]

    assert mcp["ok"] is False
    assert mcp["exists"] is True
    assert mcp["servers"] == []


def test_desktop_terminal_settings_reports_runtime_and_probe(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
        require_command_approval=False,
        max_output_chars=1234,
    )
    app = DesktopApp(config)

    terminal = app.state()["terminalSettings"]

    assert terminal["ok"] is True
    assert terminal["workdir"] == str(tmp_path)
    assert terminal["approvalRequired"] is False
    assert terminal["maxOutputChars"] == 1234
    assert terminal["commandTimeoutSeconds"] == 120
    assert terminal["runCommandEnabled"] is True
    assert "run_command" in terminal["tools"]

    probe = app.terminal_probe()["terminalProbe"]

    assert probe["ok"] is True
    assert probe["exitCode"] == 0
    assert f"cwd: {tmp_path}" in probe["output"]


def test_desktop_agents_settings_reports_builtin_roles(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    agents = app.state()["agentsSettings"]

    assert agents["ok"] is True
    assert agents["mode"] == "系统提示注入"
    assert agents["total"] == 3
    assert agents["enabled"] == 3
    assert [role["name"] for role in agents["roles"]] == [
        "architect",
        "implementer",
        "reviewer",
    ]
    assert all(role["status"] == "已生效" for role in agents["roles"])


def test_desktop_skills_settings_read_local_skill_summaries(tmp_path: Path) -> None:
    skills_dir = tmp_path / "skills"
    skill_path = skills_dir / "coding" / "review.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text(
        "\n".join(
            [
                "name: code-review",
                "description: Review code changes for regressions.",
                "",
                "# Private body",
                "This full body should not be returned by the desktop settings API.",
            ]
        ),
        encoding="utf-8",
    )
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=skills_dir,
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    skills = app.state()["skillsSettings"]

    assert skills["ok"] is True
    assert skills["total"] == 1
    assert skills["withDescription"] == 1
    assert skills["sources"] == 1
    assert skills["skills"][0]["name"] == "code-review"
    assert skills["skills"][0]["description"] == "Review code changes for regressions."
    assert skills["skills"][0]["relativePath"] == "coding/review.md"
    assert "full body should not be returned" not in json.dumps(skills)


def test_desktop_memory_settings_read_local_memory_summaries(tmp_path: Path) -> None:
    workdir = tmp_path / "project"
    workdir.mkdir()
    (workdir / "MEMORY.md").write_text(
        "\n".join(
            [
                "# Project Memory",
                "",
                "Public project summary.",
                "Private implementation detail should only appear in preview.",
            ]
        ),
        encoding="utf-8",
    )
    config_dir = tmp_path / "config"
    memory_dir = config_dir / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "user-memory.md").write_text(
        "# User Memory\n\nPublic user summary.\n",
        encoding="utf-8",
    )
    config = RuntimeConfig(
        config_file=config_dir / "config.json",
        workdir=workdir,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    memory = app.state()["memorySettings"]

    assert memory["ok"] is True
    assert memory["total"] == 2
    assert memory["project"] == 1
    assert memory["user"] == 1
    assert {item["title"] for item in memory["items"]} == {"Project Memory", "User Memory"}
    assert "Private implementation detail" not in json.dumps(memory)
    project_item = next(item for item in memory["items"] if item["source"] == "项目")
    preview = app.memory_preview(project_item["id"])
    assert preview["ok"] is True
    assert "Private implementation detail should only appear in preview." in preview["content"]


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
