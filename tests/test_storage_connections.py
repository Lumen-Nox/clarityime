"""Regression: handler threads must finish before temp dir cleanup on Windows."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from clarityime.server import ClarityHandler
from clarityime.storage import contacts as contacts_mod
from clarityime.storage import speaker as speaker_mod
from tests._auth_util import auth_headers, bind_test_data_dir


def _start_test_server(
    *,
    wait_for_handlers_on_close: bool = True,
) -> tuple[tempfile.TemporaryDirectory, ThreadingHTTPServer, threading.Thread, str, int]:
    tmpdir = tempfile.TemporaryDirectory()
    root = Path(tmpdir.name)
    token = bind_test_data_dir(root / "data")
    contacts_mod.DEFAULT_DB = root / "contacts.db"
    speaker_mod.DEFAULT_DB = root / "speaker.db"
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), ClarityHandler)
    if wait_for_handlers_on_close:
        httpd.daemon_threads = False
        httpd.block_on_close = True
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return tmpdir, httpd, thread, token, port


def _stop_test_server_fixed(
    httpd: ThreadingHTTPServer,
    thread: threading.Thread,
    tmpdir: tempfile.TemporaryDirectory,
) -> None:
    httpd.shutdown()
    thread.join(timeout=10)
    httpd.server_close()
    tmpdir.cleanup()


def _stop_test_server_broken(
    httpd: ThreadingHTTPServer,
    tmpdir: tempfile.TemporaryDirectory,
) -> None:
    """Legacy teardown — matches pre-fix tests; fails on Windows under load."""
    httpd.shutdown()
    httpd.server_close()
    tmpdir.cleanup()


def _fire_concurrent_db_requests(base: str, token: str, *, count: int = 8) -> list[threading.Thread]:
    """Start client threads that hit sqlite-backed handlers; do not wait."""

    def hit_speaker() -> None:
        try:
            urllib.request.urlopen(
                urllib.request.Request(f"{base}/v1/speaker", method="GET"),
                timeout=5,
            )
        except Exception:
            pass

    def hit_contacts(n: int) -> None:
        body = json.dumps({"name": f"Alice-{n}", "style_notes": "formal"}).encode("utf-8")
        try:
            urllib.request.urlopen(
                urllib.request.Request(
                    f"{base}/v1/contacts",
                    data=body,
                    headers={"Content-Type": "application/json", **auth_headers(token)},
                    method="POST",
                ),
                timeout=5,
            )
        except Exception:
            pass

    workers: list[threading.Thread] = []
    for i in range(count):
        workers.append(threading.Thread(target=hit_contacts, args=(i,)))
    workers.append(threading.Thread(target=hit_speaker))
    for worker in workers:
        worker.start()
    return workers


class StorageConnectionCleanupTests(unittest.TestCase):
    def test_handler_threads_release_db_before_tempdir_cleanup(self) -> None:
        tmpdir, httpd, thread, token, port = _start_test_server()
        base = f"http://127.0.0.1:{port}"

        workers = _fire_concurrent_db_requests(base, token)

        try:
            _stop_test_server_fixed(httpd, thread, tmpdir)
        except PermissionError:
            self.fail("tmpdir.cleanup() raised PermissionError — handler threads still hold DB files")
        finally:
            for worker in workers:
                worker.join(timeout=10)


if __name__ == "__main__":
    if os.environ.get("CLARITYIME_BROKEN_TEARDOWN") == "1":
        tmpdir, httpd, thread, token, port = _start_test_server(
            wait_for_handlers_on_close=False
        )
        base = f"http://127.0.0.1:{port}"
        workers = _fire_concurrent_db_requests(base, token)
        try:
            _stop_test_server_broken(httpd, tmpdir)
            raise SystemExit("expected PermissionError on broken teardown, but cleanup succeeded")
        except PermissionError as exc:
            print(f"PermissionError (expected): {exc}")
            raise SystemExit(1)
        finally:
            thread.join(timeout=10)
            for worker in workers:
                worker.join(timeout=10)
    else:
        unittest.main()
