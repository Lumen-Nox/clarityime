"""Generate clarification candidates — dual output: original + for_listener."""

from __future__ import annotations

from clarityime.cerome.human import cerome_from_contact
from clarityime.cerome.listener_presets import get_listener_preset
from clarityime.clarify.local_rules import (
    clarify_dual_for_listener,
    clarify_for_structured,
    preserve_original,
)
from clarityime.models import AudienceMode, ContactProfile, SpeakerProfile


def clarify_candidates(
    text: str,
    *,
    mode: AudienceMode,
    nbest: list[str] | None = None,
    contact: ContactProfile | None = None,
    speaker: SpeakerProfile | None = None,
    listener_preset: str | None = None,
    max_options: int = 4,
) -> list[dict]:
    """Return ``original`` + ``for_listener`` variants (speaker words preserved)."""
    base_nbest = nbest or [text]
    original, notes_o = preserve_original(text, base_nbest)
    options: list[dict] = [
        {"text": original, "label": "original", "notes": list(notes_o)},
    ]

    if mode == AudienceMode.CONTACT and contact:
        cerome = cerome_from_contact(contact)
        _orig, for_listener, notes = clarify_dual_for_listener(
            text,
            cerome,
            base_nbest,
            lexicon=contact.preferred_words,
        )
        options.append(
            {
                "text": for_listener,
                "label": "for_listener",
                "notes": notes,
            }
        )
    elif mode == AudienceMode.STRUCTURED:
        for_listener, notes_s = clarify_for_structured(text, base_nbest)
        options.append(
            {
                "text": for_listener,
                "label": "for_listener",
                "notes": notes_s,
            }
        )
    elif listener_preset:
        preset = get_listener_preset(listener_preset)
        if preset:
            from clarityime.clarify.listener_adapt import adapt_for_listener

            for_listener, notes_l = adapt_for_listener(original, preset)
            options.append(
                {
                    "text": for_listener,
                    "label": "for_listener",
                    "notes": notes_l,
                }
            )
    else:
        options[0]["label"] = "standard"

    seen: set[str] = set()
    out: list[dict] = []
    for opt in options:
        t = opt["text"].strip()
        if not t:
            continue
        dedupe_key = (
            f"{opt['label']}:{t}"
            if opt["label"] in ("original", "for_listener", "standard")
            else t
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        out.append(opt)
    return out[:max_options]
