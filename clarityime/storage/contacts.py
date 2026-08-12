"""Local-only contact profile storage (SQLite). Never syncs to cloud."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from clarityime.models import ContactProfile
from clarityime.paths import app_data_dir
from clarityime.secure_store import is_sealed, open_json, open_text, seal_json, seal_text
from clarityime.cerome.human import cerome_from_contact, merge_cerome_into_contact, CeromeHumanProfile

DEFAULT_DB = app_data_dir() / "contacts.db"


class ContactStore:
    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path or DEFAULT_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    style_notes TEXT DEFAULT '',
                    preferred_words TEXT DEFAULT '',
                    relationship TEXT DEFAULT '',
                    age_hint TEXT DEFAULT '',
                    comprehension_notes TEXT DEFAULT '',
                    extra_json TEXT DEFAULT '{}'
                )
                """
            )

    def list_contacts(self) -> list[ContactProfile]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM contacts ORDER BY name").fetchall()
        return [self._row_to_profile(r) for r in rows]

    def get_by_name(self, name: str) -> ContactProfile | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM contacts WHERE name = ?", (name,)
            ).fetchone()
        return self._row_to_profile(row) if row else None

    def get_by_id(self, contact_id: int) -> ContactProfile | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM contacts WHERE id = ?", (contact_id,)
            ).fetchone()
        return self._row_to_profile(row) if row else None

    def upsert(self, profile: ContactProfile) -> ContactProfile:
        cerome = cerome_from_contact(profile)
        profile = merge_cerome_into_contact(profile, cerome, write_legacy=False)
        extra = dict(profile.extra)
        extra_plain = {k: v for k, v in extra.items() if k != "cerome"}
        extra_blob = seal_json(extra_plain) if extra_plain else ""
        cerome_blob = seal_json(extra.get("cerome")) if extra.get("cerome") else ""
        stored_extra = {"_sealed": extra_blob, "_cerome_sealed": cerome_blob}
        words_stored = seal_text(profile.preferred_words) if profile.preferred_words else ""
        with self._connect() as conn:
            if profile.id is None:
                cur = conn.execute(
                    """
                    INSERT INTO contacts
                    (name, style_notes, preferred_words, relationship, age_hint, comprehension_notes, extra_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        style_notes=excluded.style_notes,
                        preferred_words=excluded.preferred_words,
                        relationship=excluded.relationship,
                        age_hint=excluded.age_hint,
                        comprehension_notes=excluded.comprehension_notes,
                        extra_json=excluded.extra_json
                    """,
                    (
                        profile.name,
                        profile.style_notes,
                        words_stored,
                        profile.relationship,
                        profile.age_hint,
                        profile.comprehension_notes,
                        json.dumps(stored_extra, ensure_ascii=False),
                    ),
                )
                pid = cur.lastrowid
            else:
                conn.execute(
                    """
                    UPDATE contacts SET name=?, style_notes=?, preferred_words=?,
                    relationship=?, age_hint=?, comprehension_notes=?, extra_json=? WHERE id=?
                    """,
                    (
                        profile.name,
                        profile.style_notes,
                        words_stored,
                        profile.relationship,
                        profile.age_hint,
                        profile.comprehension_notes,
                        json.dumps(stored_extra, ensure_ascii=False),
                        profile.id,
                    ),
                )
                pid = profile.id
            row = conn.execute("SELECT * FROM contacts WHERE id = ?", (pid,)).fetchone()
        return self._row_to_profile(row)

    def export_profile(self, name: str, out_path: Path) -> None:
        profile = self.get_by_name(name)
        if not profile:
            raise ValueError(f"Contact not found: {name}")
        payload = {
            "name": profile.name,
            "style_notes": profile.style_notes,
            "preferred_words": profile.preferred_words,
            "relationship": profile.relationship,
            "age_hint": profile.age_hint,
            "comprehension_notes": profile.comprehension_notes,
            "extra": profile.extra,
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def import_profile(self, in_path: Path) -> ContactProfile:
        payload = json.loads(in_path.read_text(encoding="utf-8"))
        profile = ContactProfile(
            id=None,
            name=payload["name"],
            style_notes=payload.get("style_notes", ""),
            preferred_words=payload.get("preferred_words", ""),
            relationship=payload.get("relationship", ""),
            age_hint=payload.get("age_hint", ""),
            comprehension_notes=payload.get("comprehension_notes", ""),
            extra=payload.get("extra", {}),
        )
        return self.upsert(profile)

    def delete(self, contact_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))

    @staticmethod
    def _row_to_profile(row: sqlite3.Row) -> ContactProfile:
        raw_extra = json.loads(row["extra_json"] or "{}")
        if isinstance(raw_extra, dict) and ("_sealed" in raw_extra or "_cerome_sealed" in raw_extra):
            extra = open_json(raw_extra.get("_sealed", ""), default={})
            cerome = open_json(raw_extra.get("_cerome_sealed", ""), default=None)
            if cerome:
                extra["cerome"] = cerome
        else:
            extra = raw_extra if isinstance(raw_extra, dict) else {}
        words_raw = row["preferred_words"] or ""
        words = open_text(words_raw) if is_sealed(words_raw) else words_raw
        return ContactProfile(
            id=row["id"],
            name=row["name"],
            style_notes=row["style_notes"] or "",
            preferred_words=words,
            relationship=row["relationship"] or "",
            age_hint=row["age_hint"] or "",
            comprehension_notes=row["comprehension_notes"] if "comprehension_notes" in row.keys() else "",
            extra=extra,
        )
