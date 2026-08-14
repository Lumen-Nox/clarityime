# ClarityIME

**An IME that clarifies meaning for the person who will read it — not a tone polisher.**

Speak or type, then ClarityIME rearranges the same propositions so the *listener* spends less effort: referents land, claims come first, jargon is tabled by a declared domain. It then commits text into the focused field. Nothing is summarized. Stance, hedges, and questions stay as they were.

This is the public repository for GOAI 2026 Boundless Agents (AI + Education). Apache-2.0. Author: **Lumen**. Judge map: [docs/GOAI_2026.md](docs/GOAI_2026.md).

https://github.com/Lumen-Nox/clarityime

## How it works

```
Microphone / typed text / platform ASR
        ↓
Local rules (fillers, CJK spacing) — still the speaker's words
        ↓
Comprehension ops keyed on listener tags
  (referents, claim-first, working-memory chunks, jargon table,
   audited cross-circle analogies mixed into the same sentence)
        ↓
Optional share link  https://clarityime.app/c#<fragment>
  (payload lives in the URL fragment; a server never sees the message)
        ↓
Candidate picker → commitText / paste at caret
```

Clarification **reduces misunderstanding**. It is **not** style polish.

## Audience adaptation (run `clarityime demo`)

Raw: `嗯那个 就是我想说一下这个方案吧 因为上次联调的时候大文件上传老是超时 所以我觉得可能得先改重试那块 但是我不太确定会不会影响别的接口 你觉得呢`

| Listener | Output shape | Comprehension cost |
|----------|--------------|--------------------|
| `analytical` | one claim per line, causal edges explicit | 6.5 → **0.0** |
| `warm_flow` | single continuous voice, hedging kept audible | 6.5 → **4.5** |

Budgets follow Cowan (2001) and Sweller (1988). Invariants (no new content, no lost content, hedges kept, speech-act kept) reject any adaptation that would rewrite the speaker. See [docs/COMPREHENSION_MODEL.md](docs/COMPREHENSION_MODEL.md).

Public preset names: `analytical`, `warm_flow`, `fast_scan`, `narrative`. A saved contact carries its own tag set instead.

## What is in this version (0.6.6)

| Piece | What a judge can check |
|---|---|
| Tag registry | 17 families, ~310 bilingual tags. Personality **never** implies domain knowledge. **edu / topic** grant study-circle vocabulary; **age / gender / place never** grant words or pick a language. |
| Cross-circle analogies | Audited 1:1 table in `clarify/analogy.py`. A listener who owns FPS hears `守椅（就像架点）` — same proposition, their word. No owned analog → plain T1 jargon. No LLM. |
| Affect-first layout | Fi / Fe / high-agreeableness listeners see stance or feeling clauses before logistics (`A8a`). Same propositions, different order. |
| Jargon table | Fixed local substitutions in `clarify/paraphrase.py`. Circle-insiders keep the term. |
| Contact learning | Count ratings per contact. Threshold **3**, no LLM. Same evidence → same outcome. |
| Share link | `encode` / `decode` round-trip in tests. The viewer page at `clarityime.app` is **not deployed yet**; the fragment protocol is real. |
| Determinism | `tests/test_determinism.py` AST-scans `clarify/` for `random` / HTTP / LLM imports. |
| Demo contrast | `clarityime demo` now prints the same sentence for two classmates: no game/meme tags → plain gloss; FPS + memes → `守椅（就像架点）` and the speaker's `破防`. |

## Quick start

Default install is **clarify / demo / serve** with no ASR and no global hotkeys. The only runtime dependency is `rich`.

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -e .

# Optional:
# pip install -e ".[asr]"      # local Whisper + microphone
# pip install -e ".[desktop]"  # global hotkey + clipboard paste
# pip install -e ".[all]"

clarityime serve
clarityime clarify "嗯那个 我明天可能 大概 要请假"
clarityime demo
python -m unittest discover tests -v
```

On Linux/macOS: `python3 -m venv .venv` and `source .venv/bin/activate`.

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

Mutating endpoints require header `X-ClarityIME-Token` (written to the data directory on first `serve`). Loopback only (`127.0.0.1`).

## Privacy

- Core binds to **loopback only**.
- Clarification runs **offline** (rule engine in `clarityime/clarify/`).
- Share-link payloads sit in the URL **fragment**; they are not POSTed to a server.
- `cloud_sync` and `aggregate_research` default to **off**.

See [SECURITY.md](SECURITY.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

## Platform status

| Platform | Path | Status |
|----------|------|--------|
| **Windows tray host** | `platforms/windows/ClarityIMEHost/` | Hotkey + settings + paste |
| **Windows TSF IME** | `platforms/windows/ClarityIMETSF/` | System keyboard |
| **Android IME** | `platforms/android/ClarityIME/` | InputMethodService + SpeechRecognizer |
| Linux (IBus / fcitx5), macOS, iOS | `platforms/linux` · `macos` · `ios` | Source in-tree; not the supported demo path |

Windows install: `platforms/windows/install.ps1` · Android: `platforms/android/README.md`.

## License

Apache License 2.0 — [LICENSE](LICENSE) and [NOTICE](NOTICE).
