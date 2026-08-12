"""Listener adaptation — make the SAME propositions cheaper to understand.

This module never rewrites the speaker's stance, tone, or register.
It applies the evidence-backed comprehension operations in
``clarityime.clarify.comprehension`` (see ``docs/COMPREHENSION_MODEL.md``),
selected by the listener's Cerome numbers.

Persuasion here is *not* tone-matching. It is Petty & Cacioppo's (1986) central
route: lowering processing cost so the speaker's existing argument is actually
evaluated, plus the fluency→credibility effect (Reber & Schwarz, 1999).
"""

from __future__ import annotations

from dataclasses import dataclass

from clarityime.cerome.human import CeromeHumanProfile
from clarityime.clarify.comprehension import (
    ComprehensionCost,
    check_invariants,
    chunk_units,
    claim_first,
    comprehension_cost,
    content_preserved,
    dedupe_repeats,
    flow_join,
    render_lines,
    resolve_referents,
    restore_subjects,
    signal_relations,
    split_clauses,
)

__all__ = [
    "ListenerPlan",
    "plan_from_cerome",
    "adapt_for_listener",
    "adapt_with_report",
    "content_preserved",
]


@dataclass
class ListenerPlan:
    """Which comprehension ops this listener needs, derived from Cerome."""

    resolve_referents: bool = True
    restore_subjects: bool = True
    claim_first: bool = False
    signal_relations: bool = False
    flow: bool = False
    capacity: int = 26

    def tags(self) -> list[str]:
        out = [f"capacity:{self.capacity}"]
        if self.resolve_referents:
            out.append("A1")
        if self.restore_subjects:
            out.append("A2")
        if self.claim_first:
            out.append("A3")
        out.append("A4")
        if self.signal_relations:
            out.append("A5")
        if self.flow:
            out.append("A7")
        return out


def plan_from_cerome(cerome: CeromeHumanProfile) -> ListenerPlan:
    """Cerome numbers → op set. MBTI presets only set the numbers."""
    l1, l2, l3 = cerome.l1, cerome.l2, cerome.l3

    # Working-memory budget per line (Cowan 2001; Sweller 1988)
    capacity = int(round(34 - 16 * l1.load_sensitivity))
    capacity = max(16, min(36, capacity))

    flow = l2.warmth >= 0.75 or l1.empathy_need >= 0.75
    has_gaps = bool(l3.comprehension_gaps.strip())

    return ListenerPlan(
        resolve_referents=True,
        restore_subjects=True,
        # Gernsbacher first-mention advantage matters most for fast/efficient listeners
        claim_first=(l2.efficiency >= 0.7 or l1.pace >= 0.65) and not flow,
        # Causal signaling pays off for precision-seeking or gap-prone listeners
        signal_relations=(l2.precision >= 0.7 or l2.clarity >= 0.75 or has_gaps) and not flow,
        flow=flow,
        capacity=capacity,
    )


def _apply_lexicon(text: str, words: str, notes: list[str]) -> str:
    """User-configured term swaps (explicitly approved, applied before ops)."""
    if not words:
        return text
    out = text
    for pair in words.split(","):
        if "->" not in pair:
            continue
        a, b = (part.strip() for part in pair.split("->", 1))
        if a and a in out:
            out = out.replace(a, b)
            notes.append(f"lexicon:{a}→{b}")
    return out


def adapt_with_report(
    original: str,
    cerome: CeromeHumanProfile,
    *,
    lexicon: str = "",
) -> tuple[str, list[str], ComprehensionCost, ComprehensionCost]:
    """Return (adapted, notes, cost_before, cost_after)."""
    notes: list[str] = ["listener_adapt"]
    plan = plan_from_cerome(cerome)
    notes.append("ops:" + "+".join(plan.tags()))

    reference = _apply_lexicon(original, lexicon or cerome.l3.preferred_words, notes)
    cost_before = comprehension_cost(reference, plan.capacity)

    clauses = split_clauses(reference)
    if not clauses:
        return original, notes + ["empty"], cost_before, cost_before

    clauses = dedupe_repeats(clauses, notes)
    if plan.resolve_referents:
        clauses = resolve_referents(clauses, notes)
    if plan.restore_subjects:
        clauses = restore_subjects(clauses, notes)
    if plan.claim_first:
        clauses = claim_first(clauses, notes)

    if plan.flow:
        lines = flow_join(clauses, notes)
    else:
        lines = chunk_units(clauses, plan.capacity, notes)
        if plan.signal_relations:
            lines = signal_relations(lines, notes)

    adapted = render_lines(lines)

    report = check_invariants(reference, adapted)
    notes.extend(report.as_notes())
    if not report.ok:
        return reference, notes + ["fallback:original"], cost_before, cost_before

    cost_after = comprehension_cost(adapted, plan.capacity)
    notes.append(f"cost:{cost_before.total}→{cost_after.total}")
    return adapted, notes, cost_before, cost_after


def adapt_for_listener(
    original: str,
    cerome: CeromeHumanProfile,
    *,
    lexicon: str = "",
) -> tuple[str, list[str]]:
    """Same propositions, lower processing cost for this listener."""
    adapted, notes, _before, _after = adapt_with_report(
        original, cerome, lexicon=lexicon
    )
    return adapted, notes


# Legacy alias used by older tests
_words_preserved = content_preserved
