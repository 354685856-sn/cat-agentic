# Cat Agentic handoff — 2026-07-13

## Project and goal

- Project: `/Users/mac/Documents/Codex/cat-agentic`
- Branch: `codex/v0.30-settings-management`
- HEAD: `5fbedef`
- Product goal: finish a reliable Mac application whose visible UI and useful
  product behaviors are systematically aligned with the locally visible Claude
  Code Haha 0.4.7 experience, while keeping Cat Agentic original and clean-room.
- User priority: do not wait for the user to find obvious UI, language, button,
  overflow, or startup defects. Inspect and validate each page before handoff.
- Release order confirmed by Nan Ge: finish product UI/functionality first;
  Developer ID signing, notarization, and stapling are the final release stage.

## Non-negotiable clean-room boundary

- Allowed references: the locally visible Claude Code Haha UI, public product
  behavior, public README, and public screenshots.
- Do not read, copy, translate, or reuse cc-haha source, prompts, constants,
  strings, module layout, or internal implementation. Its public repository
  states that it is based on leaked source, so public availability does not make
  its code an acceptable implementation reference for Cat Agentic.
- Delete temporary QA screenshots immediately after inspection. Do not leave
  test screenshots on the Desktop.

## Completed product work

- Dark workbench surfaces are consistent across composer, project picker,
  Worktree, inspector, dialogs, and scheduled tasks; the former white panels and
  bright pink treatment were removed.
- Desktop display languages are complete Simplified Chinese and English only.
  Traditional Chinese, Japanese, and Korean remain separate model reply
  languages. Dynamic shell and settings state rerenders when language changes.
- Fixed Skills summary overflow, settings close `×`, labeled Terminal action,
  top-tab overlap, right-side clipping, three-column minimum-width bugs, and
  removed non-functional inspector imitation controls.
- Provider settings visible alignment at 1128x794:
  - app sidebar: 282px
  - settings navigation: 181px
  - settings top bar: 44px
  - provider card: `x=495`, `y=131.1`, `w=601`, `h=64`
  - only configured/current providers appear in the main list
  - configured-card actions appear on hover/focus
- Added About as the bottom settings entry. It contains the installed version,
  official repository, manual-update boundary, and a real update check.
- `/api/update-check` is local-only and reads a fixed GitHub Releases endpoint
  with an 8-second timeout, 128 KiB limit, version validation, and redacted
  failure details. It does not download or install anything.
- Current real result: installed `0.17.0` is newer than public Release `v0.16.0`.
- Desktop and 390x844 About/Provider views, provider dialog, close button, and
  Chinese/English update results passed browser checks with no page-level
  horizontal overflow.

## macOS delivery state

- Installed app: `/Applications/Cat Agentic.app`
- Version: `0.17.0`
- Bundle content ID:
  `9ea2e21a628068cbca92565283c35153452518141517917c7063fa9a473e3429`
- Current runtime PID: `17559`
- Current healthy URL: `http://127.0.0.1:63832`
- Runtime state last checked:
  - provider: `anthropic`
  - model: `claude-3-5-sonnet-latest`
  - workdir: `/Users/mac/Documents`
- Final DMG:
  `/Users/mac/Documents/Codex/cat-agentic/dist/Cat-Agentic-0.17.0-macos-preview.dmg`
- DMG SHA-256:
  `44ee012220236c7e5c2f94a8b8cec6a0521fe1b5c4ba9e7b5a61eaa2df9cd4da`
- DMG mount/start smoke, installed-app cold start, dynamic-port fallback,
  `/api/state`, persistent runtime reuse, and duplicate double-click with one
  actual runtime process passed.
- Port 8765 is also used by an unrelated `xinyuan_scan` process. Do not kill it.
  Cat Agentic correctly falls back to an available loopback port.
- The app is still unsigned and unnotarized. It requires macOS 12+ and a host
  Python 3.10+ runtime. Signing work is deliberately deferred until the product
  is stable.

## Packaging recovery completed

- PyPI/Hatchling HTTPS repeatedly timed out on this Mac.
- Added `scripts/build-offline-wheel.py`, a standard-library project-wheel
  builder that includes package files, metadata, dependencies, console entry
  points, and RECORD hashes.
- `scripts/build-macos-preview-dmg.sh` uses normal Hatchling when available. If
  it is unavailable and a verified local Cat app exists, it reuses that app's
  dependency wheelhouse and builds only the current pure-Python project wheel
  offline.
- The offline wheel installed with the bundled dependencies in a fresh venv and
  `cat-agentic --version` returned `0.17.0`.

## Verification evidence

- Full test suite: `84 passed`
- Ruff: passed
- mypy: passed for 15 source files
- `git diff --check`: passed
- Packaging syntax: `bash -n` passed
- Offline wheel: fresh-venv install passed
- DMG smoke: passed
- Installed app final start URL: `http://127.0.0.1:63832`
- Installed duplicate-launch runtime process count: 1

## H5 Access visual slice completed after handoff

- Reworked only the H5 Access page in `src/x_agentic_workflow/desktop.py` and
  its static UI assertions in `tests/test_desktop.py`; Provider, About, and the
  macOS packaging files were not revisited.
- Applied the public/visible Crow5 product lesson without copying assets,
  strings, source, colors, or internal structure: the page now scans as current
  service, connection settings, and secure authorization.
- The current URL, port, and restart state now sit in a compact status bar.
  Network, keepalive, reverse-proxy, and trust guidance remains available under
  a collapsed disclosure instead of occupying the whole first screen.
- One-time-link and revoke controls are progressively disclosed from real H5
  state: both are hidden before LAN readiness, link creation appears when the
  listener is ready, and revoke appears only for a pending link or authorized
  session. Existing one-time-token, cookie, and revocation behavior is unchanged.
- Browser QA passed in Simplified Chinese and English at `1128x794` and
  `390x844`; there was no horizontal overflow or clipped H5 text. Expanded help
  remained scroll-safe. Console result: 0 errors, 0 warnings.
- Post-slice gates: `84 passed`; Ruff passed; `python -m mypy` passed for 15
  source files; `git diff --check` passed. The `.venv/bin/mypy` wrapper itself
  still has a stale pre-rename shebang, so use `.venv/bin/python -m mypy`.
- No DMG rebuild or installed-app replacement was performed for this UI-only
  slice.
- Nan Ge supplied a screenshot of a launcher alert claiming Python 3.10+ is
  missing, although the handed-off installed service was already healthy at
  `127.0.0.1:63832`. This was not reproduced or diagnosed here; keep it as a
  separate launcher-path anomaly and do not conflate it with H5 work.

## macOS Finder Python discovery fix completed on 2026-07-18

- Root cause of Nan Ge's alert was confirmed from the actual GUI-like
  environment: `/usr/bin/python3` is Python `3.9.6`, while the usable Python
  `3.14.3` is `/usr/local/bin/python3`. The launcher used only
  `command -v python3`, accepted the first path, failed the `>=3.10` check, and
  never tried the usable interpreter.
- `packaging/macos/cat-agentic-distribution-launcher.zsh` now searches the PATH
  result plus `/usr/local/bin/python3`, `/opt/homebrew/bin/python3`, and the
  standard Python framework paths, selecting the first executable that passes
  the real `sys.version_info >= (3, 10)` check.
- Added static launcher contracts in `tests/test_distribution_docs.py`. A
  sanitized Finder-like PATH selection command returned
  `/usr/local/bin/python3`; it skipped the system 3.9.6 interpreter.
- Full verification: `85 passed`; Ruff passed; mypy passed for 15 source files;
  `zsh -n`, `bash -n`, and `git diff --check` passed.
- No DMG rebuild, installed-app replacement, or commit was performed. The
  current installed app remains the previous bundle; a future package rebuild
  is required before this launcher fix reaches `/Applications`.

## Computer Use visual slice completed on 2026-07-14

- Reworked only the Computer Use presentation in
  `src/x_agentic_workflow/desktop.py` and its static assertions in
  `tests/test_desktop.py`; the existing six real backend checks, macOS pane
  allowlist, Provider, About, H5 Access, and packaging behavior were preserved.
- Replaced the oversized three-stat overview and tall capability cards with a
  compact readiness bar plus two scannable groups: Local Environment and System
  Permissions. Counts and permission state still come from `/api/computer-use`.
- Progressive disclosure is state-driven: Open System Settings appears only for
  an actionable Accessibility or Screen Recording permission, and never beside
  an already granted permission.
- Simplified Chinese and English passed browser QA at `1128x794` and `390x844`.
  Longer English copy and mobile layouts remain vertically scrollable with no
  horizontal overflow. Console result: 0 errors, 0 warnings.
- A synthetic missing Screen Recording state confirmed one allowlisted action,
  correct `5/6` and `1/2` counts, and no action on the granted Accessibility
  row. The System Settings action itself was not clicked during QA.
- Post-slice gates: `84 passed`; Ruff passed; `python -m mypy src` passed for 15
  source files; `git diff --check` passed. No DMG rebuild or installed-app
  replacement was performed for this UI-only slice.

## Token Usage visual slice completed on 2026-07-14

- Current scope is presentation-only. The existing real backend remains intact:
  project-local session aggregation, character-based token estimates, 30/90/365
  day API ranges, accessible calendar cells, and range-scoped recent sessions.
- Changes applied in `src/x_agentic_workflow/desktop.py`:
  - replaced three detached 128px summary cards with one compact, divided summary
    strip;
  - tightened Token-specific section gaps and moved the estimation/billing
    boundary into the heatmap card as a compact footer;
  - removed the redundant success line while preserving an explicit error-only
    result via the new `tokenReadFailed` translation;
  - added a translated range-control name plus dynamic `aria-pressed` state;
  - fixed Token-only recent-session cards so long English titles and IDs wrap
    inside the 390px panel instead of creating an internal horizontal scrollbar;
  - restored a visible error color after the settings-center cascade had
    overridden the Token failure state with ordinary gray text.
- A user-reported global header issue was fixed without changing completed page
  content: chat and scheduled-task views now expose a named `x` that hides the
  redundant top navigation, plus a named restore control. The existing Settings
  `x` still returns to chat. The interaction passed at 1036px and 390px.
- Final browser QA:
  - Simplified Chinese `1128x794` and English `1128x794` empty states fit the
    summary, heatmap, method boundary, recent heading, and empty state;
  - real 30/90/365 requests returned 30/90/365 accessible calendar cells, kept
    the selected range active, and restored all buttons to enabled;
  - English `390x844` has document/body widths of exactly 390px and a 379px
    Token panel; only the heatmap and settings navigation scroll internally;
  - browser-only populated state rendered `2.8K`, `6.3K`, and `18.4K` plus
    three long recent-session rows with no horizontal clipping or local writes;
  - browser-only failure state displayed the translated error in explicit error
    color with no overflow; dark-theme error color was also checked;
  - keyboard Enter changed the focused range to 30 days, returned 30 cells, and
    updated accessible pressed state to `true`; console was 0 errors / 0 warnings.
- Public screenshot `11_token_usage.png` could not be downloaded because both
  GitHub Raw and GitHub API TLS handshakes timed out. No cc-haha source was read;
  this should not relax the clean-room boundary or block Cat-first polish.
- Final gates: targeted `2 passed, 60 deselected`; full `84 passed`; Ruff passed;
  mypy passed for 15 source files; `git diff --check` passed.
- The Playwright session and isolated source server were closed, all temporary QA
  screenshots and `/tmp/cat-token-usage-qa` were removed, and the supplied Desktop
  screenshot was deleted after inspection. No DMG rebuild, installed-app
  replacement, or commit was performed.

## Homepage workbench hierarchy completed on 2026-07-15

- The homepage now starts with the contextual inspector collapsed. At
  `1128x794`, the three columns are `280 / 792 / 56px` and the composer is
  `728px` wide instead of competing with a permanently open 300px inspector.
  The real inspector remains one click away and updates its translated title
  and accessible name between expand and collapse.
- The composer is more compact, uses a restrained teal primary action, and
  exposes the configured model as a real button. Claude, Gemini, DeepSeek,
  GPT/OpenAI, and fallback model families receive distinct aurora-style color
  treatments; clicking the capsule opens the existing Provider settings rather
  than pretending that an inline model switcher exists.
- The dark chat workbench uses scoped graphite/teal tokens without changing the
  completed Settings pages. The model capsule is the only intentionally vivid
  signature element and respects `prefers-reduced-motion`.
- Simplified Chinese and English passed at `1128x794` and `390x844`. The
  390px composer now fits every control through the project switcher
  (`bottom=666px`) instead of extending below the 844px viewport inside a
  hidden-overflow parent. The mobile action area is explicitly split into
  attachment/validation and model/run rows; no text clips or turns vertical.
- The model button has a translated accessible name containing the active model,
  the inspector button reports the correct state, document/body widths match
  the viewport, and the console reported 0 errors / 0 warnings. Clicking the
  model capsule opened the real Provider panel.
- Targeted tests: `4 passed, 59 deselected`. Final gates: `85 passed`; Ruff,
  mypy for 15 source files, and `git diff --check` passed.
- The isolated source server, Playwright browser, temporary HOME, QA screenshots,
  and user-supplied temporary screenshot were removed. No DMG rebuild,
  installed-app replacement, commit, or external Skill install occurred.

## Homepage runtime dispatch refinement completed on 2026-07-18

- Nan Ge approved continued reference to the public `super.engineering`
  product layout. Only public product hierarchy and interaction principles were
  used; no source, assets, private prompts, strings, or internal structure were
  copied.
- The homepage runtime panel now has a compact task-flow eyebrow, explicit task
  status, current-agent dispatch text, and a real current-model chip. The chip
  reads the configured model and reuses the existing Claude/Gemini/DeepSeek/
  OpenAI/fallback model-family color mapping; it does not invent pause, cancel,
  or multi-process controls.
- The panel remains hidden in idle/error states and is only revealed by the
  existing `setTaskRunning(true)` path while `/api/ask` is executing. The
  composer remains bottom-aligned and the existing inspector/task context rules
  are unchanged.
- Fresh source-server browser checks: English `1128x794` and `390x844` both
  report body/document widths equal to the viewport, composer bottoms at `774`
  and `830`, no idle run panel or inspector, and zero console warnings/errors.
  The isolated HOME intentionally had no API key, so the real request entered
  the existing error state without sending data to an external provider; the
  running-panel path is covered by static assertions and the existing async
  send flow.
- Verification after the final selector correction:
  `85 passed`; Ruff passed; mypy passed for 15 source files; `git diff --check`
  passed. No DMG rebuild, installed-app replacement, or commit was performed.

Commands used for the final gates:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/x_agentic_workflow
git diff --check
bash -n scripts/build-macos-preview-dmg.sh scripts/smoke-macos-preview-dmg.sh
./scripts/build-macos-preview-dmg.sh
./scripts/smoke-macos-preview-dmg.sh dist/Cat-Agentic-0.17.0-macos-preview.dmg
```

## Dirty worktree — preserve everything

## 2026-07-18 continuation — Crow5-inspired homepage workbench

- User-authorized visual research was limited to the visible Douyin Crow5 video and public official site. The resulting Cat treatment uses the public hierarchy only: narrow activity rail, session/project rail, central task/composer canvas, and contextual right outcomes rail.
- Updated `src/x_agentic_workflow/desktop.py` and `tests/test_desktop.py`: activity controls now occupy a 48px rail; the existing session/project view is a separate sidebar; ocean is the default theme and comic is optional; top-right is a real read-only provider endpoint plus existing connection test. The inspector remains backed by real Cat file ledger/validation/worktree/diff state only.
- A JavaScript apostrophe syntax error in English quick-task strings was found during browser QA and protected by test assertions plus a rendered-script `node --check` smoke check.
- Final evidence: Chinese Ocean `1128x794` and `390x844` browser checks passed, including no horizontal overflow and mobile sidebar collapse. Full verification: `86 passed`, Ruff, mypy for 15 files, and `git diff --check` all pass. Temporary server stopped. No commit, DMG rebuild, or `/Applications` replacement.

No commit was created. The worktree contains accumulated user/project changes:

```text
 M AGENTS.md
 M README.md
 M apps/macos/Cat Agentic.app/Contents/Info.plist
 M docs/product/macos-app.md
 M docs/product/macos-distribution.md
 M packaging/macos/cat-agentic-distribution-launcher.zsh
 M scripts/build-macos-preview-dmg.sh
 M scripts/smoke-macos-preview-dmg.sh
 M src/x_agentic_workflow/agent.py
 M src/x_agentic_workflow/config.py
 M src/x_agentic_workflow/desktop.py
 M src/x_agentic_workflow/mcp.py
 M tests/test_agent.py
 M tests/test_desktop.py
 M tests/test_distribution_docs.py
?? .github/workflows/pages.yml
?? .playwright-cli/
?? docs/product/cat-agentic-handoff-2026-07-13.md
?? scripts/build-offline-wheel.py
?? site/
?? tests/test_download_page.py
```

Do not reset, checkout, delete, or broadly reformat these files. `desktop.py`
contains multiple completed settings slices, not just the latest About change.

## Exact continuation for the new window

1. Read, in order:
   - `/Users/mac/Documents/Codex/PROJECTS.md`
   - `/Users/mac/Documents/Codex/active-context.md`
   - `/Users/mac/Documents/Codex/cat-agentic/AGENTS.md`
   - `/Users/mac/Documents/Codex/cat-agentic/docs/product/clean-room-scope.md`
   - this handoff
   - current `git status --short`
2. Do not redo the completed Provider/About/H5 Access/Computer Use/macOS
   packaging slices.
3. Token Usage is complete. Continue visible page-by-page alignment only where
   a real backend and public or locally visible references exist:
   - IM (`07_im.png`) only after its real backend and failure states exist
   - Scheduled Tasks (`08_scheduled_task.png`)
   - workspace/changes/worktree (`10_desktop_workspace.png` and
     `13_workspace_changes_worktree.png`)
4. For each slice: inspect visible reference, measure Cat at 1128x794, implement
   only real behavior, verify Chinese and English, verify 390x844, check button
   names/close state/overflow, run targeted tests, then run full gates at the
   delivery checkpoint.
5. Rebuild and reinstall the Mac app only after a coherent page slice and full
   gates are complete. Back up an existing `/Applications/Cat Agentic.app`
   before replacement and remove the backup only after cold-start verification.
6. Keep the signing decision deferred. The local Claude Code Haha 0.4.7 copy is
   not a release-quality signature reference: it has Team ID `D3RS24869F`, a
   hardened-runtime signature and stapled marker, but strict verification says
   `invalid signature (code or signature have been modified)`.

## Durable context already updated

## 2026-07-20 Ocean settings visual-QA follow-up

- 2026-07-26 GitHub CI remediation: PR #31 added only the missing protected fixture `tests/fixtures/sync/keryk-ai/.claude/settings.local.json`, merged as `2dbbc262a58543455c3e74d3cb26f8ed3b8a6567`. On `main`, Docker Build `30191217216`, CI `30191217265`, and Fork Sync Compatibility `30191217238` all passed. Historical Docker red notifications were from the earlier `{{REGISTRY}}` template bug, already corrected in the current workflow.
- Ocean nested-surface repair is complete in `src/x_agentic_workflow/desktop.py`, with static regression coverage in `tests/test_desktop.py`.
- Desktop `1128x794` and mobile `390x844`: all enabled settings views have no visible white surfaces and no horizontal overflow; console is clean.
- Safe controls verified: new chat, scheduled view, sidebar collapse/restore, settings close, model shortcut, Skills shortcut. Do not treat external/network/write controls as automatically authorized.
- Full gates: `86 passed`, Ruff, mypy (15 files), rendered JS syntax, and `git diff --check`. No commit, packaging, or installed-app replacement.
- 2026-07-20 follow-up: authorization was received; DMG `Cat-Agentic-0.17.0-macos-preview.dmg` SHA-256 `8fc1346597a0d9fe5b43c705e06c5d5697faf39ecb6312febd37d13e2c5008a8` built and smoke-tested. The old `/Applications/Cat Agentic.app` is backed up as `/Applications/Cat Agentic.app.backup-20260720-202523`; the new app cold-launched successfully and served `/api/state`. It is still unsigned and Gatekeeper-rejected, so it remains a developer preview.

- `/Users/mac/Documents/Codex/active-context.md`
- `/Users/mac/Documents/Obsidian Vault/01_Projects/Cat-Agentic/README.md`
- project `README.md`
- `docs/product/macos-app.md`
- `docs/product/macos-distribution.md`
