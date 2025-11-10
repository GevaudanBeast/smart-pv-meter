#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 X.Y.Z"
  exit 1
fi

VERSION="$1"
INTEGRATION_DIR="custom_components/spvm"

if ! command -v jq >/dev/null 2>&1; then
  echo "jq requis"; exit 1
fi

MANIFEST="${INTEGRATION_DIR}/manifest.json"
[ -f "$MANIFEST" ] || { echo "manquant: $MANIFEST"; exit 1; }

tmp="$(mktemp)"
jq --arg v "$VERSION" '.version = $v' "$MANIFEST" > "$tmp" && mv "$tmp" "$MANIFEST"

if [ -f "hacs.json" ]; then
  tmp="$(mktemp)"
  jq --arg fn "smart-pv-meter-v${VERSION}.zip" '
    .zip_release = true
    | .filename = $fn
    | .render_readme = (has("render_readme") and .render_readme) or true
  ' hacs.json > "$tmp" && mv "$tmp" hacs.json
fi

git add -A
git commit -m "chore(release): v${VERSION}" || true
git tag -f "v${VERSION}"
echo "Bump OK → v${VERSION}"
