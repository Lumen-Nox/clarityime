# ClarityIME TSF Text Input Processor

Windows **Text Services Framework (TSF)** skeleton for registering ClarityIME as a system input method.

## What works (skeleton)

- COM-exported `ITfTextInputProcessor` (`ClarityTextInputProcessor`)
- TIP registry layout for **Settings → Time & language → Keyboard → Add input method**
- Voice pipeline: Python capture → HTTP `/v1/candidates` → WinForms picker → `ITfInsertAtSelection`
- Debug log: `%LOCALAPPDATA%\ClarityIME\tsf-debug.log`

## What is TODO (needs native COM polish)

| Item | Notes |
|------|-------|
| `ITfKeystrokeMgr::AdviseKeyEventSink` cookie | Skeleton calls Advise; verify F9 in real apps |
| Composition / candidate window in-place | Currently modal WinForms picker |
| `ITfDisplayAttribute` / UI element | For inline composition bar |
| C++ in-proc DLL | If managed COM host fails in some apps, ship minimal C++ shim |
| Auto-start `clarityime serve` | Tray host still recommended |

## Build

```powershell
cd platforms\windows
.\build.ps1 -IncludeTsf
# or
dotnet build ClarityIMETSF\ClarityIMETSF.csproj -c Release
```

Output: `ClarityIMETSF\bin\Release\net8.0-windows\ClarityIMETSF.dll` + `ClarityIMETSF.comhost.dll`

## Register (admin PowerShell)

```powershell
cd platforms\windows
.\install-tsf.ps1
```

Then: **Settings → Time & language → Language & region → Add a language / keyboard → ClarityIME**

Hotkey when key sink is active: **F9** → voice clarify → pick candidate → commit at caret.

## Unregister

```powershell
.\install-tsf.ps1 -Unregister
```

## Coexistence with tray host

Keep using `clarityime-host` (Ctrl+Shift+Space) — TSF and tray share the same Python core on port 17800.
