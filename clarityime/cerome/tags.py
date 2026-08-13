"""Listener tags — the ONLY thing rules are allowed to key on.

Hard rule:
    Rules key on **tags**, not on people; **never infer one tag from another** (one documented exception below).

The bug this file exists to prevent: reading "INTJ" and concluding "knows tech
jargon". Personality says how someone *processes*; it says nothing about what
vocabulary they *own*.

The one licensed derivation
---------------------------
    personality / self-report  →  PROCESSING     ✅  that is what those
                                                     instruments measure
    anything                   →  DOMAIN         ❌  except HOBBY / DOMAIN /
                                                     SOURCE tags, which are
                                                     statements about what the
                                                     person actually does

Enforced at runtime by an assert in :func:`derive_processing_tags` and by
``tests/test_comprehension.py::test_personality_never_implies_domain_knowledge``.

The vocabulary itself lives in :mod:`clarityime.cerome.tag_registry` (bilingual,
~110 tags across 12 families).
"""

from __future__ import annotations

from dataclasses import dataclass

from clarityime.cerome.tag_registry import (
    FAMILIES,
    REGISTRY,
    catalog,
    expand,
    label,
    quick_setup,
    search,
    tag_def,
)

__all__ = [
    "ListenerTags",
    "UnknownTagError",
    "ALL_TAGS",
    "DOMAIN_TAGS",
    "REGISTER_TAGS",
    "PROCESSING_TAGS",
    "validate",
    "parse_tags",
    "derive_processing_tags",
    "listener_tags",
    "describe",
    "catalog",
    "search",
    "quick_setup",
]


def _family(name: str) -> frozenset[str]:
    return frozenset(t for t, d in REGISTRY.items() if d.family == name)


DOMAIN_TAGS = _family("domain")
REGISTER_TAGS = _family("register")
PROCESSING_TAGS = _family("processing")
PERSONALITY_TAGS = (
    _family("mbti") | _family("function") | _family("bigfive") | _family("enneagram")
)
ALL_TAGS = frozenset(REGISTRY)


class UnknownTagError(ValueError):
    pass


@dataclass(frozen=True)
class ListenerTags:
    tags: frozenset[str]

    def has(self, tag: str) -> bool:
        return tag in self.tags

    def domains(self) -> frozenset[str]:
        """Vocabulary this person owns — from DOMAIN, HOBBY and SOURCE grants."""
        _, granted = expand(set(self.tags))
        return frozenset(granted)

    def knows(self, domain: str) -> bool:
        return domain in self.domains()

    def family(self, name: str) -> list[str]:
        return sorted(t for t in self.tags if (d := tag_def(t)) and d.family == name)

    def sorted(self) -> list[str]:
        return sorted(self.tags)

    def __or__(self, other: "ListenerTags") -> "ListenerTags":
        return ListenerTags(self.tags | other.tags)


def validate(tags) -> ListenerTags:
    unknown = sorted(set(tags) - ALL_TAGS)
    if unknown:
        near = {u: _suggest(u) for u in unknown}
        raise UnknownTagError(f"unknown tag(s): {unknown}; did you mean {near}?")
    return ListenerTags(frozenset(tags))


def _suggest(bad: str) -> list[str]:
    b = bad.lower().strip()
    return sorted(t for t in ALL_TAGS if b in t or t in b)[:3]


def parse_tags(raw) -> ListenerTags:
    """Accept 'mbti_intj,hobby_gaming' or a list. Also accepts bare 'INTJ'."""
    if not raw:
        return ListenerTags(frozenset())
    items = (
        [t.strip() for t in raw.replace(";", ",").split(",") if t.strip()]
        if isinstance(raw, str)
        else [str(t).strip() for t in raw if str(t).strip()]
    )
    normed = []
    for t in items:
        low = t.lower()
        if low not in REGISTRY and f"mbti_{low}" in REGISTRY:
            low = f"mbti_{low}"  # 'INTJ' → 'mbti_intj'
        normed.append(low)
    return validate(normed)


# --------------------------------------------------------------------------- #
# Cerome numbers → PROCESSING tags (documented, deterministic, no domains)
# --------------------------------------------------------------------------- #

NUMBER_RULES: tuple[tuple[str, str], ...] = (
    ("conclusion_first", "L2.efficiency ≥ .7 or L1.pace ≥ .65"),
    ("cause_explicit", "L2.precision ≥ .7 or L2.clarity ≥ .75"),
    ("short_chunks", "L1.load_sensitivity ≥ .7"),
    ("long_chunks", "L1.load_sensitivity ≤ .4"),
    ("tone_visible", "L2.warmth ≥ .7 or L1.empathy_need ≥ .7"),
    ("no_padding", "L2.efficiency ≥ .8 and L2.warmth ≤ .4"),
    ("context_first", "L1.detail ≥ .7 and L1.pace ≤ .55"),
    ("value_order", "always — every listener weighs supports"),
)


def derive_processing_tags(cerome) -> ListenerTags:
    """Cerome L1/L2 + declared tags → processing tags. **Never a domain tag.**"""
    l1, l2 = cerome.l1, cerome.l2
    out: set[str] = {"value_order"}
    if l2.efficiency >= 0.7 or l1.pace >= 0.65:
        out.add("conclusion_first")
    if l2.precision >= 0.7 or l2.clarity >= 0.75:
        out.add("cause_explicit")
    if l1.load_sensitivity >= 0.7:
        out.add("short_chunks")
    if l1.load_sensitivity <= 0.4:
        out.add("long_chunks")
    if l2.warmth >= 0.7 or l1.empathy_need >= 0.7:
        out.add("tone_visible")
    if l2.efficiency >= 0.8 and l2.warmth <= 0.4:
        out.add("no_padding")
    if l1.detail >= 0.7 and l1.pace <= 0.55:
        out.add("context_first")

    # Declared tags contribute their documented processing implications.
    implied, _domains_ignored_here = expand(set(getattr(cerome, "tags", None) or []))
    out |= implied

    assert not (out & DOMAIN_TAGS), "processing derivation must never emit a domain tag"
    assert out <= PROCESSING_TAGS, f"non-processing tag leaked: {out - PROCESSING_TAGS}"
    return ListenerTags(frozenset(out))


def listener_tags(cerome) -> ListenerTags:
    """Declared tags ∪ derived processing tags."""
    declared = parse_tags(getattr(cerome, "tags", None))
    return declared | derive_processing_tags(cerome)


def describe(tags: ListenerTags, lang: str = "zh") -> list[str]:
    """Bilingual, grouped, for the settings UI and audit notes."""
    sep = "、" if lang.startswith("zh") else ", "
    lines: list[str] = []
    for fam in FAMILIES:
        got = tags.family(fam)
        if not got:
            continue
        lines.append(f"{fam}: " + sep.join(label(t, lang) for t in got))
    return lines
