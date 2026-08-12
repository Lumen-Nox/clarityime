"""Local speaker (self) profile — help others understand how *I* speak."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from clarityime.models import SpeakerProfile
from clarityime.paths import app_data_dir
from clarityime.secure_store import is_sealed, open_json, seal_json

DEFAULT_DB = app_data_dir() / "speaker.db"


class SpeakerStore:
    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path or DEFAULT_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS speaker (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    display_name TEXT DEFAULT 'me',
                    oral_patterns TEXT DEFAULT '',
                    vague_phrases TEXT DEFAULT '',
                    preferred_length TEXT DEFAULT 'medium',
                    correction_log TEXT DEFAULT '[]',
                    extra_json TEXT DEFAULT '{}'
                )
                """
            )
            conn.execute(
                "INSERT OR IGNORE INTO speaker (id, display_name) VALUES (1, 'me')"
            )

    def get(self) -> SpeakerProfile:
        with closing(self._connect()) as conn, conn:
            row = conn.execute("SELECT * FROM speaker WHERE id = 1").fetchone()
        log_raw = row["correction_log"] or ""
        if not log_raw or log_raw == "[]":
            correction_log = []
        elif is_sealed(log_raw):
            correction_log = open_json(log_raw, default=[])
        else:
            correction_log = json.loads(log_raw)
        extra_raw = row["extra_json"] or ""
        if not extra_raw or extra_raw == "{}":
            extra = {}
        elif is_sealed(extra_raw):
            extra = open_json(extra_raw, default={})
        else:
            extra = json.loads(extra_raw)
        return SpeakerProfile(
            display_name=row["display_name"] or "me",
            oral_patterns=row["oral_patterns"] or "",
            vague_phrases=row["vague_phrases"] or "",
            preferred_length=row["preferred_length"] or "medium",
            correction_log=correction_log if isinstance(correction_log, list) else [],
            extra=extra if isinstance(extra, dict) else {},
        )

    def update(self, profile: SpeakerProfile) -> SpeakerProfile:
        log_stored = seal_json(profile.correction_log) if profile.correction_log else "[]"
        extra_stored = seal_json(profile.extra) if profile.extra else "{}"
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                UPDATE speaker SET display_name=?, oral_patterns=?, vague_phrases=?,
                preferred_length=?, correction_log=?, extra_json=? WHERE id=1
                """,
                (
                    profile.display_name,
                    profile.oral_patterns,
                    profile.vague_phrases,
                    profile.preferred_length,
                    log_stored,
                    extra_stored,
                ),
            )
        return self.get()

    def log_correction(self, raw: str, preferred: str) -> None:
        p = self.get()
        prefix = "[user_feedback]"
        if preferred.startswith(prefix):
            note = preferred[len(prefix) :].strip()
            feedback_log = list(p.extra.get("user_feedback_log", []))[-49:]
            feedback_log.append({"raw": raw, "note": note})
            p.extra["user_feedback_log"] = feedback_log
        else:
            log = list(p.correction_log)[-49:]
            log.append({"raw": raw, "preferred": preferred})
            p.correction_log = log
        self.update(p)
