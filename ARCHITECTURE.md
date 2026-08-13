# ClarityIME · Integrated IME architecture (v0.5)

## Core principle

ClarityIME is an **integrated input method**, not a floating dictation overlay. Users switch to the ClarityIME keyboard; speech → clarify → commit at the caret happens inside the IME flow.

```
┌─────────────────────────────────────────────────────────┐
│  Platform IME shell (Windows TSF / Android keyboard)    │
│  ┌─────────┐   ┌──────────────┐   ┌─────────────────┐  │
│  │ 🎤 voice │ → │ local / ASR  │ → │ commitText      │  │
│  └─────────┘   └──────────────┘   └─────────────────┘  │
│         ↓ clarify (local rules or HTTP)                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Python core  127.0.0.1:17800  (clarityime serve)│   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Repository layout

| Path | Platform | Role |
|------|----------|------|
| `clarityime/server.py` | All | Local HTTP API |
| `clarityime/clarify/` | All | Offline meaning-preserving clarify engine |
| `clarityime/cerome/` | All | Audience / speaker tagging for routing |
| `platforms/android/ClarityIME/` | Android | **InputMethodService** + SpeechRecognizer |
| `platforms/windows/ClarityIMEHost/` | Windows | Tray host → capture → candidates → paste |
| `platforms/windows/ClarityIMETSF/` | Windows | TSF system IME · F9 → core → insert |
| `platforms/windows/install.ps1` | Windows | Install + PATH; prefers bundled `clarityime-core.exe` |
| `scripts/build_core.ps1` | Windows | PyInstaller → `platforms/windows/dist/clarityime-core.exe` |
| `scripts/smoke_core.ps1` | Dev | venv core · `:17899` health + candidates |
| `scripts/e2e_pipeline.ps1` | Dev | End-to-end API pipeline smoke |

This open-source slice ships **Windows and Android** as the supported IME shells. Linux (IBus/fcitx5), macOS, and iOS trees are included as source; they are not required to run `clarityime demo`.

## HTTP API (`clarityime serve`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/health` | IME startup check |
| GET | `/v1/security/status` | Auth / encryption status |
| POST | `/v1/clarify` | Single clarified result |
| POST | `/v1/candidates` | Multiple swipe candidates |
| POST | `/v1/feedback` | Speaker correction log |
| POST | `/v1/bundles` | Save N-best + candidate snapshot |
| GET | `/v1/bundles/{id}` | Load bundle JSON |
| GET | `/v1/contacts` | Audience list |
| GET | `/v1/contacts/export?name=` | Export public contact bundle |
| POST | `/v1/contacts/import` | Import bundle (merge) |

Full table: see [README.md](README.md).

## Closed-source IME constraint

Third-party closed IMEs (e.g. Sogou, iFlytek) cannot host ClarityIME as a plugin inside their voice pipeline. The supported path is: **ClarityIME is its own switchable keyboard** (TSF / InputMethodService). We do not integrate external dictation overlays such as Typeless.

## Deployment: Python vs bundled core

| Mode | Path | Notes |
|------|------|-------|
| **Development** | `.venv` + `pip install -e .` | Default |
| **Windows one-file** | `platforms/windows/dist/clarityime-core.exe` | `scripts/build_core.ps1`; `install.ps1` copies to `%LOCALAPPDATA%\Programs\ClarityIME\` |
| **Data directory** | `clarityime/paths.py` → `app_data_dir()` | Dev: `CLARITYIME_DATA_DIR` or `~/.clarityime/data`; frozen: `%CLARITYIME_ROOT%/data/` |

Environment variables: `CLARITYIME_CORE_EXE` (and legacy `CLARITYIME_CORE`) point shells at the bundled exe.

## Size notes

- Core Python ~5 MB (without Whisper weights)
- Bundled exe ~97 MB one-file (includes faster-whisper / onnxruntime; **excludes** model weights)
- Whisper models download on first `capture` (Hugging Face cache)
- Android APK target <15 MB (embedded rules, no model)
