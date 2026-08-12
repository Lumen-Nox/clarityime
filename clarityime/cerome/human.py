"""Cerome L1–L5 tags for *human* audience/speaker modeling in ClarityIME.

Mapping (communication observer lens):
  L1 — baselines: pace, formality, detail, empathy need, load sensitivity
  L2 — values: clarity, warmth, efficiency, precision, humor
  L3 — relational (PRIVATE): lexicon, jargon, comprehension gaps
  L4 — context: formality setting, stress, novelty
  L5 — mood label for UX / clarify routing

Empathic accuracy in unconstrained settings is often ~20–35% (Ickes, 1997).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from clarityime.models import ContactProfile, SpeakerProfile

_CLIP = lambda x: max(0.0, min(1.0, float(x)))


@dataclass
class CeromeL1Comm:
    """Communication baselines (0–1)."""

    pace: float = 0.5
    formality: float = 0.5
    detail: float = 0.5
    empathy_need: float = 0.5
    load_sensitivity: float = 0.5

    def to_dict(self) -> dict[str, float]:
        return {k: round(_CLIP(v), 3) for k, v in asdict(self).items()}


@dataclass
class CeromeL2Values:
    clarity: float = 0.7
    warmth: float = 0.5
    efficiency: float = 0.5
    precision: float = 0.5
    humor: float = 0.3

    def to_dict(self) -> dict[str, float]:
        return {k: round(_CLIP(v), 3) for k, v in asdict(self).items()}

    def top_tags(self, n: int = 3) -> list[str]:
        ranked = sorted(self.to_dict().items(), key=lambda x: x[1], reverse=True)
        return [k for k, v in ranked[:n] if v >= 0.55]


@dataclass
class CeromeL3Relational:
    """Dyadic slot — never exported in mutual pairing bundles."""

    preferred_words: str = ""
    shared_jargon: str = ""
    comprehension_gaps: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "preferred_words": self.preferred_words,
            "shared_jargon": self.shared_jargon,
            "comprehension_gaps": self.comprehension_gaps,
        }


@dataclass
class CeromeL4Context:
    formality: float = 0.5
    stress: float = 0.3
    novelty: float = 0.5

    def to_dict(self) -> dict[str, float]:
        return {k: round(_CLIP(v), 3) for k, v in asdict(self).items()}


@dataclass
class CeromeL5Mood:
    label: str = "steady"

    def to_dict(self) -> dict[str, str]:
        return {"label": self.label}


@dataclass
class CeromeHumanProfile:
    l1: CeromeL1Comm = field(default_factory=CeromeL1Comm)
    l2: CeromeL2Values = field(default_factory=CeromeL2Values)
    l3: CeromeL3Relational = field(default_factory=CeromeL3Relational)
    l4: CeromeL4Context = field(default_factory=CeromeL4Context)
    l5: CeromeL5Mood = field(default_factory=CeromeL5Mood)

    def to_dict(self) -> dict[str, Any]:
        return {
            "L1": self.l1.to_dict(),
            "L2": self.l2.to_dict(),
            "L3": self.l3.to_dict(),
            "L4": self.l4.to_dict(),
            "L5": self.l5.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> CeromeHumanProfile:
        if not isinstance(data, dict):
            return cls()
        l1d = data.get("L1") or data.get("l1") or {}
        l2d = data.get("L2") or data.get("l2") or {}
        l3d = data.get("L3") or data.get("l3") or {}
        l4d = data.get("L4") or data.get("l4") or {}
        l5d = data.get("L5") or data.get("l5") or {}
        return cls(
            l1=CeromeL1Comm(
                pace=float(l1d.get("pace", 0.5)),
                formality=float(l1d.get("formality", 0.5)),
                detail=float(l1d.get("detail", 0.5)),
                empathy_need=float(l1d.get("empathy_need", 0.5)),
                load_sensitivity=float(l1d.get("load_sensitivity", 0.5)),
            ),
            l2=CeromeL2Values(
                clarity=float(l2d.get("clarity", 0.7)),
                warmth=float(l2d.get("warmth", 0.5)),
                efficiency=float(l2d.get("efficiency", 0.5)),
                precision=float(l2d.get("precision", 0.5)),
                humor=float(l2d.get("humor", 0.3)),
            ),
            l3=CeromeL3Relational(
                preferred_words=str(l3d.get("preferred_words", "")),
                shared_jargon=str(l3d.get("shared_jargon", "")),
                comprehension_gaps=str(l3d.get("comprehension_gaps", "")),
            ),
            l4=CeromeL4Context(
                formality=float(l4d.get("formality", 0.5)),
                stress=float(l4d.get("stress", 0.3)),
                novelty=float(l4d.get("novelty", 0.5)),
            ),
            l5=CeromeL5Mood(label=str(l5d.get("label", "steady"))),
        )

    def to_clarify_hints(self, *, name: str, relationship: str, age_hint: str = "") -> dict[str, str]:
        """Flatten Cerome tags into legacy hint dict for clarify engine."""
        style_parts: list[str] = []
        if self.l1.pace <= 0.35:
            style_parts.append("慢节奏")
        elif self.l1.pace >= 0.65:
            style_parts.append("快节奏")
        if self.l1.formality >= 0.65 or self.l4.formality >= 0.65:
            style_parts.append("正式")
        if self.l2.efficiency >= 0.65:
            style_parts.append("简短")
        if "简短" in style_parts or self.l2.efficiency >= 0.7:
            style_parts.append("口语")
        if self.l2.warmth >= 0.65:
            style_parts.append("温和")
        if self.l2.precision >= 0.7:
            style_parts.append("精确")

        comprehension = self.l3.comprehension_gaps.strip()
        if not comprehension and self.l1.load_sensitivity >= 0.6:
            comprehension = "易信息过载，需分步"
        if not comprehension and self.l2.clarity >= 0.75:
            comprehension = "需要结构化表达"

        words = self.l3.preferred_words.strip()
        if not words and self.l3.shared_jargon:
            words = self.l3.shared_jargon

        return {
            "name": name,
            "relationship": relationship,
            "style": " ".join(style_parts),
            "age": age_hint,
            "comprehension": comprehension,
            "words": words,
            "cerome_l5": self.l5.label,
            "cerome_l2_top": ",".join(self.l2.top_tags()),
        }

    def public_export(self) -> dict[str, Any]:
        """Safe slice for mutual pairing — no L3 secrets."""
        return {
            "L1": self.l1.to_dict(),
            "L2": self.l2.to_dict(),
            "L4": self.l4.to_dict(),
            "L5": self.l5.to_dict(),
        }


def _infer_l1_from_legacy(style: str, relationship: str) -> CeromeL1Comm:
    formality = 0.5
    if relationship in ("老师", "教授", "上级", "老板", "mentor"):
        formality = 0.75
    if "正式" in style:
        formality = max(formality, 0.7)
    if "口语" in style or "简短" in style:
        formality = min(formality, 0.4)
    detail = 0.5
    if "详细" in style or "精确" in style:
        detail = 0.75
    if "简短" in style:
        detail = 0.35
    pace = 0.45 if "慢节奏" in style else 0.55 if "快节奏" in style else 0.5
    return CeromeL1Comm(
        pace=pace,
        formality=formality,
        detail=detail,
        empathy_need=0.55 if "温和" in style else 0.45,
        load_sensitivity=0.55,
    )


def _infer_l2_from_legacy(style: str, comprehension: str) -> CeromeL2Values:
    return CeromeL2Values(
        clarity=0.75 if comprehension else 0.65,
        warmth=0.65 if "温和" in style else 0.45,
        efficiency=0.7 if "简短" in style or "口语" in style else 0.5,
        precision=0.7 if "精确" in style else 0.5,
        humor=0.35,
    )


def cerome_from_contact(profile: ContactProfile) -> CeromeHumanProfile:
    stored = profile.extra.get("cerome")
    if isinstance(stored, dict):
        base = CeromeHumanProfile.from_dict(stored)
    else:
        base = CeromeHumanProfile(
            l1=_infer_l1_from_legacy(profile.style_notes, profile.relationship),
            l2=_infer_l2_from_legacy(profile.style_notes, profile.comprehension_notes),
            l4=CeromeL4Context(
                formality=0.7
                if profile.relationship in ("老师", "教授", "上级", "老板")
                else 0.45
            ),
        )
    base.l3.preferred_words = profile.preferred_words or base.l3.preferred_words
    base.l3.comprehension_gaps = (
        profile.comprehension_notes or base.l3.comprehension_gaps
    )
    return base


def cerome_from_speaker(profile: SpeakerProfile) -> CeromeHumanProfile:
    stored = profile.extra.get("cerome")
    if isinstance(stored, dict):
        return CeromeHumanProfile.from_dict(stored)
    length_map = {"short": 0.35, "medium": 0.5, "long": 0.7}
    detail = length_map.get(profile.preferred_length, 0.5)
    return CeromeHumanProfile(
        l1=CeromeL1Comm(detail=detail, load_sensitivity=0.5),
        l2=CeromeL2Values(clarity=0.7, efficiency=0.55),
        l3=CeromeL3Relational(
            comprehension_gaps=profile.vague_phrases,
            shared_jargon=profile.oral_patterns,
        ),
        l5=CeromeL5Mood(label="steady"),
    )


def merge_cerome_into_contact(
    profile: ContactProfile,
    cerome: CeromeHumanProfile,
    *,
    write_legacy: bool = False,
) -> ContactProfile:
    profile.extra = dict(profile.extra)
    profile.extra["cerome"] = cerome.to_dict()
    if not write_legacy:
        return profile
    hints = cerome.to_clarify_hints(
        name=profile.name,
        relationship=profile.relationship,
        age_hint=profile.age_hint,
    )
    if hints.get("style"):
        profile.style_notes = hints["style"]
    if cerome.l3.preferred_words:
        profile.preferred_words = cerome.l3.preferred_words
    if cerome.l3.comprehension_gaps:
        profile.comprehension_notes = cerome.l3.comprehension_gaps
    return profile


def cerome_public_export(profile: ContactProfile) -> dict[str, Any]:
    return cerome_from_contact(profile).public_export()
