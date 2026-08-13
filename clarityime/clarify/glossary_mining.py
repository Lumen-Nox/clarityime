"""Mine candidate slang from PUBLIC text corpora → human review queue → table.

What this is and is not
------------------------
This module never talks to the network itself and never decides that a word
means something. It is the deterministic middle of a three-step pipeline:

    1. COLLECT  (outside this module, e.g. a scraper hitting public posts/
                 comments/hashtags — never DMs, never login-walled content)
    2. MINE     (this module: pure frequency counting, no AI, no guessing
                 of meaning)
    3. REVIEW   (a human reads the candidates, writes the plain-language
                 gloss by hand, and only then a candidate becomes a real
                 JARGON_TABLE / GAME tag_registry entry)

Why frequency counting and not an LLM summarising "what slang means":
frequency is a fact about the corpus (this word appears often in posts
tagged <domain> and rarely elsewhere). "What it means" is an inference, and
inferences are exactly what this pipeline must not fabricate. A human writes
the gloss; this module only tells the human WHERE to look.

Corpus format
-------------
A corpus is a list of ``CorpusPost`` — plain text plus the domain tag it was
collected under (e.g. posts pulled from a "第五人格" hashtag get
domain="asym_horror"). The domain label is supplied by whoever ran the
collector (a hashtag, a subreddit, a game's official forum section), not
inferred by this module.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from clarityime.clarify.paraphrase import JARGON_TABLE

__all__ = [
    "CorpusPost",
    "Candidate",
    "mine_candidates",
    "load_corpus_jsonl",
    "write_review_queue",
]


@dataclass(frozen=True)
class CorpusPost:
    text: str
    domain: str  # the tag this post was collected under, e.g. "asym_horror"
    lang: str = "zh"  # reading language of the post, e.g. "zh" | "en" | "ja"


@dataclass(frozen=True)
class Candidate:
    term: str
    domain: str
    lang: str
    #: how many posts in *this* domain contained it
    in_domain_count: int
    #: how many posts OUTSIDE this domain contained it (0 = looks domain-specific)
    outside_count: int
    example: str  # one real sentence, for the human reviewer to read in context

    @property
    def specificity(self) -> float:
        """1.0 = only ever seen inside this domain. 0.0 = everywhere. Not a
        meaning score — purely "how likely is this jargon vs. common speech"."""
        total = self.in_domain_count + self.outside_count
        return self.in_domain_count / total if total else 0.0


#: Chinese has no spaces, so real segmentation needs a dictionary — which is
#: exactly what we don't have yet for slang. Sliding 2-4 char windows over
#: each CJK run is the standard cheap substitute for candidate mining (the
#: real word gets counted at every length; the human reviewer picks the
#: right cut). Latin-script runs use normal whitespace tokenisation.
#:
#: Note the mining relies on TWO filters, not one:
#:   1. this stop-phrase list catches grammar glue that would otherwise look
#:      "frequent" in any domain (因为/所以/可能/如果/一直 …) — a closed,
#:      human-maintained list, same audit standard as JARGON_TABLE.
#:   2. ``min_specificity`` in :func:`mine_candidates` catches everything
#:      else: a phrase that shows up equally across domains is background
#:      chatter, jargon shows up mostly in ONE domain. This is the real
#:      signal — the stop list only removes the noisiest, most predictable
#:      false positives so a small test corpus doesn't drown in them.
_CJK_RUN = re.compile(r"[\u4e00-\u9fff]{2,}")
_LATIN_WORD = re.compile(r"[A-Za-z]{2,}")
_STOP_PHRASES = frozenset(
    "这个 那个 然后 就是 可能 应该 觉得 因为 所以 但是 如果 虽然 一直 已经 现在 "
    "今天 昨天 明天 今天很 我今天 因为我 所以没 忙所以 天很忙".split()
)


def _cjk_ngrams(run: str) -> set[str]:
    out: set[str] = set()
    for size in (2, 3, 4):
        for i in range(len(run) - size + 1):
            gram = run[i : i + size]
            if gram not in _STOP_PHRASES:
                out.add(gram)
    return out


_EN_STOP = frozenset(
    {"the", "and", "was", "for", "with", "that", "this", "have", "from", "just", "really"}
)


def _tokens(text: str) -> set[str]:
    out: set[str] = set()
    for run in _CJK_RUN.findall(text):
        out |= _cjk_ngrams(run)
    for word in _LATIN_WORD.findall(text):
        if word.lower() not in _EN_STOP:
            out.add(word.lower())
    return out


def mine_candidates(
    posts: list[CorpusPost],
    *,
    min_in_domain: int = 3,
    min_specificity: float = 0.7,
    known: frozenset[str] | None = None,
) -> list[Candidate]:
    """Pure counting — no meaning is ever assigned here.

    A term becomes a candidate only if it shows up at least ``min_in_domain``
    times inside one domain AND is rare everywhere else (``min_specificity``).
    That combination is what makes it *look like* jargon; whether it's real,
    and what it means, is the human reviewer's call.
    """
    known = known or frozenset(JARGON_TABLE)
    by_domain: dict[str, Counter[str]] = {}
    examples: dict[tuple[str, str], str] = {}
    lang_of: dict[str, str] = {}

    for post in posts:
        toks = _tokens(post.text)
        by_domain.setdefault(post.domain, Counter()).update(toks)
        lang_of[post.domain] = post.lang
        for t in toks:
            examples.setdefault((post.domain, t), post.text)

    total_outside: dict[str, Counter[str]] = {}
    for dom, counts in by_domain.items():
        outside = Counter()
        for other_dom, other_counts in by_domain.items():
            if other_dom != dom:
                outside.update(other_counts)
        total_outside[dom] = outside

    out: list[Candidate] = []
    for dom, counts in by_domain.items():
        for term, n in counts.items():
            if term in known or n < min_in_domain:
                continue
            outside_n = total_outside[dom].get(term, 0)
            cand = Candidate(
                term=term,
                domain=dom,
                lang=lang_of.get(dom, "zh"),
                in_domain_count=n,
                outside_count=outside_n,
                example=examples.get((dom, term), ""),
            )
            if cand.specificity >= min_specificity:
                out.append(cand)

    out.sort(key=lambda c: (-c.in_domain_count, c.term))
    return out


def load_corpus_jsonl(path: str) -> list[CorpusPost]:
    """Read ``{"text": ..., "domain": ..., "lang": "zh"}`` per line.

    This is the hand-off point from a collector (whatever fetched the public
    posts) to the miner. The collector is responsible for only including
    posts that were public and for stamping the correct domain/lang.
    """
    import json

    posts: list[CorpusPost] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            posts.append(
                CorpusPost(
                    text=row["text"],
                    domain=row["domain"],
                    lang=row.get("lang", "zh"),
                )
            )
    return posts


def write_review_queue(candidates: list[Candidate], path: str) -> None:
    """One line per candidate — a human opens this file and either deletes
    the line (reject) or fills in the gloss and moves it into
    ``JARGON_TABLE`` / ``tag_registry.py`` by hand. Nothing here writes to
    the live tables automatically."""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# 候选黑话 review queue — 人工确认后手动搬进 JARGON_TABLE，本文件不会被系统读取\n")
        fh.write("# term\tdomain\tlang\tin_domain\toutside\tspecificity\texample\n")
        for c in candidates:
            fh.write(
                f"{c.term}\t{c.domain}\t{c.lang}\t{c.in_domain_count}\t"
                f"{c.outside_count}\t{c.specificity:.2f}\t{c.example}\n"
            )
