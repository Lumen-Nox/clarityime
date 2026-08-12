# ClarityIME Security

**Version:** 0.4.0 · **Last updated:** 2026-08-12

ClarityIME is a **local-first IME**. Contacts, speaker profile, and consent live on your machine.

## Threat model

| Assumption | Meaning |
|---|---|
| **Single user, single machine** | One person uses ClarityIME on a PC/phone they control |
| **Loopback-only core** | `clarityime serve` binds to `127.0.0.1` only — not LAN/WAN |
| **Trusted OS session** | We protect against casual LAN exposure, other local apps, and misconfiguration — not kernel malware |

We **do not** claim protection against: compromised admin accounts, physical disk theft without full-disk encryption, or malware running as the same user (it can read `.local_api_token`).

## What is protected (0.4)

| Control | Implementation |
|---|---|
| **Loopback bind** | `clarityime/security.py` → `assert_loopback_host()` |
| **Consent defaults** | `cloud_sync` and `aggregate_research` default **off** |
| **Local API token** | Mutating `/v1/*` requires `X-ClarityIME-Token` (`clarityime/api_auth.py`) |
| **Field encryption (CIM1)** | `preferred_words`, speaker `correction_log` / sensitive `extra` sealed at rest (`clarityime/secure_store.py`) |
| **Master key** | Windows **DPAPI** wrap → `data/.master_key.wrapped`; dev fallback `data/.master_key.dev` |
| **Audience tags (Cerome L1–L5)** | Communication-facing tags for clarify routing; pairing exports **public L1/L2/L4/L5 only** — L3 relational secrets never leave device |
| **Audit log** | `data/security_audit.log` — auth failures, contact writes (no plaintext content) |
| **Security status** | `GET /v1/security/status` |

## Pairing / export privacy

Mutual contact bundles (`/v1/contacts/export`) include:

- `name`, `relationship`, `style`, `comprehension`
- **`cerome`** public slice (L1/L2/L4/L5)

Never exported: `preferred_words`, `id`, `correction_log`, **Cerome L3** (lexicon / dyadic secrets).

## Your responsibilities

1. Enable **BitLocker / FileVault** (or equivalent full-disk encryption)
2. Do **not** expose port `17800` via firewall or reverse proxy
3. Review **Privacy** before enabling cloud sync or aggregate research
4. Treat `data/.local_api_token` like a session secret (0600 permissions where supported)

## Pre-release checks

```powershell
python -m unittest discover tests -v
python -m unittest tests.test_server_security tests.test_secure_store tests.test_cerome_profile -v
.\scripts\e2e_pipeline.ps1
# Must fail — core refuses non-loopback bind:
clarityime serve --host 0.0.0.0
```

## References

- [RFC 8252 — OAuth 2.0 for Native Apps](https://datatracker.ietf.org/doc/html/rfc8252) (loopback redirect pattern)

## Reporting

Open a **GitHub Security Advisory** on the published repository, or email the maintainers listed in the repository with steps to reproduce and `clarityime --version`.
