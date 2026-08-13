"""Cerome observer tags for ClarityIME human profiles (audience + speaker).

Cerome L1–L5 here = *communication-facing tags* for clarify routing.
Observer framework (not agent substrate) — see Ideas/Aura/Cerome是observer框架.
"""

from clarityime.cerome.human import (
    CeromeHumanProfile,
    cerome_from_contact,
    cerome_from_speaker,
    cerome_public_export,
    merge_cerome_into_contact,
)

__all__ = [
    "CeromeHumanProfile",
    "cerome_from_contact",
    "cerome_from_speaker",
    "cerome_public_export",
    "merge_cerome_into_contact",
]
