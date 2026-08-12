"""N-best ASR utterance bundles — one utterance, all hypotheses, shareable on localhost.

API (loopback only, see ``clarityime.server``):

POST /v1/bundles
    Body: ``{"raw": str, "nbest": [str, ...], "candidates": [{text, label, ...}],
           "mode": "default"|"contact"|"ai", "picked": str|null}``
    → ``{"bundle_id": str, "timestamp": str, "url": "http://127.0.0.1:17800/v1/bundles/{id}"}``

GET /v1/bundles/{bundle_id}
    → full bundle JSON (404 if missing)

POST /v1/feedback (when ``nbest`` present)
    Same speaker log as before; also persists an utterance bundle with ``picked=preferred``.
    Response adds ``bundle_id`` and ``bundle_url`` when a bundle was saved.

Storage: ``{app_data_dir}/bundles/{bundle_id}.json``
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from clarityime.paths import app_data_dir

BUNDLE_KIND = "clarityime.utterance"
BUNDLE_VERSION = "1"

# Test override (see tests/test_utterance_bundle.py).
_BUNDLES_ROOT: Path | None = None


def bundles_dir() -> Path:
    if _BUNDLES_ROOT is not None:
        root = _BUNDLES_ROOT
    else:
        root = app_data_dir() / "bundles"
    root.mkdir(parents=True, exist_ok=True)
    return root


def create_bundle(
    raw: str,
    nbest: list[str],
    candidates: list[dict[str, Any]],
    mode: str,
    *,
    picked: str | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable utterance bundle (does not write to disk)."""
    if not raw.strip():
        raise ValueError("raw_required")
    if not nbest:
        nbest = [raw]
    bundle_id = uuid.uuid4().hex
    timestamp = datetime.now(timezone.utc).isoformat()
    return {
        "kind": BUNDLE_KIND,
        "version": BUNDLE_VERSION,
        "bundle_id": bundle_id,
        "timestamp": timestamp,
        "raw": raw,
        "nbest": list(nbest),
        "candidates": list(candidates),
        "mode": mode,
        "picked": picked,
    }


def save_bundle(bundle: dict[str, Any], *, root: Path | None = None) -> Path:
    """Persist bundle to ``data/bundles/{bundle_id}.json``."""
    bundle_id = bundle.get("bundle_id")
    if not bundle_id:
        raise ValueError("bundle_id_required")
    dest = (root or bundles_dir()) / f"{bundle_id}.json"
    dest.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest


def load_bundle(bundle_id: str, *, root: Path | None = None) -> dict[str, Any] | None:
    """Load bundle by id; returns ``None`` if file does not exist."""
    path = (root or bundles_dir()) / f"{bundle_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def bundle_local_url(bundle_id: str, host: str = "127.0.0.1", port: int = 17800) -> str:
    return f"http://{host}:{port}/v1/bundles/{bundle_id}"


def save_utterance_bundle(
    raw: str,
    nbest: list[str] | None,
    candidates: list[dict[str, Any]] | None,
    mode: str,
    *,
    picked: str | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Create and persist bundle; returns the full bundle dict."""
    bundle = create_bundle(
        raw,
        nbest or [raw],
        candidates or [],
        mode,
        picked=picked,
    )
    save_bundle(bundle, root=root)
    return bundle
