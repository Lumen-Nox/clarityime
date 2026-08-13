"""Cerome listener presets — how *this person* parses speech (not how speaker should talk).

Refs: PAT Cerome framework; MBTI as comprehension prior only (observer lens).

| Key | Archetype | Easier to parse when… |
|-----|-----------|------------------------|
| intj / d_type | INTJ (Ni–Te) | Causal chain visible; one claim per line; low social padding |
| s_type | INFP (Fi–Ne) | Feeling + nuance stay in one flow; hedging kept visible |
| a_type | ENTP (Ne–Ti) | Short scannable lines; hooks / questions pop out |
| i_type | INFJ (Ni–Fe) | Meaning beats separated; context before pivot words |
"""

from __future__ import annotations

from clarityime.cerome.human import (
    CeromeHumanProfile,
    CeromeL1Comm,
    CeromeL2Values,
    CeromeL3Relational,
    CeromeL4Context,
    CeromeL5Mood,
)
from clarityime.cerome.tags import validate

LISTENER_PRESET_ALIASES: dict[str, str] = {
    "intj": "d_type",
    "d": "d_type",
    "d_type": "d_type",
    "analytical": "d_type",
    "s": "s_type",
    "s_type": "s_type",
    "infp": "s_type",
    "warm_flow": "s_type",
    "a": "a_type",
    "a_type": "a_type",
    "entp": "a_type",
    "fast_scan": "a_type",
    "i": "i_type",
    "i_type": "i_type",
    "infj": "i_type",
    "narrative": "i_type",
}


PRESET_META: dict[str, str] = {}


def _profile(
    *,
    tag: str,
    mbti: str,
    pace: float,
    formality: float,
    detail: float,
    empathy_need: float,
    clarity: float,
    warmth: float,
    efficiency: float,
    precision: float,
    comprehension: str,
    load_sensitivity: float = 0.55,
    tags: tuple[str, ...] = (),
) -> CeromeHumanProfile:
    """Build a preset.

    ``tags`` may only contain **declared** facts. A personality preset must not
    carry a domain tag: knowing someone is INTJ tells you nothing about whether
    they know 「排期」. Domain tags are added per-contact by the user.
    """
    profile = CeromeHumanProfile(
        l1=CeromeL1Comm(
            pace=pace,
            formality=formality,
            detail=detail,
            empathy_need=empathy_need,
            load_sensitivity=load_sensitivity,
        ),
        l2=CeromeL2Values(
            clarity=clarity,
            warmth=warmth,
            efficiency=efficiency,
            precision=precision,
            humor=0.35 if tag == "a_type" else 0.25,
        ),
        l3=CeromeL3Relational(
            comprehension_gaps=comprehension,
            shared_jargon=f"preset:{tag}",
        ),
        l4=CeromeL4Context(formality=formality, stress=0.3, novelty=0.5),
        l5=CeromeL5Mood(label="steady"),
        tags=list(validate(tags).sorted()),
    )
    PRESET_META[tag] = mbti
    return profile


# INTJ / D — logical scaffold, causal edges explicit, minimal emotional re-flow
D_TYPE = _profile(
    tag="d_type",
    mbti="INTJ",
    pace=0.55,
    formality=0.55,
    detail=0.55,
    empathy_need=0.35,
    clarity=0.9,
    warmth=0.28,
    efficiency=0.88,
    precision=0.82,
    load_sensitivity=0.5,
    # Personality only. No hobby / domain / source tag — those are things the
    # user declares about a real person, not things "INTJ" tells us.
    tags=("mbti_intj",),
    comprehension="先抓判断/请求，再读原因；讨厌猜隐含结论",
)

# INFP / S — keep speaker hedging & feeling words in one continuous voice
S_TYPE = _profile(
    tag="s_type",
    mbti="INFP",
    pace=0.42,
    formality=0.35,
    detail=0.72,
    empathy_need=0.82,
    clarity=0.58,
    warmth=0.88,
    efficiency=0.32,
    precision=0.48,
    load_sensitivity=0.35,
    tags=("mbti_infp",),
    comprehension="需要感受到态度和语气；不要拆成冷清单",
)

# ENTP / A — punchy lines, options & questions stand out
A_TYPE = _profile(
    tag="a_type",
    mbti="ENTP",
    pace=0.72,
    formality=0.4,
    detail=0.48,
    empathy_need=0.45,
    clarity=0.78,
    warmth=0.52,
    efficiency=0.82,
    precision=0.55,
    load_sensitivity=0.85,
    tags=("mbti_entp",),
    comprehension="快速扫读；一句一线；问句要醒目",
)

# INFJ / I — narrative beats, pivot words (但是/所以) get breathing room
I_TYPE = _profile(
    tag="i_type",
    mbti="INFJ",
    pace=0.48,
    formality=0.5,
    detail=0.78,
    empathy_need=0.72,
    clarity=0.68,
    warmth=0.62,
    efficiency=0.42,
    precision=0.58,
    load_sensitivity=0.45,
    tags=("mbti_infj",),
    comprehension="先懂整体意思，再读转折；上下文不能丢",
)

# Neutral general listener — used by STRUCTURED mode (no specific person known)
NEUTRAL = _profile(
    tag="neutral",
    mbti="—",
    pace=0.5,
    formality=0.5,
    detail=0.6,
    empathy_need=0.5,
    clarity=0.78,
    warmth=0.5,
    efficiency=0.55,
    precision=0.6,
    load_sensitivity=0.55,
    comprehension="通用读者：句子别太长，因果分开",
)

PRESETS: dict[str, CeromeHumanProfile] = {
    "d_type": D_TYPE,
    "s_type": S_TYPE,
    "a_type": A_TYPE,
    "i_type": I_TYPE,
}


def normalize_listener_preset(raw: str | None) -> str | None:
    if not raw:
        return None
    key = raw.strip().lower().replace("-", "_")
    key = LISTENER_PRESET_ALIASES.get(key, key)
    return key if key in PRESETS else None


def get_listener_preset(raw: str | None) -> CeromeHumanProfile | None:
    key = normalize_listener_preset(raw)
    if not key:
        return None
    return PRESETS[key]


def preset_summary() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for key, p in PRESETS.items():
        rows.append(
            {
                "preset": key,
                "mbti_hint": PRESET_META.get(key, ""),
                "comprehension": p.l3.comprehension_gaps,
            }
        )
    return rows
