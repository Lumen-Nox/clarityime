# ClarityIME — Linux IME integration (IBus / Fcitx5)

ClarityIME is an **integrated input method** on Linux — **voice clarify inside IME** (IBus / Fcitx5): voice capture, ASR n-best, and clarification candidates run inside the IME shell and talk to the local core (`clarityime serve`). Not an overlay on 搜狗/讯飞, not Typeless; no external dictation app is required.

**We do NOT integrate Typeless or external ASR apps — ClarityIME includes its own ASR + clarify pipeline.**

Differentiation: **audience-targeted clarification**, not style polish.

## Install

```bash
cd code-ClarityIME/platforms/linux
chmod +x install.sh
./install.sh            # interactive: IBus / Fcitx5 / both
./install.sh fcitx5     # Fcitx5 only
./install.sh ibus       # IBus only
```

### Dependencies

| Component | Ubuntu / Debian | Arch Linux |
|-----------|-----------------|------------|
| Core | `python3`, `python3-venv`, `curl` | `python`, `curl` |
| IBus | `ibus`, `python3-gi`, `gir1.2-ibus-1.0` | `ibus`, `python-gobject` |
| Fcitx5 | `fcitx5`, `fcitx5-configtool`, `libfcitx5core-dev`, `cmake`, `g++` | `fcitx5`, `fcitx5-configtool`, `fcitx5-devel`, `cmake`, `gcc` |

## Use

1. Core: `systemctl --user start clarityime-serve` (auto-enabled by install)
2. Switch to **ClarityIME** input method
3. **F9** or **Ctrl+Shift+V** → speak → pick candidate
   - **Enter**, **Space**, or **`1`** → top recommendation (highlighted as `★ 推荐`)
   - **`2`–`9`** → other options (each shows its `[label]`)
   - **`;`** or **Esc** → cancel
4. **`auto_apply_top`** in `settings.json` (via `GET/POST /v1/settings`): when `true`, commits the top candidate immediately without showing the picker
5. CLI voice test: `clarityime-voice`

### IBus

- **Settings → Keyboard → Input Sources → Add ClarityIME**
- Or: `ibus-setup` → Input Method → Add → ClarityIME
- Mode menu: default / ai / contact

### Fcitx5

- `fcitx5-configtool` → Input Method → **+** → ClarityIME
- Or: `fcitx5-remote -o` then add ClarityIME
- Set Fcitx5 as GTK/QT IM module in desktop settings if needed

## Architecture

| Path | Role |
|------|------|
| `ibus-clarityime/engine.py` | IBus engine (Python + GObject) |
| `fcitx5/clarityime/clarityime.cpp` | Fcitx5 native addon (C++) |
| `fcitx5/clarityime/engine.py` | Shared clarify/candidates/voice logic + CLI |
| Core API | `POST /v1/candidates` (with optional `nbest`), `GET /v1/settings` |

Voice flow: IME → Python capture (`raw` + `nbest`) → `POST /v1/candidates` → candidate bar → commit + optional `POST /v1/feedback`.

Fcitx5 has no official Python IME API; the C++ addon delegates HTTP/voice/offline fallback to `engine.py` via subprocess.

## Offline test (no Fcitx5/IBus required)

```bash
python3 platforms/linux/fcitx5/clarityime/engine.py offline "嗯那个你好" default
python3 platforms/linux/fcitx5/clarityime/engine.py candidates --text "嗯那个你好" --mode default --nbest '["嗯那个你好","你好"]'
python3 platforms/linux/fcitx5/clarityime/engine.py auto-apply-top
```

Expected offline fallback (core down): strips fillers and adds punctuation → `你好。`

## Environment

| Variable | Default |
|----------|---------|
| `CLARITYIME_ROOT` | `~/code-ClarityIME` |
| `CLARITYIME_CORE` | `http://127.0.0.1:17800` |
| `CLARITYIME_FCITX5_ENGINE` | `~/.local/share/clarityime/fcitx5/engine.py` |

## Ubuntu / Arch quick install (Fcitx5)

**Ubuntu / Debian:**

```bash
sudo apt install fcitx5 fcitx5-configtool libfcitx5core-dev cmake g++ \
  python3 python3-venv curl
cd ~/code-ClarityIME/platforms/linux && ./install.sh fcitx5
fcitx5-configtool   # add ClarityIME, move above keyboard
systemctl --user restart clarityime-serve
```

**Arch Linux:**

```bash
sudo pacman -S fcitx5 fcitx5-configtool fcitx5-devel cmake gcc python curl
cd ~/code-ClarityIME/platforms/linux && ./install.sh fcitx5
fcitx5-configtool
systemctl --user restart clarityime-serve
```

After login, select **ClarityIME** from the Fcitx5 tray → press **F9** to clarify speech.
