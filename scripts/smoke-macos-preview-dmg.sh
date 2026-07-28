#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DMG="${1:-}"
LOG_FILE="$HOME/Library/Logs/cat-agentic/desktop-app.log"

if [[ -z "$DMG" ]]; then
  DMG="$(ls -t "$ROOT"/dist/*-macos-preview.dmg | head -1)"
fi

if [[ ! -f "$DMG" ]]; then
  echo "DMG not found: $DMG" >&2
  exit 1
fi

before_size=0
if [[ -f "$LOG_FILE" ]]; then
  before_size="$(wc -c < "$LOG_FILE" | tr -d ' ')"
fi

plist="$(mktemp)"
hdiutil attach "$DMG" -nobrowse -plist > "$plist"
volume="$(python3 - "$plist" <<'PY'
import plistlib
import sys

with open(sys.argv[1], "rb") as f:
    data = plistlib.load(f)

for entity in data.get("system-entities", []):
    mount = entity.get("mount-point")
    if mount:
        print(mount)
        break
PY
)"
rm "$plist"

cleanup() {
  if [[ -n "${volume:-}" ]]; then
    hdiutil detach "$volume" -quiet >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

app="$volume/Cat Agentic.app"
plutil -lint "$app/Contents/Info.plist" >/dev/null
test -d "$app/Contents/Resources/source/src/x_agentic_workflow"
open "$app"

url=""
deadline=$((SECONDS + 120))
while [[ "$SECONDS" -lt "$deadline" ]]; do
  if [[ -f "$LOG_FILE" ]]; then
    url="$(tail -c +"$((before_size + 1))" "$LOG_FILE" 2>/dev/null \
      | python3 -c 'import re,sys; text=sys.stdin.read(); urls=re.findall(r"cat-agentic desktop UI running at (http://127\.0\.0\.1:\d+)", text); print(urls[-1] if urls else "")')"
  fi
  if [[ -n "$url" ]]; then
    python3 - "$url" <<'PY'
import json
import sys
from urllib.request import urlopen

url = sys.argv[1]
payload = json.loads(urlopen(url + "/api/state", timeout=20).read().decode("utf-8"))
print(
    {
        "url": url,
        "provider": payload["provider"],
        "model": payload["model"],
        "workdir": payload["workdir"],
        "sessionId": payload["sessionId"],
    }
)
PY
    exit 0
  fi
  sleep 2
done

echo "Timed out waiting for desktop UI URL in $LOG_FILE" >&2
tail -120 "$LOG_FILE" >&2 || true
exit 1
