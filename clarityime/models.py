"""Shared data structures for ASR → clarification pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AudienceMode(str, Enum):
    """Who the clarified text is intended for (面向对象)."""

    DEFAULT = "default"
    CONTACT = "contact"
    STRUCTURED = "structured"


def parse_audience_mode(raw: str | None) -> AudienceMode:
    """Normalize mode id; legacy ``ai`` maps to ``structured``."""
    v = (raw or "default").strip().lower()
    if v in ("ai", "structured"):
        return AudienceMode.STRUCTURED
    try:
        return AudienceMode(v)
    except ValueError:
        return AudienceMode.DEFAULT


@dataclass
class AsrCandidate:
    text: str
    confidence: float = 0.0
    source: str = "primary"


@dataclass
class AsrResult:
    candidates: list[AsrCandidate] = field(default_factory=list)
    language: str = "zh"
    backend: str = "local"
    used_network: bool = False

    @property
    def primary(self) -> str:
        return self.candidates[0].text if self.candidates else ""

    def top_n(self, n: int = 3) -> list[str]:
        return [c.text for c in self.candidates[:n]]


@dataclass
class ContactProfile:
    """Audience object — a specific person, not a generic role template."""

    id: int | None
    name: str
    style_notes: str = ""
    preferred_words: str = ""
    relationship: str = ""
    age_hint: str = ""
    comprehension_notes: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_clarify_hints(self) -> dict[str, str]:
        from clarityime.cerome.human import cerome_from_contact

        return cerome_from_contact(self).to_clarify_hints(
            name=self.name,
            relationship=self.relationship,
            age_hint=self.age_hint,
        )

    def to_polish_hints(self) -> dict[str, str]:
        return self.to_clarify_hints()


@dataclass
class SpeakerProfile:
    """Speaker modeling — how *I* talk, so others understand me better."""

    display_name: str = "me"
    oral_patterns: str = ""
    vague_phrases: str = ""
    preferred_length: str = "medium"
    correction_log: list[dict[str, str]] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def cerome_tags(self) -> dict[str, Any]:
        from clarityime.cerome.human import cerome_from_speaker

        return cerome_from_speaker(self).to_dict()


@dataclass
class ClarifyRequest:
    asr: AsrResult
    mode: AudienceMode
    contact: ContactProfile | None = None
    speaker: SpeakerProfile | None = None


@dataclass
class ClarifyResult:
    raw_primary: str
    clarified: str
    mode: AudienceMode
    used_network: bool
    original: str = ""
    for_listener: str = ""
    notes: list[str] = field(default_factory=list)
    all_candidates_considered: list[str] = field(default_factory=list)

    @property
    def polished(self) -> str:
        return self.clarified


PolishRequest = ClarifyRequest
PolishResult = ClarifyResult
