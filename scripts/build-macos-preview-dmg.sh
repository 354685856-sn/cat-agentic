#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="X Agentic Workflow"
VERSION="$("$ROOT/.venv/bin/python" -c 'import x_agentic_workflow; print(x_agentic_workflow.__version__)' 2>/dev/null || ROOT="$ROOT" python3 -c 'import os, tomllib, pathlib; print(tomllib.loads((pathlib.Path(os.environ["ROOT"]) / "pyproject.toml").read_text())["project"]["version"])')"
BUILD_ROOT="$ROOT/build/macos-preview"
APP_TEMPLATE="$ROOT/apps/macos/${APP_NAME}.app"
DIST_APP="$BUILD_ROOT/${APP_NAME}.app"
SOURCE_DIR="$DIST_APP/Contents/Resources/source"
DMG_DIR="$BUILD_ROOT/dmg-root"
DMG_PATH="$ROOT/dist/${APP_NAME// /-}-${VERSION}-macos-preview.dmg"

rm -rf "$BUILD_ROOT"
mkdir -p "$SOURCE_DIR" "$DMG_DIR" "$ROOT/dist"

ditto "$APP_TEMPLATE" "$DIST_APP"
install -m 755 "$ROOT/packaging/macos/x-agentic-workflow-distribution-launcher.zsh" \
  "$DIST_APP/Contents/MacOS/x-agentic-workflow"

rsync -a \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude "build" \
  --exclude "dist" \
  --exclude ".pytest_cache" \
  --exclude ".mypy_cache" \
  --exclude ".ruff_cache" \
  "$ROOT/" "$SOURCE_DIR/"

cp "$ROOT/docs/product/macos-app.md" "$DMG_DIR/README-macOS-preview.md"
ditto "$DIST_APP" "$DMG_DIR/${APP_NAME}.app"
ln -s /Applications "$DMG_DIR/Applications"

rm -f "$DMG_PATH"
hdiutil create \
  -volname "$APP_NAME $VERSION Preview" \
  -srcfolder "$DMG_DIR" \
  -ov \
  -format UDZO \
  "$DMG_PATH"

echo "$DMG_PATH"
