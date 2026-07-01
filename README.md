# x-agentic-workflow

Clean-room Python terminal agentic coding assistant.

This repo contains two layers:

- the SAFe Agentic Workflow harness for developing the product;
- the `x-agentic-workflow` runtime in `src/x_agentic_workflow`.

The runtime targets the same category as Codex CLI, Gemini CLI, aider, Cline,
and Claude-style coding assistants, while using original Python code.

## v0.1 capability

- Hybrid terminal UI:
  - `xaw chat` interactive shell UI
  - `xaw run -p "..."` headless one-shot mode
  - `xaw tui` Textual full-screen hybrid terminal UI
- BYOK model providers:
  - Anthropic Messages API
  - OpenAI-compatible Chat Completions API
- Sandboxed tools:
  - `read_file`
  - `write_file`
  - `list_dir`
  - `search`
  - `run_command` with user approval
- Session save/resume.
- Local Skills loaded by name.
- Lifecycle Hooks directory.
- MCP configuration discovery interface.
- Multi-agent role prompt interface.

## Install for development

Install from TestPyPI during release validation:

```bash
python3 -m venv /tmp/xaw-testpypi
/tmp/xaw-testpypi/bin/python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple \
  x-agentic-workflow
/tmp/xaw-testpypi/bin/xaw --version
```

After the production PyPI release:

```bash
pipx install x-agentic-workflow
```

For local development:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Configure

Secrets stay in environment variables, not in config files.

Anthropic:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
xaw init --provider anthropic --model claude-3-5-sonnet-latest
```

OpenAI-compatible:

```bash
export OPENAI_API_KEY="sk-..."
xaw init \
  --provider openai-compatible \
  --base-url https://api.openai.com/v1 \
  --model gpt-4.1
```

For DeepSeek, OpenRouter, DashScope, Ollama, LM Studio, or another provider,
use its OpenAI-compatible base URL and model name.

## Run

```bash
xaw doctor
xaw chat
xaw tui
xaw run -p "list this project and explain what it does"
```

`xaw tui` opens a multi-panel terminal app:

- left rail: workspace, provider, model, sessions, Skills, Hooks, MCP status
- center: transcript and prompt composer
- right rail: tool registry, approval status, keyboard shortcuts
- shortcuts: `Ctrl+S` submit, `Ctrl+R` reset, `Ctrl+D` doctor, `Ctrl+A`
  approval view, `Ctrl+L` clear, `Ctrl+Q` quit

Resume a session:

```bash
xaw sessions
xaw chat --session 20260630-120000
```

## Safety model

- File access is restricted to the selected project directory.
- Path traversal such as `../outside` is blocked.
- Commands run in the project directory and require explicit approval by
  default.
- Config files store provider metadata only. API keys stay in environment
  variables.

## Clean-room rule

See [docs/product/clean-room-scope.md](docs/product/clean-room-scope.md).

The project may align product capabilities with existing terminal AI coding
assistants, but it must not copy or translate restricted source code,
implementation structure, private prompts, private constants, or UI text.

## Development checks

```bash
python -m pytest
python -m ruff check .
python -m mypy src/x_agentic_workflow
xaw smoke-openai-compatible --allow-skip
```

## Release status

Version `0.1.0` is published to PyPI:

<https://pypi.org/project/x-agentic-workflow/0.1.0/>

Version `0.1.0` is also published to TestPyPI for install verification:

<https://test.pypi.org/project/x-agentic-workflow/0.1.0/>

Production PyPI publishing should use a fresh PyPI API token and `twine upload
dist/*` after the release checklist passes.
