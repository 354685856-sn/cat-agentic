# x-agentic-workflow release checklist

Last updated: 2026-07-03

## v0.15.0 release target

- Package: `x-agentic-workflow`
- CLI commands:
  - `xaw chat`
  - `xaw tui`
  - `xaw run -p "..."`
  - `xaw doctor`
  - `xaw sessions`
  - `xaw smoke-openai-compatible`
- Install target: `pipx install x-agentic-workflow`
- UI target: `xaw tui` multi-panel hybrid terminal app with workspace status,
  selectable sessions, extension status, live tool-call timeline, latest file
  diff viewer, approval status, transcript, composer, and shortcut help.
- Runtime target: tool dispatch emits structured events and `write_file`
  returns diff metadata for auditability.
- Desktop target: `xaw desktop` launches a clean-room local browser UI, and
  `apps/macos/X Agentic Workflow.app` provides a GitHub-download developer
  preview double-click launcher for macOS.
- Provider Settings target: the desktop UI can save provider metadata, test
  connectivity, avoid storing secret values, and redact secret-looking provider
  errors before displaying them.
- Project Validation target: the desktop UI can run a read-only current-project
  validation and report key files, git state, and recommended verification
  commands.
- Project Switching target: the desktop UI can switch the active local workdir,
  persist recent project paths, reset chat state, and re-run project validation
  after a switch.
- Project Sessions target: desktop sessions are scoped by active workdir so the
  session list only shows conversations for the current project.
- File Ledger target: desktop captures `write_file` tool results and renders
  changed files plus the latest unified diff in the inspector.
- Persisted File Ledger target: desktop writes file-change ledger metadata into
  the active session JSON and restores it when that session is opened.
- Multi-file Diff target: desktop can select a prior file change and render its
  diff instead of only showing the newest diff.
- Desktop UI Alignment target: desktop home screen uses a focused empty-session
  layout, settings uses the provider-management layout, and unimplemented
  sidebar/settings entries are not shown as fake navigation.
- Desktop Session Recovery target: desktop shows restorable session summaries,
  can filter local sessions by title/id, and clearly indicates when a session
  has been restored.
- Desktop Text Attachments target: the composer `+` selects bounded local text
  files, shows removable attachment chips, and submits validated file context
  without exposing attachment bodies when sessions are restored.
- Provider Status UX target: settings reflects the actually saved provider,
  preserves unsaved form drafts across UI state refreshes, and blocks duplicate
  save/test submissions.
- Composer Draft Recovery target: desktop persists bounded text drafts by
  project and session, restores after browser refresh, and clears after a
  successful send without persisting attachment bodies.
- Distribution target: `scripts/build-macos-preview-dmg.sh` builds a preview
  DMG with a bundled clean-room source snapshot for customer testing.

## Required checks

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/x_agentic_workflow
.venv/bin/xaw --version
.venv/bin/xaw desktop --help
.venv/bin/xaw smoke-openai-compatible --allow-skip
.venv/bin/python -m build
.venv/bin/python -m twine check dist/x_agentic_workflow-*
```

## Desktop delivery checks

```bash
plutil -lint "apps/macos/X Agentic Workflow.app/Contents/Info.plist"
test -x "apps/macos/X Agentic Workflow.app/Contents/MacOS/x-agentic-workflow"
./scripts/build-macos-preview-dmg.sh
./scripts/smoke-macos-preview-dmg.sh
./scripts/check-macos-signing.sh "apps/macos/X Agentic Workflow.app"
```

Before public customer distribution, additionally verify:

- macOS first launch from a clean user account.
- API keys and provider headers never appear in logs.
- Local browser UI starts after app relaunch.
- Session list and recent project state survive app restart.
- DMG/app version matches `pyproject.toml`, `__version__`, Git tag, and release
  notes.
- Signed/notarized builds pass Gatekeeper without manual `xattr` commands.

## Optional real provider smoke

Only run with a disposable key or trusted local environment:

```bash
OPENAI_API_KEY=... .venv/bin/xaw smoke-openai-compatible \
  --base-url https://api.openai.com/v1 \
  --model gpt-4.1-mini
```

For OpenAI-compatible providers such as DeepSeek, OpenRouter, DashScope,
Ollama, or LM Studio, replace `--base-url` and `--model` with provider-specific
values.

## GitHub/PyPI notes

- Do not commit `.env`, API keys, local sessions, or smoke output containing
  provider responses.
- Keep `docs/product/clean-room-scope.md` in the release.
- Keep `docs/product/competitor-release-lessons.md` limited to public product
  and release observations; do not add restricted source-derived details.
- Verify `README.md` documents `xaw tui` as Textual full-screen UI.
- TestPyPI v0.1.0 is published at:
  `https://test.pypi.org/project/x-agentic-workflow/0.1.0/`
- Before production PyPI upload, use a fresh PyPI token. If a token was pasted
  into chat or a screenshot, delete it in the package index account and create a
  replacement.
- Production upload command:

```bash
TWINE_USERNAME=__token__ .venv/bin/python -m twine upload dist/*
```

Enter the PyPI API token only at the terminal prompt. Do not paste tokens into
chat, screenshots, docs, or shell history.

## Release-note discipline

Before tagging a version, create:

- `release-notes/vX.Y.Z.md` with highlights, fixes, testing, confidence, and
  scope risk.
- `artifacts/quality-runs/<timestamp>/report.md` with exact validation commands
  and outcomes.
- A release commit message that includes `Tested:`, `Confidence:`, and
  `Scope-risk:` lines.

This mirrors the public release evidence pattern observed in `cc-haha` without
copying implementation details.

## Implementation milestones

### v0.6 Provider settings

- [x] Settings panel in clean-room UI.
- [x] Save provider metadata.
- [x] API key secure entry plan: config stores env var names only; secret-value
  storage remains future keychain work.
- [x] Connectivity check.
- [x] Redacted provider trace for connection-test errors.

### v0.7 Project validation

- [x] Current-project validation button in desktop UI.
- [x] Read-only project path/key-file/git-state checks.
- [x] Recommended verification commands based on project markers.

### v0.8 Project switching

- [x] Project path input and switch button in desktop UI.
- [x] Workdir switching through `/api/project/switch`.
- [x] Recent project paths persisted in local config.
- [x] Automatic validation after project switch.
- [x] Invalid project path feedback in inspector.

### v0.9 Project sessions

- [x] Project-scoped desktop session directories.
- [x] Desktop session list filtered to active project.
- [x] Switching projects rebuilds the matching session store.
- [x] Same folder name under different paths maps to distinct session storage.

### v0.10 File ledger

- [x] Capture `write_file` tool-result metadata in desktop state.
- [x] Render file-change ledger in the right inspector.
- [x] Render latest unified diff in the right inspector.
- [x] Clear file-change ledger on new desktop chat and project switch.

### v0.11 Persisted file ledger

- [x] Persist file-change ledger metadata per desktop session.
- [x] Preserve file-change metadata when message saves update session JSON.
- [x] Restore file-change ledger when opening an existing desktop session.
- [x] Select any visible file-change entry and render its diff.
- [x] Keep old session JSON without `file_changes` load-compatible.

### v0.11.1 Desktop UI alignment

- [x] Remove dashboard-style home stats and heatmap.
- [x] Align home to a focused empty-session screen with bottom composer.
- [x] Align settings to current provider-management capability.
- [x] Remove unimplemented fake navigation entries from sidebar and settings.

### v0.12 Session recovery and filtering

- [x] Derive desktop session titles from the first user message.
- [x] Expose session summaries with updated time, message count, and file-change count.
- [x] Render searchable local session list in the sidebar.
- [x] Show restored-session title and visible restore pill after opening a session.

### v0.13 Safe text attachments

- [x] Composer `+` opens a text-file picker.
- [x] Render removable attachment chips before sending.
- [x] Enforce five-file, 128 KiB per-file, and 256 KiB total limits.
- [x] Revalidate names/content/limits on the server.
- [x] Cancel stale asynchronous file reads after send/session/project changes.
- [x] Restore session UI with attachment names but without raw attachment bodies.

### v0.14 Provider status UX

- [x] Render the actually saved provider/model/base URL/API key environment name.
- [x] Show saved, missing-key, and unsaved-draft status.
- [x] Preserve unsaved provider draft values across chat/settings transitions.
- [x] Disable save/test buttons while a provider request is active.
- [x] Guard duplicate save/test submissions.
- [x] Remove fake add-provider button and hardcoded provider sample cards.

### v0.15 Composer draft recovery

- [x] Persist text drafts by resolved project workdir and session id.
- [x] Restore drafts after browser refresh and session return.
- [x] Keep new-session drafts isolated from the previous session.
- [x] Clear persisted draft after successful send.
- [x] Bound drafts to 64 KiB and tolerate unavailable local storage.
- [x] Keep attachment contents out of draft persistence.
- [x] Use microsecond session ids to prevent rapid new-session collisions.
