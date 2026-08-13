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

from dataclasses import dataclass, field

from clarityime.cerome.human import CeromeHumanProfile
from clarityime.cerome.tags import ListenerTags, listener_tags
from clarityime.clarify.comprehension import (
    ComprehensionCost,
    check_invariants,
    chunk_units,
    claim_first,
    comprehension_cost,
    content_preserved,
    dedupe_repeats,
    order_supports,
    render_lines,
    resolve_referents,
    restore_subjects,
    signal_relations,
    signal_sequence,
    split_clauses,
)
from clarityime.clarify.details import detail_diff
from clarityime.clarify.oral import strip_oral
from clarityime.clarify.paraphrase import (
    Substitution,
    denominalize,
    jargon_domains,
    simplify_jargon,
    tighten_redundancy,
)

__all__ = [
    "AdaptResult",
    "ListenerPlan",
    "plan_from_tags",
    "plan_from_cerome",
    "adapt_for_listener",
    "adapt_with_report",
    "content_preserved",
]


@dataclass
class ListenerPlan:
    """Which comprehension ops this listener needs. Keyed on tags only."""

    resolve_referents: bool = True
    restore_subjects: bool = True
    claim_first: bool = False
    signal_relations: bool = False
    flow: bool = False
    value_order: bool = False
    simplify_jargon: bool = True
    keep_tone: bool = True
    sequence_explicit: bool = False
    concrete_first: bool = False
    capacity: int = 26
    known_domains: frozenset[str] = frozenset()
    #: Which curated jargon table to scan — the listener's declared reading
    #: language (``reads_<lang>``). Never auto-translated between languages.
    reading_lang: str = "zh"
    listener_tags: tuple[str, ...] = ()
    weights: dict[str, float] = field(default_factory=dict)

    def tags(self) -> list[str]:
        out = [f"capacity:{self.capacity}"]
        if self.simplify_jargon:
            out.append("T1")
        out.append("T2")
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
        if self.value_order:
            out.append("A8")
        if self.sequence_explicit:
            out.append("A9")
        return out


def plan_from_tags(
    tags: ListenerTags, l2, *, auto_domains: frozenset[str] = frozenset()
) -> ListenerPlan:
    """Tags → op set. **This is the only place op selection happens.**

    Nothing in here reads a name, a personality label, or free-text notes. If a
    behaviour is not expressible as a tag, it does not exist.

    ``auto_domains`` is the one addition that is not a declared tag: domains
    learned from repeated feedback evidence (see
    ``clarityime.cerome.contact_learning``). ``define_terms`` is an explicit
    user override and still wins over it — a person can always say "translate
    everything for me" regardless of what past messages suggest.
    """
    # Tags can disagree — INFP is Fi (flowing) but Ne (scanning), and a declared
    # load_sensitivity may point the other way. Contradiction resolves to the
    # default rather than letting whichever branch is written first win.
    short, long = tags.has("short_chunks"), tags.has("long_chunks")
    capacity = 26 if short == long else (18 if short else 32)

    flow = tags.has("tone_visible")
    # define_terms overrides ownership: translate everything, no matter what
    # domains they own (for 不熟的人 / 没接触过 / 朋友说的 sources).
    domains = frozenset() if tags.has("define_terms") else (tags.domains() | auto_domains)

    # reads_<lang> picks which curated table to scan. Multiple declared →
    # take the lowest id alphabetically so the choice is deterministic and
    # not "whichever was inserted last".
    lang_tags = sorted(t for t in tags.family("lang") if t.startswith("reads_"))
    reading_lang = lang_tags[0][len("reads_"):] if lang_tags else "zh"

    return ListenerPlan(
        resolve_referents=True,
        restore_subjects=True,
        # Gernsbacher first-mention advantage: only for listeners tagged for it
        claim_first=tags.has("conclusion_first") and not flow,
        signal_relations=tags.has("cause_explicit") and not flow,
        flow=flow,
        value_order=tags.has("value_order"),
        sequence_explicit=tags.has("sequence_explicit"),
        concrete_first=tags.has("concrete_first"),
        # T1 fires per-domain: a term is translated only if its domain is unowned
        simplify_jargon=bool(set(jargon_domains(reading_lang)) - set(domains)),
        keep_tone=not tags.has("no_padding"),
        capacity=capacity,
        known_domains=domains,
        reading_lang=reading_lang,
        listener_tags=tuple(tags.sorted()),
        weights={
            "precision": l2.precision,
            "warmth": l2.warmth,
            "efficiency": l2.efficiency,
        },
    )


def plan_from_cerome(cerome: CeromeHumanProfile) -> ListenerPlan:
    """Cerome → tags → plan. Kept as the public entry point."""
    return plan_from_tags(
        listener_tags(cerome),
        cerome.l2,
        auto_domains=frozenset(getattr(cerome, "auto_domains", None) or ()),
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


@dataclass
class AdaptResult:
    """Everything needed to audit one adaptation."""

    text: str
    notes: list[str]
    cost_before: ComprehensionCost
    cost_after: ComprehensionCost
    baseline: str  # original after audited substitutions, before any re-layout
    substitutions: list[Substitution]
    plan: ListenerPlan

    def __iter__(self):  # legacy 4-tuple unpacking
        return iter((self.text, self.notes, self.cost_before, self.cost_after))

    @property
    def reduction_pct(self) -> float:
        if not self.cost_before.total:
            return 0.0
        drop = self.cost_before.total - self.cost_after.total
        return round(100 * drop / self.cost_before.total, 1)


def adapt_with_report(
    original: str,
    cerome: CeromeHumanProfile,
    *,
    lexicon: str = "",
) -> AdaptResult:
    """Adapt for this listener and report cost, plan, and every substitution."""
    notes: list[str] = ["listener_adapt"]
    plan = plan_from_cerome(cerome)
    notes.append("ops:" + "+".join(plan.tags()))

    reference = _apply_lexicon(original, lexicon or cerome.l3.preferred_words, notes)
    cost_before = comprehension_cost(reference, plan.capacity)

    # --- Stage 0: oral markers, judged one occurrence at a time -------------
    # 「就是」at the front is hesitation; 「，就是风险有点多」is 只不过. Tone particles
    # survive unless this listener is tagged no_padding.
    reworded, dropped = strip_oral(reference, drop_tone=not plan.keep_tone)
    notes.extend(mk.note() for mk in dropped)

    # --- Stage 1: meaning-preserving rewrites (audited table, no generation) ---
    subs: list[Substitution] = []
    if plan.simplify_jargon:
        reworded, jargon_subs = simplify_jargon(
            reworded, known_domains=plan.known_domains, lang=plan.reading_lang
        )
        subs.extend(jargon_subs)
    reworded, nominal_subs = denominalize(reworded)
    subs.extend(nominal_subs)
    reworded, tidy_subs = tighten_redundancy(reworded)
    subs.extend(tidy_subs)
    notes.extend(s.note() for s in subs)

    # --- Stage 2: structural comprehension ops ---
    clauses = split_clauses(reworded)
    if not clauses:
        return AdaptResult(
            original, notes + ["empty"], cost_before, cost_before, reference, subs, plan
        )

    clauses = dedupe_repeats(clauses, notes)
    if plan.resolve_referents:
        clauses = resolve_referents(clauses, notes)
    if plan.restore_subjects:
        clauses = restore_subjects(clauses, notes)
    if plan.claim_first:
        clauses = claim_first(clauses, notes)
    if plan.value_order:
        clauses = order_supports(
            clauses, plan.weights, notes, concrete_first=plan.concrete_first
        )

    if plan.flow:
        # Warmth changes *where* we break, not whether working memory applies.
        # Same capacity as anyone else (Cowan 2001); we just skip the analytic
        # splits (A3 reorder / A5 one-relation-per-line) that fragment the voice.
        lines = chunk_units(clauses, plan.capacity, notes)
        notes.append("A7:flow")
    else:
        lines = chunk_units(clauses, plan.capacity, notes)
        if plan.signal_relations:
            lines = signal_relations(lines, notes)

    if plan.sequence_explicit:
        lines = signal_sequence(lines, notes)

    adapted = render_lines(lines)

    # Invariants are checked against the *post-substitution* baseline: every swap
    # came from the audited table, everything after must be reorder / re-layout.
    report = check_invariants(reworded, adapted)
    notes.extend(report.as_notes())

    # Detail-level check against the *pre-everything* reference: no 有点/可能/
    # 不过 may vanish between what the speaker said and what the listener reads.
    lost = detail_diff(reference, adapted).get("lost", [])
    if lost:
        notes.append("DETAIL_LOST:" + ",".join(lost))
        return AdaptResult(
            reference,
            notes + ["fallback:original"],
            cost_before,
            cost_before,
            reference,
            [],
            plan,
        )
    notes.append("DETAILS_PRESERVED")

    if not report.ok:
        return AdaptResult(
            reference,
            notes + ["fallback:original"],
            cost_before,
            cost_before,
            reference,
            [],
            plan,
        )

    cost_after = comprehension_cost(adapted, plan.capacity)
    notes.append(f"cost:{cost_before.total}→{cost_after.total}")
    return AdaptResult(adapted, notes, cost_before, cost_after, reworded, subs, plan)


def adapt_for_listener(
    original: str,
    cerome: CeromeHumanProfile,
    *,
    lexicon: str = "",
) -> tuple[str, list[str]]:
    """Same propositions, lower processing cost for this listener."""
    result = adapt_with_report(original, cerome, lexicon=lexicon)
    return result.text, result.notes


# Legacy alias used by older tests
_words_preserved = content_preserved
