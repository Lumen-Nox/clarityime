"""User settings — hotkey, apply mode, language, default audience."""

from __future__ import annotations

import json
from pathlib import Path

from clarityime.models import AudienceMode
from clarityime.paths import app_data_dir

DEFAULT_SETTINGS = {
    "version": 1,
    "hotkey": "ctrl+shift+space",
    "apply_mode": "auto",  # auto | inject | paste | clipboard_only
    "default_audience": AudienceMode.DEFAULT.value,
    "default_contact": None,
    "asr_language": "auto",  # auto | zh | en | ...
    "whisper_model": "base",
    "show_confirmation": False,
    "auto_apply_top": False,
    "restore_clipboard_after_apply": True,
    # Every for_listener message carries a "see original" link by default —
    # Default: most-friendly adaptation for the reader. User can switch to a
    # link-free "clean" copy in settings.
    "attach_original_link": True,
}

SETTINGS_PATH = app_data_dir() / "settings.json"


def load_settings(path: Path | None = None) -> dict:
    p = path or SETTINGS_PATH
    if not p.is_file():
        return dict(DEFAULT_SETTINGS)
    try:
        loaded = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_SETTINGS)
    return {**DEFAULT_SETTINGS, **loaded}


def save_settings(settings: dict, path: Path | None = None) -> dict:
    p = path or SETTINGS_PATH
    merged = {**DEFAULT_SETTINGS, **settings, "version": 1}
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return merged
