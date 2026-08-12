"""POST /v1/feedback — local SpeakerStore updates."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from tests._auth_util import auth_headers, bind_test_data_dir
from clarityime.server import ClarityHandler
from clarityime.storage.speaker import SpeakerStore
from clarityime.storage import speaker as speaker_mod


class FeedbackSpeakerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._db = Path(self._tmpdir.name) / "speaker.db"
        self._token = bind_test_data_dir(Path(self._tmpdir.name) / "data")
        speaker_mod.DEFAULT_DB = self._db
        self._store = SpeakerStore(self._db)
        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), ClarityHandler)
        self._port = self._httpd.server_address[1]
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def tearDown(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        self._tmpdir.cleanup()

    def _post_feedback(self, raw: str, preferred: str) -> dict:
        body = json.dumps({"raw": raw, "preferred": preferred}, ensure_ascii=False).encode(
            "utf-8"
        )
        req = urllib.request.Request(
            f"http://127.0.0.1:{self._port}/v1/feedback",
            data=body,
            headers={
                "Content-Type": "application/json",
                **auth_headers(self._token),
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def test_correction_log_stores_preferred(self) -> None:
        raw = "嗯那个我想明天去"
        preferred = "我想明天去。"
        resp = self._post_feedback(raw, preferred)
        self.assertTrue(resp["ok"])
        profile = self._store.get()
        self.assertEqual(len(profile.correction_log), 1)
        self.assertEqual(profile.correction_log[0]["raw"], raw)
        self.assertEqual(profile.correction_log[0]["preferred"], preferred)
        self.assertNotIn("user_feedback_log", profile.extra)

    def test_user_feedback_prefix_stored_separately(self) -> None:
        raw = "我想明天去。"
        note = "太正式了，保留我的语气"
        resp = self._post_feedback(raw, f"[user_feedback] {note}")
        self.assertTrue(resp["logged"])
        profile = self._store.get()
        self.assertEqual(profile.correction_log, [])
        feedback_log = profile.extra.get("user_feedback_log", [])
        self.assertEqual(len(feedback_log), 1)
        self.assertEqual(feedback_log[0]["raw"], raw)
        self.assertEqual(feedback_log[0]["note"], note)

    def test_log_correction_direct(self) -> None:
        store = SpeakerStore(self._db)
        store.log_correction("raw text", "clean text")
        store.log_correction("raw2", "[user_feedback] too stiff")
        profile = store.get()
        self.assertEqual(len(profile.correction_log), 1)
        self.assertEqual(profile.correction_log[0]["preferred"], "clean text")
        feedback = profile.extra["user_feedback_log"]
        self.assertEqual(len(feedback), 1)
        self.assertEqual(feedback[0]["note"], "too stiff")


if __name__ == "__main__":
    unittest.main()
