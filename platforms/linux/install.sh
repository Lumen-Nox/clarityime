#!/usr/bin/env bash
# Install ClarityIME on Linux — IBus or Fcitx5 + Python core
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LINUX_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="${HOME}/.local/share/clarityime"
BIN_DIR="${HOME}/.local/bin"
PREFIX="${HOME}/.local"

usage() {
  cat <<EOF
ClarityIME Linux installer

Usage:
  ./install.sh              # interactive: choose IBus or Fcitx5
  ./install.sh ibus         # IBus engine only
  ./install.sh fcitx5       # Fcitx5 addon only
  ./install.sh both         # install both frameworks

Requires Python 3.9+ and curl.
IBus also needs: ibus python3-gi gir1.2-ibus-1.0
Fcitx5 also needs: fcitx5 fcitx5-config-tool libfcitx5core-dev cmake g++
EOF
}

pick_framework() {
  if [[ "${1:-}" == "ibus" || "${1:-}" == "fcitx5" || "${1:-}" == "both" ]]; then
    echo "$1"
    return
  fi
  echo "Choose input method framework:"
  echo "  1) IBus"
  echo "  2) Fcitx5"
  echo "  3) Both"
  read -r -p "Enter 1/2/3 [1]: " choice
  case "${choice:-1}" in
    1) echo "ibus" ;;
    2) echo "fcitx5" ;;
    3) echo "both" ;;
    *) echo "ibus" ;;
  esac
}

install_core() {
  echo "ClarityIME core → $INSTALL_DIR"
  python3 -m venv "$ROOT/.venv" 2>/dev/null || true
  "$ROOT/.venv/bin/pip" install -e "$ROOT" -q

  mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$INSTALL_DIR/fcitx5"
  export CLARITYIME_ROOT="$ROOT"
  export CLARITYIME_CORE="http://127.0.0.1:17800"

  if ! grep -q CLARITYIME_ROOT "${HOME}/.profile" 2>/dev/null; then
    {
      echo "export CLARITYIME_ROOT=\"$ROOT\""
      echo "export CLARITYIME_CORE=\"http://127.0.0.1:17800\""
      echo "export CLARITYIME_FCITX5_ENGINE=\"$INSTALL_DIR/fcitx5/engine.py\""
    } >> "${HOME}/.profile"
  fi

  cat > "$BIN_DIR/clarityime-serve" <<EOF
#!/usr/bin/env bash
cd "$ROOT" && "$ROOT/.venv/bin/python" -m clarityime.main serve
EOF
  chmod +x "$BIN_DIR/clarityime-serve"

  cat > "$BIN_DIR/clarityime-voice" <<EOF
#!/usr/bin/env bash
export CLARITYIME_ROOT="$ROOT"
export CLARITYIME_CORE="http://127.0.0.1:17800"
raw=\$("$ROOT/.venv/bin/python" -m clarityime.main capture --seconds 5 | python3 -c "import sys,json; print(json.load(sys.stdin).get('raw',''))")
curl -s -X POST "\$CLARITYIME_CORE/v1/candidates" -H 'Content-Type: application/json' \\
  -d "{\\"text\\":\\"\$raw\\",\\"mode\\":\\"default\\"}" | python3 -c "import sys,json; d=json.load(sys.stdin); c=d.get('candidates') or []; print(c[0]['text'] if c else '')"
EOF
  chmod +x "$BIN_DIR/clarityime-voice"

  mkdir -p "${HOME}/.config/systemd/user"
  cat > "${HOME}/.config/systemd/user/clarityime-serve.service" <<EOF
[Unit]
Description=ClarityIME core API
After=network.target

[Service]
ExecStart=$BIN_DIR/clarityime-serve
Restart=on-failure

[Install]
WantedBy=default.target
EOF
  systemctl --user enable clarityime-serve.service 2>/dev/null || true
  systemctl --user start clarityime-serve.service 2>/dev/null || clarityime-serve &
}

install_ibus() {
  echo "Installing IBus engine → $INSTALL_DIR"
  cp "$LINUX_DIR/ibus-clarityime/engine.py" "$INSTALL_DIR/"
  sed "s|@INSTALLDIR@|$INSTALL_DIR|g" "$LINUX_DIR/ibus-clarityime/clarityime.xml" > "$INSTALL_DIR/clarityime.xml"
  mkdir -p "${HOME}/.local/share/ibus/component"
  cp "$INSTALL_DIR/clarityime.xml" "${HOME}/.local/share/ibus/component/clarityime.xml"
  echo "IBus: restart ibus-daemon, then ibus-setup → Add → ClarityIME"
}

install_fcitx5() {
  echo "Installing Fcitx5 addon → $PREFIX"
  cp "$LINUX_DIR/fcitx5/clarityime/engine.py" "$INSTALL_DIR/fcitx5/engine.py"
  chmod +x "$INSTALL_DIR/fcitx5/engine.py"

  if ! command -v cmake >/dev/null 2>&1; then
    echo "ERROR: cmake required for Fcitx5 native addon. Install build deps first." >&2
    exit 1
  fi
  if ! pkg-config --exists Fcitx5Core 2>/dev/null; then
    echo "ERROR: libfcitx5core-dev (Fcitx5Core pkg-config) not found." >&2
    exit 1
  fi

  build_dir="$(mktemp -d)"
  trap 'rm -rf "$build_dir"' EXIT
  cmake -S "$LINUX_DIR/fcitx5" -B "$build_dir" \
    -DCMAKE_INSTALL_PREFIX="$PREFIX" \
    -DCMAKE_BUILD_TYPE=Release
  cmake --build "$build_dir" -j"$(nproc 2>/dev/null || echo 2)"
  cmake --install "$build_dir"
  trap - EXIT
  rm -rf "$build_dir"

  echo "Fcitx5: fcitx5-configtool → Add Input Method → ClarityIME"
  echo "        or: fcitx5-remote -o"
}

FRAMEWORK="$(pick_framework "${1:-}")"
case "$FRAMEWORK" in
  -h|--help|help) usage; exit 0 ;;
esac

install_core
case "$FRAMEWORK" in
  ibus) install_ibus ;;
  fcitx5) install_fcitx5 ;;
  both) install_ibus; install_fcitx5 ;;
  *) usage; exit 1 ;;
esac

echo "Done."
echo "1. Core API: systemctl --user start clarityime-serve"
echo "2. Voice hotkey in engine: F9 or Ctrl+Shift+V"
echo "3. Offline engine test: python3 $INSTALL_DIR/fcitx5/engine.py offline '嗯那个你好' default"
