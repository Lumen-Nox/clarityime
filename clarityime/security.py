"""Local API security — loopback bind and token auth."""

from __future__ import annotations

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})


def assert_loopback_host(host: str) -> None:
    """Refuse binding the core API to non-loopback interfaces."""
    if host not in LOOPBACK_HOSTS:
        raise SystemExit(
            f"ClarityIME core may bind only to loopback (127.0.0.1), not {host!r}.\n"
            "Binding to all interfaces would expose contacts and speaker data to your LAN."
        )


def normalize_loopback_host(host: str | None) -> str:
    """Return a safe bind host (default 127.0.0.1)."""
    resolved = (host or "127.0.0.1").strip().lower()
    assert_loopback_host(resolved)
    return "127.0.0.1" if resolved == "localhost" else resolved
