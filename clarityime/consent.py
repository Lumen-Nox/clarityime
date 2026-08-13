"""Explicit local consent — opt-in cloud sync and aggregate research flags."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from clarityime.paths import app_data_dir

DEFAULT_CONSENT = {
    "version": 1,
    "cloud_sync": False,
    "aggregate_research": False,
    "updated_at": None,
}

CONSENT_PATH = app_data_dir() / "consent.json"


def load_consent(path: Path | None = None) -> dict:
    p = path or CONSENT_PATH
    if not p.is_file():
        return dict(DEFAULT_CONSENT)
    try:
        loaded = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_CONSENT)
    return {**DEFAULT_CONSENT, **loaded}


def save_consent(
    *,
    cloud_sync: bool,
    aggregate_research: bool = False,
    path: Path | None = None,
) -> dict:
    p = path or CONSENT_PATH
    consent = {
        "version": 1,
        "cloud_sync": bool(cloud_sync),
        "aggregate_research": bool(aggregate_research),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(consent, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return consent


def require_aggregate_consent(path: Path | None = None) -> None:
    if not load_consent(path).get("aggregate_research"):
        raise PermissionError(
            "Aggregate research / training contribution is disabled. "
            "Run: python -m clarityime.main consent --aggregate-research on"
        )
