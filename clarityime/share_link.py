""""Always show the original" — one link that works on every platform.

Why a link, and why *this kind* of link
----------------------------------------
We only ever control the plain text we send. WeChat / QQ / Discord /
Instagram / iMessage / WhatsApp do not let a third-party app draw custom UI
inside the recipient's chat bubble, and none of them expose a public
"register a translation/adaptation provider" hook the way, say, a browser
extension API does — their built-in "Translate" buttons are closed,
single-purpose (language↔language), and not something we can plug a
per-listener comprehension adaptation into.

What *does* work everywhere, because it's just text: a URL. Every one of
those apps auto-links `https://...` in plain messages. So "cross-platform
support" here means one thing — ship a link the recipient can tap that shows
original + adapted side by side in their normal browser, no app required.

Why the payload lives in the URL FRAGMENT, not on a server
------------------------------------------------------------
``https://clarityime.app/c#<payload>`` — everything after ``#`` is a
"fragment": browsers never send it in the HTTP request, so a static,
stateless page can decode and render it client-side and our server (if any)
never sees, stores, or can leak the message. This keeps the same
loopback/local-first guarantee the rest of ClarityIME has
(``GET /v1/security/status`` → ``loopback_only``): the *sharing* mechanism
does not require us to run a message-storing cloud service.

Contrast with the existing ``clarityime/storage/utterance_bundle.py``:
that one builds ``http://127.0.0.1:17800/...`` links — perfect for the
sender reviewing bundles on their OWN machine, useless as a link mailed to
someone else's phone. This module is for the *recipient-facing* link.

Deployment note (not done in this environment): ``clarityime.app`` needs a
tiny static HTML+JS page that reads ``location.hash``, base64url-decodes it,
and renders original/adapted. ``SHARE_VIEWER_BASE`` below is a placeholder
until that page exists; the encode/decode logic in this module is already
real and round-trips.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass

__all__ = [
    "SHARE_VIEWER_BASE",
    "SharePayload",
    "encode_share_payload",
    "decode_share_payload",
    "build_share_link",
    "append_share_link",
]

#: Replace with the real deployed viewer once it exists. Everything else in
#: this module works regardless of what this string is.
SHARE_VIEWER_BASE = "https://clarityime.app/c"

#: Payload schema version — bump if the JSON shape changes, so an old link
#: opened after an update still fails safely instead of mis-rendering.
_SCHEMA = 1


@dataclass(frozen=True)
class SharePayload:
    original: str
    for_listener: str
    listener_tags: tuple[str, ...] = ()


def encode_share_payload(payload: SharePayload) -> str:
    """Deterministic — same payload always encodes to the same string."""
    raw = json.dumps(
        {
            "v": _SCHEMA,
            "original": payload.original,
            "for_listener": payload.for_listener,
            "listener_tags": list(payload.listener_tags),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_share_payload(fragment: str) -> SharePayload:
    """Inverse of :func:`encode_share_payload`. Raises ``ValueError`` on a
    corrupt or unsupported-version fragment — callers must not guess."""
    padded = fragment + "=" * (-len(fragment) % 4)
    try:
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - re-raise as one clear error type
        raise ValueError(f"corrupt share link: {exc}") from exc
    if data.get("v") != _SCHEMA:
        raise ValueError(f"unsupported share link version: {data.get('v')!r}")
    return SharePayload(
        original=data.get("original", ""),
        for_listener=data.get("for_listener", ""),
        listener_tags=tuple(data.get("listener_tags", [])),
    )


def build_share_link(
    original: str,
    for_listener: str,
    *,
    listener_tags: tuple[str, ...] = (),
    base: str = SHARE_VIEWER_BASE,
) -> str:
    payload = SharePayload(original=original, for_listener=for_listener, listener_tags=listener_tags)
    return f"{base}#{encode_share_payload(payload)}"


def append_share_link(
    for_listener: str,
    original: str,
    *,
    listener_tags: tuple[str, ...] = (),
    enabled: bool = True,
    lang: str = "zh",
) -> str:
    """Attach a "see original" link to the outgoing message.

    ``enabled`` is the settings toggle (``attach_original_link``, default
    True). When the two texts are identical there is nothing extra to show,
    so no link is added even if enabled — a link to "the same sentence
    twice" is noise, not friendliness.
    """
    if not enabled or for_listener.strip() == original.strip():
        return for_listener
    link = build_share_link(original, for_listener, listener_tags=listener_tags)
    tail = f"\n（原句：{link}）" if lang.startswith("zh") else f"\n(original: {link})"
    return for_listener + tail
