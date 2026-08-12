"""Authenticated encryption for ClarityIME sensitive fields (CIM1 HMAC + stream)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from typing import Any

from clarityime.keychain import get_master_key

MAGIC = b"CIM1"
HMAC_LEN = 32
NONCE_LEN = 16
PREFIX = "cim1:"


def _stream_crypt(key: bytes, nonce: bytes, data: bytes) -> bytes:
    out = bytearray(len(data))
    counter = 0
    pos = 0
    while pos < len(data):
        block = hashlib.sha256(key + nonce + counter.to_bytes(4, "big")).digest()
        take = min(len(block), len(data) - pos)
        for i in range(take):
            out[pos + i] = data[pos + i] ^ block[i]
        pos += take
        counter += 1
    return bytes(out)


def seal_bytes(plain: bytes) -> bytes:
    key = get_master_key()
    nonce = secrets.token_bytes(NONCE_LEN)
    enc = _stream_crypt(key, nonce, plain)
    body = nonce + enc
    tag = hmac.new(key, body, hashlib.sha256).digest()
    return MAGIC + body + tag


def open_bytes(blob: bytes) -> bytes:
    if not blob.startswith(MAGIC):
        raise ValueError("not CIM1")
    if len(blob) < len(MAGIC) + NONCE_LEN + HMAC_LEN + 1:
        raise ValueError("truncated blob")
    body = blob[len(MAGIC) : -HMAC_LEN]
    tag = blob[-HMAC_LEN:]
    key = get_master_key()
    expected = hmac.new(key, body, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected):
        raise ValueError("integrity check failed")
    nonce, enc = body[:NONCE_LEN], body[NONCE_LEN:]
    return _stream_crypt(key, nonce, enc)


def seal_text(text: str) -> str:
    if not text:
        return ""
    return PREFIX + base64.urlsafe_b64encode(seal_bytes(text.encode("utf-8"))).decode("ascii")


def open_text(token: str) -> str:
    if not token:
        return ""
    if not token.startswith(PREFIX):
        return token
    raw = base64.urlsafe_b64decode(token[len(PREFIX) :].encode("ascii"))
    return open_bytes(raw).decode("utf-8")


def is_sealed(token: str) -> bool:
    return bool(token) and token.startswith(PREFIX)


def seal_json(data: Any) -> str:
    if data in (None, {}, []):
        return ""
    return seal_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))


def open_json(token: str, default: Any = None) -> Any:
    if not token:
        return default if default is not None else {}
    plain = open_text(token)
    if not plain:
        return default if default is not None else {}
    return json.loads(plain)
