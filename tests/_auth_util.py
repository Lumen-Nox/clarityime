"""Shared auth setup for HTTP integration tests."""

from __future__ import annotations

from pathlib import Path

import clarityime.api_auth as api_auth
import clarityime.paths as paths_mod


def bind_test_data_dir(data_dir: Path) -> str:
    data_dir.mkdir(parents=True, exist_ok=True)
    paths_mod.app_data_dir = lambda: data_dir  # type: ignore[method-assign]
    api_auth._TOKEN_CACHE = None
    api_auth._TOKEN_FILE = data_dir / "local_api.token"
    api_auth._AUDIT_FILE = data_dir / "security_audit.log"
    return api_auth.ensure_local_api_token()


def auth_headers(token: str) -> dict[str, str]:
    return {"X-ClarityIME-Token": token}
