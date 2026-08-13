#!/usr/bin/env bash
# Install ClarityIME macOS: Python core (LaunchAgent) + optional IMK app copy
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
IMK_DEST="$HOME/Library/Input Methods/ClarityIME.app"
AGENT_LABEL="com.clarityime.serve"
AGENT_DEST="$HOME/Library/LaunchAgents/${AGENT_LABEL}.plist"
TEMPLATE="$SCRIPT_DIR/LaunchAgents/com.clarityime.serve.plist.template"
VENV_PY="$ROOT/.venv/bin/python3"

echo "ClarityIME root: $ROOT"

# Python venv + editable install
python3 -m venv "$ROOT/.venv" 2>/dev/null || true
"$ROOT/.venv/bin/pip" install -e "$ROOT" -q

# Shell env for manual runs / Xcode schemes
launchctl setenv CLARITYIME_ROOT "$ROOT" 2>/dev/null || true
ZPROFILE="$HOME/.zprofile"
if ! grep -q 'CLARITYIME_ROOT=' "$ZPROFILE" 2>/dev/null; then
  echo "export CLARITYIME_ROOT=\"$ROOT\"" >> "$ZPROFILE"
  echo "Added CLARITYIME_ROOT to $ZPROFILE"
fi

# LaunchAgent from template (clarityime serve @ login)
mkdir -p "$HOME/Library/LaunchAgents"
if [[ ! -f "$TEMPLATE" ]]; then
  echo "Missing template: $TEMPLATE"
  exit 1
fi

sed \
  -e "s|@@CLARITYIME_ROOT@@|$ROOT|g" \
  -e "s|@@CLARITYIME_VENV_PYTHON@@|$VENV_PY|g" \
  "$TEMPLATE" > "$AGENT_DEST"

launchctl bootout "gui/$(id -u)/$AGENT_LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$AGENT_DEST" 2>/dev/null || \
  launchctl load "$AGENT_DEST" 2>/dev/null || true

echo "LaunchAgent installed → $AGENT_DEST"
echo "Core logs: $ROOT/.clarityime-serve.log"

# Copy built IMK app if present
BUILT="$SCRIPT_DIR/dist/ClarityIME.app"
if [[ -d "$BUILT" ]]; then
  mkdir -p "$(dirname "$IMK_DEST")"
  rm -rf "$IMK_DEST"
  cp -R "$BUILT" "$IMK_DEST"
  echo "Installed IMK app → $IMK_DEST"
  echo "Next: log out and back in, then enable ClarityIME in System Settings (see README)."
else
  echo ""
  echo "IMK app not installed yet (build first):"
  echo "  cd platforms/macos && ./build.sh"
  echo "  then re-run ./install.sh"
fi

echo "Done."
