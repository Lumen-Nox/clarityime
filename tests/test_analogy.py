"""Cross-circle analogies: audited table, mixed into daily output, no AI."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import unittest
from dataclasses import replace

from clarityime.cerome.listener_presets import PRESETS
from clarityime.cerome.tag_registry import REGISTRY
from clarityime.clarify.analogy import (
    ANALOGY_TABLES,
    format_analogy,
    pick_analogy,
)
from clarityime.clarify.listener_adapt import adapt_with_report
from clarityime.clarify.local_rules import preserve_original
from clarityime.clarify.paraphrase import JARGON_TABLES, simplify_jargon


class TableIntegrityTests(unittest.TestCase):
    def test_every_source_term_is_in_the_jargon_table(self) -> None:
        for lang, table in ANALOGY_TABLES.items():
            jargon = JARGON_TABLES[lang]
            for term in table:
                self.assertIn(term, jargon, f"{lang}:{term} has no jargon row to hang on")

    def test_no_mapping_points_at_the_term_own_domain_as_the_only_option(self) -> None:
        for lang, table in ANALOGY_TABLES.items():
            jargon = JARGON_TABLES[lang]
            for term, options in table.items():
                src_domain = jargon[term][1]
                self.assertTrue(options, f"{lang}:{term} empty")
                self.assertNotIn(src_domain, options, f"{lang}:{term} tautology {src_domain}")

    def test_analog_never_equals_source(self) -> None:
        for table in ANALOGY_TABLES.values():
            for term, options in table.items():
                for analog in options.values():
                    self.assertNotEqual(analog, term)

    def test_target_domains_are_real_tags(self) -> None:
        for table in ANALOGY_TABLES.values():
            for options in table.values():
                for domain in options:
                    self.assertIn(domain, REGISTRY, domain)


class PickTests(unittest.TestCase):
    def test_fps_listener_gets_chair_camping_as_holding_an_angle(self) -> None:
        got = pick_analogy("守椅", src_domain="asym_horror", owned={"fps"})
        self.assertEqual(got, ("fps", "架点"))

    def test_no_owned_domain_means_no_analogy(self) -> None:
        self.assertIsNone(pick_analogy("守椅", src_domain="asym_horror", owned=set()))
        self.assertIsNone(pick_analogy("守椅", src_domain="asym_horror", owned={"gacha"}))

    def test_owning_the_source_domain_is_not_enough_to_pick(self) -> None:
        # pick_analogy itself doesn't see "already owned source" — simplify_jargon
        # skips before calling. Still must not return a tautology row.
        self.assertIsNone(
            pick_analogy("守椅", src_domain="asym_horror", owned={"asym_horror"})
        )

    def test_tie_breaks_alphabetically(self) -> None:
        got = pick_analogy("秒倒", src_domain="asym_horror", owned={"moba", "fps"})
        self.assertEqual(got[0], "fps")

    def test_format_keeps_the_speaker_word(self) -> None:
        self.assertEqual(format_analogy("守椅", "架点", "zh"), "守椅（就像架点）")
        self.assertEqual(format_analogy("gank", "flank", "en"), "gank (like flank)")
        self.assertEqual(format_analogy("推し", "本命", "ja"), "推し（本命みたい）")
        self.assertEqual(format_analogy("최애", "本命", "ko"), "최애 (本命 같은 거)")


class PipelineTests(unittest.TestCase):
    def test_mixed_into_the_sentence_not_a_second_message(self) -> None:
        text, subs = simplify_jargon(
            "监管者一直守椅", known_domains={"fps"}, lang="zh"
        )
        self.assertEqual(text, "追人的一方一直守椅（就像架点）")
        kinds = {s.kind for s in subs}
        self.assertIn("analogy", kinds)
        self.assertIn("jargon", kinds)  # 监管者 has no fps analog → plain T1

    def test_no_game_tag_still_gets_plain_t1(self) -> None:
        text, subs = simplify_jargon("监管者一直守椅", known_domains=set(), lang="zh")
        self.assertEqual(text, "追人的一方一直守着倒地的人不走")
        self.assertTrue(all(s.kind == "jargon" for s in subs))
        self.assertNotIn("就像", text)

    def test_owning_source_domain_leaves_the_word(self) -> None:
        text, subs = simplify_jargon(
            "监管者一直守椅", known_domains={"asym_horror"}, lang="zh"
        )
        self.assertEqual(text, "监管者一直守椅")
        self.assertEqual(subs, [])

    def test_define_terms_style_empty_owned_never_analogizes(self) -> None:
        # define_terms clears known_domains in the plan; same input as outsider.
        text, _ = simplify_jargon("开团了", known_domains=frozenset(), lang="zh")
        self.assertEqual(text, "发起团战了")

    def test_english_fps_player_hears_gank_as_flank(self) -> None:
        text, subs = simplify_jargon(
            "that gank was a throw", known_domains={"fps", "gaming"}, lang="en"
        )
        self.assertIn("gank (like flank)", text)
        self.assertTrue(any(s.kind == "analogy" for s in subs))

    def test_end_to_end_listener_adapt_is_deterministic(self) -> None:
        original, _ = preserve_original("监管者一直守椅")
        who = replace(PRESETS["a_type"], tags=["mbti_entp", "game_valorant"])
        a = adapt_with_report(original, who).text
        b = adapt_with_report(original, who).text
        self.assertEqual(a, b)
        self.assertIn("就像架点", a)


if __name__ == "__main__":
    unittest.main()
