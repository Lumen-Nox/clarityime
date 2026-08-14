"""Affect markers are first-class details — losing 委屈 is a failure."""

from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clarityime.clarify.details import extract_details, details_preserved


class AffectDetailTests(unittest.TestCase):
    def test_live_affect_words_are_extracted(self) -> None:
        text = "我有点委屈，也害怕大家失望，但还是安心。"
        roles = {d.surface: d.role for d in extract_details(text)}
        self.assertEqual(roles.get("委屈"), "affect")
        self.assertEqual(roles.get("害怕"), "affect")
        self.assertEqual(roles.get("失望"), "affect")
        self.assertEqual(roles.get("安心"), "affect")
        self.assertEqual(roles.get("有点"), "degree")

    def test_dropping_an_affect_word_fails_preservation(self) -> None:
        before = "我委屈，也心累。"
        after = "我心累。"
        self.assertFalse(details_preserved(before, after))
        self.assertTrue(details_preserved(before, before))


if __name__ == "__main__":
    unittest.main()
