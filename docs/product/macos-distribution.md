# macOS preview DMG distribution

This project can build a developer-preview macOS DMG:

```bash
./scripts/build-macos-preview-dmg.sh
```

The generated file is written to:

```text
dist/X-Agentic-Workflow-<version>-macos-preview.dmg
```

## How the preview DMG works

The DMG contains:

- `X Agentic Workflow.app`
- `Applications` shortcut
- `README-macOS-preview.md`

The app bundle includes a source snapshot under:

```text
X Agentic Workflow.app/Contents/Resources/source
```

On first launch, the app copies that bundled source into:

```text
~/Library/Application Support/x-agentic-workflow/source
```

Then it creates a local `.venv`, installs the local package, starts
`xaw desktop`, and opens the clean-room local browser UI.

The preferred local port is `127.0.0.1:8765`. If another process already uses
that port, the desktop server falls back to an available local port and opens
that URL.

## Current distribution status

This DMG is for developer preview and customer testing.

It is not yet a production notarized macOS release. For broad public
distribution, the next steps are:

1. Enroll/use an Apple Developer account.
2. Sign the `.app` with a Developer ID Application certificate.
3. Create the DMG.
4. Sign the DMG.
5. Submit for Apple notarization.
6. Staple the notarization ticket.
7. Verify on a clean Mac account.

## Logs

Runtime logs:

```text
~/Library/Logs/x-agentic-workflow/desktop-app.log
```

## Smoke test

After building the DMG:

```bash
./scripts/smoke-macos-preview-dmg.sh
```

Or pass an explicit DMG path:

```bash
./scripts/smoke-macos-preview-dmg.sh dist/X-Agentic-Workflow-0.5.0-macos-preview.dmg
```

The smoke test mounts the DMG, verifies the app bundle, opens the app, waits for
the local desktop URL, checks `/api/state`, and detaches the DMG.

## Signing check

For a preview build:

```bash
./scripts/check-macos-signing.sh "apps/macos/X Agentic Workflow.app"
```

For a mounted or copied customer app:

```bash
./scripts/check-macos-signing.sh "/Applications/X Agentic Workflow.app"
```

Production customer builds should show:

- `Developer ID Application` authority
- hardened runtime
- `Notarization Ticket=stapled`
- `spctl` accepted with `Notarized Developer ID`

## Requirements

- macOS 12+
- Python 3 available as `python3`
- User-provided API keys through environment variables or future in-app settings
