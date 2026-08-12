"""Unit tests for deterministic local clarify rules."""

from __future__ import annotations

import unittest

from clarityime.cerome.listener_presets import get_listener_preset
from clarityime.clarify.candidates import clarify_candidates
from clarityime.clarify.listener_adapt import _words_preserved, adapt_for_listener
from clarityime.clarify.local_rules import (
    clarify_dual_for_listener,
    preserve_original,
)
from clarityime.models import AudienceMode, ContactProfile


class LocalRulesTests(unittest.TestCase):
    def test_preserve_original_keeps_hedging(self) -> None:
        raw = "就是我觉得这个方案还行，胜算挺高的，而且周期也长"
        original, _ = preserve_original(raw)
        self.assertIn("还行", original)
        self.assertIn("挺高", original)
        self.assertNotIn("不太行", original)

    def test_dual_output_words_preserved(self) -> None:
        raw = "对对对然后那个就是我明天可能去不了因为我要去看医生"
        preset = get_listener_preset("d_type")
        assert preset is not None
        original, for_listener, _ = clarify_dual_for_listener(raw, preset)
        self.assertIn("因为", original)
        self.assertIn("医生", original)
        self.assertTrue(_words_preserved(original, for_listener))

    def test_d_type_vs_s_type_layout_differs(self) -> None:
        raw = "嗯我觉得吧这个方向其实还可以，就是风险也有点多，而且周期比较长，但是团队士气还行"
        original, _ = preserve_original(raw)
        d = get_listener_preset("d_type")
        s = get_listener_preset("s_type")
        assert d is not None and s is not None
        d_out, _ = adapt_for_listener(original, d)
        s_out, _ = adapt_for_listener(original, s)
        self.assertTrue(_words_preserved(original, d_out))
        self.assertTrue(_words_preserved(original, s_out))
        self.assertNotEqual(d_out, s_out)

    def test_candidates_contact_dual_labels(self) -> None:
        raw = "我明天可能去不了因为我要去看医生"
        contact = ContactProfile(
            id=1,
            name="Alex",
            relationship="同学",
            extra={"cerome": get_listener_preset("d_type").to_dict() if get_listener_preset("d_type") else {}},
        )
        opts = clarify_candidates(raw, mode=AudienceMode.CONTACT, contact=contact)
        labels = {c["label"] for c in opts}
        self.assertIn("original", labels)
        self.assertIn("for_listener", labels)
        orig = next(c["text"] for c in opts if c["label"] == "original")
        hear = next(c["text"] for c in opts if c["label"] == "for_listener")
        self.assertIn("因为", orig)
        self.assertNotIn("不好意思", orig)
        self.assertTrue(_words_preserved(orig, hear))

    def test_listener_preset_param(self) -> None:
        raw = "就是我觉得这个方案还行，胜算挺高的，而且周期也长"
        opts = clarify_candidates(raw, mode=AudienceMode.DEFAULT, listener_preset="intj")
        labels = {c["label"] for c in opts}
        self.assertIn("original", labels)
        self.assertIn("for_listener", labels)

    def test_deterministic_repeat(self) -> None:
        raw = "嗯那个你好，就是我想问一下这个项目大概什么时候能做完啊"
        a = clarify_candidates(raw, mode=AudienceMode.DEFAULT, listener_preset="s_type")
        b = clarify_candidates(raw, mode=AudienceMode.DEFAULT, listener_preset="s_type")
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
