"""Comprehension engine — invariants + evidence-backed ops.

Basis: docs/COMPREHENSION_MODEL.md
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import unittest
from dataclasses import replace

from clarityime.cerome.listener_presets import PRESETS
from clarityime.cerome.tags import UnknownTagError, listener_tags, validate
from clarityime.clarify.details import detail_diff, extract_details
from clarityime.clarify.oral import MEANING, NOISE, TONE, classify_oral, strip_oral
from clarityime.clarify.comprehension import (
    check_invariants,
    claim_first,
    comprehension_cost,
    resolve_referents,
    restore_subjects,
    split_clauses,
)
from clarityime.clarify.listener_adapt import adapt_with_report, plan_from_cerome
from clarityime.clarify.paraphrase import JARGON_TERMS
from clarityime.clarify.local_rules import preserve_original

SAMPLES = [
    "就是我觉得这个方案还行，胜算挺高的，而且周期也长",
    "那个，就是我明天可能去不了，因为家里有事，然后作业我可能得晚一天交",
    "因为API接口它老是超时，所以那个功能我们可能得先关掉，不过风险还行",
    "嗯我想说就是这个项目大概什么时候能做完，因为要跟别的排期对齐",
    "我跟你说啊，其实我对这个方向还挺有感觉的，虽然数据不太够，但是我觉得值得试试",
]

# Words the engine must never inject (register/politeness = changing the speaker)
FORBIDDEN_INJECTIONS = ("不好意思", "麻烦您", "抱歉", "您好", "请问", "总结", "要点")


class InvariantTests(unittest.TestCase):
    def test_no_new_or_lost_content_any_listener(self) -> None:
        """After the audited substitutions, nothing may be added or dropped."""
        for raw in SAMPLES:
            original, _ = preserve_original(raw)
            for key, profile in PRESETS.items():
                res = adapt_with_report(original, profile)
                report = check_invariants(res.baseline, res.text)
                self.assertTrue(
                    report.ok,
                    f"{key} violated on {raw!r}: new={report.new_content} "
                    f"lost={report.lost_content} hedges={report.lost_hedges}",
                )

    def test_every_substitution_comes_from_the_audited_table(self) -> None:
        """No generation: each swap must be traceable to a reviewable rule."""
        allowed_kinds = {"jargon", "analogy", "nominal", "redundancy", "lexicon"}
        for raw in SAMPLES:
            original, _ = preserve_original(raw)
            for key, profile in PRESETS.items():
                res = adapt_with_report(original, profile)
                for sub in res.substitutions:
                    self.assertIn(sub.kind, allowed_kinds, f"{key}: {sub}")
                    if sub.kind == "jargon":
                        self.assertEqual(JARGON_TERMS.get(sub.src), sub.dst)
                    if sub.kind == "analogy":
                        self.assertTrue(
                            sub.dst.startswith(sub.src),
                            f"analogy must keep the speaker's word: {sub}",
                        )
                    self.assertIn(sub.src, res.baseline + original)

    def test_jargon_kept_only_for_declared_domains(self) -> None:
        """Audience design keys on a DECLARED domain tag, never on personality."""
        original, _ = preserve_original("这个接口老是超时，我们得先复盘一下")

        insider = replace(PRESETS["d_type"], tags=["tech", "business"])
        outsider = PRESETS["d_type"]  # same personality, no domain declared

        got_in = adapt_with_report(original, insider).text
        got_out = adapt_with_report(original, outsider).text

        self.assertIn("超时", got_in)  # tech declared → keep
        self.assertIn("复盘", got_in)  # business declared → keep
        self.assertIn("响应太慢", got_out)  # nothing declared → translate
        self.assertIn("回顾", got_out)

    def test_personality_never_implies_domain_knowledge(self) -> None:
        """INTJ personality tag must not imply tech domain knowledge."""
        for key, profile in PRESETS.items():
            tags = listener_tags(profile)
            self.assertEqual(
                tags.domains(), frozenset(), f"{key} invented a domain tag from personality"
            )

    def test_unknown_tag_is_rejected(self) -> None:
        with self.assertRaises(UnknownTagError):
            validate(["tech", "很聪明"])

    def test_question_never_becomes_a_statement(self) -> None:
        """Illocutionary force is meaning (Searle 1969), not formatting."""
        for raw in (
            "老师我想问一下，这个作业能不能晚一天交，因为我这周有点忙",
            "这个项目大概什么时候能做完，因为要跟别的排期对齐",
        ):
            original, _ = preserve_original(raw)
            for key, profile in PRESETS.items():
                out = adapt_with_report(original, profile).text
                self.assertIn("？", out, f"{key} flattened a question: {out!r}")

    def test_hedges_survive(self) -> None:
        original, _ = preserve_original("我觉得这个方案还行，胜算挺高的，可能周期也长")
        for profile in PRESETS.values():
            adapted, _n, _b, _a = adapt_with_report(original, profile)
            for hedge in ("觉得", "还行", "挺", "可能"):
                self.assertIn(hedge, adapted)

    def test_polarity_never_lost(self) -> None:
        original, _ = preserve_original("我明天可能去不了，因为家里有事，我不太确定")
        for profile in PRESETS.values():
            adapted, _n, _b, _a = adapt_with_report(original, profile)
            self.assertGreaterEqual(adapted.count("不"), original.count("不"))

    def test_no_politeness_injection(self) -> None:
        original, _ = preserve_original("我明天可能去不了，因为家里有事")
        for key, profile in PRESETS.items():
            adapted, _n, _b, _a = adapt_with_report(original, profile)
            for word in FORBIDDEN_INJECTIONS:
                self.assertNotIn(word, adapted, f"{key} injected {word}")

    def test_deterministic(self) -> None:
        original, _ = preserve_original(SAMPLES[1])
        for profile in PRESETS.values():
            first, _n, _b, _a = adapt_with_report(original, profile)
            second, _n2, _b2, _a2 = adapt_with_report(original, profile)
            self.assertEqual(first, second)


class OperationTests(unittest.TestCase):
    def test_a1_referent_uses_existing_noun(self) -> None:
        notes: list[str] = []
        clauses = split_clauses("这个方案我觉得还行，它周期也长")
        out = resolve_referents(clauses, notes)
        self.assertIn("方案周期也长", out)
        self.assertTrue(any(n.startswith("A1") for n in notes))

    def test_a2_restores_dropped_subject(self) -> None:
        notes: list[str] = []
        clauses = split_clauses("我明天可能去不了，因为要去看医生")
        out = restore_subjects(clauses, notes)
        self.assertEqual(out[1], "因为我要去看医生")

    def test_a3_claim_first_reorders_only(self) -> None:
        notes: list[str] = []
        clauses = split_clauses("因为家里有事，我明天可能去不了")
        out = claim_first(clauses, notes)
        self.assertEqual(out, ["我明天可能去不了", "因为家里有事"])
        self.assertIn("A3:claim_first", notes)

    def test_a3_skips_explicit_because_so_pair(self) -> None:
        notes: list[str] = []
        clauses = split_clauses("因为接口老是超时，所以我们先关掉")
        self.assertEqual(claim_first(clauses, notes), clauses)


class CostTests(unittest.TestCase):
    def test_cost_never_increases(self) -> None:
        for raw in SAMPLES:
            original, _ = preserve_original(raw)
            for key, profile in PRESETS.items():
                _text, _notes, before, after = adapt_with_report(original, profile)
                self.assertLessEqual(
                    after.total, before.total, f"{key} made {raw!r} harder"
                )

    def test_bridging_detected_and_repaired(self) -> None:
        original, _ = preserve_original("我明天可能去不了，因为要去看医生")
        before = comprehension_cost(original)
        self.assertGreater(before.bridging, 0)
        adapted, _n, _b, after = adapt_with_report(original, PRESETS["d_type"])
        self.assertEqual(after.bridging, 0)
        self.assertIn("因为我要去看医生", adapted)


class PlanTests(unittest.TestCase):
    def test_warm_listener_gets_fewer_breaks_than_analytic(self) -> None:
        original, _ = preserve_original(SAMPLES[2])
        plan = plan_from_cerome(PRESETS["s_type"])
        self.assertTrue(plan.flow)
        warm, _n, _b, _a = adapt_with_report(original, PRESETS["s_type"])
        analytic, _n2, _b2, _a2 = adapt_with_report(original, PRESETS["d_type"])
        self.assertLess(warm.count("\n"), analytic.count("\n"))

    def test_fast_listener_gets_short_lines(self) -> None:
        original, _ = preserve_original(SAMPLES[2])
        plan = plan_from_cerome(PRESETS["a_type"])
        self.assertLessEqual(plan.capacity, 22)
        adapted, _n, _b, _a = adapt_with_report(original, PRESETS["a_type"])
        self.assertIn("\n", adapted)

    def test_presets_produce_distinct_layouts(self) -> None:
        original, _ = preserve_original(SAMPLES[2])
        outs = {
            key: adapt_with_report(original, p).text for key, p in PRESETS.items()
        }
        self.assertNotEqual(outs["s_type"], outs["d_type"])

    def test_plan_is_a_pure_function_of_tags(self) -> None:
        """Two profiles with the same tags must get byte-identical plans."""
        a = plan_from_cerome(PRESETS["d_type"])
        b = plan_from_cerome(replace(PRESETS["d_type"], l5=PRESETS["d_type"].l5))
        self.assertEqual(a.tags(), b.tags())
        self.assertEqual(a.listener_tags, b.listener_tags)


class OralMarkerTests(unittest.TestCase):
    """有时候口语化有意思，有时候没有 — verdict depends on position."""

    def test_initial_jiushi_is_noise_but_medial_is_meaning(self) -> None:
        head = classify_oral("就是我觉得还行")[0]
        self.assertEqual(head.verdict, NOISE)
        medial = [m for m in classify_oral("方案还行，就是风险有点多") if m.surface == "就是"][0]
        self.assertEqual(medial.verdict, MEANING)
        self.assertEqual(medial.reason, "restrictive_concession")

    def test_qishi_is_always_meaning(self) -> None:
        for text in ("其实我不太同意", "我看了一下，其实还行"):
            marks = [m for m in classify_oral(text) if m.surface == "其实"]
            self.assertTrue(all(m.verdict == MEANING for m in marks), text)

    def test_final_particles_are_tone_not_noise(self) -> None:
        marks = {m.surface: m.verdict for m in classify_oral("你先做吧")}
        self.assertEqual(marks["吧"], TONE)

    def test_tone_survives_for_tone_visible_listener(self) -> None:
        kept, _ = strip_oral("嗯，你先做吧", drop_tone=False)
        self.assertIn("吧", kept)
        self.assertNotIn("嗯", kept)
        dropped, _ = strip_oral("嗯，你先做吧", drop_tone=True)
        self.assertNotIn("吧", dropped)

    def test_nage_before_a_noun_is_a_demonstrative(self) -> None:
        marks = [m for m in classify_oral("那个功能先关掉") if m.surface == "那个"]
        self.assertEqual(marks[0].verdict, MEANING)
        kept, _ = strip_oral("那个功能先关掉")
        self.assertIn("那个功能", kept)

    def test_first_ranhou_is_sequence_later_ones_are_filler(self) -> None:
        verdicts = [
            m.verdict for m in classify_oral("先写完，然后交上去，然后然后再说") if m.surface == "然后"
        ]
        self.assertEqual(verdicts[0], MEANING)
        self.assertTrue(all(v == NOISE for v in verdicts[1:]))


class DetailTests(unittest.TestCase):
    """意思是每个细节的意思，不是整句的意思。"""

    def test_sentence_decomposes_into_roles(self) -> None:
        roles = {d.role: d.surface for d in extract_details("我觉得还行，不过周期有点长")}
        self.assertEqual(roles["stance"], "我觉得")
        self.assertEqual(roles["concession"], "不过")
        self.assertEqual(roles["degree"], "有点")

    def test_downtoner_loss_is_a_failure(self) -> None:
        diff = detail_diff("周期有点长", "周期长")
        self.assertIn("degree:有点", diff["lost"])

    def test_negation_scope_is_tracked(self) -> None:
        diff = detail_diff("我不一定去", "我一定去")
        self.assertTrue(diff.get("lost") or diff.get("added"))

    def test_every_preset_preserves_every_detail(self) -> None:
        for raw in SAMPLES:
            original, _ = preserve_original(raw)
            for key, profile in PRESETS.items():
                res = adapt_with_report(original, profile)
                self.assertNotIn(
                    "lost", detail_diff(res.baseline, res.text), f"{key} lost a detail on {raw!r}"
                )


if __name__ == "__main__":
    unittest.main()
