"""Security regression tests — loopback bind + consent defaults."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from clarityime.consent import load_consent, save_consent
from clarityime.security import assert_loopback_host, normalize_loopback_host
from tests._auth_util import bind_test_data_dir


class LoopbackHostTests(unittest.TestCase):
    def test_accepts_loopback_variants(self) -> None:
        for host in ("127.0.0.1", "localhost", "::1"):
            self.assertIn(normalize_loopback_host(host), ("127.0.0.1", "::1", "localhost"))

    def test_rejects_all_interfaces(self) -> None:
        with self.assertRaises(SystemExit):
            assert_loopback_host("0.0.0.0")

    def test_rejects_lan_ip(self) -> None:
        with self.assertRaises(SystemExit):
            assert_loopback_host("192.168.1.1")


class ConsentDefaultsTests(unittest.TestCase):
    def test_defaults_off(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "consent.json"
            c = load_consent(path)
            self.assertFalse(c["cloud_sync"])
            self.assertFalse(c["aggregate_research"])


class ConsentPersistenceTests(unittest.TestCase):
    def test_save_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "consent.json"
            saved = save_consent(
                cloud_sync=True,
                aggregate_research=False,
                path=path,
            )
            self.assertTrue(saved["cloud_sync"])
            self.assertFalse(saved["aggregate_research"])
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(loaded["cloud_sync"])


class LocalApiAuthTests(unittest.TestCase):
    def test_fresh_token_creation_does_not_deadlock(self) -> None:
        import clarityime.api_auth as api_auth

        with tempfile.TemporaryDirectory() as tmp:
            bind_test_data_dir(Path(tmp) / "data")
            token = api_auth.ensure_local_api_token()
            self.assertGreater(len(token), 16)
            plain = Path(tmp) / "data" / ".local_api_token"
            self.assertTrue(plain.is_file())

    def test_mutating_post_without_token_rejected(self) -> None:
        import threading
        from http.client import HTTPConnection
        from http.server import ThreadingHTTPServer

        from clarityime.server import ClarityHandler

        tmp = tempfile.TemporaryDirectory()
        bind_test_data_dir(Path(tmp.name) / "data")
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), ClarityHandler)
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            conn = HTTPConnection("127.0.0.1", port, timeout=5)
            conn.request(
                "POST",
                "/v1/consent",
                body=b'{"cloud_sync": true}',
                headers={"Content-Type": "application/json"},
            )
            resp = conn.getresponse()
            self.assertEqual(resp.status, 401)
            conn.close()
        finally:
            httpd.shutdown()
            httpd.server_close()
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
