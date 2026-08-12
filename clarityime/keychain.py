"""OS-backed master key for ClarityIME encrypted blobs (Windows DPAPI first)."""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

from clarityime import paths

_KEY_FILE = paths.app_data_dir() / ".master_key.wrapped"
_PLAIN_KEY_FILE = paths.app_data_dir() / ".master_key.dev"
_KEY_LEN = 32


def _dpapi_available() -> bool:
    return sys.platform == "win32"


def _dpapi_protect(data: bytes) -> bytes:
    import ctypes
    import ctypes.wintypes as wt

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wt.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

    def _blob(raw: bytes) -> DATA_BLOB:
        buf = ctypes.create_string_buffer(raw)
        return DATA_BLOB(len(raw), ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte)))

    in_blob = _blob(data)
    out_blob = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    ):
        raise OSError("CryptProtectData failed")
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)


def _dpapi_unprotect(data: bytes) -> bytes:
    import ctypes
    import ctypes.wintypes as wt

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wt.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

    def _blob(raw: bytes) -> DATA_BLOB:
        buf = ctypes.create_string_buffer(raw)
        return DATA_BLOB(len(raw), ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte)))

    in_blob = _blob(data)
    out_blob = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    ):
        raise OSError("CryptUnprotectData failed")
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)


def _machine_fallback_key() -> bytes:
    seed = f"clarityime-v1:{paths.app_data_dir()}:{os.environ.get('USERNAME', 'user')}"
    return hashlib.sha256(seed.encode()).digest()


def get_master_key() -> bytes:
    data_dir = paths.app_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    key_file = data_dir / ".master_key.wrapped"
    plain_key_file = data_dir / ".master_key.dev"
    if key_file.is_file() and _dpapi_available():
        wrapped = key_file.read_bytes()
        raw = _dpapi_unprotect(wrapped)
        if len(raw) != _KEY_LEN:
            raise ValueError("invalid wrapped master key length")
        return raw

    if plain_key_file.is_file():
        raw = plain_key_file.read_bytes()
        if len(raw) == _KEY_LEN:
            return raw

    raw = os.urandom(_KEY_LEN)
    if _dpapi_available():
        key_file.write_bytes(_dpapi_protect(raw))
    else:
        plain_key_file.write_bytes(raw)
        try:
            plain_key_file.chmod(0o600)
        except OSError:
            pass
    return raw


def key_backend_label() -> str:
    data_dir = paths.app_data_dir()
    if (data_dir / ".master_key.wrapped").is_file() and _dpapi_available():
        return "windows-dpapi"
    if (data_dir / ".master_key.dev").is_file():
        return "file-fallback"
    return "ephemeral"
