"""Resolve writable data directory (dev tree vs PyInstaller frozen exe)."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def app_data_dir() -> Path:
    """Persistent data dir: repo ``data/`` in dev; ``CLARITYIME_ROOT/data`` when frozen."""
    override = os.environ.get("CLARITYIME_DATA_DIR")
    if override:
        return Path(override)
    if getattr(sys, "frozen", False):
        root = os.environ.get("CLARITYIME_ROOT")
        if root:
            return Path(root) / "data"
        return Path.home() / ".clarityime" / "data"
    return Path(__file__).resolve().parents[1] / "data"
