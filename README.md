# cat-agentic

Cat Codex is the primary desktop workbench for this repository, backed by the
official Codex App Server protocol. The existing Python `cat-agentic` runtime
and its browser desktop remain available as compatibility/legacy surfaces while
the new workbench becomes the main product UI.

## Cat Codex workbench (primary app)

`apps/cat-codex` is the first-stage React/TypeScript/Vite desktop-workbench
shell wrapped by a Tauri 2 cross-platform desktop shell. Its interaction model
intentionally follows the familiar Codex desktop workbench structure: projects
and sessions on the left, conversation and Agent
events in the center, Files / Diff / Output / Plugins on the right, and a
composer with model and permission state at the bottom. The visual system is
Cat Codex's own dark slate and acid-lime identity; it does not copy Codex
assets or reproduce the UI pixel-for-pixel.

The App Server boundary is isolated in `apps/cat-codex/src/lib/codex`:

- `types.ts` models the documented JSON-RPC messages and
  `initialize → initialized → thread/start → turn/start` lifecycle.
- `transport.ts` provides a replaceable WebSocket transport plus an explicit
  native stdio/Unix placeholder for a future Tauri shell.
- `client.ts` only reports ready after a real transport and initialization
  handshake; a missing endpoint never becomes a fake success.

Provider and plugin boundaries are also explicit. Provider adapters reserve
OpenAI/Codex, DeepSeek, Claude, Gemini, local models, and OpenAI-compatible
endpoints. The plugin registry is intentionally empty in this first stage;
future signed manifests may extend providers, tools, MCP, skills, panels, or
workflows. The UI labels all of these as not installed/not connected until
there is a real implementation.

Run the primary workbench locally:

```bash
cd apps/cat-codex
npm install
npm run dev
```

See [`apps/cat-codex/README.md`](apps/cat-codex/README.md) for the integration
boundary, Tauri/macOS/Windows build notes, and build command. The current local
validation covers the frontend build and macOS `.app`/`.dmg` bundle; a Windows
artifact still requires a Windows runner with WebView2 and Tauri prerequisites.

## Legacy runtime and UI

The Python terminal agent runtime in `src/x_agentic_workflow` is preserved for
compatibility. `cat-agentic desktop` and `apps/macos/Cat Agentic.app` are legacy
surfaces during this migration; they are not the primary Cat Codex interface.

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
- Desktop themes and localization:
  - keep the composer, project picker, Worktree controls, inspector, dialogs, and
    scheduled-task surfaces inside one consistent dark workbench palette
  - offer only the complete Simplified Chinese and English desktop bundles;
    Traditional Chinese, Japanese, and Korean remain available as independent
    model reply-language preferences
  - rerender shell and dynamic state together when display language changes, so
    project badges, empty states, tooltips, environment status, and settings copy
    do not remain in the previous language
- Desktop About and updates:
  - show the installed app version and official repository in a dedicated About page
  - read the latest public GitHub Release through a bounded, read-only local endpoint
  - distinguish newer, current, and update-available builds without downloading or
    installing anything automatically
- Desktop H5 Access:
  - bind the desktop service to the local network with validated host, port, and
    disconnect keepalive settings
  - create a 10-minute, one-time phone link that is exchanged for an HttpOnly,
    SameSite=Strict session cookie and then immediately invalidated
  - keep pairing and session token digests in memory only, reject unauthorized
    remote requests, and let the local desktop revoke all remote access
- Desktop Skills Browser:
  - discover project, user, and plugin-local skill summaries with source, size,
    version, search, and stable server-generated IDs
  - select a skill to read a bounded local preview through `/api/skills/preview`
    with root-path validation and local secret redaction
  - keep third-party install and execution out of this slice until those flows
    have explicit approval and a separate runtime boundary
- Desktop Plugin Browser:
  - select a local plugin card to inspect a bounded, redacted manifest preview,
    relative file tree, and bundled Skill metadata
  - use server-generated plugin IDs and root-scoped path validation; plugin
    detail payloads omit absolute paths and never install or execute code
- Desktop Marketplace catalog:
  - read only allowlisted public GitHub Raw `marketplace.json` manifests for
    Anthropic Agent Skills and Trail of Bits
  - show source, version, trust, install, and execution states with explicit
    failure and empty states; this slice never downloads, installs, writes, or
    executes third-party plugins
  - expose the fetched byte count, SHA-256 fingerprint, fetch time, mutable source
    revision, and unverified signature state before any future permission review
- Desktop Computer Use readiness:
  - inspect the active Python runtime, virtual environment, local screenshot and
    automation commands, supported browser path, and macOS Accessibility / Screen
    Recording permissions
  - open only the allowlisted macOS privacy settings pane after an explicit user click
  - keep screenshot, click, and keyboard control inactive until the runtime and system
    permissions are ready
- Desktop Token Usage:
  - aggregate project-local session records into today, yesterday, and recent-30-day
    summaries
  - switch the daily trend between 30 days, 90 days, and one year through real API
    queries
  - render an accessible calendar heatmap and range-scoped recent sessions
  - label the character-based local estimate clearly; it is not provider billing
- Desktop Trace and Diagnostics:
  - write one local JSONL trace per session when Trace is enabled, while excluding
    prompt bodies, tool argument values, diffs, and known secret values
  - browse recent Trace files through a fixed local directory and read a bounded,
    redacted preview without accepting arbitrary paths from the browser
  - rerun eight local readiness checks and export a redacted Markdown diagnostics
    report that omits API key values, messages, file contents, and Trace contents
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

On macOS, double-clicking that app bundle prepares a versioned persistent
runtime under `~/Library/Application Support/cat-agentic/runtimes`, installs
from the bundled offline wheelhouse when compatible, starts the desktop
command, and opens the clean-room browser UI. A second double-click reuses the
healthy running service instead of starting another server.

The current local preview artifact is
`dist/Cat-Agentic-0.17.0-macos-preview.dmg`. It requires macOS 12 and a local
Python 3.10 or newer. The preview is intentionally unsigned and unnotarized;
public distribution still requires Developer ID signing, hardened runtime,
notarization, stapling, and an accepted Gatekeeper check.

Details and customer notes:
[docs/product/macos-app.md](docs/product/macos-app.md)

Preview DMG packaging is documented in:
[docs/product/macos-distribution.md](docs/product/macos-distribution.md)

## Customer website

The customer-facing homepage and download experience live in `site/`:

- `site/index.html`: product homepage with the real desktop workspace preview
- `site/download/index.html`: platform downloads, installation help, and release status
- `.github/workflows/pages.yml`: GitHub Pages deployment from `main`

Preview the site locally:

```bash
python -m http.server --directory site 8000
```

The download page reads public GitHub Releases metadata in the browser. It shows
the newest source release separately from the newest available DMG, falls back to
the real v0.5.0 preview DMG when the API is unavailable, and uses the published
`x-agentic-workflow` pipx path for Windows and Linux until native installers exist.

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
