"""POST/GET /v1/bundles and feedback-triggered utterance bundle persistence."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from clarityime.server import ClarityHandler
from clarityime.storage import utterance_bundle as bundle_mod
from clarityime.storage.utterance_bundle import create_bundle, load_bundle, save_bundle
from clarityime.storage import speaker as speaker_mod
from clarityime.storage.speaker import SpeakerStore
from tests._auth_util import auth_headers, bind_test_data_dir


SAMPLE = "嗯那个你好，就是我想问一下这个项目大概什么时候能做完啊"
NBEST = [
    SAMPLE,
    "我想问一下这个项目大概什么时候能做完",
]
CANDIDATES = [
    {"text": "我想问一下这个项目大概什么时候能做完？", "label": "standard"},
    {"text": "这个项目大概什么时候能做完？", "label": "concise"},
]


class UtteranceBundleStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        bundle_mod._BUNDLES_ROOT = Path(self._tmpdir.name) / "bundles"

    def tearDown(self) -> None:
        bundle_mod._BUNDLES_ROOT = None
        self._tmpdir.cleanup()

    def test_create_bundle_has_id_and_timestamp(self) -> None:
        bundle = create_bundle(SAMPLE, NBEST, CANDIDATES, "default")
        self.assertTrue(bundle["bundle_id"])
        self.assertTrue(bundle["timestamp"])
        self.assertEqual(bundle["kind"], "clarityime.utterance")
        self.assertEqual(bundle["raw"], SAMPLE)
        self.assertEqual(bundle["nbest"], NBEST)
        self.assertEqual(bundle["candidates"], CANDIDATES)
        self.assertEqual(bundle["mode"], "default")
        self.assertIsNone(bundle["picked"])

    def test_save_and_load_roundtrip(self) -> None:
        bundle = create_bundle(SAMPLE, NBEST, CANDIDATES, "ai", picked=CANDIDATES[0]["text"])
        path = save_bundle(bundle)
        self.assertTrue(path.is_file())
        loaded = load_bundle(bundle["bundle_id"])
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded["bundle_id"], bundle["bundle_id"])
        self.assertEqual(loaded["picked"], CANDIDATES[0]["text"])


class UtteranceBundleApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmpdir = tempfile.TemporaryDirectory()
        root = Path(cls._tmpdir.name)
        cls._token = bind_test_data_dir(root / "data")
        bundle_mod._BUNDLES_ROOT = root / "bundles"
        speaker_mod.DEFAULT_DB = root / "speaker.db"
        cls._httpd = ThreadingHTTPServer(("127.0.0.1", 0), ClarityHandler)
        cls._port = cls._httpd.server_address[1]
        cls._thread = threading.Thread(target=cls._httpd.serve_forever, daemon=True)
        cls._thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._httpd.shutdown()
        cls._httpd.server_close()
        bundle_mod._BUNDLES_ROOT = None
        cls._tmpdir.cleanup()

    @property
    def _base(self) -> str:
        return f"http://127.0.0.1:{self._port}"

    def _post(self, path: str, body: dict) -> dict:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base}{path}",
            data=data,
            headers={"Content-Type": "application/json", **auth_headers(self._token)},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            return json.loads(resp.read().decode("utf-8"))

    def _get(self, path: str) -> dict:
        req = urllib.request.Request(f"{self._base}{path}", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def test_post_bundles_persists_json(self) -> None:
        resp = self._post(
            "/v1/bundles",
            {
                "raw": SAMPLE,
                "nbest": NBEST,
                "candidates": CANDIDATES,
                "mode": "default",
            },
        )
        bundle_id = resp["bundle_id"]
        self.assertTrue(bundle_id)
        self.assertIn("timestamp", resp)
        self.assertIn("url", resp)
        self.assertIn(f"/v1/bundles/{bundle_id}", resp["url"])
        path = bundle_mod.bundles_dir() / f"{bundle_id}.json"
        self.assertTrue(path.is_file())

    def test_get_bundle_returns_saved(self) -> None:
        created = self._post(
            "/v1/bundles",
            {"raw": SAMPLE, "nbest": NBEST, "candidates": CANDIDATES, "mode": "ai"},
        )
        fetched = self._get(f"/v1/bundles/{created['bundle_id']}")
        self.assertEqual(fetched["raw"], SAMPLE)
        self.assertEqual(fetched["nbest"], NBEST)
        self.assertEqual(fetched["mode"], "ai")

    def test_get_missing_bundle_404(self) -> None:
        req = urllib.request.Request(f"{self._base}/v1/bundles/doesnotexist", method="GET")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=5)
        self.assertEqual(ctx.exception.code, 404)

    def test_feedback_saves_bundle_when_nbest_present(self) -> None:
        preferred = CANDIDATES[0]["text"]
        resp = self._post(
            "/v1/feedback",
            {
                "raw": SAMPLE,
                "preferred": preferred,
                "nbest": NBEST,
                "candidates": CANDIDATES,
                "mode": "default",
            },
        )
        self.assertTrue(resp["ok"])
        self.assertIn("bundle_id", resp)
        self.assertIn("bundle_url", resp)
        bundle = self._get(f"/v1/bundles/{resp['bundle_id']}")
        self.assertEqual(bundle["picked"], preferred)
        profile = SpeakerStore().get()
        self.assertEqual(len(profile.correction_log), 1)

    def test_feedback_without_nbest_no_bundle(self) -> None:
        resp = self._post(
            "/v1/feedback",
            {"raw": SAMPLE, "preferred": CANDIDATES[0]["text"]},
        )
        self.assertTrue(resp["ok"])
        self.assertNotIn("bundle_id", resp)


if __name__ == "__main__":
    unittest.main()
