# macOS double-click app

This repository includes a clean-room local macOS app launcher:

```text
apps/macos/Cat Agentic.app
```

After cloning or downloading the repository on macOS, a user can double-click
that app bundle to launch the browser desktop UI.

## What the app does

- Reads the bundled app version and offline Python wheelhouse.
- Creates a versioned persistent runtime under Application Support on first launch.
- Installs from the bundled wheels without network access when the Mac Python runtime
  matches the build; otherwise it falls back to the bundled source and package index.
- Reuses that runtime on later launches instead of rebuilding `.venv`.
- Restores the most recently selected project when it still exists, otherwise starts
  from `~/Documents`.
- Starts:

```bash
xaw desktop --host 127.0.0.1 --port 8765
```

- Opens the clean-room local UI in the default browser.
- Provides an About page with the installed version and a bounded, read-only
  GitHub Release update check; updates remain manual in the developer preview.
- Opens the already-running local UI when the app is double-clicked again instead of
  starting a duplicate server.
- If port `8765` is already in use, `xaw desktop` falls back to an available
  local port and opens that URL.

## Logs

Runtime logs are written to:

```text
~/Library/Logs/cat-agentic/desktop-app.log
```

## Customer notes

- Python 3.10 or newer must be available on the Mac. The current developer-preview
  build bundles app dependencies but does not yet embed the Python interpreter.
- API keys are not bundled or stored in the app. Users still bring their own
  keys through environment variables or future in-app settings.
- This launcher is suitable for GitHub download / developer preview use.
- For public distribution, build a signed and notarized `.dmg` or `.pkg`.
