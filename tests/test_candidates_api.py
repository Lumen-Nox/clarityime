"""POST /v1/candidates — dual output original + for_listener."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from clarityime.models import ContactProfile
from clarityime.server import ClarityHandler
from clarityime.storage.contacts import ContactStore
from clarityime.storage import contacts as contacts_mod
from clarityime.storage import speaker as speaker_mod


SAMPLE = "嗯那个你好，就是我想问一下这个项目大概什么时候能做完啊"
LONG = (
    "嗯我觉得吧这个方向其实还可以就是风险也有点多然后周期比较长但是团队士气还行你要是有空我们可以再聊细一点"
)
NBEST = [SAMPLE, "我想问一下这个项目大概什么时候能做完"]


class CandidatesApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmpdir = tempfile.TemporaryDirectory()
        root = Path(cls._tmpdir.name)
        contacts_mod.DEFAULT_DB = root / "contacts.db"
        speaker_mod.DEFAULT_DB = root / "speaker.db"
        ContactStore().upsert(
            ContactProfile(
                id=None,
                name="TestTeacher",
                relationship="老师",
                style_notes="温和",
            )
        )
        cls._httpd = ThreadingHTTPServer(("127.0.0.1", 0), ClarityHandler)
        cls._httpd.daemon_threads = False
        cls._httpd.block_on_close = True
        cls._port = cls._httpd.server_address[1]
        cls._thread = threading.Thread(target=cls._httpd.serve_forever, daemon=True)
        cls._thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._httpd.shutdown()
        cls._thread.join(timeout=10)
        cls._httpd.server_close()
        cls._tmpdir.cleanup()

    def _post(self, body: dict) -> dict:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{self._port}/v1/candidates",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            return json.loads(resp.read().decode("utf-8"))

    def test_requires_text(self) -> None:
        req = urllib.request.Request(
            f"http://127.0.0.1:{self._port}/v1/candidates",
            data=json.dumps({}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=5)
        self.assertEqual(ctx.exception.code, 400)

    def test_default_original_only(self) -> None:
        payload = self._post({"text": SAMPLE, "nbest": NBEST, "mode": "default"})
        self.assertIn("original", payload)
        self.assertEqual(payload["original"], payload["for_listener"])
        labels = [c["label"] for c in payload["candidates"]]
        self.assertIn("standard", labels)

    def test_listener_preset_dual(self) -> None:
        payload = self._post(
            {"text": LONG, "mode": "default", "listener_preset": "d_type"}
        )
        self.assertIn("original", payload)
        self.assertIn("for_listener", payload)
        labels = {c["label"] for c in payload["candidates"]}
        self.assertIn("original", labels)
        self.assertIn("for_listener", labels)

    def test_structured_dual(self) -> None:
        payload = self._post({"text": LONG, "mode": "structured"})
        labels = {c["label"] for c in payload["candidates"]}
        self.assertIn("original", labels)
        self.assertIn("for_listener", labels)
        self.assertFalse(any("要点：" in c["text"] for c in payload["candidates"]))

    def test_contact_mode_dual(self) -> None:
        payload = self._post(
            {
                "text": SAMPLE,
                "nbest": NBEST,
                "mode": "contact",
                "contact": "TestTeacher",
            }
        )
        labels = {c["label"] for c in payload["candidates"]}
        self.assertIn("original", labels)
        self.assertIn("for_listener", labels)

    def test_deterministic_same_input(self) -> None:
        body = {
            "text": SAMPLE,
            "nbest": NBEST,
            "mode": "default",
            "listener_preset": "s_type",
        }
        a = self._post(body)
        b = self._post(body)
        self.assertEqual(a["candidates"], b["candidates"])


if __name__ == "__main__":
    unittest.main()
