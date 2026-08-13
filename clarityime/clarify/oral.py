"""Oral markers — decide **per occurrence** whether a spoken particle carries meaning.

Some oral particles are noise; others carry discourse meaning or tone — classify per occurrence.
depending on position:

    嗯那个，就是我觉得…      「就是」sentence-initial   → hesitation, no content
    方案还行，就是风险有点多   「就是」after a clause     → 只不过, a concession
    其实我不太同意          「其实」                  → counter-expectation marker
    你先做吧                「吧」sentence-final       → softener (tone, not noise)

So each occurrence gets one of three verdicts:

  NOISE    — hesitation/floor-holding, deleting it changes nothing.
  MEANING  — a discourse marker with propositional force. **Never** deletable.
  TONE     — attitude/politeness/softening. Deletable only for a listener
             tagged ``no_padding``; kept for ``tone_visible``.

Evidence
  * Discourse markers are procedural, not decorative: they instruct the hearer
    how to relate the clause to context (Schiffrin 1987; Fraser 1999).
  * 「其实」/「就是」as 反预期 and 限定 markers in Mandarin (Biq 2001; Wang & Huang
    2006, *Journal of Pragmatics*, on 其实 as counter-expectation).
  * Sentence-final particles 吧/啊/呢 encode speaker stance and mitigate face
    threat (Li & Thompson 1981; Chu 2009) — removing them shifts illocutionary
    force, which is exactly the illocutionary-shift failure we guard against.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = ["OralMark", "NOISE", "MEANING", "TONE", "classify_oral", "strip_oral"]

NOISE = "noise"
MEANING = "meaning"
TONE = "tone"

_BOUNDARY = "，,。；;！!？?、\n"


@dataclass(frozen=True)
class OralMark:
    surface: str
    start: int
    end: int
    verdict: str
    reason: str

    def note(self) -> str:
        return f"oral:{self.surface}:{self.verdict}"


_SENTENCE_END = "。；;！!？?\n"

# Segments made only of these have no content — a 「就是」after them is still
# hesitation, not 只不过.
_NOISE_ONLY = re.compile(r"^[嗯呃啊那个就是然后对你知道吗怎么说呢我跟说，,、\s]*$")


def _at_clause_start(text: str, i: int) -> bool:
    j = i - 1
    while j >= 0 and text[j] in " \u3000":
        j -= 1
    return j < 0 or text[j] in _BOUNDARY


def _utterance_initial(text: str, i: int) -> bool:
    """True at the very start, or after a full stop, or after a contentless run.

    「就是我觉得…」        → initial, hesitation
    「嗯那个，就是我觉得…」 → preceding segment is all filler, still hesitation
    「方案还行，就是风险多」 → preceding segment has content, so this is 只不过
    """
    j = i - 1
    while j >= 0 and text[j] in " \u3000":
        j -= 1
    if j < 0:
        return True
    if text[j] in _SENTENCE_END:
        return True
    if text[j] not in _BOUNDARY:
        return False
    # Comma: look back one segment and ask whether it said anything.
    k = j - 1
    while k >= 0 and text[k] not in _BOUNDARY:
        k -= 1
    return bool(_NOISE_ONLY.match(text[k + 1 : j]))


def _at_clause_end(text: str, j: int) -> bool:
    k = j
    while k < len(text) and text[k] in " \u3000":
        k += 1
    return k >= len(text) or text[k] in _BOUNDARY


# Pure hesitation — no position ever makes these contentful.
_PURE_NOISE = ("嗯", "呃", "唉那个", "那个啥", "对对对", "你知道吗", "怎么说呢", "我跟你说啊")

_SCAN = re.compile(
    r"嗯+|呃+|啊+|那个啥|那个|就是说|就是|其实|然后|反正|你知道吗|你知道|怎么说呢"
    r"|我跟你说啊|对对对|吧|呢|嘛|哦|喔"
)


def _verdict(text: str, surface: str, start: int, end: int, seen: dict[str, int]) -> tuple[str, str]:
    head = _at_clause_start(text, start)
    tail = _at_clause_end(text, end)

    if surface.startswith(("嗯", "呃")):
        return NOISE, "hesitation"
    if surface in ("对对对", "你知道吗", "你知道", "怎么说呢", "我跟你说啊"):
        return NOISE, "floor_holding"

    if surface == "那个啥":
        return NOISE, "hesitation"
    if surface == "那个":
        # 「那个功能」is a demonstrative — real reference, not hesitation.
        after = text[end : end + 1]
        if after and after not in _BOUNDARY and after not in "就是":
            return MEANING, "demonstrative"
        return NOISE, "hesitation"

    if surface in ("就是", "就是说"):
        if _utterance_initial(text, start):
            return NOISE, "hesitation_initial"
        # 「方案还行，就是风险有点多」= 只不过 → restrictive concession
        return MEANING, "restrictive_concession"

    if surface == "其实":
        return MEANING, "counter_expectation"

    if surface == "反正":
        return MEANING, "regardless"

    if surface == "然后":
        # First one can mark real sequence; later ones are chaining filler.
        seen["然后"] = seen.get("然后", 0) + 1
        return (MEANING, "sequence") if seen["然后"] == 1 else (NOISE, "chaining")

    if surface.startswith("啊"):
        # sentence-final 啊 softens; mid-sentence 啊 is hesitation
        return (TONE, "softener") if tail else (NOISE, "hesitation")

    if surface in ("吧", "呢", "嘛", "哦", "喔"):
        return (TONE, "final_particle") if tail else (NOISE, "hesitation")

    return NOISE, "unclassified"


def classify_oral(text: str) -> list[OralMark]:
    """Label every oral marker occurrence. Deterministic, position-sensitive."""
    seen: dict[str, int] = {}
    marks: list[OralMark] = []
    for m in _SCAN.finditer(text):
        verdict, reason = _verdict(text, m.group(0), m.start(), m.end(), seen)
        marks.append(OralMark(m.group(0), m.start(), m.end(), verdict, reason))
    return marks


def strip_oral(text: str, *, drop_tone: bool = False) -> tuple[str, list[OralMark]]:
    """Remove NOISE marks. TONE goes only when the listener is tagged ``no_padding``.

    MEANING is never removed — that is the invariant this module exists for.
    """
    marks = classify_oral(text)
    removed = [
        mk for mk in marks if mk.verdict == NOISE or (drop_tone and mk.verdict == TONE)
    ]
    out = []
    cursor = 0
    for mk in removed:
        out.append(text[cursor : mk.start])
        cursor = mk.end
    out.append(text[cursor:])
    joined = "".join(out)
    joined = re.sub(r"[，,]{2,}", "，", joined)
    joined = re.sub(r"^[，,、\s]+", "", joined)
    joined = re.sub(r"[，,]\s*(?=[。；;！!？?])", "", joined)
    return joined.strip(), removed
