# ClarityIME — platform shells

Each platform is an **integrated input method** (TSF / InputMethodService / IMK / IBus / keyboard extension) — **voice clarify inside IME**, not a standalone overlay, not a stack on 搜狗/讯飞, not Typeless.

**We do NOT integrate Typeless or external ASR apps — ClarityIME includes its own ASR + clarify pipeline.**

Differentiation: **audience-targeted clarification** (preserve intent, reduce misunderstanding), not style polish.

| Platform | Path | Status |
|----------|------|--------|
| **Core API** | `../../clarityime/server.py` | ✅ `clarityime serve` (:17800) |
| **Core bundle** | `../../scripts/build_core.ps1` | ✅ PyInstaller → `clarityime-core.exe` |
| **Windows tray** | `windows/ClarityIMEHost/` | ✅ UI 设置 + Ctrl+Shift+Space |
| **Windows TSF** | `windows/ClarityIMETSF/` | ✅ 系统 IME — `install-tsf.ps1` · F9 |
| **Android** | `android/ClarityIME/` | ✅ IME + Settings + **Onboarding** + ViewPager2 候选 |
| **Linux IBus** | `linux/ibus-clarityime/` | ✅ F9 / Ctrl+Shift+V + lookup |
| **Linux Fcitx5** | `linux/fcitx5/clarityime/` | ✅ addon |
| **macOS** | `macos/` | ✅ IMK · `project.yml` + `build.sh` + `install.sh` |
| **iOS** | `ios/` | ✅ Host + Keyboard + **offline feedback queue** (`FeedbackSync`) |

## Shared contract

All shells call `http://127.0.0.1:17800` when core is running:

- `POST /v1/clarify`
- `POST /v1/candidates`
- `POST /v1/feedback`
- `GET/POST /v1/contacts` · `GET /v1/contacts/export` · `POST /v1/contacts/import` · `GET/POST /v1/settings` · `GET/POST /v1/consent`

Voice capture:

| Platform | ASR source |
|----------|------------|
| Windows tray / TSF | `clarityime capture` or bundled `clarityime-core.exe` |
| macOS IMK | Python capture subprocess |
| Linux IBus/Fcitx5 | `clarityime capture` |
| Android | `SpeechRecognizer` in IME |
| iOS | **ClarityHost** `SFSpeechRecognizer` → App Group → keyboard |

Offline fallback: embedded rules in each shell when core unreachable.

## Quick links

- Windows: `windows/README.md` · TSF: `windows/install-tsf.ps1`
- macOS: `macos/README.md` — System Settings → Keyboard → Text Input
- iOS: `ios/README.md` — Host app + keyboard extension (device required)
- Android: `android/README.md`
- Linux: `linux/README.md`
