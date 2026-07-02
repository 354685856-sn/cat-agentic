#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-apps/macos/X Agentic Workflow.app}"

if [[ ! -e "$TARGET" ]]; then
  echo "Target not found: $TARGET" >&2
  exit 1
fi

echo "== codesign =="
codesign -dv --verbose=4 "$TARGET" 2>&1 || true

echo ""
echo "== Gatekeeper =="
spctl --assess --type execute --verbose=4 "$TARGET" 2>&1 || true

echo ""
echo "Note: unsigned preview builds may be rejected. Production customer builds must show:"
echo "- Developer ID Application authority"
echo "- Hardened runtime"
echo "- Notarization Ticket=stapled"
echo "- spctl accepted / Notarized Developer ID"
