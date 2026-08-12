"""Local API token + audit log (single-user loopback hardening)."""

from __future__ import annotations

import json
import secrets
import threading
from datetime import datetime, timezone

from clarityime import paths
from clarityime.secure_store import is_sealed, open_text, seal_text

_TOKEN_FILE = paths.app_data_dir() / "local_api.token"
_AUDIT_FILE = paths.app_data_dir() / "security_audit.log"
_LOCK = threading.Lock()
_TOKEN_CACHE: str | None = None

MUTATING_PREFIXES = (
    "/v1/contacts",
    "/v1/feedback",
    "/v1/consent",
    "/v1/settings",
    "/v1/bundles",
)


def ensure_local_api_token() -> str:
    global _TOKEN_CACHE
    created = False
    with _LOCK:
        if _TOKEN_CACHE:
            return _TOKEN_CACHE
        data_dir = paths.app_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        token_file = data_dir / "local_api.token"
        plain_path = data_dir / ".local_api_token"
        if token_file.is_file():
            raw = token_file.read_text(encoding="utf-8").strip()
            _TOKEN_CACHE = open_text(raw) if is_sealed(raw) else raw
            return _TOKEN_CACHE
        if plain_path.is_file():
            _TOKEN_CACHE = plain_path.read_text(encoding="utf-8").strip()
            return _TOKEN_CACHE
        token = secrets.token_urlsafe(32)
        token_file.write_text(seal_text(token) + "\n", encoding="utf-8")
        plain_path.write_text(token + "\n", encoding="utf-8")
        try:
            token_file.chmod(0o600)
            plain_path.chmod(0o600)
        except OSError:
            pass
        _TOKEN_CACHE = token
        created = True
    if created:
        audit("api_token_created", {"path": str(paths.app_data_dir() / "local_api.token")})
    return _TOKEN_CACHE


def read_local_api_token() -> str | None:
    try:
        return ensure_local_api_token()
    except OSError:
        return None


def validate_request_token(header_value: str | None) -> bool:
    expected = read_local_api_token()
    if not expected:
        return True
    if not header_value:
        return False
    return secrets.compare_digest(header_value.strip(), expected)


def requires_auth(path: str, method: str) -> bool:
    if method not in ("POST", "DELETE", "PUT", "PATCH"):
        return False
    if path in ("/v1/clarify", "/v1/candidates"):
        return False
    return any(path == p or path.startswith(p + "/") for p in MUTATING_PREFIXES)


def audit(event: str, detail: dict | None = None) -> None:
    line = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "detail": detail or {},
    }
    try:
        data_dir = paths.app_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        audit_file = data_dir / "security_audit.log"
        with _LOCK:
            with audit_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(line, ensure_ascii=False) + "\n")
    except OSError:
        pass
