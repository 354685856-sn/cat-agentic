# x-agentic-workflow release checklist

Last updated: 2026-07-01

## v0.5.1 release target

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
.venv/bin/python -m twine check dist/*
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
