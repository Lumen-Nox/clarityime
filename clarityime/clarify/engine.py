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

PolishRequest = ClarifyRequest
PolishResult = ClarifyResult


def clarify(request: ClarifyRequest, *, listener_preset: str | None = None) -> ClarifyResult:
    candidates = request.asr.top_n(3)
    primary = request.asr.primary
    original, notes_o = preserve_original(primary, candidates)
    for_listener = original
    notes: list[str] = list(notes_o)

    if request.mode == AudienceMode.CONTACT:
        if not request.contact:
            raise ValueError("CONTACT mode requires a contact profile")
        cerome = cerome_from_contact(request.contact)
        original, for_listener, notes = clarify_dual_for_listener(
            primary,
            cerome,
            candidates,
            lexicon=request.contact.preferred_words,
        )
    elif request.mode == AudienceMode.STRUCTURED:
        for_listener, notes_s = clarify_for_structured(primary, candidates)
        notes = notes_s
    elif listener_preset:
        preset = get_listener_preset(listener_preset)
        if preset:
            from clarityime.clarify.listener_adapt import adapt_for_listener

            for_listener, notes_l = adapt_for_listener(original, preset)
            notes = notes_o + notes_l

    clarified = for_listener
    return ClarifyResult(
        raw_primary=primary,
        original=original,
        for_listener=for_listener,
        clarified=clarified,
        mode=request.mode,
        used_network=False,
        notes=notes,
        all_candidates_considered=candidates,
    )


def polish(request: ClarifyRequest, **kwargs) -> ClarifyResult:
    return clarify(request, **kwargs)
