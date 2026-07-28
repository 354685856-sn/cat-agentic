#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="Cat Agentic"
VERSION="$("$ROOT/.venv/bin/python" -c 'import x_agentic_workflow; print(x_agentic_workflow.__version__)' 2>/dev/null || ROOT="$ROOT" python3 -c 'import os, tomllib, pathlib; print(tomllib.loads((pathlib.Path(os.environ["ROOT"]) / "pyproject.toml").read_text())["project"]["version"])')"
BUILD_ROOT="$ROOT/build/macos-preview"
APP_TEMPLATE="$ROOT/apps/macos/${APP_NAME}.app"
DIST_APP="$BUILD_ROOT/${APP_NAME}.app"
SOURCE_DIR="$DIST_APP/Contents/Resources/source"
WHEELHOUSE_DIR="$DIST_APP/Contents/Resources/wheelhouse"
DMG_DIR="$BUILD_ROOT/dmg-root"
DMG_PATH="$ROOT/dist/${APP_NAME// /-}-${VERSION}-macos-preview.dmg"

rm -rf "$BUILD_ROOT"
mkdir -p "$SOURCE_DIR" "$WHEELHOUSE_DIR" "$DMG_DIR" "$ROOT/dist"

ditto "$APP_TEMPLATE" "$DIST_APP"
install -m 755 "$ROOT/packaging/macos/cat-agentic-distribution-launcher.zsh" \
  "$DIST_APP/Contents/MacOS/cat-agentic"
plutil -replace CFBundleShortVersionString -string "$VERSION" "$DIST_APP/Contents/Info.plist"
plutil -replace CFBundleVersion -string "$VERSION" "$DIST_APP/Contents/Info.plist"

rsync -a \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude "build" \
  --exclude "dist" \
  --exclude ".pytest_cache" \
  --exclude ".mypy_cache" \
  --exclude ".ruff_cache" \
  --exclude "__pycache__" \
  --exclude "*.pyc" \
  "$ROOT/" "$SOURCE_DIR/"

INSTALLED_WHEELHOUSE="/Applications/${APP_NAME}.app/Contents/Resources/wheelhouse"
if "$ROOT/.venv/bin/python" -c 'import hatchling' >/dev/null 2>&1; then
  "$ROOT/.venv/bin/python" -m pip wheel \
    --disable-pip-version-check \
    --no-build-isolation \
    --wheel-dir "$WHEELHOUSE_DIR" \
    "$ROOT"
elif [[ -d "$INSTALLED_WHEELHOUSE" ]]; then
  find "$INSTALLED_WHEELHOUSE" -maxdepth 1 -type f -name '*.whl' \
    ! -name 'cat_agentic-*.whl' -exec cp {} "$WHEELHOUSE_DIR/" \;
  "$ROOT/.venv/bin/python" "$ROOT/scripts/build-offline-wheel.py" \
    "$ROOT" "$WHEELHOUSE_DIR"
else
  "$ROOT/.venv/bin/python" -m pip wheel \
    --disable-pip-version-check \
    --wheel-dir "$WHEELHOUSE_DIR" \
    "$ROOT"
fi

printf '%s\n' "$VERSION" > "$DIST_APP/Contents/Resources/version.txt"
{
  shasum -a 256 "$WHEELHOUSE_DIR"/*.whl
  shasum -a 256 "$DIST_APP/Contents/MacOS/cat-agentic"
} | shasum -a 256 | awk '{print $1}' > "$DIST_APP/Contents/Resources/bundle-id.txt"
"$ROOT/.venv/bin/python" -c \
  'import platform, sys; print(f"python={sys.version_info.major}.{sys.version_info.minor} architecture={platform.machine()}")' \
  > "$DIST_APP/Contents/Resources/build-runtime.txt"

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
