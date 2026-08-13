# ClarityIME — Windows (IME integration)

ClarityIME on Windows is **input-method integration**: a local **Python core** (`clarityime serve` on `127.0.0.1:17800`) plus **platform shells** that call `/v1/*` and commit text into the focused field. We do **not** integrate [Typeless](https://typeless.com) or any third-party dictation overlay — users switch to **ClarityIME** (TSF) or use the **tray host** as a keyboard companion, not a separate ASR app on top of another IME.

## Architecture (IME-first)

```
┌─────────────────────────────────────────────────────────────┐
│  Windows shells (pick one or both)                          │
│  • ClarityIMETSF — system IME, F9 → core → insert at caret  │
│  • clarityime-host — tray + hotkey, paste after candidates  │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP 127.0.0.1:17800
┌───────────────────────────▼─────────────────────────────────┐
│  clarityime-core.exe  OR  python -m clarityime serve        │
│  GET /v1/health · POST /v1/candidates · contacts, consent   │
└─────────────────────────────────────────────────────────────┘
```

| Component | Role | User-facing |
|-----------|------|-------------|
| **Core** | Clarify rules, contacts, optional Whisper `capture` | Background service |
| **Tray host** (`clarityime-host.exe`) | Settings, onboarding, Ctrl+Shift+Space voice flow | Notification area |
| **TSF** (`ClarityIMETSF`) | Registered **Text Input Processor** — true system keyboard | Settings → add **ClarityIME** keyboard |

The tray host is **not** a replacement for TSF: it is a **development-friendly host** and settings UI. Production “type in any app as an IME” path is **`install-tsf.ps1`** + enable the ClarityIME keyboard.

---

## Install flow (`install.ps1`)

From PowerShell (admin **not** required for tray install):

```powershell
cd code-ClarityIME\platforms\windows
.\install.ps1
```

What `install.ps1` does:

1. **Core**
   - If `dist\clarityime-core.exe` exists (from `scripts\build_core.ps1`), copies it to `%LOCALAPPDATA%\Programs\ClarityIME\` and sets user env **`CLARITYIME_CORE_EXE`** (and legacy **`CLARITYIME_CORE`**) to that path.
   - Otherwise creates/uses repo **`.venv`**, `pip install -e`, and clears `CLARITYIME_CORE_EXE` (CLI wrappers use venv `clarityime.exe`).
2. **Host** — runs `build.ps1` if `dist\clarityime-host.exe` is missing; copies host into `%LOCALAPPDATA%\Programs\ClarityIME\`.
3. **PATH** — adds install dir (and venv `Scripts` in fallback mode) to the user `Path`.
4. **Autostart** — optional scheduled task **ClarityIMECore** + Startup shortcut **`clarityime-start.cmd`** (core + tray).

After install, open a **new terminal** and run:

```powershell
clarityime-start          # tray + core
clarityime --version      # bundled exe or venv CLI
```

Bundled core build (optional, no Python needed at runtime):

```powershell
cd code-ClarityIME
.\scripts\build_core.ps1
.\platforms\windows\install.ps1
```

### User environment variables

| Variable | When set | Meaning |
|----------|----------|---------|
| `CLARITYIME_ROOT` | Always | Repo path (`data\` lives here in dev) |
| `CLARITYIME_CORE_EXE` | Bundled core | Absolute path to `clarityime-core.exe` |
| `CLARITYIME_VENV` | Fallback only | `.venv` directory |

---

## TSF vs tray host

| | **Tray host** | **TSF (ClarityIMETSF)** |
|---|---------------|-------------------------|
| Install | `install.ps1` | `install-tsf.ps1` (**Administrator**, HKLM) |
| Integration | Hotkey + paste | System input method |
| Best for | Settings, quick dev smoke | “ClarityIME” in language bar |
| Shared core | Same `:17800` API | Same `:17800` API |

Prerequisites for TSF: **`install.ps1` already done** (core reachable), **.NET 8 SDK** to publish the COM host.

```powershell
# Administrator PowerShell
cd code-ClarityIME\platforms\windows
.\install-tsf.ps1
```

Then: **Settings → Time & language → Keyboard → Add keyboard → ClarityIME**, switch IME, **F9** in a text field.

Unregister: `.\install-tsf.ps1 -Unregister` (admin).

Details: `ClarityIMETSF/README.md` · debug log: `%LOCALAPPDATA%\ClarityIME\tsf-debug.log`

---

## Automated smoke test

Validates host artifact (optional build), core `--version`, live **`serve`**, and HTTP API — **not** Typeless or external dictation tools:

```powershell
cd code-ClarityIME
.\scripts\windows_smoke.ps1
```

Steps inside the script:

1. Build **`clarityime-host.exe`** via `platforms\windows\build.ps1` if missing (`-SkipHostBuild` to skip).
2. Verify **`platforms\windows\dist\clarityime-core.exe --version`** **or** `.venv\Scripts\python.exe -m clarityime --version`.
3. Start core in the background (`serve --host 127.0.0.1 --port 17800`).
4. **`GET /v1/health`** and **`POST /v1/candidates`** (sample text).
5. Stop the core process.

---

## Use (tray UI)

1. `clarityime-start` or sign-in (Startup shortcut).
2. **Ctrl+Shift+Space** or double-click tray → speak → pick candidate → paste.
3. Tray → **Settings**: core status, mode, contacts, consent.

First run: onboarding (clarify vs polish).

## CLI (optional)

```powershell
clarityime serve
clarityime contacts list
clarityime settings --show
```

With bundled exe, `clarityime.cmd` invokes `%CLARITYIME_CORE_EXE%`.

## Build only

```powershell
.\build.ps1                 # dist\clarityime-host.exe
.\build.ps1 -IncludeTsf     # + dist-tsf\ ClarityIMETSF publish
```

## Requirements

- Python 3.9+ (core fallback; bundled exe can omit)
- .NET 8 SDK (tray host + TSF)
- Windows 10/11 microphone permission for voice capture
