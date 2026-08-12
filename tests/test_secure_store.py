"""CIM1 seal/open + field encryption at rest."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import clarityime.paths as paths_mod
from clarityime.models import ContactProfile
from clarityime.secure_store import is_sealed, open_text, seal_text
from clarityime.storage.contacts import ContactStore
from clarityime.storage import contacts as contacts_mod


class SecureStoreTests(unittest.TestCase):
    def test_seal_roundtrip(self) -> None:
        plain = "secret lexicon -> mapped"
        token = seal_text(plain)
        self.assertTrue(is_sealed(token))
        self.assertEqual(open_text(token), plain)

    def test_contacts_encrypt_preferred_words_on_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "data"
            paths_mod.app_data_dir = lambda: data  # type: ignore[method-assign]
            db = data / "contacts.db"
            contacts_mod.DEFAULT_DB = db
            store = ContactStore(db)
            store.upsert(
                ContactProfile(
                    id=None,
                    name="Enc",
                    preferred_words="口语->书面",
                    relationship="friend",
                )
            )
            raw = db.read_bytes()
            self.assertNotIn("口语->书面".encode(), raw)
            loaded = store.get_by_name("Enc")
            assert loaded is not None
            self.assertEqual(loaded.preferred_words, "口语->书面")


if __name__ == "__main__":
    unittest.main()
