"""Share links: fragment-only payload (server never sees content), deterministic,
default-on but skippable, and wired into the engine's for_listener output."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import unittest

from clarityime.share_link import (
    SharePayload,
    append_share_link,
    build_share_link,
    decode_share_payload,
    encode_share_payload,
)


class RoundTripTests(unittest.TestCase):
    def test_encode_decode_round_trips(self) -> None:
        payload = SharePayload(
            original="那个方案我觉得还行",
            for_listener="这个方案我认为可行。",
            listener_tags=("mbti_intj", "hobby_gaming"),
        )
        fragment = encode_share_payload(payload)
        back = decode_share_payload(fragment)
        self.assertEqual(back.original, payload.original)
        self.assertEqual(back.for_listener, payload.for_listener)
        self.assertEqual(back.listener_tags, payload.listener_tags)

    def test_encoding_is_deterministic(self) -> None:
        payload = SharePayload(original="a", for_listener="b")
        self.assertEqual(encode_share_payload(payload), encode_share_payload(payload))

    def test_corrupt_fragment_raises_instead_of_guessing(self) -> None:
        with self.assertRaises(ValueError):
            decode_share_payload("not-valid-base64!!!")

    def test_wrong_schema_version_raises(self) -> None:
        import base64
        import json

        raw = json.dumps({"v": 999, "original": "x", "for_listener": "y"}).encode("utf-8")
        fragment = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
        with self.assertRaises(ValueError):
            decode_share_payload(fragment)

    def test_link_is_only_after_the_hash_no_query_params(self) -> None:
        link = build_share_link("原句", "听者版")
        self.assertIn("#", link)
        base, fragment = link.split("#", 1)
        self.assertNotIn("?", base)
        # decodable straight from the fragment half of the URL
        decode_share_payload(fragment)


class AppendShareLinkTests(unittest.TestCase):
    def test_default_on_appends_link_when_texts_differ(self) -> None:
        out = append_share_link("听者版本", "原始版本", enabled=True)
        self.assertIn("原句", out)
        self.assertIn("clarityime.app/c#", out)

    def test_disabled_never_appends(self) -> None:
        out = append_share_link("听者版本", "原始版本", enabled=False)
        self.assertEqual(out, "听者版本")

    def test_identical_texts_skip_link_even_if_enabled(self) -> None:
        out = append_share_link("一样的话", "一样的话", enabled=True)
        self.assertEqual(out, "一样的话")

    def test_english_lang_uses_english_label(self) -> None:
        out = append_share_link("listener version", "original version", enabled=True, lang="en")
        self.assertIn("(original:", out)
        self.assertNotIn("原句", out)


if __name__ == "__main__":
    unittest.main()
