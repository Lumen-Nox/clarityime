"""Auto-build a contact's profile from feedback — like a photo app learning a
face, not like an LLM guessing a personality.

Design goal: users should not have to manually create an audience object for
every recipient. The system learns from repeated ratings on *this contact's*
messages (threshold 3, pure counting, no LLM), the same way a photo app
learns a face from confirmations.

Why this does NOT reopen the "no inference" rule
--------------------------------------------------
``cerome/tags.py`` bans inferring a DOMAIN from a PERSONALITY tag (reading
"INTJ" and concluding "knows tech jargon" — that is a guess about someone we
have never gotten feedback from). This module never does that. It only reacts
to *behavioural evidence from this exact contact*:

    "we simplified 「排期」 for them, they rated it bad, 3 times, 0 times good"
        → they clearly already understood 「排期」; simplifying it was
          unwanted, not helpful. Stop simplifying that domain for them.

That is not a personality guess. It is the same category of evidence as a
face-recognition app being told "no, that's not Dad" three times before it
stops suggesting the tag — pure counting over logged events, fully
deterministic (same evidence history → same outcome, see
``AUTO_LEARN_THRESHOLD``), and fully auditable (every count has a
timestamped evidence list a human can read and undo).

No AI is used anywhere in this file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from clarityime.clarify.paraphrase import domain_of

__all__ = [
    "AUTO_LEARN_THRESHOLD",
    "LearningUpdate",
    "record_feedback",
    "auto_learned_domains",
    "forget_domain",
    "next_auto_object_name",
]

#: net (bad - good) mentions of a domain, on THIS contact, before we trust the
#: evidence enough to stop translating that domain for them. Three independent
#: "no, that was unnecessary" beats one — matches the human-review threshold
#: used elsewhere in this codebase for jargon promotion (see
#: docs/COMPREHENSION_MODEL.md §7.6) rather than inventing a new bar.
AUTO_LEARN_THRESHOLD = 3


@dataclass
class LearningUpdate:
    """What changed in a contact's ``extra`` dict, for the caller to persist
    and for the settings UI to show ("why did you add this tag?")."""

    extra: dict[str, Any]
    newly_learned: list[str] = field(default_factory=list)
    newly_forgotten: list[str] = field(default_factory=list)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_feedback(
    extra: dict[str, Any],
    *,
    rating: str,
    substitutions: list[dict[str, str]] | None = None,
    lang: str = "zh",
) -> LearningUpdate:
    """Fold one rated message into a contact's ``extra`` dict.

    Pure function: takes the contact's current ``extra`` (as loaded from
    ``ContactStore``), returns a new ``extra`` plus what changed. Caller is
    responsible for persisting it (``ContactStore.upsert``) — this module
    never touches storage or the audited ``JARGON_TABLE`` itself.
    """
    extra = dict(extra)
    counts: dict[str, dict[str, Any]] = {
        k: dict(v) for k, v in (extra.get("domain_feedback_counts") or {}).items()
    }
    learned: set[str] = set(extra.get("auto_learned_domains") or [])
    newly_learned: list[str] = []
    newly_forgotten: list[str] = []

    domains_in_message = {
        d for s in (substitutions or []) if s.get("kind") == "jargon"
        for d in [domain_of(s.get("from", ""), lang)]
        if d
    }

    if rating in ("good", "bad") and domains_in_message:
        for domain in domains_in_message:
            slot = counts.setdefault(domain, {"good": 0, "bad": 0, "evidence": []})
            slot[rating] += 1
            slot["evidence"] = (slot.get("evidence") or [])[-9:] + [
                {"rating": rating, "at": _now()}
            ]
            net = slot["bad"] - slot["good"]
            if domain not in learned and net >= AUTO_LEARN_THRESHOLD:
                learned.add(domain)
                newly_learned.append(domain)
                slot["bad"] = slot["good"] = 0  # fresh window; see reversal below
            elif domain in learned and net <= -AUTO_LEARN_THRESHOLD:
                # Reversed just as automatically: enough "good" ratings after
                # learning means simplifying that domain was fine after all —
                # same as a photo app un-learning a bad face match. Compared
                # against the fresh window opened when we first learned it,
                # so this needs AUTO_LEARN_THRESHOLD *new* good ratings, not
                # "cancel out the original bad ones".
                learned.discard(domain)
                newly_forgotten.append(domain)
                slot["bad"] = slot["good"] = 0  # fresh window after a reversal

    extra["domain_feedback_counts"] = counts
    extra["auto_learned_domains"] = sorted(learned)
    return LearningUpdate(extra=extra, newly_learned=newly_learned, newly_forgotten=newly_forgotten)


def auto_learned_domains(extra: dict[str, Any]) -> list[str]:
    return sorted(extra.get("auto_learned_domains") or [])


def forget_domain(extra: dict[str, Any], domain: str) -> dict[str, Any]:
    """Manual override — the equivalent of renaming a mis-recognised face.
    Removes the domain and resets its counters so evidence starts fresh."""
    extra = dict(extra)
    learned = set(extra.get("auto_learned_domains") or [])
    learned.discard(domain)
    extra["auto_learned_domains"] = sorted(learned)
    counts = {k: dict(v) for k, v in (extra.get("domain_feedback_counts") or {}).items()}
    counts.pop(domain, None)
    extra["domain_feedback_counts"] = counts
    return extra


def next_auto_object_name(existing_names: list[str] | set[str], *, lang: str = "zh") -> str:
    """Album-style placeholder name when the user says yes without typing one.

    ``对象 1``, ``对象 2``, … (or ``Person 1`` in English) — deterministic,
    skips names already taken so a second yes never collides.
    """
    prefix = "对象 " if lang.startswith("zh") else "Person "
    taken = set(existing_names)
    n = 1
    while f"{prefix}{n}" in taken:
        n += 1
    return f"{prefix}{n}"
