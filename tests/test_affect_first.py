"""affect_first: stance/feeling clauses lead for Fi/Fe listeners. No LLM."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import unittest

from clarityime.cerome.tags import derive_processing_tags, listener_tags
from clarityime.cerome.human import CeromeL1Comm, CeromeL2Values
from clarityime.clarify.comprehension import order_supports
from clarityime.clarify.listener_adapt import plan_from_tags


def _blank_cerome(tags):
    return type(
        "C",
        (),
        {
            "l1": CeromeL1Comm(),
            "l2": CeromeL2Values(),
            "tags": tags,
        },
    )()


class AffectFirstTests(unittest.TestCase):
    def test_infp_implies_affect_first_intj_does_not(self) -> None:
        infp = derive_processing_tags(_blank_cerome(["mbti_infp"]))
        intj = derive_processing_tags(_blank_cerome(["mbti_intj"]))
        self.assertTrue(infp.has("affect_first"))
        self.assertFalse(intj.has("affect_first"))

    def test_feeling_clause_leads_when_flag_is_on(self) -> None:
        clauses = ["因为成本会超预算", "因为我担心大家会累"]
        notes: list[str] = []
        out = order_supports(clauses, {"warmth": 0.5, "precision": 0.5}, notes, affect_first=True)
        self.assertEqual(out[0], "因为我担心大家会累")
        self.assertIn("A8:affect_first", notes)

    def test_same_clauses_without_flag_keep_cost_first(self) -> None:
        clauses = ["因为成本会超预算", "因为我担心大家会累"]
        notes: list[str] = []
        out = order_supports(clauses, {"precision": 0.9, "warmth": 0.2}, notes)
        self.assertEqual(out[0], "因为成本会超预算")

    def test_plan_exposes_a8a_only_when_tagged(self) -> None:
        tagged = listener_tags(_blank_cerome(["mbti_infp"]))
        plain = listener_tags(_blank_cerome(["mbti_intj"]))
        self.assertIn("A8a", plan_from_tags(tagged, CeromeL2Values()).tags())
        self.assertNotIn("A8a", plan_from_tags(plain, CeromeL2Values()).tags())


if __name__ == "__main__":
    unittest.main()
