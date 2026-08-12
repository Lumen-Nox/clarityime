# ClarityIME — Android Input Method

ClarityIME is an **integrated input method** — **voice clarify inside IME** (`InputMethodService`), not a floating overlay app, not a stack on 搜狗/讯飞, not Typeless.

**We do NOT integrate Typeless or external ASR apps — ClarityIME includes its own ASR + clarify pipeline.**

Differentiation: **audience-targeted clarification**, not style polish.

## Build

1. Open `platforms/android/ClarityIME` in **Android Studio**
2. Sync Gradle → **Build → Build APK(s)**
3. Install on device (USB debug or copy APK)

Or with CLI (requires Android SDK + gradle):

```bash
cd platforms/android/ClarityIME
./gradlew assembleDebug
# APK: app/build/outputs/apk/debug/app-debug.apk
```

## Enable

1. Settings → System → Languages → **On-screen keyboard** → Manage keyboards
2. Enable **ClarityIME**
3. In any app, switch keyboard to ClarityIME (🌐 key)
4. Tap **🎤 Voice clarify** on keyboard toolbar

**First open:** onboarding walks through clarity ≠ polish, three audience modes, and one-tap top candidate. Replay anytime from **⚙ Settings → Show onboarding again**.

## Onboarding (`OnboardingActivity`)

Three-step intro (shown once via `SharedPreferences` flag `onboarding_completed`):

| Step | Topic |
|------|--------|
| 1 | **清晰化 ≠ 润色** — preserve intent, remove filler, reduce misunderstanding |
| 2 | **Modes** — `default` / `contact` / `ai` and where to configure contacts |
| 3 | **How to use** — enable IME, voice button, swipe candidates, long-press feedback |

Launched automatically on first keyboard open; skippable. Settings can reopen without clearing the flag.

## Settings UI (`SettingsActivity`)

Open from keyboard toolbar **⚙ Settings**:

| Feature | Notes |
|---------|--------|
| Core status + refresh | `GET /v1/health` on `127.0.0.1:17800` |
| Show onboarding again | Reopens `OnboardingActivity` |
| Audience mode | `default` / `ai` / `contact` → SharedPreferences |
| Contact picker | Spinner synced with contact list |
| Contacts CRUD | List / add-update / delete via `/v1/contacts` (core must be running) |
| ASR language | Spinner: `auto`, `zh`, `en`, `ja`, `ko` |
| One-tap top candidate | Skip candidate strip; auto-commit best option |
| Privacy / consent | `cloud_sync`, `aggregate_research` (defaults OFF) |

Parity with Windows tray **SettingsForm** for contacts + mode + ASR + consent.

## Candidate strip

After voice ASR:

```
🎤 → SpeechRecognizer (up to 5 nbest hypotheses)
   → ClarifyClient.candidates(text, mode, contact, nbest)
   → ViewPager2 (swipe ← → between recommended + alternates)
   → tap page to commitText into app
```

- **Top recommendation** — green card, one tap to send
- **Alternates** — swipe horizontally on candidate pager
- **都不对…** — **long-press** opens feedback dialog → `POST /v1/feedback` with `[user_feedback]` note
- **One-tap mode** — Settings checkbox auto-sends top without showing pager

Offline fallback: `ClarifyRules` when core is not reachable.

## Flow

```
🎤 → Android SpeechRecognizer (multilingual, full nbest passed to core)
   → ClarifyClient (localhost:17800 or offline ClarifyRules)
   → ViewPager2 candidate pages → commitText into focused app
```

## Optional: full Python core on device

Run in Termux:

```bash
pip install -e .
clarityime serve
```

Then ClarifyClient uses full rules + contacts from desktop sync.

### API token (v0.4+)

Mutating endpoints (`POST /v1/contacts`, consent, feedback) require header `X-ClarityIME-Token`. After `clarityime serve`, copy token from:

- `data/.local_api_token` under your install / repo root
- or set env `CLARITYIME_API_TOKEN` in Termux before starting the IME app session

`LocalApiAuth.kt` also checks SharedPreferences key `local_api_token` (paste in a future settings field).

Contact saves include **Cerome L2/L4/L5** tags derived from style/comprehension fields.

## Permissions

- Microphone (voice)
- Internet (optional, for core API on LAN/localhost)

## Key files

| File | Role |
|------|------|
| `ClarityInputMethodService.kt` | IME service, voice, candidate pager |
| `OnboardingActivity.kt` | First-run intro |
| `ClarityPrefs.kt` | SharedPreferences keys |
| `ClarifyClient.kt` | HTTP client to core (`nbest` on `/v1/candidates`) |
| `SettingsActivity.kt` | Mode, contacts, consent |
