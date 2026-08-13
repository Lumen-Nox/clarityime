# Cerome audience tags in ClarityIME

> Cerome here = **observer tags** for clarify routing, not agent substrate.  
> See `Ideas/Aura/Cerome是observer框架_PAT是base_2026-06-02.md`.

## Layer mapping (human → communication)

| Layer | Field | Used for |
|---|---|---|
| **L1** | pace, formality, detail, empathy_need, load_sensitivity | Baseline clarify style |
| **L2** | clarity, warmth, efficiency, precision, humor | Value-weighted simplification |
| **L3** | preferred_words, shared_jargon, comprehension_gaps | **Private** — local only |
| **L4** | formality, stress, novelty | Situational register |
| **L5** | mood label | UX + strained → shorter sentences |

## API

- `GET /v1/contacts` → each row includes `cerome` public export
- `POST /v1/contacts` → optional `cerome` dict merged via `merge_cerome_into_contact`
- Pairing bundle → `cerome` public slice auto-included

## Legacy migration

Existing `style_notes` / `relationship` / `comprehension_notes` auto-infer Cerome on read; upsert writes sealed L3 + `extra.cerome`.

## Code

- `clarityime/cerome/human.py`
- `clarityime/clarify/local_rules.py` — `cerome:l2_*` / `cerome:l5_*` notes
