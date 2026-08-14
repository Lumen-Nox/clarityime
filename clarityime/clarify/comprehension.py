"""Comprehension engine — lower the listener's processing cost, add nothing.

Design basis: ``docs/COMPREHENSION_MODEL.md``.

Allowed operations (each is evidence-backed and non-additive):

===  =======================================  ==========================================
A1   resolve_referents  它/这个 → 已出现的名词    Britton & Gülgöz (1991); Haviland & Clark (1974)
A2   restore_subjects   补回省略的主语            Li & Thompson (1981); Kintsch argument overlap
A3   claim_first        结论前置（只调顺序）       Gernsbacher (1990) first-mention advantage
A4   chunk_units        按工作记忆容量切块         Sweller (1988); Cowan (2001)
A5   signal_relations   因果/转折独立成行          Sanders & Noordman (2000); Lorch (1989)
A6   dedupe_repeats     去掉完全重复片段           extraneous load
A7   flow_join          高共情听者不切碎           McNamara et al. (1996)
===  =======================================  ==========================================

Hard invariants (see :func:`check_invariants`): no new content, no lost content,
hedges preserved, polarity stable, deterministic.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from clarityime.clarify.paraphrase import count_jargon  # noqa: F401  (re-export)

PUNCT = "，,；;。！？!?、：: \t\n\u3000"

REASON_PREFIXES = ("因为", "由于")
CONTRAST_PREFIXES = ("但是", "但", "不过", "然而", "可是")
ADDITIVE_PREFIXES = ("而且", "还有", "并且", "另外")
CONSEQUENCE_PREFIXES = ("所以", "因此", "于是")
RELATION_PREFIXES = (
    REASON_PREFIXES + CONTRAST_PREFIXES + ADDITIVE_PREFIXES + CONSEQUENCE_PREFIXES
)

SUBJECT_PRONOUNS = ("我们", "你们", "他们", "咱们", "大家", "我", "你", "您", "他", "她", "它")

QUESTION_MARKERS = (
    "吗",
    "么",
    "是不是",
    "能不能",
    "可不可以",
    "能否",
    "什么",
    "怎么",
    "哪",
    "谁",
    "多久",
    "几时",
)

# Hedging / attitude — must survive every transform
HEDGES = (
    "还行",
    "还可以",
    "可能",
    "大概",
    "也许",
    "比较",
    "相对",
    "感觉",
    "觉得",
    "挺",
    "稍微",
    "有点",
    "似乎",
    "好像",
    "未必",
    "不一定",
    "应该",
    "差不多",
)

NEGATIONS = ("不", "没", "别", "无", "非")

# Oral noise that A6 may drop (only these may disappear)
DROPPABLE = set("嗯啊呃呗嘛哈") | {"那个", "就是", "对对对", "你知道", "怎么说呢", "我跟你说"}

_NOUN_CORE = (
    "接口|系统|服务|页面|模块|功能|项目|方案|方向|团队|周期|成本|风险|数据|格式|"
    "前端|后端|作业|问题|需求|流程|会议|报告|文档|代码|版本|计划|预算|资源|进度"
)
_NOUN_PATTERN = re.compile(
    rf"(?:[A-Za-z][A-Za-z0-9_.\-]*)?(?:{_NOUN_CORE})|[A-Za-z][A-Za-z0-9_.\-]{{2,}}"
)


# --------------------------------------------------------------------------- #
# Text ↔ clause representation
# --------------------------------------------------------------------------- #


def content_tokens(text: str) -> list[str]:
    """Characters that carry content (punctuation & whitespace removed)."""
    return [c for c in text if c not in PUNCT]


def split_clauses(text: str) -> list[str]:
    """Split into clause units; punctuation dropped (re-applied at render)."""
    parts = re.split(r"[，,；;。！？!?\n]+", text)
    return [p.strip() for p in parts if p.strip()]


def _is_question(clause: str) -> bool:
    return any(m in clause for m in QUESTION_MARKERS)


def _terminal(clause: str, force_question: bool = False) -> str:
    if force_question or _is_question(clause):
        return "？"
    return "。"


def render_lines(lines: list[list[str]]) -> str:
    """Render grouped clauses; each inner list is one visual line."""
    out: list[str] = []
    for group in lines:
        if not group:
            continue
        body = "，".join(group)
        # Illocutionary force belongs to the whole utterance, not the last clause.
        # 「能不能晚一天交，因为我这周有点忙」is a request; ending it in 。 would
        # silently turn the author's question into a statement (Searle 1969, speech acts).
        out.append(body + _terminal(group[-1], force_question=any(map(_is_question, group))))
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# A1 — resolve referents
# --------------------------------------------------------------------------- #


def _antecedents(text: str) -> list[tuple[int, str]]:
    return [(m.start(), m.group(0)) for m in _NOUN_PATTERN.finditer(text)]


def resolve_referents(clauses: list[str], notes: list[str]) -> list[str]:
    """它/这个 → the noun the speaker already said (no new lexical material)."""
    joined_prefix = ""
    out: list[str] = []
    for clause in clauses:
        new_clause = clause
        cands = _antecedents(joined_prefix)
        if cands:
            antecedent = cands[-1][1]
            # bare 它/它们 as subject
            replaced = re.sub(r"^它们?(?=[^，,])", antecedent, new_clause)
            if replaced == new_clause:
                replaced = re.sub(r"(?<=[，,、])它们?(?=[^，,])", antecedent, new_clause)
            if replaced == new_clause:
                replaced = re.sub(r"^(?:这|那)个(?![\u4e00-\u9fff])", antecedent, new_clause)
            if replaced != new_clause:
                notes.append(f"A1:referent→{antecedent}")
                new_clause = replaced
        out.append(new_clause)
        joined_prefix += new_clause
    return out


# --------------------------------------------------------------------------- #
# A2 — restore dropped subjects (zero anaphora)
# --------------------------------------------------------------------------- #


def _leading_subject(clause: str) -> str | None:
    for p in SUBJECT_PRONOUNS:
        if clause.startswith(p):
            return p
    m = _NOUN_PATTERN.match(clause)
    if m and m.start() == 0:
        return m.group(0)
    return None


def _has_subject_after_connective(rest: str) -> bool:
    if not rest:
        return True
    if any(rest.startswith(p) for p in SUBJECT_PRONOUNS):
        return True
    m = _NOUN_PATTERN.match(rest)
    return bool(m and m.start() == 0)


def restore_subjects(clauses: list[str], notes: list[str]) -> list[str]:
    """Re-state the subject the speaker already used, where Chinese dropped it."""
    out: list[str] = []
    current_subject: str | None = None
    for clause in clauses:
        subj = _leading_subject(clause)
        if subj:
            current_subject = subj
            out.append(clause)
            continue
        matched_prefix = next(
            (p for p in RELATION_PREFIXES if clause.startswith(p)),
            None,
        )
        if matched_prefix and current_subject:
            rest = clause[len(matched_prefix) :]
            if rest and not _has_subject_after_connective(rest):
                out.append(f"{matched_prefix}{current_subject}{rest}")
                notes.append(f"A2:subject→{current_subject}")
                continue
        out.append(clause)
    return out


# --------------------------------------------------------------------------- #
# A3 — claim first (reorder only)
# --------------------------------------------------------------------------- #


def _clause_role(clause: str) -> str:
    if any(clause.startswith(p) for p in REASON_PREFIXES):
        return "reason"
    if any(clause.startswith(p) for p in CONTRAST_PREFIXES):
        return "contrast"
    if any(clause.startswith(p) for p in ADDITIVE_PREFIXES):
        return "addition"
    if any(clause.startswith(p) for p in CONSEQUENCE_PREFIXES):
        return "consequence"
    return "claim"


def claim_first(clauses: list[str], notes: list[str]) -> list[str]:
    """Move leading reason clauses behind the claim — Gernsbacher foundation."""
    if len(clauses) < 2:
        return clauses
    roles = [_clause_role(c) for c in clauses]
    if roles[0] != "reason":
        return clauses
    first_claim = next((i for i, r in enumerate(roles) if r in ("claim", "consequence")), None)
    if first_claim is None:
        return clauses
    # 因为…所以… is already an explicit signalled pair — reordering would leave
    # 所以 dangling at the front and read worse. Leave it to A5 signaling.
    if roles[first_claim] == "consequence":
        return clauses
    reasons = clauses[:first_claim]
    rest = clauses[first_claim:]
    notes.append("A3:claim_first")
    return rest + reasons


# --------------------------------------------------------------------------- #
# A6 — dedupe exact repeats
# --------------------------------------------------------------------------- #


VALUE_CUES: dict[str, tuple[str, ...]] = {
    "precision": ("数据", "成本", "格式", "错误", "风险", "问题", "接口", "指标"),
    "warmth": ("觉得", "感觉", "希望", "担心", "士气", "累", "难", "开心", "抱歉"),
    "efficiency": ("时间", "截止", "来不及", "赶", "快", "慢", "周期", "排期", "天"),
}


SEQUENCE_PREFIXES = ("首先", "其次", "然后", "接着", "之后", "最后", "先", "再")

#: clauses naming something you can point at — a number, a date, a case
_CONCRETE = re.compile(r"\d|上次|昨天|今天|明天|上周|例如|比如|这次|那次")


def _affinity(clause: str, weights: dict[str, float], *, concrete_first: bool = False) -> float:
    score = 0.0
    for dim, cues in VALUE_CUES.items():
        hits = sum(1 for c in cues if c in clause)
        if re.search(r"\d", clause) and dim == "precision":
            hits += 1
        score += hits * weights.get(dim, 0.5)
    if concrete_first and _CONCRETE.search(clause):
        # Se-dominant / low-openness listeners anchor on the concrete instance
        # before they will process the abstraction (Paivio 1971, dual coding).
        score += 2.0
    return score


def order_supports(
    clauses: list[str],
    weights: dict[str, float],
    notes: list[str],
    *,
    concrete_first: bool = False,
) -> list[str]:
    """A8 — among *supporting* clauses only, lead with what this listener weighs.

    The claim, contrasts and consequences keep their slots, so the argument
    skeleton is untouched; only interchangeable reasons/additions are resorted.
    """
    out = list(clauses)
    changed = False
    # Only swap clauses of the *same* discourse role, so 因为/而且 never trade places
    for role in ("reason", "addition"):
        slots = [i for i, c in enumerate(clauses) if _clause_role(c) == role]
        if len(slots) < 2:
            continue
        ranked = sorted(
            slots, key=lambda i: -_affinity(clauses[i], weights, concrete_first=concrete_first)
        )
        if ranked == slots:
            continue
        for slot, src in zip(slots, ranked):
            out[slot] = clauses[src]
        changed = True
    if not changed:
        return clauses
    notes.append("A8:concrete_first" if concrete_first else "A8:value_order")
    return out


def signal_sequence(lines: list[list[str]], notes: list[str]) -> list[list[str]]:
    """A9 — one step per line for listeners who read procedurally (Si, 尽责性高).

    Layout only: 先/然后/最后 already exist in the text, we just stop hiding the
    step boundary inside a run-on line (Lorch 1989, signalling in text).
    """
    out: list[list[str]] = []
    changed = False
    for group in lines:
        current: list[str] = []
        for clause in group:
            if current and clause.startswith(SEQUENCE_PREFIXES):
                out.append(current)
                current = [clause]
                changed = True
            else:
                current.append(clause)
        if current:
            out.append(current)
    if changed:
        notes.append("A9:sequence")
    return out


def dedupe_repeats(clauses: list[str], notes: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for c in clauses:
        if c in seen:
            notes.append("A6:dedupe")
            continue
        seen.add(c)
        out.append(c)
    return out


# --------------------------------------------------------------------------- #
# A4 / A5 / A7 — layout
# --------------------------------------------------------------------------- #


def chunk_units(clauses: list[str], max_chars: int, notes: list[str]) -> list[list[str]]:
    """Group clauses into lines within working-memory capacity."""
    lines: list[list[str]] = []
    buf: list[str] = []
    size = 0
    for c in clauses:
        # +1 for the separator/terminal punctuation the renderer will add
        cost = len(c) + 1
        if buf and size + cost > max_chars:
            lines.append(buf)
            buf, size = [], 0
        buf.append(c)
        size += cost
    if buf:
        lines.append(buf)
    if len(lines) > 1:
        notes.append(f"A4:chunk≤{max_chars}")
    return lines


def signal_relations(lines: list[list[str]], notes: list[str]) -> list[list[str]]:
    """Give causal / contrast clauses their own line (layout signal only)."""
    out: list[list[str]] = []
    changed = False
    for group in lines:
        current: list[str] = []
        for clause in group:
            role = _clause_role(clause)
            if role in ("reason", "contrast", "consequence") and current:
                out.append(current)
                out.append([clause])
                current = []
                changed = True
            else:
                current.append(clause)
        if current:
            out.append(current)
    if changed:
        notes.append("A5:signal_relation")
    return out


def flow_join(clauses: list[str], notes: list[str]) -> list[list[str]]:
    """Single continuous block — keep the speaker's emotional rhythm intact."""
    notes.append("A7:flow")
    return [list(clauses)]


# --------------------------------------------------------------------------- #
# Invariants
# --------------------------------------------------------------------------- #


@dataclass
class InvariantReport:
    ok: bool
    new_content: list[str] = field(default_factory=list)
    lost_content: list[str] = field(default_factory=list)
    lost_hedges: list[str] = field(default_factory=list)
    polarity_delta: int = 0
    force_kept: bool = True

    def as_notes(self) -> list[str]:
        if self.ok:
            return ["invariants:ok"]
        problems = []
        if self.new_content:
            problems.append("new_content")
        if self.lost_content:
            problems.append("lost_content")
        if self.lost_hedges:
            problems.append("lost_hedges")
        if self.polarity_delta:
            problems.append("polarity")
        if not self.force_kept:
            problems.append("speech_act")
        return [f"invariants:violated({','.join(problems)})"]


def check_invariants(original: str, adapted: str) -> InvariantReport:
    src = Counter(content_tokens(original))
    dst = Counter(content_tokens(adapted))

    new_content = sorted(set(dst) - set(src))
    lost = sorted((set(src) - set(dst)) - DROPPABLE)
    lost_hedges = [h for h in HEDGES if h in original and h not in adapted]
    pol_src = sum(src[n] for n in NEGATIONS)
    pol_dst = sum(dst[n] for n in NEGATIONS)

    # Speech act must survive: a question may not come back as a statement.
    force_kept = not (_is_question(original) and "？" not in adapted)

    ok = (
        not new_content
        and not lost
        and not lost_hedges
        and pol_dst >= pol_src
        and force_kept
    )
    return InvariantReport(
        ok=ok,
        new_content=new_content,
        lost_content=lost,
        lost_hedges=lost_hedges,
        polarity_delta=pol_dst - pol_src,
        force_kept=force_kept,
    )


def content_preserved(original: str, adapted: str) -> bool:
    return check_invariants(original, adapted).ok


# --------------------------------------------------------------------------- #
# Comprehension cost
# --------------------------------------------------------------------------- #


@dataclass
class ComprehensionCost:
    bridging: int
    foundation_delay: int
    max_unit: int
    overload_units: int
    unsignaled_causal: int

    @property
    def total(self) -> float:
        return round(
            2.0 * self.bridging
            + 1.5 * self.overload_units
            + 1.0 * self.unsignaled_causal
            + self.foundation_delay / 20.0,
            2,
        )

    def to_dict(self) -> dict[str, float]:
        return {
            "bridging": self.bridging,
            "foundation_delay": self.foundation_delay,
            "max_unit": self.max_unit,
            "overload_units": self.overload_units,
            "unsignaled_causal": self.unsignaled_causal,
            "total": self.total,
        }


def comprehension_cost(text: str, capacity: int = 26) -> ComprehensionCost:
    """Estimate listener processing cost (lower is easier to understand)."""
    lines = [ln for ln in text.split("\n") if ln.strip()]
    clauses = split_clauses(text)

    bridging = 0
    current_subject: str | None = None
    for clause in clauses:
        if re.match(r"^它们?(?![\u4e00-\u9fff])", clause):
            bridging += 1
        subj = _leading_subject(clause)
        if subj:
            current_subject = subj
            continue
        prefix = next((p for p in RELATION_PREFIXES if clause.startswith(p)), None)
        if prefix and current_subject and not _has_subject_after_connective(clause[len(prefix) :]):
            bridging += 1

    foundation_delay = 0
    for clause in clauses:
        if _clause_role(clause) == "claim":
            break
        foundation_delay += len(clause)

    unit_lengths = [len(re.sub(r"[\s]", "", ln)) for ln in lines] or [0]
    max_unit = max(unit_lengths)
    overload_units = sum(1 for n in unit_lengths if n > capacity)

    unsignaled = 0
    for ln in lines:
        parts = split_clauses(ln)
        for idx, clause in enumerate(parts):
            if idx > 0 and _clause_role(clause) in ("reason", "contrast", "consequence"):
                unsignaled += 1

    return ComprehensionCost(
        bridging=bridging,
        foundation_delay=foundation_delay,
        max_unit=max_unit,
        overload_units=overload_units,
        unsignaled_causal=unsignaled,
    )
