#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
work_dir="${RUNNER_TEMP:-${TMPDIR:-/tmp}}/cat-codex-openai-codex"
source_dir="$work_dir/source"
target_dir="$project_dir/src-tauri/resources"

rm -rf "$work_dir"
mkdir -p "$target_dir"
git clone --depth 1 https://github.com/openai/codex.git "$source_dir"
cargo build --release --manifest-path "$source_dir/codex-rs/Cargo.toml" --bin codex

binary="$source_dir/codex-rs/target/release/codex"
if [ "${RUNNER_OS:-}" = "Windows" ]; then
  binary="$binary.exe"
fi
test -f "$binary"
if [ "${RUNNER_OS:-}" = "Windows" ]; then
  cp "$binary" "$target_dir/codex.exe"
else
  cp "$binary" "$target_dir/codex"
  chmod +x "$target_dir/codex"
fi
