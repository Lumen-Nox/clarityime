"""Glossary mining: pure frequency counting, human-gated, never auto-writes."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import unittest

from clarityime.clarify.glossary_mining import (
    Candidate,
    CorpusPost,
    load_corpus_jsonl,
    mine_candidates,
    write_review_queue,
)
from clarityime.clarify.paraphrase import JARGON_TABLE


class MiningTests(unittest.TestCase):
    def test_domain_specific_slang_is_found(self) -> None:
        # 红温 = "so angry your face goes red" — real slang, deliberately NOT
        # in JARGON_TABLE yet, so we can prove mining finds *new* terms.
        posts = [
            CorpusPost("这局对面直接红温了三个，我们守椅赢的", "asym_horror"),
            CorpusPost("红温真的太快了，根本反不过来", "asym_horror"),
            CorpusPost("对面又红温了，太惨了", "asym_horror"),
            CorpusPost("今天天气不错，出去玩了一整天", "gaming"),
            CorpusPost("原神抽卡十连全歪了", "gacha"),
        ]
        cands = mine_candidates(posts, min_in_domain=2, min_specificity=0.5)
        terms = {c.term for c in cands}
        self.assertIn("红温", terms)

    def test_already_known_terms_are_skipped(self) -> None:
        posts = [CorpusPost("监管者一直守椅", "asym_horror")] * 5
        cands = mine_candidates(posts, min_in_domain=2)
        self.assertNotIn("监管者", {c.term for c in cands})  # already in JARGON_TABLE

    def test_ordinary_chatter_is_filtered_by_cross_domain_frequency(self) -> None:
        """The real filter is specificity, not the stop list: ordinary phrasing
        shows up in every domain, jargon shows up mostly in one."""
        # Same exact sentence tagged under three different domains: real
        # jargon would only show up under ONE of these, ordinary phrasing
        # shows up under all of them equally.
        posts = (
            [CorpusPost("因为我今天很忙所以没去", "school")] * 4
            + [CorpusPost("因为我今天很忙所以没去", "asym_horror")] * 4
            + [CorpusPost("因为我今天很忙所以没去", "gacha")] * 4
        )
        cands = mine_candidates(posts, min_in_domain=2, min_specificity=0.6)
        self.assertEqual(cands, [])  # nothing survives; it's everywhere

    def test_known_stop_phrases_are_never_candidates_even_if_domain_only(self) -> None:
        posts = [CorpusPost("因为所以可能应该觉得如果虽然一直已经现在", "school")] * 5
        cands = mine_candidates(posts, min_in_domain=2)
        stop_hits = {c.term for c in cands} & {"因为", "所以", "可能", "应该", "如果", "虽然", "一直", "已经", "现在"}
        self.assertEqual(stop_hits, set())

    def test_word_seen_everywhere_is_not_domain_specific(self) -> None:
        posts = (
            [CorpusPost("大家都在说卷心菜好吃", "asym_horror")] * 3
            + [CorpusPost("卷心菜真的好吃", "gacha")] * 3
        )
        cands = mine_candidates(posts, min_in_domain=2, min_specificity=0.9)
        self.assertNotIn("卷心菜", {c.term for c in cands})

    def test_mining_is_deterministic(self) -> None:
        posts = [
            CorpusPost("落地成盒真的很难受", "fps"),
            CorpusPost("落地成盒", "fps"),
            CorpusPost("落地成盒了", "fps"),
        ]
        a = mine_candidates(posts, min_in_domain=2)
        b = mine_candidates(posts, min_in_domain=2)
        self.assertEqual([c.term for c in a], [c.term for c in b])

    def test_review_queue_never_touches_jargon_table(self) -> None:
        before = dict(JARGON_TABLE)
        cands = [
            Candidate(
                term="落地成盒", domain="fps", lang="zh",
                in_domain_count=5, outside_count=0, example="落地成盒",
            )
        ]
        with tempfile.TemporaryDirectory() as tmp:
            out = str(Path(tmp) / "queue.tsv")
            write_review_queue(cands, out)
            self.assertTrue(Path(out).exists())
            content = Path(out).read_text(encoding="utf-8")
            self.assertIn("落地成盒", content)
        self.assertEqual(dict(JARGON_TABLE), before)  # untouched

    def test_corpus_round_trips_through_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "corpus.jsonl")
            Path(path).write_text(
                '{"text": "秒倒了", "domain": "asym_horror", "lang": "zh"}\n'
                '{"text": "gg wp", "domain": "fps", "lang": "en"}\n',
                encoding="utf-8",
            )
            posts = load_corpus_jsonl(path)
        self.assertEqual(len(posts), 2)
        self.assertEqual(posts[1].lang, "en")


if __name__ == "__main__":
    unittest.main()
