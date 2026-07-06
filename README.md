# cat-agentic

Clean-room Python terminal agentic coding assistant.

This repo contains two layers:

- the SAFe Agentic Workflow harness for developing the product;
- the `cat-agentic` runtime in the compatibility module `src/x_agentic_workflow`.

The runtime targets the same category as Codex CLI, Gemini CLI, aider, Cline,
and Claude-style coding assistants, while using original Python code.

## Current capability

- Hybrid terminal UI:
  - `cat-agentic chat` interactive shell UI
  - `cat-agentic run -p "..."` headless one-shot mode
  - `cat-agentic tui` Textual full-screen hybrid terminal UI
  - `cat-agentic desktop` clean-room local browser desktop UI
  - `xaw` remains available as a compatibility command
  - `apps/macos/Cat Agentic.app` double-click macOS launcher
- BYOK model providers:
  - Anthropic Messages API
  - OpenAI-compatible Chat Completions API
- Desktop Provider Settings:
  - save provider metadata without storing API key values
  - run a local provider connectivity check
  - redact API keys and token-like values from connection-test errors
- Desktop Project Validation:
  - validate the current project path from the local browser UI
  - report key project files, git state, and recommended verification commands
  - keep validation read-only for the first v0.7 workflow slice
- Desktop Project Switching:
  - switch the active local project path from the desktop UI
  - persist recent project paths in local config
  - reset the desktop chat and re-run project validation after a switch
- Desktop Project Sessions:
  - scope desktop session files to the active project path
  - filter the desktop session list to the current project
  - restore the correct project-local session list when switching back
- Desktop File Ledger:
  - capture `write_file` tool results in a desktop file-change ledger
  - render changed files and the latest unified diff in the right inspector
  - clear the ledger when starting a new desktop chat or switching projects
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

The rename has not been published yet. For the current development branch:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cat-agentic --version
```

After a future production release under the new package name:

```bash
pipx install cat-agentic
```

Published versions through `0.16.0` remain under the historical
`x-agentic-workflow` package and repository name.

## Configure

Secrets stay in environment variables, not in config files.

Anthropic:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
cat-agentic init --provider anthropic --model claude-3-5-sonnet-latest
```

OpenAI-compatible:

```bash
export OPENAI_API_KEY="sk-..."
cat-agentic init \
  --provider openai-compatible \
  --base-url https://api.openai.com/v1 \
  --model gpt-4.1
```

For DeepSeek, OpenRouter, DashScope, Ollama, LM Studio, or another provider,
use its OpenAI-compatible base URL and model name.

## Run

```bash
cat-agentic doctor
cat-agentic chat
cat-agentic tui
cat-agentic desktop
cat-agentic run -p "list this project and explain what it does"
```

`cat-agentic tui` opens a multi-panel terminal app:

- left rail: workspace, provider, model, sessions, Skills, Hooks, MCP status
- center: transcript and prompt composer
- right rail: live tool-call timeline, latest file diff, approval status,
  keyboard shortcuts
- shortcuts: `Ctrl+S` submit, `Ctrl+R` reset, `Ctrl+D` doctor, `Ctrl+A`
  approval view, `Ctrl+N/P` select a recent session, `Ctrl+O` open selected
  session, `Ctrl+L` clear, `Ctrl+Q` quit

When a model uses `write_file`, the TUI shows the latest unified diff in the
Diff Viewer panel. Tool calls and tool results are also recorded in the Tool
Timeline panel so a run is easier to audit.

Resume a session:

```bash
cat-agentic sessions
cat-agentic chat --session 20260630-120000
```

## macOS double-click app

For GitHub download / developer-preview use, this repo includes:

```text
apps/macos/Cat Agentic.app
```

On macOS, double-clicking that app bundle prepares `.venv`, installs the local
package, starts the desktop command, and opens the clean-room browser UI.

Details and customer notes:
[docs/product/macos-app.md](docs/product/macos-app.md)

Preview DMG packaging is documented in:
[docs/product/macos-distribution.md](docs/product/macos-distribution.md)

Clean-room product lessons and legal open-source reference planning:

- [docs/product/competitor-release-lessons.md](docs/product/competitor-release-lessons.md)
- [docs/product/legal-open-source-reference-map.md](docs/product/legal-open-source-reference-map.md)

## Safety model

- File access is restricted to the selected project directory.
- Path traversal such as `../outside` is blocked.
- Commands run in the project directory and require explicit approval by
  default.
- Config files store provider metadata only. API keys stay in environment
  variables.
- Desktop provider connection-test errors are redacted before they are returned
  to the local browser UI.

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
cat-agentic smoke-openai-compatible --allow-skip
```

## Release status

Current local release target: `0.17.0`, introducing the `cat-agentic` brand,
desktop UI alignment, local scheduling, Git workspace status, and Worktree controls.

Version `0.15.0` is published on GitHub with scoped composer draft recovery:

<https://github.com/354685856-sn/cat-agentic/releases/tag/v0.15.0>

Version `0.14.0` is published on GitHub with provider status and form reliability:

<https://github.com/354685856-sn/cat-agentic/releases/tag/v0.14.0>

Version `0.13.0` is published on GitHub with safe desktop text attachments:

<https://github.com/354685856-sn/cat-agentic/releases/tag/v0.13.0>

Version `0.12.0` is published on GitHub with desktop session recovery and filtering:

<https://github.com/354685856-sn/cat-agentic/releases/tag/v0.12.0>

Version `0.11.1` is published on GitHub with desktop UI alignment:

<https://github.com/354685856-sn/cat-agentic/releases/tag/v0.11.1>

Version `0.11.0` is published on GitHub with persisted desktop File Ledger:

<https://github.com/354685856-sn/cat-agentic/releases/tag/v0.11.0>

Version `0.10.0` is published on GitHub with desktop File Ledger:

<https://github.com/354685856-sn/cat-agentic/releases/tag/v0.10.0>

Version `0.9.0` is published on GitHub with desktop Project Sessions:

<https://github.com/354685856-sn/cat-agentic/releases/tag/v0.9.0>

Version `0.8.0` is published on GitHub with desktop Project Switching:

<https://github.com/354685856-sn/cat-agentic/releases/tag/v0.8.0>

Version `0.7.0` is published on GitHub with desktop Project Validation:

<https://github.com/354685856-sn/cat-agentic/releases/tag/v0.7.0>

Version `0.6.0` is published on GitHub with desktop Provider Settings:

<https://github.com/354685856-sn/cat-agentic/releases/tag/v0.6.0>

Version `0.5.0` is published on GitHub as a macOS preview distribution:

<https://github.com/354685856-sn/cat-agentic/releases/tag/v0.5.0>

Version `0.2.0` is published to PyPI:

<https://pypi.org/project/x-agentic-workflow/0.2.0/>

Version `0.1.0` is also published to TestPyPI for install verification:

<https://test.pypi.org/project/x-agentic-workflow/0.1.0/>

Production PyPI publishing should use a fresh PyPI API token and `twine upload
dist/*` after the release checklist passes.
