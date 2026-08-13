"""Clarification orchestration — local rules only, deterministic, no network."""

from __future__ import annotations

from clarityime.cerome.human import cerome_from_contact
from clarityime.cerome.listener_presets import get_listener_preset
from clarityime.models import AudienceMode, ClarifyRequest, ClarifyResult
from clarityime.clarify.local_rules import (
    clarify_dual_for_listener,
    clarify_for_structured,
    preserve_original,
)
from clarityime.settings import load_settings
from clarityime.share_link import append_share_link

PolishRequest = ClarifyRequest
PolishResult = ClarifyResult


def clarify(
    request: ClarifyRequest,
    *,
    listener_preset: str | None = None,
    attach_link: bool | None = None,
) -> ClarifyResult:
    """Speaker line + listener line, with a full audit of what changed and why."""
    from clarityime.cerome.listener_presets import NEUTRAL
    from clarityime.clarify.listener_adapt import adapt_with_report

    candidates = request.asr.top_n(3)
    primary = request.asr.primary
    original, notes_o = preserve_original(primary, candidates)

    cerome = None
    lexicon = ""
    if request.mode == AudienceMode.CONTACT:
        if not request.contact:
            raise ValueError("CONTACT mode requires a contact profile")
        cerome = cerome_from_contact(request.contact)
        lexicon = request.contact.preferred_words
    elif request.mode == AudienceMode.STRUCTURED:
        cerome = NEUTRAL
    elif listener_preset:
        cerome = get_listener_preset(listener_preset)

    if cerome is None:
        return ClarifyResult(
            raw_primary=primary,
            original=original,
            for_listener=original,
            clarified=original,
            mode=request.mode,
            used_network=False,
            notes=list(notes_o),
            all_candidates_considered=candidates,
        )

    result = adapt_with_report(original, cerome, lexicon=lexicon)
    link_enabled = attach_link
    if link_enabled is None:
        link_enabled = bool(load_settings().get("attach_original_link", True))
    for_listener = append_share_link(
        result.text,
        original,
        listener_tags=tuple(result.plan.listener_tags),
        enabled=link_enabled,
        lang=getattr(result.plan, "reading_lang", "zh"),
    )
    return ClarifyResult(
        raw_primary=primary,
        original=original,
        for_listener=for_listener,
        clarified=for_listener,
        mode=request.mode,
        used_network=False,
        notes=list(notes_o) + result.notes,
        all_candidates_considered=candidates,
        substitutions=[
            {"from": s.src, "to": s.dst, "kind": s.kind} for s in result.substitutions
        ],
        listener_tags=list(result.plan.listener_tags),
        cost={
            "before": result.cost_before.to_dict(),
            "after": result.cost_after.to_dict(),
            "reduction_pct": result.reduction_pct,
        },
    )


def polish(request: ClarifyRequest, **kwargs) -> ClarifyResult:
    return clarify(request, **kwargs)
