# x-agentic-workflow release checklist

Last updated: 2026-06-30

## v0.2 release target

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
  sessions, extension status, tool registry, approval status, transcript,
  composer, and shortcut help.

## Required checks

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/x_agentic_workflow
.venv/bin/xaw --version
.venv/bin/xaw smoke-openai-compatible --allow-skip
.venv/bin/python -m build
.venv/bin/python -m twine check dist/*
```

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
