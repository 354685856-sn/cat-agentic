#!/bin/zsh
set -euo pipefail

APP_EXEC="$0"
APP_MACOS_DIR="$(cd "$(dirname "$APP_EXEC")" && pwd)"
APP_CONTENTS_DIR="$(cd "$APP_MACOS_DIR/.." && pwd)"
SOURCE_ROOT="$APP_CONTENTS_DIR/Resources/source"
WHEELHOUSE_ROOT="$APP_CONTENTS_DIR/Resources/wheelhouse"
VERSION_FILE="$APP_CONTENTS_DIR/Resources/version.txt"
BUNDLE_ID_FILE="$APP_CONTENTS_DIR/Resources/bundle-id.txt"
APP_SUPPORT_DIR="$HOME/Library/Application Support/cat-agentic"
LOG_DIR="$HOME/Library/Logs/cat-agentic"
LOG_FILE="$LOG_DIR/desktop-app.log"

mkdir -p "$LOG_DIR" "$APP_SUPPORT_DIR"

show_missing_python() {
  osascript -e 'display dialog "Cat Agentic 需要 Python 3.10 或更高版本。请先安装新版 Python，再重新打开应用。" buttons {"好"} default button "好" with icon caution' >/dev/null 2>&1 || true
}

show_broken_bundle() {
  osascript -e 'display dialog "Cat Agentic 的应用文件不完整。请重新下载并安装。" buttons {"好"} default button "好" with icon caution' >/dev/null 2>&1 || true
}

show_startup_failure() {
  osascript -e 'display dialog "Cat Agentic 启动失败。详细日志位于 ~/Library/Logs/cat-agentic/desktop-app.log" buttons {"好"} default button "好" with icon caution' >/dev/null 2>&1 || true
}

find_existing_url() {
  [[ -f "$LOG_FILE" ]] || return 1
  "$PYTHON_BIN" - "$LOG_FILE" <<'PY'
import json
import re
import sys
from urllib.request import urlopen

text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
urls = re.findall(r"cat-agentic desktop UI running at (http://[^\s]+)", text)
for url in reversed(urls[-12:]):
    try:
        payload = json.loads(urlopen(url + "/api/state", timeout=3).read())
    except Exception:
        continue
    if all(key in payload for key in ("provider", "model", "workdir", "sessionId")):
        print(url)
        raise SystemExit(0)
raise SystemExit(1)
PY
}

select_workdir() {
  "$RUNTIME_PYTHON" <<'PY'
import json
from pathlib import Path

config = Path.home() / ".x-agentic-workflow" / "config.json"
if config.is_file():
    try:
        recent = json.loads(config.read_text(encoding="utf-8")).get("recent_projects", [])
    except (OSError, ValueError):
        recent = []
    for raw in recent:
        if isinstance(raw, str):
            candidate = Path(raw).expanduser()
            if candidate.is_dir():
                print(candidate.resolve())
                raise SystemExit(0)
documents = Path.home() / "Documents"
print(documents if documents.is_dir() else Path.home())
PY
}

find_python() {
  local candidate
  local from_path
  local -a candidates
  candidates=()
  from_path="$(command -v python3 || true)"
  [[ -n "$from_path" ]] && candidates+=("$from_path")
  candidates+=(/usr/local/bin/python3 /opt/homebrew/bin/python3)
  setopt local_options null_glob
  candidates+=(/Library/Frameworks/Python.framework/Versions/*/bin/python3)
  for candidate in "${candidates[@]}"; do
    [[ -x "$candidate" ]] || continue
    if "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
      print -r -- "$candidate"
      return 0
    fi
  done
  return 1
}

PYTHON_BIN="$(find_python || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  show_missing_python
  exit 1
fi
if [[ ! -d "$SOURCE_ROOT" || ! -f "$VERSION_FILE" || ! -f "$BUNDLE_ID_FILE" ]]; then
  show_broken_bundle
  exit 1
fi

EXISTING_URL="$(find_existing_url || true)"
if [[ -n "$EXISTING_URL" ]]; then
  open "$EXISTING_URL"
  exit 0
fi

BUNDLE_VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"
BUNDLE_ID="$(tr -cd '[:alnum:]._-' < "$BUNDLE_ID_FILE")"
if [[ -z "$BUNDLE_VERSION" || -z "$BUNDLE_ID" ]]; then
  show_broken_bundle
  exit 1
fi

RUNTIME_ROOT="$APP_SUPPORT_DIR/runtimes/$BUNDLE_ID"
VENV_ROOT="$RUNTIME_ROOT/.venv"
RUNTIME_PYTHON="$VENV_ROOT/bin/python"
INSTALL_MARKER="$RUNTIME_ROOT/installed-version.txt"

prepare_runtime() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting Cat Agentic $BUNDLE_VERSION"
  echo "Bundle: $BUNDLE_ID"
  echo "Python: $($PYTHON_BIN --version 2>&1) ($PYTHON_BIN)"
  mkdir -p "$RUNTIME_ROOT"

  if [[ ! -x "$RUNTIME_PYTHON" ]]; then
    echo "Creating persistent runtime"
    "$PYTHON_BIN" -m venv "$VENV_ROOT"
  fi

  if [[ ! -f "$INSTALL_MARKER" || "$(<"$INSTALL_MARKER")" != "$BUNDLE_VERSION" ]]; then
    echo "Installing bundled Cat Agentic runtime"
    if [[ -d "$WHEELHOUSE_ROOT" ]] && \
      "$RUNTIME_PYTHON" -m pip install -q --no-index \
        --find-links "$WHEELHOUSE_ROOT" "cat-agentic==$BUNDLE_VERSION"; then
      echo "Installed from bundled offline wheelhouse"
    else
      echo "Offline wheels do not match this Python; falling back to the bundled source"
      "$RUNTIME_PYTHON" -m pip install -q "$SOURCE_ROOT"
    fi
    "$VENV_ROOT/bin/cat-agentic" --version
    printf '%s\n' "$BUNDLE_VERSION" > "$INSTALL_MARKER"
  else
    echo "Using persistent Cat Agentic runtime"
  fi
}

if ! prepare_runtime >>"$LOG_FILE" 2>&1; then
  show_startup_failure
  exit 1
fi

WORKDIR="$(select_workdir)"
{
  echo "Project: $WORKDIR"
  echo "Launching clean-room desktop UI"
} >>"$LOG_FILE"

cd "$WORKDIR"
LOG_OFFSET=0
if [[ -f "$LOG_FILE" ]]; then
  LOG_OFFSET="$(wc -c < "$LOG_FILE" | tr -d ' ')"
fi

/usr/bin/nohup "$VENV_ROOT/bin/cat-agentic" desktop --host 127.0.0.1 --port 8765 \
  >>"$LOG_FILE" 2>&1 </dev/null &
SERVER_PID=$!
disown "$SERVER_PID" >/dev/null 2>&1 || true

STARTUP_URL=""
DEADLINE=$((SECONDS + 60))
while [[ "$SECONDS" -lt "$DEADLINE" ]]; do
  if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    show_startup_failure
    exit 1
  fi
  STARTUP_URL="$(tail -c "+$((LOG_OFFSET + 1))" "$LOG_FILE" 2>/dev/null \
    | "$PYTHON_BIN" -c 'import re,sys; text=sys.stdin.read(); urls=re.findall(r"cat-agentic desktop UI running at (http://127\.0\.0\.1:\d+)", text); print(urls[-1] if urls else "")')"
  if [[ -n "$STARTUP_URL" ]] && "$PYTHON_BIN" - "$STARTUP_URL" <<'PY'
import json
import sys
from urllib.request import urlopen

payload = json.loads(urlopen(sys.argv[1] + "/api/state", timeout=3).read())
raise SystemExit(0 if all(key in payload for key in ("provider", "model", "workdir", "sessionId")) else 1)
PY
  then
    exit 0
  fi
  sleep 0.5
done

kill "$SERVER_PID" >/dev/null 2>&1 || true
show_startup_failure
exit 1
