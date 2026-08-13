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

    def log_adapt_rating(
        self,
        *,
        original: str,
        for_listener: str,
        rating: str,
        substitutions: list[dict] | None = None,
        listener_tags: list[str] | None = None,
        note: str = "",
        contact_name: str | None = None,
        reading_lang: str = "zh",
    ) -> dict[str, list[str]]:
        """Store a rating on a listener-adaptation, for manual audit.

        This never re-trains anything and never touches the audited
        JARGON_TABLE itself. The product contract is: show original + adapted,
        let the user rate it, then optimize from those ratings. Editing the
        *table* is still a human reading this log.

        What it DOES update automatically (album-style learning from ratings):

        * ``contact_name`` given → repeated ratings tied to the same jargon
          domain feed ``contact_learning.record_feedback`` and — once there
          is enough consistent evidence for THIS contact — silently stop
          translating that domain for them.
        * ``contact_name`` NOT given (DEFAULT mode, no object picked) → the
          same evidence accumulates in a single shared "pending" bucket
          instead. Once a domain crosses the threshold there, we do **not**
          silently create anything (there is no name to attach it to) — we
          only record a *suggestion*. ``resolve_object_suggestion`` turns a
          yes/no answer into either a new/updated contact or a dismissal.

        Pure counting either way, no AI; see contact_learning.py for the
        exact rule and how to undo it.

        Returns ``{"auto_learned_domains": [...], "suggested_new_contact_domains": [...]}``.
        """
        p = self.get()
        log = list(p.extra.get("adapt_rating_log", []))[-199:]
        log.append(
            {
                "original": original,
                "for_listener": for_listener,
                "rating": rating,  # "good" | "bad" | free text
                "note": note,
                "substitutions": substitutions or [],
                "listener_tags": listener_tags or [],
                "contact_name": contact_name or "",
            }
        )
        p.extra["adapt_rating_log"] = log
        self.update(p)

        from clarityime.cerome.contact_learning import record_feedback

        if contact_name:
            from clarityime.storage.contacts import ContactStore

            store = ContactStore()
            contact = store.get_by_name(contact_name)
            if contact is None:
                return {"auto_learned_domains": [], "suggested_new_contact_domains": []}
            update = record_feedback(
                contact.extra,
                rating=rating,
                substitutions=substitutions,
                lang=reading_lang,
            )
            # Persist every time a jargon domain was touched, not only once a
            # threshold fires — otherwise the running counts never accumulate
            # across separate ratings and the threshold is never reached.
            if update.extra != contact.extra:
                contact.extra = update.extra
                store.upsert(contact)
            return {"auto_learned_domains": update.newly_learned, "suggested_new_contact_domains": []}

        # No object picked (DEFAULT mode): accumulate anonymously, suggest instead of auto-applying.
        p = self.get()
        pending = dict(p.extra.get("pending_object_feedback", {}))
        update = record_feedback(pending, rating=rating, substitutions=substitutions, lang=reading_lang)
        p.extra["pending_object_feedback"] = update.extra
        newly_suggested = list(update.newly_learned)
        if newly_suggested:
            # A fresh threshold crossing re-opens a prompt even if the user
            # said "no" last time (album apps also re-ask after more photos).
            dismissed = set(p.extra.get("dismissed_object_suggestions", [])) - set(newly_suggested)
            p.extra["dismissed_object_suggestions"] = sorted(dismissed)
            suggested = set(p.extra.get("suggested_new_objects", [])) | set(newly_suggested)
            p.extra["suggested_new_objects"] = sorted(suggested)
        self.update(p)
        return {"auto_learned_domains": [], "suggested_new_contact_domains": newly_suggested}

    def pending_object_suggestions(self) -> list[str]:
        """Domains currently waiting on a yes/no answer — for the settings UI
        to render "建议创建一个新对象" prompts."""
        return sorted(self.get().extra.get("suggested_new_objects", []))

    def preview_auto_object_name(self, *, lang: str = "zh") -> str:
        from clarityime.cerome.contact_learning import next_auto_object_name
        from clarityime.storage.contacts import ContactStore

        return next_auto_object_name(
            [c.name for c in ContactStore().list_contacts()], lang=lang
        )

    def resolve_object_suggestion(
        self, domain: str, *, accept: bool, name: str = "", lang: str = "zh"
    ) -> dict[str, object]:
        """User answers the "建议创建一个新对象吗？" prompt for one domain.

        ``accept=True`` creates a contact (album-style). If ``name`` is empty,
        we pick the next unused ``对象 N`` so saying yes is enough. A supplied
        name is used as-is; if that contact already exists, the domain is added
        to it (merge, like tagging a face onto an existing album).

        ``accept=False`` dismisses the current prompt. Counts reset, so a
        later fresh threshold can ask again.

        Either way the pending window for this domain resets, so the next
        person's messages start counting from zero rather than partial credit
        from whoever triggered this suggestion.
        """
        p = self.get()
        suggested = set(p.extra.get("suggested_new_objects", []))
        if domain not in suggested:
            return {"ok": False, "error": "not_suggested"}
        suggested.discard(domain)
        p.extra["suggested_new_objects"] = sorted(suggested)

        pending = dict(p.extra.get("pending_object_feedback", {}))
        evidence = dict(pending.get("domain_feedback_counts", {}).get(domain, {}))

        created_name = ""
        auto_named = False
        if accept:
            from clarityime.cerome.contact_learning import next_auto_object_name
            from clarityime.storage.contacts import ContactStore
            from clarityime.models import ContactProfile

            store = ContactStore()
            chosen = name.strip()
            if not chosen:
                chosen = next_auto_object_name(
                    [c.name for c in store.list_contacts()], lang=lang
                )
                auto_named = True
            contact = store.get_by_name(chosen) or ContactProfile(id=None, name=chosen)
            contact.extra = dict(contact.extra)
            learned = set(contact.extra.get("auto_learned_domains", []))
            learned.add(domain)
            contact.extra["auto_learned_domains"] = sorted(learned)
            counts = dict(contact.extra.get("domain_feedback_counts", {}))
            counts[domain] = evidence  # carry the evidence trail over, don't re-count
            contact.extra["domain_feedback_counts"] = counts
            saved = store.upsert(contact)
            created_name = saved.name
        else:
            dismissed = set(p.extra.get("dismissed_object_suggestions", []))
            dismissed.add(domain)
            p.extra["dismissed_object_suggestions"] = sorted(dismissed)

        from clarityime.cerome.contact_learning import forget_domain

        p.extra["pending_object_feedback"] = forget_domain(pending, domain)
        self.update(p)
        result: dict[str, object] = {"ok": True, "accepted": accept, "domain": domain}
        if accept:
            result["contact_name"] = created_name
            result["auto_named"] = auto_named
        return result

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
