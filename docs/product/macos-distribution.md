# macOS preview DMG distribution

This project can build a developer-preview macOS DMG:

```bash
./scripts/build-macos-preview-dmg.sh
```

The generated file is written to:

```text
dist/Cat-Agentic-<version>-macos-preview.dmg
```

## How the preview DMG works

The DMG contains:

- `Cat Agentic.app`
- `Applications` shortcut
- `README-macOS-preview.md`

The app bundle includes a source snapshot under:

```text
Cat Agentic.app/Contents/Resources/source
```

It also includes an offline wheelhouse under:

```text
Cat Agentic.app/Contents/Resources/wheelhouse
```

The normal build uses the declared Hatchling backend. If PyPI is unavailable
and a previously verified local Cat Agentic app is installed, the build reuses
that app's dependency wheelhouse and creates the current pure-Python project
wheel with `scripts/build-offline-wheel.py`. The resulting wheel is installed
and version-checked during smoke testing.

On first launch, the app creates a versioned persistent runtime under:

```text
~/Library/Application Support/cat-agentic/runtimes
```

It installs from the bundled wheelhouse when it matches the available Python,
starts `cat-agentic desktop`, and opens the clean-room local browser UI. Later
launches reuse the runtime and an already-running server. If the bundled wheels
do not match the Mac Python version or architecture, installation falls back to
the bundled source and the configured Python package index.

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
~/Library/Logs/cat-agentic/desktop-app.log
```

## Smoke test

After building the DMG:

```bash
./scripts/smoke-macos-preview-dmg.sh
```

Or pass an explicit DMG path:

```bash
./scripts/smoke-macos-preview-dmg.sh dist/Cat-Agentic-0.17.0-macos-preview.dmg
```

The smoke test mounts the DMG, verifies the app bundle, opens the app, waits for
the local desktop URL, checks `/api/state`, and detaches the DMG.

## Signing check

For a preview build:

```bash
./scripts/check-macos-signing.sh "apps/macos/Cat Agentic.app"
```

For a mounted or copied customer app:

```bash
./scripts/check-macos-signing.sh "/Applications/Cat Agentic.app"
```

Production customer builds should show:

- `Developer ID Application` authority
- hardened runtime
- `Notarization Ticket=stapled`
- `spctl` accepted with `Notarized Developer ID`

## Requirements

- macOS 12+
- Python 3.10 or newer available as `python3`
- The preview bundles Python dependencies for the build machine but does not yet
  embed the Python interpreter; a signed production build should bundle a universal
  runtime or ship separate Intel and Apple Silicon artifacts.
- User-provided API keys through environment variables or future in-app settings
