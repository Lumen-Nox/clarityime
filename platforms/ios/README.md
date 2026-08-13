# ClarityIME — iOS (Host App + Keyboard Extension)

ClarityIME is an **integrated input method** — **voice clarify inside IME** (Host captures → keyboard commits). It is **not** an overlay on system keyboards, not a stack on 搜狗/讯飞, not Typeless.

**We do NOT integrate Typeless or external ASR apps — ClarityIME includes its own ASR + clarify pipeline.**

Differentiation: **audience-targeted clarification**, not style polish.

Apple does not allow third-party **keyboard extensions** to access the microphone. ClarityIME splits the voice pipeline:

| Target | Role |
|--------|------|
| **ClarityHost** (container app) | `SFSpeechRecognizer`, Settings, publishes clarified candidates |
| **ClarityKeyboard** (extension) | Reads App Group, shows candidates, `textDocumentProxy.insertText` |
| **Shared/** | `ClarifyRules`, `SharedStore`, optional `ClarifyClient` |

App Group: `group.com.clarityime`

---

## File tree

```
platforms/ios/
├── README.md                          ← this file
├── Shared/
│   ├── AppGroupConstants.swift        # suite name + UserDefaults keys
│   ├── ClarifyRules.swift             # offline clarify (mirrors Kotlin + Python)
│   ├── ClarifyClient.swift            # optional localhost :17800
│   └── SharedStore.swift              # App Group read/write
├── ClarityHost/
│   ├── ClarityHostApp.swift           # @main SwiftUI app
│   ├── ContentView.swift              # mic UI + candidate preview
│   ├── OnboardingView.swift           # 3-step first-run (clarity / modes / flow)
│   ├── SettingsView.swift             # mode, contact placeholder, ASR locale
│   ├── SpeechRecognizerService.swift  # AVAudioEngine + SFSpeechRecognizer
│   ├── Info.plist
│   └── ClarityHost.entitlements       # App Groups template
└── ClarityKeyboard/
    ├── KeyboardViewController.swift   # extension UI + App Group consumer
    ├── Info.plist
    └── ClarityKeyboard.entitlements   # App Groups template
```

---

## Xcode setup (Host + Extension)

### 1. Create the Xcode project

1. **File → New → Project → iOS → App**
2. Product Name: `ClarityHost`, Interface: **SwiftUI**, Language: **Swift**
3. Bundle ID example: `com.clarityime.host`
4. Save inside `platforms/ios/` (or copy generated project next to these sources)

### 2. Add the keyboard extension

1. **File → New → Target → Custom Keyboard Extension**
2. Name: `ClarityKeyboard`, bundle ID: `com.clarityime.keyboard`
3. Replace generated `KeyboardViewController.swift` with `ClarityKeyboard/KeyboardViewController.swift`
4. Replace extension `Info.plist` with `ClarityKeyboard/Info.plist`

### 3. Add shared Swift files to **both** targets

In Xcode, add `Shared/*.swift` to the project and check **Target Membership** for:

- ✅ ClarityHost  
- ✅ ClarityKeyboard  

Also add host-only files only to ClarityHost; keyboard controller only to ClarityKeyboard.

### 4. App Group capability (both targets)

For **ClarityHost** and **ClarityKeyboard**:

1. Select target → **Signing & Capabilities**
2. **+ Capability → App Groups**
3. Add: `group.com.clarityime`  
   (must match Apple Developer portal if using a team)

4. Set **Code Signing Entitlements**:
   - Host: `ClarityHost/ClarityHost.entitlements`
   - Extension: `ClarityKeyboard/ClarityKeyboard.entitlements`

### 5. Host Info.plist keys

Ensure host `Info.plist` includes (already in template):

- `NSMicrophoneUsageDescription`
- `NSSpeechRecognitionUsageDescription`

### 6. Keyboard extension settings

In extension `Info.plist` (`RequestsOpenAccess` = **true**) so App Group + network (optional core) work. Users must enable **Allow Full Access** in iOS Settings → Keyboard.

### 7. Build & run on device

Speech recognition requires a **physical device** (simulator support is limited).

1. Run **ClarityHost** scheme first → grant mic + speech permissions  
2. **Settings → General → Keyboard → Keyboards → Add ClarityIME** → enable Full Access  
3. Open any app, switch to ClarityIME keyboard  
4. In host app: tap 🎤 → speak → switch to keyboard → tap **↻ Voice** or wait for poll → pick candidate

---

## Data flow

```
┌─────────────────────────────────────────────────────────────────┐
│ ClarityHost (container app)                                      │
│  SettingsView ──save──► SharedStore (UserDefaults App Group)     │
│  SpeechRecognizerService                                         │
│    🎤 AVAudioEngine → SFSpeechRecognizer → raw transcript        │
│    ClarifyRules / ClarifyClient → [ClarifyCandidate]             │
│    publishVoiceResult() ──► voice_pending_commit = true          │
└───────────────────────────────┬─────────────────────────────────┘
                                │ group.com.clarityime
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ ClarityKeyboard (extension)                                      │
│  Timer poll + ↻ Voice → read voice_candidates_json               │
│  User taps candidate → textDocumentProxy.insertText              │
│  clearVoicePending() + ClarifyClient.feedback (if core up)       │
│  Manual paste → ✨ Clarify → same candidate UI (offline rules)   │
└─────────────────────────────────────────────────────────────────┘

Optional (usually unavailable on iPhone):
  ClarifyClient → http://127.0.0.1:17800/v1/candidates
```

### App Group keys

| Key | Writer | Purpose |
|-----|--------|---------|
| `audience_mode` | Host | `default` / `ai` / `contact` |
| `default_contact` | Host | contact label |
| `contact_hints_json` | Host | offline contact-mode hints |
| `asr_language` | Host | e.g. `zh-CN` |
| `auto_apply_top` | Host | one-tap top candidate |
| `onboarding_completed` | Host | first-run wizard done |
| `voice_session_id` | Host | monotonic; keyboard ignores stale sessions |
| `voice_raw_text` | Host | last ASR transcript |
| `voice_candidates_json` | Host | JSON `[{text,label}]` |
| `voice_pending_commit` | Host → Keyboard | keyboard should show picker |
| `voice_status_message` | Host | listening / ready / committed |

---

## Offline clarify rules

Swift `ClarifyRules.swift` mirrors:

- `platforms/android/.../ClarifyRules.kt`
- `clarityime/clarify/local_rules.py`

Semantics: **clarify** (fillers out, punctuation, meaning preserved) — not style polish.

Modes:

| Mode | Behavior |
|------|----------|
| `default` | Strip fillers, split long run-ons, punctuate; concise + explicit_subject variants |
| `ai` | Drop greetings; `Intent:` or bullet propositions |
| `contact` | Relationship/register/lexicon hints from Settings placeholder |

---

## App Store / privacy notes

- Declare microphone + speech recognition usage (host only).  
- Keyboard extension does **not** record audio.  
- Clarify-only, local-first; optional LAN core is best-effort.  
- Full Access required for App Group sync.

---

## Version

- **v0.4** — Host app + App Group voice pipeline + shared offline rules + **OnboardingView**
- **v0.3** — Keyboard-only paste → clarify MVP
