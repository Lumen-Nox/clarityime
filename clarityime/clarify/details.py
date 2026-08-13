"""Detail units — meaning is decomposed, not treated as one blob.

Meaning is not one vague whole — each span can carry its own role.
the **detail**: a span that carries one piece of meaning, with a role saying what
kind of meaning it is. 「这个方案还行，胜算挺高，不过周期有点长」 is not one meaning,
it is six:

    stance   还行        moderate endorsement, not enthusiasm
    degree   挺          intensifier on 胜算
    epistemic —
    concession 不过      the pivot; deleting it flips the shape of the argument
    degree   有点        downtoner on 周期长 — 「有点长」≠「长」
    quantity —

Each role is checked independently after adaptation. Losing a single 有点 is a
failure even if every character of the sentence survives somewhere else.

Evidence
  * Propositional analysis: comprehension is measured over idea units, not
    sentences (Kintsch & van Dijk 1978).
  * Hedges and downtoners are propositional operators, not politeness garnish —
    they change commitment strength (Lakoff 1973; Hyland 1998, *Hedging in
    Scientific Research Articles*).
  * Degree modifiers shift the scalar value asserted (Kennedy & McNally 2005).
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

__all__ = ["Detail", "ROLE_MARKERS", "extract_details", "detail_diff", "details_preserved"]


@dataclass(frozen=True)
class Detail:
    surface: str
    role: str
    start: int

    def key(self) -> tuple[str, str]:
        return (self.role, self.surface)


#: role → surface markers. Ordered longest-first inside each role at build time.
ROLE_MARKERS: dict[str, tuple[str, ...]] = {
    # who is committing to this, and how strongly
    "stance": ("我觉得", "我认为", "我感觉", "我看", "个人觉得", "觉得", "认为", "感觉"),
    # scalar strength — 「有点长」和「长」是两个意思
    "degree": (
        "有点儿", "有点", "稍微", "略微", "比较", "还挺", "挺", "特别", "非常",
        "太", "极其", "超级", "多少有些", "有些", "不太", "不怎么", "还行", "一般",
    ),
    # commitment to truth
    "epistemic": (
        "一定", "肯定", "必然", "应该", "大概", "可能", "也许", "或许", "说不定",
        "未必", "不一定", "差不多", "基本上", "好像", "似乎",
    ),
    "cause": ("因为", "由于", "所以", "因此", "导致"),
    "concession": ("虽然", "但是", "不过", "然而", "可是", "只不过", "尽管"),
    "condition": ("如果", "要是", "假如", "万一", "除非", "只要"),
    "request": ("能不能", "可不可以", "可以吗", "麻烦", "希望", "想问", "想请", "拜托"),
    "negation": ("不是", "没有", "不能", "不会", "别", "无法"),
    "affect": (
        "抱歉", "不好意思", "担心", "着急", "开心", "难受", "累", "士气",
        "压力", "紧张", "生气", "遗憾",
    ),
    "sequence": ("首先", "其次", "最后", "先", "再", "接着", "之后"),
}

_ROLE_SCANS: dict[str, re.Pattern[str]] = {
    role: re.compile("|".join(re.escape(m) for m in sorted(markers, key=len, reverse=True)))
    for role, markers in ROLE_MARKERS.items()
}

_QUANTITY = re.compile(r"\d+(?:\.\d+)?\s*(?:[个次天周月年%点分小时人条件]|万|千|百)?")


def extract_details(text: str) -> list[Detail]:
    """Every meaning-bearing detail with its role. Deterministic and order-stable."""
    found: list[Detail] = []
    claimed: list[tuple[int, int]] = []

    def overlaps(a: int, b: int) -> bool:
        return any(not (b <= s or a >= e) for s, e in claimed)

    # Longer roles first so 「不一定」 wins over 「一定」, 「不是」 over 「是」.
    for role in ("epistemic", "negation", "stance", "concession", "condition",
                 "request", "cause", "degree", "affect", "sequence"):
        for m in _ROLE_SCANS[role].finditer(text):
            if overlaps(m.start(), m.end()):
                continue
            claimed.append((m.start(), m.end()))
            found.append(Detail(m.group(0), role, m.start()))

    for m in _QUANTITY.finditer(text):
        if m.group(0).strip() and not overlaps(m.start(), m.end()):
            claimed.append((m.start(), m.end()))
            found.append(Detail(m.group(0).strip(), "quantity", m.start()))

    return sorted(found, key=lambda d: d.start)


def detail_diff(before: str, after: str) -> dict[str, list[str]]:
    """Which details were lost or invented. Empty dict = every detail survived."""
    b = Counter(d.key() for d in extract_details(before))
    a = Counter(d.key() for d in extract_details(after))
    lost = [f"{r}:{s}" for (r, s), n in (b - a).items() for _ in range(n)]
    added = [f"{r}:{s}" for (r, s), n in (a - b).items() for _ in range(n)]
    out: dict[str, list[str]] = {}
    if lost:
        out["lost"] = sorted(lost)
    if added:
        out["added"] = sorted(added)
    return out


def details_preserved(before: str, after: str) -> bool:
    return not detail_diff(before, after)
