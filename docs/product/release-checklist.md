# x-agentic-workflow release checklist

Last updated: 2026-07-03

## v0.9.0 release target

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
- [ ] File-change ledger and diff workspace.
