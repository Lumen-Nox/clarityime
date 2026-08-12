"""Comprehension engine — invariants + evidence-backed ops.

Basis: docs/COMPREHENSION_MODEL.md
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import unittest

from clarityime.cerome.listener_presets import PRESETS
from clarityime.clarify.comprehension import (
    check_invariants,
    claim_first,
    comprehension_cost,
    resolve_referents,
    restore_subjects,
    split_clauses,
)
from clarityime.clarify.listener_adapt import adapt_with_report, plan_from_cerome
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
        for raw in SAMPLES:
            original, _ = preserve_original(raw)
            for key, profile in PRESETS.items():
                adapted, _notes, _b, _a = adapt_with_report(original, profile)
                report = check_invariants(original, adapted)
                self.assertTrue(
                    report.ok,
                    f"{key} violated on {raw!r}: new={report.new_content} "
                    f"lost={report.lost_content} hedges={report.lost_hedges}",
                )

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
        adapted, _n, _b, after = adapt_with_report(original, PRESETS["analytical"])
        self.assertEqual(after.bridging, 0)
        self.assertIn("因为我要去看医生", adapted)


class PlanTests(unittest.TestCase):
    def test_warm_listener_gets_single_flow_block(self) -> None:
        original, _ = preserve_original(SAMPLES[2])
        plan = plan_from_cerome(PRESETS["warm_flow"])
        self.assertTrue(plan.flow)
        adapted, _n, _b, _a = adapt_with_report(original, PRESETS["warm_flow"])
        self.assertNotIn("\n", adapted)

    def test_fast_listener_gets_short_lines(self) -> None:
        original, _ = preserve_original(SAMPLES[2])
        plan = plan_from_cerome(PRESETS["fast_scan"])
        self.assertLessEqual(plan.capacity, 22)
        adapted, _n, _b, _a = adapt_with_report(original, PRESETS["fast_scan"])
        self.assertIn("\n", adapted)

    def test_presets_produce_distinct_layouts(self) -> None:
        original, _ = preserve_original(SAMPLES[2])
        outs = {
            key: adapt_with_report(original, p)[0] for key, p in PRESETS.items()
        }
        self.assertNotEqual(outs["warm_flow"], outs["analytical"])


if __name__ == "__main__":
    unittest.main()
