"""Cerome L1-L5 human profile tags for ClarityIME."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from clarityime.cerome.human import (
    CeromeHumanProfile,
    CeromeL2Values,
    cerome_from_contact,
    cerome_public_export,
)
from clarityime.models import ContactProfile
from clarityime.storage.contacts import ContactStore
from clarityime.storage import contacts as contacts_mod
from clarityime.storage.pairing import export_contact_bundle, import_contact_bundle


class CeromeProfileTests(unittest.TestCase):
    def test_legacy_contact_infers_cerome(self) -> None:
        p = ContactProfile(
            id=None,
            name="Teacher",
            relationship="老师",
            style_notes="简短 正式",
            comprehension_notes="需要例子",
        )
        cerome = cerome_from_contact(p)
        hints = cerome.to_clarify_hints(name=p.name, relationship=p.relationship)
        self.assertIn("正式", hints["style"])
        self.assertIn("cerome_l2_top", hints)

    def test_l2_efficiency_affects_hints(self) -> None:
        cerome = CeromeHumanProfile(l2=CeromeL2Values(efficiency=0.9, clarity=0.8))
        hints = cerome.to_clarify_hints(name="Sam", relationship="friend")
        self.assertIn("简短", hints["style"])

    def test_public_export_excludes_l3(self) -> None:
        p = ContactProfile(
            id=None,
            name="Sam",
            preferred_words="secret->word",
            relationship="friend",
        )
        pub = cerome_public_export(p)
        self.assertIn("L1", pub)
        self.assertNotIn("L3", pub)

    def test_pairing_bundle_includes_cerome_public(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "contacts.db"
            contacts_mod.DEFAULT_DB = db
            store = ContactStore(db)
            saved = store.upsert(
                ContactProfile(
                    id=None,
                    name="Alex",
                    relationship="mentor",
                    style_notes="精确",
                    comprehension_notes="skips steps",
                )
            )
            assert saved.id is not None
            bundle = export_contact_bundle(saved.id, store=store)
            self.assertIn("cerome", bundle)
            self.assertIn("L2", bundle["cerome"])
            self.assertNotIn("L3", bundle["cerome"])

    def test_import_cerome_merges_without_leaking_words(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "contacts.db"
            contacts_mod.DEFAULT_DB = db
            store = ContactStore(db)
            bundle = {
                "kind": "clarityime.contact",
                "name": "Jordan",
                "relationship": "colleague",
                "style": "direct",
                "comprehension": "needs context",
                "cerome": {
                    "L1": {
                        "pace": 0.6,
                        "formality": 0.4,
                        "detail": 0.5,
                        "empathy_need": 0.5,
                        "load_sensitivity": 0.5,
                    },
                    "L2": {
                        "clarity": 0.8,
                        "warmth": 0.4,
                        "efficiency": 0.7,
                        "precision": 0.6,
                        "humor": 0.2,
                    },
                    "L4": {"formality": 0.4, "stress": 0.2, "novelty": 0.5},
                    "L5": {"label": "steady"},
                },
            }
            saved = import_contact_bundle(bundle, store=store)
            self.assertEqual(saved.name, "Jordan")
            self.assertIn("cerome", saved.extra)
            self.assertEqual(saved.preferred_words, "")


if __name__ == "__main__":
    unittest.main()
