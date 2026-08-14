"""Cross-circle analogies — same proposition, in a word the listener already owns.

> Mix this into daily for_listener output, not a separate
> "ask first" mode. Chat-community pattern: 「我是玩 A 的，能不能用 A 的方式
> 给我解释」→ 「这个就类似于你们的 X」.

This is still T1, not generation. Every mapping is an audited 1:1 pair
(source term → analog term in a *different* domain). The engine never invents
a comparison; if no row matches a domain the listener actually owns, we fall
back to the plain-language gloss in ``JARGON_TABLE`` — same as before.

Why this does not violate NO_NEW_CONTENT
----------------------------------------
The parenthetical is packaging, like T1's 「ddl → 截止时间」. It is applied
*before* invariant checks (those run on the post-substitution baseline vs
layout). The analog term comes from a human-reviewed table, not an LLM.
We keep the speaker's original word (「守椅（就像架点）」) so the claim is
not replaced by a different game's ontology — Gentner (1983) structure-mapping:
the relation is "this plays the same role as X", not "this IS X".

Determinism: if several owned domains have a mapping, pick the
alphabetically-first domain id (same rule as ``reading_lang``).
"""

from __future__ import annotations

__all__ = [
    "ANALOGY_TABLES",
    "pick_analogy",
    "format_analogy",
]

#: term → {listener_domain: analog_term}
#: Only high-confidence role mappings. Ambiguous / cute-but-wrong pairs stay out
#: (same bar as AMBIGUOUS_BLOCKLIST). Reverse mappings are listed explicitly;
#: we never auto-invert (「架点≈守椅」is true; auto-inverting a one-way pair
#: would invent a comparison).
ANALOGY_TABLE_ZH: dict[str, dict[str, str]] = {
    "守椅": {"fps": "架点"},
    "架点": {"asym_horror": "守椅"},
    "遛鬼": {"moba": "风筝", "fps": "风筝"},
    "秒倒": {"fps": "秒杀", "moba": "秒杀"},
    "落地成盒": {"asym_horror": "秒倒", "moba": "秒杀"},
    "开团": {"fps": "冲点"},
    "送人头": {"fps": "白给"},
    "金手指": {"gaming": "开挂"},
    "开挂": {"webnovel": "金手指"},
    "穿越": {"anime": "异世界"},
    "异世界": {"webnovel": "穿越"},
    "本命": {"gaming": "主玩"},
    "主玩": {"fandom": "本命"},
    "补番": {"film_tv": "补剧"},
    "补剧": {"anime": "补番"},
    "彩蛋": {"gaming": "隐藏关"},
    "隐藏关": {"film_tv": "彩蛋"},
}

ANALOGY_TABLE_EN: dict[str, dict[str, str]] = {
    "gank": {"fps": "flank"},
    "camping": {"asym_horror": "face-camping"},
    "feeding": {"fps": "taking bad fights"},
    "isekai": {"webnovel": "transmigration"},
    "transmigration": {"anime": "isekai"},
    "golden finger": {"gaming": "cheat"},
    "easter egg": {"gaming": "secret level"},
}

ANALOGY_TABLES: dict[str, dict[str, dict[str, str]]] = {
    "zh": ANALOGY_TABLE_ZH,
    "en": ANALOGY_TABLE_EN,
}


def pick_analogy(
    term: str,
    *,
    src_domain: str,
    owned: frozenset[str] | set[str],
    lang: str = "zh",
) -> tuple[str, str] | None:
    """Return ``(listener_domain, analog_term)`` or None.

    Never picks the term's own domain (that would be a tautology). Never
    guesses a domain the listener did not declare / auto-learn.
    """
    options = ANALOGY_TABLES.get(lang, {}).get(term)
    if not options:
        return None
    hits = sorted(d for d in options if d in owned and d != src_domain)
    if not hits:
        return None
    dest = hits[0]
    analog = options[dest]
    if not analog or analog == term:
        return None
    return dest, analog


def format_analogy(term: str, analog: str, lang: str = "zh") -> str:
    """Keep the speaker's word, attach the listener's equivalent.

    Mixed into the sentence, not a second message.
    """
    code = (lang or "zh").lower()
    if code.startswith("zh") or code == "yue":
        return f"{term}（就像{analog}）"
    if code.startswith("ja"):
        return f"{term}（{analog}みたい）"
    if code.startswith("ko"):
        return f"{term} ({analog} 같은 거)"
    return f"{term} (like {analog})"
