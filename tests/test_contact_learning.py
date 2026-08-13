"""Auto-learning a contact's domains from feedback — pure counting, no AI,
reversible like renaming a mis-recognised face in a photo app."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests._auth_util import bind_test_data_dir

from clarityime.cerome.contact_learning import (
    AUTO_LEARN_THRESHOLD,
    forget_domain,
    next_auto_object_name,
    record_feedback,
)
from clarityime.cerome.human import cerome_from_contact
from clarityime.clarify.listener_adapt import plan_from_cerome
from clarityime.models import ContactProfile


def _jargon_sub(term: str) -> dict:
    return {"from": term, "to": "x", "kind": "jargon"}


class RecordFeedbackTests(unittest.TestCase):
    def test_below_threshold_learns_nothing(self) -> None:
        extra: dict = {}
        for _ in range(AUTO_LEARN_THRESHOLD - 1):
            update = record_feedback(extra, rating="bad", substitutions=[_jargon_sub("ddl")])
            extra = update.extra
        self.assertEqual(extra.get("auto_learned_domains", []), [])

    def test_threshold_bad_ratings_auto_learns_domain(self) -> None:
        extra: dict = {}
        learned_events: list[str] = []
        for _ in range(AUTO_LEARN_THRESHOLD):
            update = record_feedback(extra, rating="bad", substitutions=[_jargon_sub("ddl")])
            extra = update.extra
            learned_events.extend(update.newly_learned)
        self.assertIn("tech", extra["auto_learned_domains"])
        self.assertEqual(learned_events, ["tech"])  # fires exactly once, at the threshold

    def test_good_ratings_never_trigger_learning(self) -> None:
        extra: dict = {}
        for _ in range(AUTO_LEARN_THRESHOLD + 5):
            update = record_feedback(extra, rating="good", substitutions=[_jargon_sub("ddl")])
            extra = update.extra
        self.assertEqual(extra.get("auto_learned_domains", []), [])

    def test_mixed_ratings_need_net_threshold_not_raw_count(self) -> None:
        extra: dict = {}
        sequence = ["bad", "good", "bad", "good", "bad", "bad"]  # net = 2 bad, not enough
        for rating in sequence:
            update = record_feedback(extra, rating=rating, substitutions=[_jargon_sub("ddl")])
            extra = update.extra
        self.assertEqual(extra.get("auto_learned_domains", []), [])

    def test_learning_reverses_after_enough_good_ratings(self) -> None:
        extra: dict = {}
        for _ in range(AUTO_LEARN_THRESHOLD):
            extra = record_feedback(extra, rating="bad", substitutions=[_jargon_sub("ddl")]).extra
        self.assertIn("tech", extra["auto_learned_domains"])
        for _ in range(AUTO_LEARN_THRESHOLD):
            update = record_feedback(extra, rating="good", substitutions=[_jargon_sub("ddl")])
            extra = update.extra
        self.assertNotIn("tech", extra["auto_learned_domains"])
        self.assertEqual(update.newly_forgotten, ["tech"])

    def test_non_jargon_substitutions_carry_no_domain(self) -> None:
        extra: dict = {}
        for _ in range(10):
            sub = {"from": "进行讨论", "to": "讨论", "kind": "nominal"}
            update = record_feedback(extra, rating="bad", substitutions=[sub])
            extra = update.extra
        self.assertEqual(extra.get("auto_learned_domains", []), [])

    def test_evidence_trail_is_human_readable_and_capped(self) -> None:
        extra: dict = {}
        for _ in range(20):
            update = record_feedback(extra, rating="bad", substitutions=[_jargon_sub("ddl")])
            extra = update.extra
        evidence = extra["domain_feedback_counts"]["tech"]["evidence"]
        self.assertLessEqual(len(evidence), 10)
        self.assertTrue(all("rating" in e and "at" in e for e in evidence))

    def test_forget_domain_resets_counters(self) -> None:
        extra: dict = {}
        for _ in range(AUTO_LEARN_THRESHOLD):
            extra = record_feedback(extra, rating="bad", substitutions=[_jargon_sub("ddl")]).extra
        extra = forget_domain(extra, "tech")
        self.assertNotIn("tech", extra["auto_learned_domains"])
        self.assertNotIn("tech", extra["domain_feedback_counts"])

    def test_deterministic_same_sequence_same_outcome(self) -> None:
        def run() -> dict:
            extra: dict = {}
            for rating in ["bad", "good", "bad", "bad", "bad"]:
                extra = record_feedback(extra, rating=rating, substitutions=[_jargon_sub("ddl")]).extra
            return extra

        self.assertEqual(run(), run())


class PlanIntegrationTests(unittest.TestCase):
    """auto_domains actually suppresses jargon simplification once learned."""

    def _cerome_with_auto_domain(self, domain: str):
        profile = ContactProfile(id=None, name="tester", extra={"auto_learned_domains": [domain]})
        return cerome_from_contact(profile)

    def test_auto_learned_domain_flows_into_plan_known_domains(self) -> None:
        cerome = self._cerome_with_auto_domain("tech")
        plan = plan_from_cerome(cerome)
        self.assertIn("tech", plan.known_domains)

    def test_define_terms_tag_overrides_auto_learning(self) -> None:
        profile = ContactProfile(
            id=None,
            name="tester",
            extra={"auto_learned_domains": ["tech"], "tags": "define_terms"},
        )
        cerome = cerome_from_contact(profile)
        plan = plan_from_cerome(cerome)
        self.assertEqual(plan.known_domains, frozenset())


class EndToEndFeedbackLoopTests(unittest.TestCase):
    """SpeakerStore.log_adapt_rating(contact_name=...) actually persists the
    learned domain onto that contact via ContactStore — full round trip."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        base = Path(self._tmpdir.name)
        bind_test_data_dir(base / "data")

        from clarityime.storage import contacts as contacts_mod
        from clarityime.storage import speaker as speaker_mod

        contacts_mod.DEFAULT_DB = base / "contacts.db"
        speaker_mod.DEFAULT_DB = base / "speaker.db"
        self._contacts_mod = contacts_mod
        self._speaker_mod = speaker_mod

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_repeated_bad_ratings_auto_tag_the_contact(self) -> None:
        from clarityime.storage.contacts import ContactStore
        from clarityime.storage.speaker import SpeakerStore

        contacts = ContactStore()
        contacts.upsert(ContactProfile(id=None, name="小明"))

        store = SpeakerStore()
        result: dict = {}
        for _ in range(AUTO_LEARN_THRESHOLD):
            result = store.log_adapt_rating(
                original="ddl 是明天",
                for_listener="截止时间是明天。",
                rating="bad",
                substitutions=[_jargon_sub("ddl")],
                contact_name="小明",
            )

        self.assertEqual(result["auto_learned_domains"], ["tech"])
        self.assertEqual(result["suggested_new_contact_domains"], [])
        refreshed = contacts.get_by_name("小明")
        self.assertIn("tech", refreshed.extra.get("auto_learned_domains", []))

        cerome = cerome_from_contact(refreshed)
        plan = plan_from_cerome(cerome)
        self.assertIn("tech", plan.known_domains)

    def test_unknown_contact_name_is_a_silent_noop(self) -> None:
        from clarityime.storage.speaker import SpeakerStore

        store = SpeakerStore()
        result = store.log_adapt_rating(
            original="ddl 是明天",
            for_listener="截止时间是明天。",
            rating="bad",
            substitutions=[_jargon_sub("ddl")],
            contact_name="不存在的人",
        )
        self.assertEqual(result["auto_learned_domains"], [])
        self.assertEqual(result["suggested_new_contact_domains"], [])


class AutoNameTests(unittest.TestCase):
    def test_first_object_is_one(self) -> None:
        self.assertEqual(next_auto_object_name([]), "对象 1")

    def test_skips_taken_names(self) -> None:
        self.assertEqual(next_auto_object_name(["对象 1", "对象 2", "小明"]), "对象 3")

    def test_english_prefix(self) -> None:
        self.assertEqual(next_auto_object_name(["Person 1"], lang="en"), "Person 2")


class DefaultAudienceSuggestionTests(unittest.TestCase):
    """DEFAULT mode never silently creates a contact — it asks, then yes/no."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        base = Path(self._tmpdir.name)
        bind_test_data_dir(base / "data")

        from clarityime.storage import contacts as contacts_mod
        from clarityime.storage import speaker as speaker_mod

        contacts_mod.DEFAULT_DB = base / "contacts.db"
        speaker_mod.DEFAULT_DB = base / "speaker.db"

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _rate_default(self, store, n: int) -> dict:
        result: dict = {}
        for _ in range(n):
            result = store.log_adapt_rating(
                original="ddl 是明天",
                for_listener="截止时间是明天。",
                rating="bad",
                substitutions=[_jargon_sub("ddl")],
            )
        return result

    def test_threshold_on_default_audience_suggests_does_not_create(self) -> None:
        from clarityime.storage.contacts import ContactStore
        from clarityime.storage.speaker import SpeakerStore

        store = SpeakerStore()
        result = self._rate_default(store, AUTO_LEARN_THRESHOLD)
        self.assertEqual(result["auto_learned_domains"], [])
        self.assertEqual(result["suggested_new_contact_domains"], ["tech"])
        self.assertEqual(store.pending_object_suggestions(), ["tech"])
        self.assertEqual(ContactStore().list_contacts(), [])

    def test_yes_without_name_auto_creates_object_one(self) -> None:
        from clarityime.storage.contacts import ContactStore
        from clarityime.storage.speaker import SpeakerStore

        store = SpeakerStore()
        self._rate_default(store, AUTO_LEARN_THRESHOLD)
        resolved = store.resolve_object_suggestion("tech", accept=True)
        self.assertTrue(resolved["ok"])
        self.assertTrue(resolved["auto_named"])
        self.assertEqual(resolved["contact_name"], "对象 1")
        self.assertEqual(store.pending_object_suggestions(), [])

        created = ContactStore().get_by_name("对象 1")
        self.assertIsNotNone(created)
        self.assertIn("tech", created.extra.get("auto_learned_domains", []))

        cerome = cerome_from_contact(created)
        plan = plan_from_cerome(cerome)
        self.assertIn("tech", plan.known_domains)

    def test_yes_with_name_creates_that_contact(self) -> None:
        from clarityime.storage.contacts import ContactStore
        from clarityime.storage.speaker import SpeakerStore

        store = SpeakerStore()
        self._rate_default(store, AUTO_LEARN_THRESHOLD)
        resolved = store.resolve_object_suggestion("tech", accept=True, name="小明")
        self.assertEqual(resolved["contact_name"], "小明")
        self.assertFalse(resolved["auto_named"])
        self.assertIsNotNone(ContactStore().get_by_name("小明"))
        self.assertIsNone(ContactStore().get_by_name("对象 1"))

    def test_no_creates_nothing_and_clears_prompt(self) -> None:
        from clarityime.storage.contacts import ContactStore
        from clarityime.storage.speaker import SpeakerStore

        store = SpeakerStore()
        self._rate_default(store, AUTO_LEARN_THRESHOLD)
        resolved = store.resolve_object_suggestion("tech", accept=False)
        self.assertTrue(resolved["ok"])
        self.assertFalse(resolved["accepted"])
        self.assertEqual(store.pending_object_suggestions(), [])
        self.assertEqual(ContactStore().list_contacts(), [])

    def test_no_then_fresh_evidence_asks_again(self) -> None:
        from clarityime.storage.speaker import SpeakerStore

        store = SpeakerStore()
        self._rate_default(store, AUTO_LEARN_THRESHOLD)
        store.resolve_object_suggestion("tech", accept=False)
        result = self._rate_default(store, AUTO_LEARN_THRESHOLD)
        self.assertEqual(result["suggested_new_contact_domains"], ["tech"])
        self.assertEqual(store.pending_object_suggestions(), ["tech"])

    def test_resolve_unknown_domain_is_not_ok(self) -> None:
        from clarityime.storage.speaker import SpeakerStore

        store = SpeakerStore()
        resolved = store.resolve_object_suggestion("tech", accept=True)
        self.assertFalse(resolved["ok"])
        self.assertEqual(resolved["error"], "not_suggested")


if __name__ == "__main__":
    unittest.main()
