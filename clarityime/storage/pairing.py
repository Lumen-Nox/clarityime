"""Mutual profile import/export — safe contact bundles for two ClarityIME users.

Exports only audience-facing fields (name, relationship, style, comprehension).
Never includes local ids, preferred_words, age hints, or extra metadata.
"""

from __future__ import annotations

from typing import Any

from clarityime.models import ContactProfile
from clarityime.storage.contacts import ContactStore
from clarityime.cerome.human import cerome_public_export

BUNDLE_KIND = "clarityime.contact"
BUNDLE_VERSION = "1"

# Fields allowed in a shareable bundle (no secrets).
PUBLIC_FIELDS = frozenset({"name", "relationship", "style", "comprehension", "cerome"})

# Keys that must never appear in an exported bundle.
FORBIDDEN_BUNDLE_KEYS = frozenset(
    {
        "id",
        "preferred_words",
        "words",
        "age_hint",
        "age",
        "extra",
        "style_notes",
        "comprehension_notes",
        "correction_log",
        "oral_patterns",
        "vague_phrases",
    }
)


def export_contact_bundle(
    contact_id: int,
    store: ContactStore | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable contact bundle for mutual profile import."""
    db = store or ContactStore()
    profile = db.get_by_id(contact_id)
    if profile is None:
        raise ValueError(f"Contact not found: id={contact_id}")

    bundle = {
        "kind": BUNDLE_KIND,
        "version": BUNDLE_VERSION,
        "name": profile.name,
        "relationship": profile.relationship,
        "style": profile.style_notes,
        "comprehension": profile.comprehension_notes,
        "cerome": cerome_public_export(profile),
    }
    _assert_no_secrets(bundle)
    return bundle


def export_contact_bundle_by_name(
    name: str,
    store: ContactStore | None = None,
) -> dict[str, Any]:
    """Resolve contact by name and export a safe bundle."""
    db = store or ContactStore()
    profile = db.get_by_name(name.strip())
    if profile is None or profile.id is None:
        raise ValueError(f"Contact not found: {name}")
    return export_contact_bundle(profile.id, store=db)


def import_contact_bundle(
    bundle: dict[str, Any],
    store: ContactStore | None = None,
) -> ContactProfile:
    """Import a shared contact bundle into local storage."""
    if not isinstance(bundle, dict):
        raise ValueError("bundle must be a JSON object")

    name = (bundle.get("name") or "").strip()
    if not name:
        raise ValueError("name_required")

    kind = bundle.get("kind")
    if kind is not None and kind != BUNDLE_KIND:
        raise ValueError(f"unsupported bundle kind: {kind}")

    for key in FORBIDDEN_BUNDLE_KEYS:
        if key in bundle:
            raise ValueError(f"forbidden field in bundle: {key}")
    cerome = bundle.get("cerome")
    if isinstance(cerome, dict) and "L3" in cerome:
        raise ValueError("forbidden cerome L3 in bundle")

    db = store or ContactStore()
    existing = db.get_by_name(name)
    cerome_in = bundle.get("cerome")
    profile = ContactProfile(
        id=existing.id if existing else None,
        name=name,
        style_notes=(bundle.get("style") or bundle.get("style_notes") or "").strip(),
        preferred_words=existing.preferred_words if existing else "",
        relationship=(bundle.get("relationship") or "").strip(),
        age_hint=existing.age_hint if existing else "",
        comprehension_notes=(
            bundle.get("comprehension") or bundle.get("comprehension_notes") or ""
        ).strip(),
        extra=dict(existing.extra if existing else {}),
    )
    if isinstance(cerome_in, dict):
        from clarityime.cerome.human import CeromeHumanProfile, merge_cerome_into_contact

        profile = merge_cerome_into_contact(
            profile, CeromeHumanProfile.from_dict(cerome_in), write_legacy=True
        )
    return db.upsert(profile)


def _assert_no_secrets(bundle: dict[str, Any]) -> None:
    for key in bundle:
        if key in FORBIDDEN_BUNDLE_KEYS:
            raise ValueError(f"secret field leaked into bundle: {key}")
