#!/usr/bin/env bash
# Build standalone ClarityIME Python core (PyInstaller) — Linux/macOS reference
# Output: dist/clarityime-core (one-file) and dist/clarityime/ (one-folder)
#
#   pip install -r requirements.txt
#   pip install pyinstaller
#   ./scripts/build_core.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="$REPO_ROOT/.venv"
DIST="$REPO_ROOT/dist"
WORK="$REPO_ROOT/build/pyinstaller"
SPEC_ONEFILE="$REPO_ROOT/clarityime-onefile.spec"
SPEC_ONEDIR="$REPO_ROOT/clarityime-onedir.spec"

if [[ ! -d "$VENV" ]]; then
  echo "Creating venv at $VENV ..."
  python3 -m venv "$VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"

echo "Installing project + PyInstaller ..."
pip install -e "$REPO_ROOT" -q
pip install pyinstaller -q

if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "Error: pyinstaller not found. Run: pip install pyinstaller" >&2
  exit 1
fi

mkdir -p "$DIST" "$WORK"

echo "Building clarityime-core ..."
cd "$REPO_ROOT"
pyinstaller "$SPEC_ONEFILE" --noconfirm --clean \
  --distpath "$DIST" \
  --workpath "$WORK"

pyinstaller "$SPEC_ONEDIR" --noconfirm \
  --distpath "$DIST" \
  --workpath "$WORK/onedir"

ONE_FILE="$DIST/clarityime-core"
ONE_FOLDER="$DIST/clarityime/clarityime-core"

echo ""
if [[ -f "$ONE_FILE" ]] || [[ -x "$ONE_FILE" ]]; then
  echo "OK  one-file  -> $ONE_FILE"
  "$ONE_FILE" --version || true
else
  echo "WARN  one-file binary missing: $ONE_FILE"
fi

if [[ -x "$ONE_FOLDER" ]]; then
  echo "OK  one-folder -> $ONE_FOLDER"
fi

echo ""
echo "Usage: clarityime-core serve | capture | contacts list | ..."
