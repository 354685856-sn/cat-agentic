import hashlib
import json
import re
import socket
import subprocess
import threading
from datetime import datetime, timedelta
from http.cookiejar import CookieJar
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen

import pytest

import x_agentic_workflow.desktop as desktop_module
from x_agentic_workflow.config import RuntimeConfig
from x_agentic_workflow.desktop import (
    DesktopApp,
    _create_server,
    _handler_for,
    _project_sessions_dir,
    _prompt_with_attachment_context,
    _validate_project,
    _validate_text_attachments,
    render_desktop_html,
    render_h5_access_denied_html,
)
from x_agentic_workflow.mcp import project_private_mcp_file, project_shared_mcp_file
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
    assert '<div class="app inspector-collapsed context-idle">' in html
    assert 'id="inspectorAdd"' not in html
    assert 'id="inspectorView"' not in html
    assert 'id="closeSettings"' in html
    assert 'id="dismissTopbar"' not in html
    assert 'id="restoreTopbar"' not in html
    assert 'id="workspaceHeader"' in html
    assert 'id="sidebarOpen"' in html
    assert "$('sidebarOpen').addEventListener('click'" in html
    assert 'id="taskRunPanel"' in html
    assert 'id="taskRunEyebrow"' in html
    assert 'id="taskRunTitle"' in html
    assert 'id="taskRunModelName"' in html
    assert 'class="task-run-model-chip"' in html
    assert 'id="projectPickerToggle"' in html
    assert 'id="taskHistoryHeading"' in html
    assert 'class="hero-logo"' not in html
    assert "app.classList.toggle('context-idle', !hasTaskContext)" in html
    assert "app.classList.toggle('code-context', hasCodeContext)" in html
    assert ".app.context-active:not(.code-context).inspector-collapsed:not(.settings-open)" in html
    assert "app.classList.toggle('task-running', running)" in html
    assert "composer-engaged" in html
    assert "body.theme-dark .app:not(.settings-open) .project-header," in html
    assert "closeSettings').hidden = !settings" in html
    assert ".app { grid-template-columns: minmax(260px, 388px) minmax(0, 1fr)" in html
    assert "min-width: 520px" not in html
    assert ".app.settings-open { grid-template-columns: 282px minmax(0, 1fr) 0; }" in html
    assert (
        ".app.settings-open .settings-layout { "
        "grid-template-columns: 181px minmax(0, 1fr); }"
    ) in html
    assert ".app.settings-open .topbar { height: 44px; }" in html
    assert ".workspace-header-main" in html
    assert "settings-result provider-result" in html
    assert 'data-language="en"' in html
    assert 'data-language="zh-CN"' in html
    assert 'data-language="zh-TW"' not in html
    assert 'data-language="ja"' not in html
    assert 'data-language="ko"' not in html
    assert "I18N['zh-TW']" not in html
    assert "I18N.ja" not in html
    assert "I18N.ko" not in html
    assert "desktopLanguageCoverage" in html
    assert "Workbench surface consolidation" in html
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
    assert "/api/h5/pairing/create" in html
    assert "/api/h5/access/revoke" in html
    assert "/api/terminal" in html
    assert "/api/terminal/probe" in html
    assert "/api/mcp" in html
    assert "/api/agents" in html
    assert "/api/skills" in html
    assert "/api/skills/preview" in html
    assert "/api/memory" in html
    assert "/api/memory/preview" in html
    assert "/api/plugins" in html
    assert "/api/plugins/preview" in html
    assert "/api/marketplace" in html
    assert 'id="marketplaceReview"' in html
    assert 'id="marketplaceContentHash"' in html
    assert "marketplaceReviewBoundary" in html
    assert "/api/computer-use" in html
    assert "/api/computer-use/open-settings" in html
    assert "/api/token-usage" in html
    assert "/api/trace" in html
    assert "/api/trace/preview" in html
    assert "/api/trace/open-directory" in html
    assert "/api/diagnostics" in html
    assert "/api/diagnostics/export" in html
    assert "/api/update-check" in html
    assert 'id="pluginsSettingsPanel"' in html
    assert 'id="computerUseSettingsPanel"' in html
    assert 'id="computerUseResult"' in html
    assert 'id="computerUseReadiness"' in html
    assert 'class="computer-use-groups"' in html
    assert "computerEnvironmentGroup" in html
    assert "computerPermissionsGroup" in html
    assert 'id="tokenUsageSettingsPanel"' in html
    assert 'id="traceSettingsPanel"' in html
    assert 'id="openTraceDirectory"' in html
    assert 'id="tracePreview"' in html
    assert 'id="diagnosticsSettingsPanel"' in html
    assert 'id="exportDiagnosticsReport"' in html
    assert 'data-settings-view="plugins"' in html
    assert 'data-settings-view="computerUse"' in html
    assert 'data-settings-view="tokenUsage"' in html
    assert 'data-settings-view="trace"' in html
    assert 'data-settings-view="diagnostics"' in html
    assert 'data-settings-view="about"' in html
    assert 'id="aboutSettingsPanel"' in html
    assert 'id="checkForUpdates"' in html
    assert 'id="aboutVersion">0.17.0<' in html
    assert 'data-settings-view="general"' in html
    assert 'data-settings-view="h5"' in html
    assert 'data-settings-view="terminal"' in html
    assert 'data-settings-view="mcp"' in html
    assert 'data-settings-view="agents"' in html
    assert 'data-settings-view="skills"' in html
    assert 'data-settings-view="memory"' in html
    assert 'id="h5SettingsPanel"' in html
    assert 'id="h5ConnectionSection"' in html
    assert 'class="h5-service-bar"' in html
    assert 'class="h5-guide"' in html
    assert 'id="saveH5Settings"' in html
    assert 'id="createH5Pairing"' in html
    assert 'id="revokeH5Access"' in html
    assert 'id="copyH5Pairing"' in html
    assert 'id="h5PairingUrl"' in html
    assert "保存 H5 设置" in html
    assert 'id="terminalSettingsPanel"' in html
    assert 'id="refreshTerminalSettings"' in html
    assert 'id="runTerminalProbe"' in html
    assert "探针输出" in html
    assert 'id="mcpSettingsPanel"' in html
    assert 'id="openMcpAddView"' in html
    assert 'id="backMcpList"' in html
    assert 'id="saveMcpServer"' in html
    assert 'id="mcpTargetProject"' in html
    assert 'data-mcp-scope="project-private"' in html
    assert 'data-mcp-scope="project-shared"' in html
    assert 'data-mcp-scope="user"' in html
    assert "/api/mcp/add" in html
    assert "/api/mcp/toggle" in html
    assert "/api/mcp/delete" in html
    assert "连接自定义 MCP" in html
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
    assert "资源管理器" in html
    assert "记忆来源" in html
    assert 'id="requireCommandApproval"' in html
    assert 'id="notificationsEnabled"' in html
    assert 'id="uiScale"' in html
    assert 'data-send-mode="enter"' in html
    assert 'data-theme="pure"' in html
    assert "body.theme-dark" in html
    assert "applyTheme" in html
    assert "const I18N" in html
    assert "markGeneralDirty" in html
    assert "applyStaticTranslations" in html
    assert ".terminal-summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }" in html
    assert ".agents-hero { grid-template-columns: minmax(0, 1fr); padding: 20px 18px; }" in html
    assert ".memory-explorer { grid-template-columns: minmax(0, 1fr); min-height: 0; }" in html
    assert ".segmented.five .segment-option:last-child" in html
    assert ".app.settings-open .segmented.four" in html
    assert "Save General Settings" in html
    assert 'id="replyLanguage"' in html
    assert 'data-output-style="review"' in html
    assert 'data-permission-mode="skip"' in html
    assert 'id="thinkingEnabled"' in html
    assert 'id="autoMemoryEnabled"' in html
    assert 'id="traceEnabled"' in html
    assert 'data-network-mode="manual"' in html
    assert 'id="aiRequestTimeoutSeconds"' in html
    assert 'id="webfetchPreflightSkip"' in html
    assert 'data-web-search-provider="tavily"' in html
    assert 'id="tavilyApiKeyEnv"' in html
    assert 'data-data-dir-mode="portable"' in html
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
    assert "providerList" in html
    assert "providerModal" in html
    assert "providerPresetPills" in html
    assert "/api/provider/add" in html
    assert "/api/provider/select" in html
    assert "/api/provider/update" in html
    assert "/api/provider/delete" in html
    assert "https://api.openai.com/v1" in html
    assert "gpt-4.1" in html
    assert "providerSubmitting" in html
    assert "runProviderAction" in html
    assert "添加服务商" in html
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
    assert 'id="tokenRangeTabs"' in html
    assert "#tokenUsageResult.bad { color: #b42318; }" in html
    assert "#tokenUsageList .memory-card { box-sizing: border-box" in html
    assert "#tokenUsageList .memory-title" in html
    assert 'data-token-days="30"' in html
    assert 'data-token-days="90"' in html
    assert 'data-token-days="365" aria-pressed="true"' in html
    assert "button.setAttribute('aria-pressed', String(active))" in html
    assert 'id="tokenHeatmapGrid"' in html
    assert 'id="tokenMethodNote"' in html
    assert 'id="tokenTodayTokens"' in html
    assert "tokenState.ok === false" in html
    assert "/api/token-usage?days=${selectedTokenUsageDays}" in html
    assert html.index('class="composer-actions"') < html.index('class="project-picker"')


def test_desktop_home_has_crow5_inspired_real_quick_task_controls() -> None:
    html = render_desktop_html()

    assert 'class="activity-rail"' in html
    assert 'class="session-sidebar"' in html
    assert 'aria-label="工作区导航"' in html
    assert ".activity-rail {" in html
    assert ".session-sidebar {" in html
    assert 'id="homeQuickTasks"' in html
    assert 'data-quick-task="inspect"' in html
    assert 'data-quick-task="tests"' in html
    assert 'data-quick-task="explain"' in html
    assert "function applyQuickTask(task)" in html
    assert "$('prompt').focus()" in html
    assert ".app:not(.settings-open) .home-quick-task" in html
    assert "box-shadow: 0 3px 0" in html
    assert ".home-quick-task:active" in html
    assert 'data-theme="ocean"' in html
    assert 'data-theme="comic"' in html
    assert "body.theme-ocean" in html
    assert "body.theme-comic" in html
    assert (
        "body.theme-ocean .app:not(.settings-open) .composer textarea { background: #10263a;"
        in html
    )
    assert "body.theme-ocean #homeProviderEndpoint { border: 0; background: transparent;" in html
    assert (
        "@media (max-width: 860px) { .app:not(.settings-open) > aside:first-child "
        "{ display: none; }"
        in html
    )
    assert ".app:not(.settings-open) .sidebar-tool-btn" in html
    assert ".activity-rail #newChat" in html
    assert "#inspectorToggle {\n      box-shadow: 0 2px 0 rgba(7,35,59,.78)" in html
    assert ".app.context-idle:not(.composer-engaged) #validateProject { display: none; }" in html
    assert ".app.context-idle:not(.composer-engaged) .model { display: none; }" not in html
    assert 'id="composerSkills"' in html
    assert "document.querySelector('[data-settings-view=\"skills\"]')?.click()" in html
    assert (
        "body.theme-ocean .app:not(.settings-open) .round,\n"
        "    body.theme-ocean .app:not(.settings-open) .pill"
        in html
    )
    assert (
        "body.theme-ocean .app:not(.settings-open) .model[data-family] "
        "{ background: #123653;"
        in html
    )
    assert (
        "body.theme-ocean .app:not(.settings-open) .project-picker "
        "{ background: #0d2235;"
        in html
    )
    assert (
        "body.theme-ocean .app.settings-open { grid-template-columns: minmax(0, 1fr) 0;"
        in html
    )
    assert "body.theme-ocean .app.settings-open > aside:first-child { display: none; }" in html
    assert "body.theme-ocean .app.settings-open .settings-layout { background: #091827;" in html
    assert "body.theme-ocean .app.settings-open .segment-option { background: #10263a;" in html
    assert "body.theme-ocean .app.settings-open .field select { background: #10263a;" in html
    assert "body.theme-ocean .app.settings-open .mcp-stat { background: #10263a;" in html
    assert "body.theme-ocean .app.settings-open .mcp-empty { background: #10263a;" in html
    assert (
        "body.theme-ocean .app.settings-open .marketplace-source-select "
        "{ background: #10263a;"
        in html
    )
    assert "body.theme-ocean .app.settings-open .token-range-button { background: #123653;" in html
    assert "body.theme-ocean .app.settings-open .about-card { background: #10263a;" in html
    assert "body.theme-ocean .app.settings-open .plugin-preview-section," in html
    assert "body.theme-ocean .app.settings-open .skill-empty," in html
    assert "body.theme-ocean .app.settings-open .marketplace-section," in html
    assert "body.theme-ocean .app.settings-open .token-summary-grid," in html
    assert "body.theme-ocean .app.settings-open .token-heatmap-card { background: #10263a;" in html
    assert "body.theme-ocean .app.settings-open .about-logo," in html
    assert "body.theme-ocean .app.settings-open .about-update-panel { background: #0d2235;" in html
    assert "body.theme-ocean .app.settings-open .h5-service-bar," in html
    assert "body.theme-ocean .app.settings-open .step-btn { background: #123653;" in html
    assert (
        "body.theme-ocean .app.settings-open .provider-save-status { background: #123653;"
        in html
    )
    assert (
        'body.theme-ocean .app.settings-open .scale-row input[type="range"] '
        "{ accent-color: #78cceb;" in html
    )
    assert "body.theme-ocean .app.settings-open .agents-hero," in html
    assert "body.theme-ocean .app.settings-open .memory-explorer," in html
    assert "body.theme-ocean .app.settings-open .computer-use-readiness," in html
    assert "box-shadow: 0 2px 0 rgba(3,21,35,.86)" in html
    assert 'id="homeProviderEndpoint"' in html
    assert 'id="homeConnectionTest"' in html
    assert "Run this project\\'s tests" in html
    assert "Explain the current project\\'s core structure" in html


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
    assert 'id="model" type="button" data-family="default"' in composer_match.group("body")
    assert 'id="modelLabel">model</span>' in composer_match.group("body")
    assert "function modelFamily(model, provider)" in html
    assert "modelButton.dataset.family = modelFamily(state.model, state.provider)" in html
    assert "document.querySelector('[data-settings-view=\"provider\"]')?.click()" in html


def test_desktop_mobile_chat_remains_scrollable_and_model_controls_fit() -> None:
    html = render_desktop_html()

    assert (
        ".app.task-running:not(.settings-open) { "
        "grid-template-columns: minmax(0, 1fr); }"
    ) in html
    assert ".stage { padding: 0; overflow-x: hidden; overflow-y: auto;" in html
    assert ".hero { width: 100%; height: auto; min-height: 100%;" in html
    assert (
        ".composer .composer-actions { display: grid; "
        "grid-template-columns: minmax(0, 1fr);"
    ) in html
    assert ".right-tools { width: 100%; min-width: 0; margin-left: 0; display: grid;" in html
    assert ".model { width: 100%; max-width: none; min-width: 0; }" in html
    assert '#validateProject::before { content: "✓";' in html


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


def test_desktop_provider_profiles_add_and_select_without_secret_value(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    added = app.add_provider_profile(
        {
            "presetId": "deepseek",
            "displayName": "DeepSeek",
            "provider": "anthropic",
            "protocolLabel": "DeepSeek",
            "model": "deepseek-v4-pro",
            "baseUrl": "https://api.deepseek.com/anthropic",
            "apiKeyEnv": "ANTHROPIC_AUTH_TOKEN",
            "toolSearchEnabled": True,
        }
    )

    saved = (tmp_path / "config.json").read_text(encoding="utf-8")
    assert added["providerSave"]["ok"] is True
    assert added["provider"] == "anthropic"
    assert added["model"] == "deepseek-v4-pro"
    assert "provider_profiles" in saved
    assert "ANTHROPIC_AUTH_TOKEN" in saved
    assert "sk-" not in saved
    active = next(profile for profile in added["providerProfiles"] if profile["active"])
    selected = app.select_provider_profile({"id": active["id"]})
    assert selected["providerSave"]["ok"] is True

    updated = app.update_provider_profile(
        {
            "id": active["id"],
            "displayName": "DeepSeek Local",
            "provider": "anthropic",
            "protocolLabel": "DeepSeek",
            "model": "deepseek-v4-flash",
            "baseUrl": "https://api.deepseek.com/anthropic",
            "apiKeyEnv": "ANTHROPIC_AUTH_TOKEN",
            "toolSearchEnabled": False,
        }
    )
    assert updated["providerSave"]["ok"] is True
    assert updated["model"] == "deepseek-v4-flash"
    delete_active = app.delete_provider_profile({"id": active["id"]})
    assert delete_active["providerSave"]["ok"] is False
    assert "默认服务商不能删除" in delete_active["providerSave"]["message"]


def test_desktop_provider_presets_include_openai_official_endpoint(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    presets = app.state()["providerPresets"]
    openai = next(preset for preset in presets if preset["id"] == "openai")

    assert openai["displayName"] == "OpenAI"
    assert openai["provider"] == "openai-compatible"
    assert openai["baseUrl"] == "https://api.openai.com/v1"
    assert openai["apiKeyEnv"] == "OPENAI_API_KEY"

    added = app.add_provider_profile({"presetId": "openai"})

    assert added["providerSave"]["ok"] is True
    assert added["provider"] == "openai-compatible"
    assert added["model"] == "gpt-4.1"
    assert added["providerProfiles"][0]["displayName"] == "OpenAI"


def test_desktop_add_mcp_server_routes_by_scope(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    state = app.add_mcp_server(
        {
            "name": "chrome-devtools",
            "scope": "project-private",
            "transport": "stdio",
            "command": "npx",
            "args": ["chrome-devtools-mcp@latest"],
            "envKeys": ["CHROME_TOKEN"],
        }
    )

    private_file = project_private_mcp_file(tmp_path, tmp_path)
    saved = json.loads(private_file.read_text(encoding="utf-8"))
    assert state["mcpAdd"]["ok"] is True
    assert state["mcpSettings"]["workdir"] == str(tmp_path)
    assert state["mcpSettings"]["servers"][0]["sourceScope"] == "project-private"
    assert state["mcpSettings"]["servers"][0]["configFile"] == str(private_file)
    assert saved["mcpServers"]["chrome-devtools"]["command"] == "npx"
    assert saved["mcpServers"]["chrome-devtools"]["args"] == ["chrome-devtools-mcp@latest"]
    assert saved["mcpServers"]["chrome-devtools"]["env"] == {"CHROME_TOKEN": ""}

    shared = app.add_mcp_server(
        {
            "name": "repo-docs",
            "scope": "project-shared",
            "transport": "streamable-http",
            "url": "https://example.com/mcp",
        }
    )
    user = app.add_mcp_server(
        {
            "name": "global-search",
            "scope": "user",
            "transport": "sse",
            "url": "https://search.example.com/sse",
        }
    )
    shared_file = project_shared_mcp_file(tmp_path)
    user_file = tmp_path / "mcp.json"

    assert shared["mcpAdd"]["ok"] is True
    assert user["mcpAdd"]["ok"] is True
    assert "repo-docs" in json.loads(shared_file.read_text(encoding="utf-8"))["mcpServers"]
    assert "global-search" in json.loads(user_file.read_text(encoding="utf-8"))["mcpServers"]

    disabled = app.toggle_mcp_server(
        {"name": "chrome-devtools", "configFile": str(private_file), "enabled": False}
    )
    saved_disabled = json.loads(private_file.read_text(encoding="utf-8"))
    assert disabled["mcpSave"]["ok"] is True
    assert saved_disabled["mcpServers"]["chrome-devtools"]["enabled"] is False
    private_server = next(
        server
        for server in disabled["mcpSettings"]["servers"]
        if server["name"] == "chrome-devtools"
    )
    assert private_server["status"] == "Disabled"

    deleted = app.delete_mcp_server({"name": "chrome-devtools", "configFile": str(private_file)})
    saved_deleted = json.loads(private_file.read_text(encoding="utf-8"))
    assert deleted["mcpSave"]["ok"] is True
    assert "chrome-devtools" not in saved_deleted["mcpServers"]


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
            "theme": "classic",
            "language": "zh-CN",
            "replyLanguage": "zh-CN",
            "outputStyle": "review",
            "permissionMode": "ask",
            "thinkingEnabled": False,
            "autoMemoryEnabled": True,
            "traceEnabled": False,
            "requireCommandApproval": False,
            "sendMode": "enter",
            "uiScale": 125,
            "notificationsEnabled": True,
            "networkMode": "manual",
            "manualProxy": "http://127.0.0.1:7890",
            "aiRequestTimeoutSeconds": 900,
            "webfetchPreflightSkip": False,
            "webSearchProvider": "brave",
            "tavilyApiKeyEnv": "TAVILY_API_KEY",
            "braveApiKeyEnv": "BRAVE_SEARCH_API_KEY",
            "dataDirMode": "portable",
            "portableDataDir": str(tmp_path / "portable-data"),
        }
    )

    assert state["generalSave"]["ok"] is True
    assert state["generalSettings"]["theme"] == "classic"
    assert state["generalSettings"]["language"] == "zh-CN"
    assert state["generalSettings"]["replyLanguage"] == "zh-CN"
    assert state["generalSettings"]["outputStyle"] == "review"
    assert state["generalSettings"]["thinkingEnabled"] is False
    assert state["generalSettings"]["autoMemoryEnabled"] is True
    assert state["generalSettings"]["traceEnabled"] is False
    assert state["generalSettings"]["requireCommandApproval"] is False
    assert state["generalSettings"]["sendMode"] == "enter"
    assert state["generalSettings"]["uiScale"] == 125
    assert state["generalSettings"]["notificationsEnabled"] is True
    assert state["generalSettings"]["networkMode"] == "manual"
    assert state["generalSettings"]["manualProxy"] == "http://127.0.0.1:7890"
    assert state["generalSettings"]["aiRequestTimeoutSeconds"] == 900
    assert state["generalSettings"]["webfetchPreflightSkip"] is False
    assert state["generalSettings"]["webSearchProvider"] == "brave"
    assert state["generalSettings"]["dataDirMode"] == "portable"
    reloaded = RuntimeConfig.load(config_file=config_file, workdir=tmp_path)
    assert reloaded.desktop_theme == "classic"
    assert reloaded.desktop_language == "zh-CN"
    assert reloaded.desktop_reply_language == "zh-CN"
    assert reloaded.desktop_output_style == "review"
    assert reloaded.desktop_thinking_enabled is False
    assert reloaded.desktop_auto_memory_enabled is True
    assert reloaded.desktop_trace_enabled is False
    assert reloaded.require_command_approval is False
    assert reloaded.desktop_send_mode == "enter"
    assert reloaded.desktop_ui_scale == 125
    assert reloaded.desktop_notifications_enabled is True
    assert reloaded.desktop_network_mode == "manual"
    assert reloaded.desktop_manual_proxy == "http://127.0.0.1:7890"
    assert reloaded.ai_request_timeout_seconds == 900
    assert reloaded.desktop_web_search_provider == "brave"
    assert reloaded.desktop_data_dir_mode == "portable"


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
    invalid_display_language = app.save_general_settings(
        {
            "requireCommandApproval": True,
            "sendMode": "modifier-enter",
            "uiScale": 100,
            "notificationsEnabled": False,
            "language": "ja",
            "replyLanguage": "ja",
        }
    )

    assert invalid_mode["generalSave"]["ok"] is False
    assert invalid_scale["generalSave"]["ok"] is False
    assert invalid_display_language["generalSave"]["ok"] is False


def test_desktop_legacy_partial_display_languages_fall_back_but_reply_language_is_preserved(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps({"desktop_language": "ja", "desktop_reply_language": "ja"}),
        encoding="utf-8",
    )

    loaded = RuntimeConfig.load(config_file=config_file, workdir=tmp_path)

    assert loaded.desktop_language == "zh-CN"
    assert loaded.desktop_reply_language == "ja"


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


def test_desktop_h5_pairing_is_one_time_and_revocable(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config = RuntimeConfig(
        config_file=config_file,
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
        desktop_h5_enabled=True,
        desktop_h5_host="0.0.0.0",
    )
    config.save()
    app = DesktopApp(config)
    app.desktop_host = "0.0.0.0"
    app.desktop_port = 8765

    pairing = app.create_h5_pairing()

    assert pairing["h5Pairing"]["ok"] is True
    pairing_url = urlparse(pairing["h5Pairing"]["url"])
    token = parse_qs(pairing_url.query)["h5_token"][0]
    assert token
    assert token not in config_file.read_text(encoding="utf-8")
    assert app._h5_pairing_digest != token
    assert pairing["h5Access"]["pairingPending"] is True
    assert pairing["h5Access"]["activeSessions"] == 0

    session_token = app.consume_h5_pairing(token)

    assert session_token
    assert app.consume_h5_pairing(token) is None
    assert app.validate_h5_session(session_token) is True
    assert app._h5_access_state()["pairingPending"] is False
    assert app._h5_access_state()["activeSessions"] == 1

    revoked = app.revoke_h5_access()

    assert revoked["h5Revoke"]["ok"] is True
    assert revoked["h5Access"]["activeSessions"] == 0
    assert app.validate_h5_session(session_token) is False


def test_desktop_h5_pairing_requires_active_lan_listener(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
        desktop_h5_enabled=True,
        desktop_h5_host="0.0.0.0",
    )
    app = DesktopApp(config)
    app.desktop_host = "127.0.0.1"
    app.desktop_port = 8765

    pairing = app.create_h5_pairing()

    assert pairing["h5Pairing"]["ok"] is False
    assert pairing["h5Pairing"]["url"] == ""
    assert pairing["h5Access"]["remoteReady"] is False


def test_desktop_h5_remote_http_exchanges_token_for_cookie(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
        desktop_h5_enabled=True,
        desktop_h5_host="0.0.0.0",
    )
    app = DesktopApp(config)
    server = _create_server("127.0.0.1", 0, _handler_for(app))
    app.desktop_host = "0.0.0.0"
    app.desktop_port = server.server_port
    monkeypatch.setattr(desktop_module, "_is_loopback_address", lambda _value: False)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        with pytest.raises(HTTPError) as denied:
            urlopen(f"{base_url}/api/state", timeout=3)
        assert denied.value.code == 403
        assert "一次性安全链接" in denied.value.read().decode("utf-8")

        pairing = app.create_h5_pairing()["h5Pairing"]
        pairing_query = urlparse(pairing["url"]).query
        cookie_jar = CookieJar()
        opener = build_opener(HTTPCookieProcessor(cookie_jar))

        with opener.open(f"{base_url}/?{pairing_query}", timeout=3) as response:
            assert response.status == 200
            assert "cat-agentic" in response.read().decode("utf-8")

        cookie = next(iter(cookie_jar))
        assert cookie.name == "cat_agentic_h5"
        assert cookie.has_nonstandard_attr("HttpOnly")
        assert cookie.get_nonstandard_attr("SameSite") == "Strict"

        with opener.open(f"{base_url}/api/state", timeout=3) as response:
            state = json.loads(response.read().decode("utf-8"))
        assert state["h5Access"]["activeSessions"] == 1
        assert state["h5Access"]["pairingPending"] is False

        with pytest.raises(HTTPError) as reused:
            urlopen(f"{base_url}/?{pairing_query}", timeout=3)
        assert reused.value.code == 403
        assert "需要安全访问链接" in reused.value.read().decode("utf-8")

        local_only_request = Request(
            f"{base_url}/api/h5/pairing/create",
            data=b"{}",
            headers={"content-type": "application/json"},
            method="POST",
        )
        with pytest.raises(HTTPError) as local_only:
            opener.open(local_only_request, timeout=3)
        assert local_only.value.code == 403

        app.revoke_h5_access()
        with pytest.raises(HTTPError) as revoked:
            opener.open(f"{base_url}/api/state", timeout=3)
        assert revoked.value.code == 403
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()


def test_desktop_h5_denied_page_does_not_echo_tokens() -> None:
    html = render_h5_access_denied_html()

    assert "需要安全访问链接" in html
    assert "h5_token" not in html
    assert "一次性" in html


def test_desktop_h5_lan_address_prefers_rfc1918_networks() -> None:
    assert desktop_module._is_rfc1918_ipv4("192.168.100.167") is True
    assert desktop_module._is_rfc1918_ipv4("10.0.0.8") is True
    assert desktop_module._is_rfc1918_ipv4("172.16.20.4") is True
    assert desktop_module._is_rfc1918_ipv4("198.18.0.1") is False


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


def test_desktop_computer_use_reports_real_prerequisites(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(desktop_module.sys, "platform", "darwin")
    monkeypatch.setattr(desktop_module, "_macos_accessibility_permission", lambda: True)
    monkeypatch.setattr(desktop_module, "_macos_screen_recording_permission", lambda: False)
    monkeypatch.setattr(
        desktop_module,
        "_first_executable",
        lambda *candidates: f"/mock/{Path(candidates[0]).name}",
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

    computer_use = app._computer_use_settings_state()
    capabilities = {item["id"]: item for item in computer_use["capabilities"]}

    assert computer_use["platform"] == "macOS"
    assert computer_use["ready"] is False
    assert computer_use["permissionState"] == "action-required"
    assert capabilities["python"]["status"] == "ready"
    assert capabilities["accessibility"]["status"] == "granted"
    assert capabilities["accessibility"]["detailKey"] == "computerPermissionGrantedDetail"
    assert capabilities["screen-recording"]["status"] == "action-required"
    assert capabilities["screen-recording"]["detailKey"] == "computerPermissionRequiredDetail"
    assert capabilities["screen-recording"]["settingsPane"] == "screen-recording"
    assert capabilities["browser"]["detail"] == "/mock/chromium"


def test_desktop_computer_use_opens_allowlisted_macos_settings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened: list[tuple[list[str], dict[str, Any]]] = []

    def fake_popen(args: list[str], **kwargs: Any) -> object:
        opened.append((args, kwargs))
        return object()

    monkeypatch.setattr(desktop_module.sys, "platform", "darwin")
    monkeypatch.setattr(desktop_module, "_first_executable", lambda *_candidates: "/usr/bin/open")
    monkeypatch.setattr(desktop_module.subprocess, "Popen", fake_popen)
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)

    result = app.open_computer_use_settings({"pane": "accessibility"})
    invalid = app.open_computer_use_settings({"pane": "other"})

    assert result["ok"] is True
    assert opened[0][0] == [
        "/usr/bin/open",
        "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
    ]
    assert opened[0][1]["start_new_session"] is True
    assert invalid["ok"] is False
    assert len(opened) == 1


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
    assert agents["mode"] == "内置 Agent 索引"
    assert agents["total"] == 6
    assert agents["enabled"] == 6
    assert [role["name"] for role in agents["roles"]] == [
        "general-purpose",
        "statusline-setup",
        "Explore",
        "Plan",
        "Implement",
        "Review",
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


def test_desktop_skill_preview_is_bounded_redacted_and_path_scoped(tmp_path: Path) -> None:
    skills_dir = tmp_path / "skills"
    skill_path = skills_dir / "coding" / "review.md"
    skill_path.parent.mkdir(parents=True)
    secret = "sk-local-skill-secret-123456"
    skill_path.write_text(
        "\n".join(
            [
                "name: code-review",
                "description: Review code changes for regressions.",
                "",
                "# Local preview",
                f"api_key={secret}",
                "This body is available only through the bounded preview endpoint.",
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
    skill = app.state()["skillsSettings"]["skills"][0]

    preview = app.skill_preview(skill["id"])

    assert preview["ok"] is True
    assert preview["skill"]["relativePath"] == "coding/review.md"
    assert "path" not in preview["skill"]
    assert secret not in preview["content"]
    assert "api_key=[REDACTED]" in preview["content"]
    assert "bounded preview endpoint" in preview["content"]
    assert app.skill_preview("skill-does-not-exist")["ok"] is False


def test_desktop_extended_settings_read_local_status(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    plugin_dir = config_dir / "plugins" / "cache" / "example-plugin"
    (plugin_dir / "skills" / "demo").mkdir(parents=True)
    (plugin_dir / "skills" / "demo" / "SKILL.md").write_text(
        "name: demo\n\n# Demo\n",
        encoding="utf-8",
    )
    (plugin_dir / "plugin.json").write_text(
        json.dumps(
            {
                "displayName": "Example Plugin",
                "name": "example-plugin",
                "description": "Indexes demo skills and MCP entrypoints.",
                "version": "1.2.3",
                "homepage": "https://example.com/plugin",
                "apiKey": "sk-plugin-secret-123456",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    trace_dir = config_dir / "traces"
    trace_dir.mkdir(parents=True)
    (trace_dir / "run.jsonl").write_text('{"event":"ok"}\n', encoding="utf-8")
    config = RuntimeConfig(
        config_file=config_dir / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)
    app.sessions.save(
        "usage-session",
        [
            Message(role="user", content="hello"),
            Message(role="assistant", content="world response"),
        ],
    )

    state = app.state()

    plugins = state["pluginsSettings"]
    assert plugins["ok"] is True
    assert plugins["total"] == 1
    assert plugins["withSkills"] == 1
    assert plugins["plugins"][0]["name"] == "Example Plugin"
    assert plugins["plugins"][0]["directoryName"] == "example-plugin"
    assert plugins["plugins"][0]["description"] == "Indexes demo skills and MCP entrypoints."
    assert plugins["plugins"][0]["version"] == "1.2.3"
    assert plugins["plugins"][0]["homepage"] == "https://example.com/plugin"
    assert plugins["plugins"][0]["manifest"].endswith("plugin.json")
    assert str(Path.home() / ".codex") not in json.dumps(plugins)

    plugin_preview = app.plugin_preview(plugins["plugins"][0]["id"])
    assert plugin_preview["ok"] is True
    assert plugin_preview["plugin"]["relativePath"] == "example-plugin"
    assert "path" not in plugin_preview["plugin"]
    assert "sk-plugin-secret-123456" not in plugin_preview["manifestContent"]
    assert "[REDACTED]" in plugin_preview["manifestContent"]
    assert "skills/demo/SKILL.md" in {item["path"] for item in plugin_preview["files"]}
    assert len(plugin_preview["skills"]) == 1
    assert plugin_preview["skills"][0]["name"] == "demo"
    assert app.plugin_preview("plugin-does-not-exist")["ok"] is False

    computer_use = state["computerUseSettings"]
    assert computer_use["ok"] is True
    assert computer_use["total"] == 6
    assert {item["name"] for item in computer_use["capabilities"]} == {
        "Python 运行时",
        "虚拟环境",
        "本机工具链",
        "辅助功能权限",
        "屏幕录制权限",
        "浏览器控制",
    }

    token_usage = state["tokenUsageSettings"]
    assert token_usage["sessionCount"] == 1
    assert token_usage["messageCount"] == 2
    assert token_usage["estimatedTokens"] > 0
    assert token_usage["items"][0]["id"] == "usage-session"

    trace = state["traceSettings"]
    assert trace["enabled"] is True
    assert trace["exists"] is True
    assert trace["total"] == 1
    assert trace["files"][0]["relativePath"] == "run.jsonl"

    diagnostics = state["diagnosticsSettings"]
    assert diagnostics["checks"]
    assert {item["name"] for item in diagnostics["checks"]}.issuperset(
        {"工作目录", "配置文件", "会话目录", "MCP 配置", "Skills 索引", "插件索引"}
    )


def test_desktop_marketplace_catalog_normalizes_public_manifest(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    payload = json.dumps(
        {
            "name": "demo-marketplace",
            "metadata": {"version": "1.0.0", "description": "Public demo catalog."},
            "plugins": [
                {
                    "name": "demo-plugin",
                    "version": "2.1.0",
                    "description": "Preview-only demo plugin.",
                    "author": {"name": "Demo Author", "email": "author@example.com"},
                    "source": "./plugins/demo-plugin",
                    "skills": ["./skills/demo"],
                    "apiKey": "sk-marketplace-secret-123456",
                }
            ],
        }
    ).encode("utf-8")

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, _limit: int) -> bytes:
            return payload

    monkeypatch.setattr(desktop_module, "urlopen", lambda _request, timeout: FakeResponse())
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    catalog = DesktopApp(config).marketplace_catalog("anthropic-agent-skills")

    assert catalog["ok"] is True
    assert catalog["sourceId"] == "anthropic-agent-skills"
    assert catalog["sourceUrl"].endswith("/.claude-plugin/marketplace.json")
    assert catalog["trustState"] == "public-unverified"
    assert catalog["installState"] == "preview-only"
    assert catalog["executeState"] == "disabled"
    assert catalog["verification"] == {
        "contentSha256": hashlib.sha256(payload).hexdigest(),
        "contentBytes": len(payload),
        "fetchedAt": catalog["fetchedAt"],
        "sourceRevision": "main",
        "sourceRevisionState": "mutable",
        "signatureState": "not-verified",
    }
    assert catalog["permissionReview"] == {
        "state": "required",
        "scope": "catalog-metadata-only",
        "installState": "blocked",
        "downloadState": "disabled",
        "localWriteState": "disabled",
        "executionState": "disabled",
    }
    assert catalog["total"] == 1
    assert catalog["plugins"][0]["name"] == "demo-plugin"
    assert catalog["plugins"][0]["version"] == "2.1.0"
    assert catalog["plugins"][0]["skillCount"] == 1
    assert "apiKey" not in json.dumps(catalog)
    assert DesktopApp(config).marketplace_catalog("not-allowed")["ok"] is False

    def fail_request(*_args: object, **_kwargs: object) -> None:
        raise OSError("request token=sk-marketplace-secret-123456")

    monkeypatch.setattr(desktop_module, "urlopen", fail_request)
    failed_catalog = DesktopApp(config).marketplace_catalog("anthropic-agent-skills")
    assert failed_catalog["ok"] is False
    assert "sk-marketplace-secret-123456" not in failed_catalog["message"]
    assert "[REDACTED]" in failed_catalog["message"]


def test_desktop_update_check_reads_bounded_github_release(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    payload = json.dumps(
        {"tag_name": "v0.18.0", "published_at": "2026-07-13T08:00:00Z"}
    ).encode("utf-8")

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, limit: int) -> bytes:
            assert limit == desktop_module.UPDATE_CHECK_MAX_BYTES + 1
            return payload

    monkeypatch.setattr(desktop_module, "urlopen", lambda _request, timeout: FakeResponse())
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )

    result = DesktopApp(config).check_for_updates()

    assert result["ok"] is True
    assert result["installedVersion"] == "0.17.0"
    assert result["latestVersion"] == "0.18.0"
    assert result["updateAvailable"] is True
    assert result["versionState"] == "update-available"
    assert result["releaseUrl"].endswith("/releases/tag/v0.18.0")


def test_desktop_update_check_reports_redacted_network_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fail_request(*_args: object, **_kwargs: object) -> None:
        raise OSError("request token=sk-update-secret-123456")

    monkeypatch.setattr(desktop_module, "urlopen", fail_request)
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )

    result = DesktopApp(config).check_for_updates()

    assert result["ok"] is False
    assert result["installedVersion"] == "0.17.0"
    assert result["releaseUrl"].endswith("/releases")
    assert "sk-update-secret-123456" not in result["error"]
    assert "[REDACTED]" in result["error"]


def test_desktop_token_usage_groups_sessions_by_day_and_range(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)
    local_now = datetime.now().astimezone().replace(hour=12, minute=0, second=0, microsecond=0)
    fixtures = [
        (
            "today-session",
            local_now,
            [
                {"role": "user", "content": "a" * 40},
                {"role": "assistant", "content": "b" * 20},
            ],
        ),
        (
            "yesterday-session",
            local_now - timedelta(days=1),
            [{"role": "user", "content": "c" * 80}],
        ),
        (
            "older-session",
            local_now - timedelta(days=45),
            [{"role": "user", "content": "d" * 120}],
        ),
    ]
    for session_id, updated_at, messages in fixtures:
        app.sessions.path_for(session_id).write_text(
            json.dumps(
                {
                    "session_id": session_id,
                    "updated_at": updated_at.isoformat(),
                    "messages": messages,
                }
            ),
            encoding="utf-8",
        )

    month = app._token_usage_settings_state(30)
    quarter = app._token_usage_settings_state(90)
    fallback = app._token_usage_settings_state(7)

    assert month["periodDays"] == 30
    assert month["sessionCount"] == 2
    assert month["messageCount"] == 3
    assert month["estimatedTokens"] == 35
    assert month["today"] == {"sessions": 1, "messages": 2, "estimatedTokens": 15}
    assert month["yesterday"] == {"sessions": 1, "messages": 1, "estimatedTokens": 20}
    assert month["last30Days"]["estimatedTokens"] == 35
    assert len(month["daily"]) == 30
    assert sum(item["sessions"] for item in month["daily"]) == 2
    assert {item["level"] for item in month["daily"] if item["estimatedTokens"]} <= {1, 2, 3, 4}
    assert [item["id"] for item in month["items"]] == [
        "today-session",
        "yesterday-session",
    ]
    assert "content" not in json.dumps(month)

    assert quarter["periodDays"] == 90
    assert quarter["sessionCount"] == 3
    assert quarter["estimatedTokens"] == 65
    assert fallback["periodDays"] == 365
    assert len(fallback["daily"]) == 365


def test_desktop_trace_records_events_and_redacts_secrets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "sk-ant-trace-secret-123456"
    monkeypatch.setenv("ANTHROPIC_API_KEY", secret)
    config = RuntimeConfig(
        config_file=tmp_path / "config" / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
        desktop_trace_enabled=True,
    )
    app = DesktopApp(config)
    app._record_agent_event(
        AgentEvent(
            kind="tool_call",
            name="write_file",
            content=f"authorization={secret}",
            arguments={"path": "secret.txt", "content": secret},
        )
    )

    trace = app._trace_settings_state()

    assert trace["total"] == 1
    assert trace["files"][0]["name"].endswith(".jsonl")
    raw = Path(trace["files"][0]["path"]).read_text(encoding="utf-8")
    assert secret not in raw
    assert "[REDACTED]" in raw
    assert '"argumentKeys": ["content", "path"]' in raw
    assert "secret.txt" not in raw

    preview = app.trace_preview(trace["files"][0]["id"])
    assert preview["ok"] is True
    assert secret not in preview["content"]
    assert "[REDACTED]" in preview["content"]


def test_desktop_trace_respects_disabled_setting(tmp_path: Path) -> None:
    config = RuntimeConfig(
        config_file=tmp_path / "config" / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
        desktop_trace_enabled=False,
    )
    app = DesktopApp(config)

    app._record_agent_event(AgentEvent(kind="assistant", content="not persisted"))

    assert app._trace_settings_state()["total"] == 0
    assert not (config.config_file.parent / "traces").exists()


def test_desktop_trace_open_and_diagnostics_export_use_fixed_local_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "sk-ant-diagnostics-secret-123456"
    monkeypatch.setenv("ANTHROPIC_API_KEY", secret)
    config = RuntimeConfig(
        config_file=tmp_path / "config" / "config.json",
        workdir=tmp_path,
        sessions_dir=tmp_path / "sessions",
        skills_dir=tmp_path / "skills",
        hooks_dir=tmp_path / "hooks",
        mcp_config_file=tmp_path / "mcp.json",
    )
    app = DesktopApp(config)
    opened: list[Path] = []

    def fake_open(path: Path) -> tuple[bool, str]:
        opened.append(path)
        return True, f"opened {path}"

    monkeypatch.setattr(desktop_module, "_open_local_directory", fake_open)

    opened_result = app.open_trace_directory()
    exported = app.export_diagnostics_report()

    trace_dir = config.config_file.parent / "traces"
    assert opened_result["ok"] is True
    assert opened == [trace_dir]
    assert trace_dir.is_dir()
    assert exported["ok"] is True
    report_path = Path(exported["path"])
    assert report_path.parent == config.config_file.parent / "diagnostics"
    report = report_path.read_text(encoding="utf-8")
    assert secret not in report
    assert "API key value: [NOT EXPORTED]" in report
    assert "message bodies" in report


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
