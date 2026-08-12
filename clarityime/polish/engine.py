"""Backward-compatible re-exports — prefer clarityime.clarify."""

from clarityime.clarify.engine import clarify, polish
from clarityime.clarify.local_rules import (
    clarify_default,
    clarify_for_ai,
    clarify_for_contact,
    polish_default,
    polish_for_ai,
    polish_for_contact,
)

# Aliases
polish_default = clarify_default
polish_for_ai = clarify_for_ai
polish_for_contact = clarify_for_contact
