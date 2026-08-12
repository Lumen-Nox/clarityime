# ClarityIME

**Speech input that clarifies meaning for your audience—not just polish—and commits text into the focused field.**

ClarityIME is an integrated input method (IME): speak → clarify for who will read it → pick a candidate → insert at the caret. The Python core runs locally on `127.0.0.1:17800` with offline rule-based clarification and optional local Whisper ASR. Platform shells for **Windows** and **Android** are included in this repository.

## How it works

```
Microphone / platform ASR
        ↓
Local clarify engine (audience-aware, meaning preserved)
        ↓
Candidate picker → commitText / paste at caret
```

Clarification **reduces misunderstanding** (filler removal, referent grounding, chunking). It is **not** style polish or tone rewriting.

## Audience adaptation

The same propositions are re-laid-out to lower the *reader's* processing cost. Nothing is summarized, no stance is rewritten, and an invariant check rejects any adaptation that drops content. Run `clarityime demo` to reproduce:

Raw: `嗯那个 就是我想说一下这个方案吧 因为上次联调的时候大文件上传老是超时 所以我觉得可能得先改重试那块 但是我不太确定会不会影响别的接口 你觉得呢`

| Listener | Output shape | Comprehension cost |
|----------|--------------|--------------------|
| `analytical` | one claim per line, causal edges explicit | 6.5 → **0.0** |
| `warm_flow` | single continuous voice, hedging kept audible | 6.5 → **4.5** |

The listener profile selects which operations apply — referent resolution, subject restoration, claim-first ordering, chunking to a working-memory budget, relation signaling. Budgets follow Cowan (2001) and Sweller (1988); see [docs/COMPREHENSION_MODEL.md](docs/COMPREHENSION_MODEL.md).

Built-in profiles: `analytical`, `warm_flow`, `fast_scan`, `narrative`. A saved contact carries its own profile instead.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -e .

# Start the local API (loopback only)
clarityime serve

# Clarify sample text offline
clarityime clarify "嗯那个 我明天可能 大概 要请假"

# Interactive demo (no microphone)
clarityime demo

# Run tests
.\.venv\Scripts\python.exe -m unittest discover tests -v
```

On Linux/macOS, use `python3 -m venv .venv` and `source .venv/bin/activate` instead.

Set `CLARITYIME_DATA_DIR` to override where contacts, settings, and consent are stored (default: `~/.clarityime/data` in development).

## HTTP API (`clarityime serve`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/health` | Core readiness check |
| GET | `/v1/security/status` | Encryption and auth status |
| GET | `/v1/settings` | Read settings |
| POST | `/v1/settings` | Update settings |
| GET | `/v1/consent` | Read privacy consent flags |
| POST | `/v1/consent` | Update consent |
| GET | `/v1/contacts` | List audience profiles |
| POST | `/v1/contacts` | Create or update a contact |
| DELETE | `/v1/contacts?name=` | Delete a contact |
| GET | `/v1/contacts/export?name=` | Export public contact bundle |
| POST | `/v1/contacts/import` | Import contact bundle |
| GET | `/v1/speaker` | Speaker profile |
| POST | `/v1/clarify` | Single clarified result |
| POST | `/v1/candidates` | Multiple ranked candidates |
| POST | `/v1/feedback` | User correction / feedback log |
| POST | `/v1/bundles` | Save utterance snapshot |
| GET | `/v1/bundles/{id}` | Load utterance snapshot |

Mutating endpoints require header `X-ClarityIME-Token` (written to your data directory on first `serve`).

## Privacy and local-first

- Core binds to **loopback only** (`127.0.0.1`).
- Clarification runs **offline** by default (rule engine in `clarityime/clarify/`).
- Contacts and sensitive fields are stored locally; optional field encryption uses OS key wrapping on Windows.
- `cloud_sync` and `aggregate_research` consent flags default to **off**.

See [SECURITY.md](SECURITY.md) for the threat model and [ARCHITECTURE.md](ARCHITECTURE.md) for component layout.

## Platform status (this repo)

| Platform | Path | Status |
|----------|------|--------|
| **Windows tray host** | `platforms/windows/ClarityIMEHost/` | Hotkey + settings + paste flow |
| **Windows TSF IME** | `platforms/windows/ClarityIMETSF/` | System keyboard (`install-tsf.ps1`) |
| **Android IME** | `platforms/android/ClarityIME/` | InputMethodService + SpeechRecognizer |
| macOS / Linux / iOS | — | Not included in this open-source slice |

Windows install: `platforms/windows/install.ps1` · Android build: see `platforms/android/README.md`.

Dev smoke scripts: `scripts/smoke_core.ps1`, `scripts/e2e_pipeline.ps1`, `scripts/build_core.ps1`.

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — components and deployment
- [SECURITY.md](SECURITY.md) — threat model and encryption
- [docs/COMPREHENSION_MODEL.md](docs/COMPREHENSION_MODEL.md) — psycholinguistic clarify constraints
- [docs/CEROME_AUDIENCE.md](docs/CEROME_AUDIENCE.md) — audience tagging layers

## License

Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).
