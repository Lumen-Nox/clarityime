"""Tests for mutual contact export/import bundles and HTTP endpoints."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

from clarityime.models import ContactProfile
from clarityime.server import ClarityHandler, ThreadingHTTPServer
from clarityime.storage.contacts import ContactStore
from clarityime.storage.pairing import (
    BUNDLE_KIND,
    FORBIDDEN_BUNDLE_KEYS,
    export_contact_bundle,
    export_contact_bundle_by_name,
    import_contact_bundle,
)
from tests._auth_util import auth_headers, bind_test_data_dir


class PairingModuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.store = ContactStore(Path(self._tmpdir.name) / "contacts.db")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_export_contains_public_fields_only(self) -> None:
        saved = self.store.upsert(
            ContactProfile(
                id=None,
                name="Alex",
                style_notes="formal",
                preferred_words="secret phrase",
                relationship="teacher",
                age_hint="40s",
                comprehension_notes="jumps to conclusions",
                extra={"token": "must-not-leak"},
            )
        )
        assert saved.id is not None
        bundle = export_contact_bundle(saved.id, store=self.store)

        self.assertEqual(bundle["kind"], BUNDLE_KIND)
        self.assertEqual(bundle["name"], "Alex")
        self.assertEqual(bundle["relationship"], "teacher")
        self.assertEqual(bundle["style"], "formal")
        self.assertEqual(bundle["comprehension"], "jumps to conclusions")
        for key in FORBIDDEN_BUNDLE_KEYS:
            self.assertNotIn(key, bundle)
        self.assertNotIn("preferred_words", bundle)
        self.assertNotIn("extra", bundle)

    def test_export_by_name(self) -> None:
        self.store.upsert(
            ContactProfile(id=None, name="Sam", relationship="friend", style_notes="casual")
        )
        bundle = export_contact_bundle_by_name("Sam", store=self.store)
        self.assertEqual(bundle["name"], "Sam")
        self.assertEqual(bundle["style"], "casual")

    def test_import_creates_contact(self) -> None:
        saved = import_contact_bundle(
            {
                "kind": BUNDLE_KIND,
                "version": "1",
                "name": "Jordan",
                "relationship": "colleague",
                "style": "direct",
                "comprehension": "needs context first",
            },
            store=self.store,
        )
        self.assertEqual(saved.name, "Jordan")
        self.assertEqual(saved.relationship, "colleague")
        self.assertEqual(saved.style_notes, "direct")
        self.assertEqual(saved.comprehension_notes, "needs context first")
        self.assertEqual(saved.preferred_words, "")

    def test_import_merges_existing_without_overwriting_secrets(self) -> None:
        self.store.upsert(
            ContactProfile(
                id=None,
                name="Jordan",
                preferred_words="keep-me",
                age_hint="30",
                style_notes="old-style",
            )
        )
        saved = import_contact_bundle(
            {
                "name": "Jordan",
                "relationship": "peer",
                "style": "new-style",
                "comprehension": "misreads tone",
            },
            store=self.store,
        )
        self.assertEqual(saved.preferred_words, "keep-me")
        self.assertEqual(saved.age_hint, "30")
        self.assertEqual(saved.style_notes, "new-style")
        self.assertEqual(saved.relationship, "peer")

    def test_import_rejects_forbidden_fields(self) -> None:
        with self.assertRaises(ValueError):
            import_contact_bundle({"name": "X", "preferred_words": "no"}, store=self.store)

    def test_round_trip(self) -> None:
        created = self.store.upsert(
            ContactProfile(
                id=None,
                name="Riley",
                relationship="parent",
                style_notes="gentle",
                comprehension_notes="literal reader",
            )
        )
        assert created.id is not None
        bundle = export_contact_bundle(created.id, store=self.store)
        imported = import_contact_bundle(bundle, store=self.store)
        self.assertEqual(imported.name, "Riley")
        self.assertEqual(imported.relationship, "parent")
        self.assertEqual(imported.style_notes, "gentle")
        self.assertEqual(imported.comprehension_notes, "literal reader")


class ContactExportHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        import clarityime.storage.contacts as contacts_mod

        self._contacts_mod = contacts_mod
        self._tmpdir = tempfile.TemporaryDirectory()
        self._db_path = Path(self._tmpdir.name) / "contacts.db"
        self._orig_default = contacts_mod.DEFAULT_DB
        contacts_mod.DEFAULT_DB = self._db_path
        self._token = bind_test_data_dir(Path(self._tmpdir.name) / "data")

        store = ContactStore()
        store.upsert(
            ContactProfile(
                id=None,
                name="HTTP Contact",
                relationship="mentor",
                style_notes="concise",
                comprehension_notes="needs examples",
            )
        )

        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), ClarityHandler)
        self._port = self._httpd.server_address[1]
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def tearDown(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        self._contacts_mod.DEFAULT_DB = self._orig_default
        self._tmpdir.cleanup()

    def _conn(self) -> HTTPConnection:
        return HTTPConnection("127.0.0.1", self._port, timeout=5)

    def test_get_export_by_name(self) -> None:
        conn = self._conn()
        conn.request("GET", "/v1/contacts/export?name=HTTP%20Contact")
        resp = conn.getresponse()
        self.assertEqual(resp.status, 200)
        body = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(body["name"], "HTTP Contact")
        self.assertEqual(body["style"], "concise")
        self.assertNotIn("preferred_words", body)
        self.assertIn("cerome", body)
        conn.close()

    def test_get_export_missing_name(self) -> None:
        conn = self._conn()
        conn.request("GET", "/v1/contacts/export?name=Nobody")
        resp = conn.getresponse()
        self.assertEqual(resp.status, 404)
        conn.close()

    def test_post_import(self) -> None:
        payload = {
            "kind": BUNDLE_KIND,
            "name": "Imported Via HTTP",
            "relationship": "friend",
            "style": "chatty",
            "comprehension": "skims long text",
        }
        conn = self._conn()
        conn.request(
            "POST",
            "/v1/contacts/import",
            body=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                **auth_headers(self._token),
            },
        )
        resp = conn.getresponse()
        self.assertEqual(resp.status, 200)
        body = json.loads(resp.read().decode("utf-8"))
        self.assertTrue(body["ok"])
        self.assertEqual(body["name"], "Imported Via HTTP")
        conn.close()

        store = ContactStore(self._db_path)
        profile = store.get_by_name("Imported Via HTTP")
        self.assertIsNotNone(profile)
        assert profile is not None
        self.assertEqual(profile.style_notes, "chatty")


if __name__ == "__main__":
    unittest.main()
