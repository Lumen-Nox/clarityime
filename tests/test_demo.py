"""The demo a judge runs must show the Topic 4 contrast, not only tone."""

from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clarityime.cerome.listener_presets import get_listener_preset
from clarityime.clarify.listener_adapt import adapt_with_report
from clarityime.main import cmd_demo


class DemoTests(unittest.TestCase):
    def test_demo_exits_zero(self) -> None:
        self.assertEqual(cmd_demo(None), 0)

    def test_same_sentence_two_classmates(self) -> None:
        circle = "监管者一直守椅，听到结果我破防了"
        outsider = get_listener_preset("analytical")
        assert outsider is not None
        classmate = replace(
            outsider, tags=list(outsider.tags) + ["game_valorant", "topic_memes"]
        )
        plain = adapt_with_report(circle, outsider).text
        cross = adapt_with_report(circle, classmate).text
        self.assertIn("情绪被戳到", plain)
        self.assertNotIn("就像", plain)
        self.assertIn("就像架点", cross)
        self.assertIn("破防", cross)
        self.assertNotIn("情绪被戳到", cross)


if __name__ == "__main__":
    unittest.main()
