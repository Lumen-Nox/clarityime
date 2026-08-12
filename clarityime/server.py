"""Local HTTP API for platform IME shells — stdlib only, 127.0.0.1 only.

Endpoints
---------
GET  /v1/health
GET  /v1/settings · POST /v1/settings
GET  /v1/consent · POST /v1/consent
GET  /v1/contacts · POST /v1/contacts · DELETE /v1/contacts?name=
GET  /v1/speaker
POST /v1/clarify
POST /v1/candidates
POST /v1/feedback
POST /v1/bundles
GET  /v1/bundles/{bundle_id}

Utterance bundles (P2 — N-best shareable link, localhost)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
POST /v1/bundles
    ``{"raw", "nbest", "candidates", "mode", "picked"?}``
    → ``{"bundle_id", "timestamp", "url", ...bundle fields}``

GET /v1/bundles/{bundle_id}
    Full bundle JSON for share/review (audio not stored in v0.3 skeleton).

POST /v1/feedback
    Required: ``raw``, ``preferred``.
    Optional: ``nbest``, ``candidates``, ``mode`` — when ``nbest`` is sent, also saves
    an utterance bundle with ``picked=preferred`` and returns ``bundle_id`` + ``bundle_url``.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from clarityime.clarify.candidates import clarify_candidates
from clarityime.clarify.engine import clarify
from clarityime.consent import load_consent
from clarityime.security import normalize_loopback_host
from clarityime.api_auth import (
    audit,
    ensure_local_api_token,
    requires_auth,
    validate_request_token,
)
from clarityime.keychain import key_backend_label
from clarityime.cerome.human import CeromeHumanProfile, cerome_from_contact, merge_cerome_into_contact
from clarityime.models import AsrCandidate, AsrResult, AudienceMode, ClarifyRequest, ContactProfile, parse_audience_mode
from clarityime.settings import load_settings, save_settings
from clarityime.storage.contacts import ContactStore
from clarityime.storage.pairing import export_contact_bundle_by_name, import_contact_bundle
from clarityime.storage.speaker import SpeakerStore
from clarityime.storage.utterance_bundle import (
    bundle_local_url,
    create_bundle,
    load_bundle,
    save_bundle,
    save_utterance_bundle,
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 17800


def _resolve_contact(ref: str | None) -> ContactProfile | None:
    if not ref:
        return None
    store = ContactStore()
    profile = store.get_by_name(ref)
    if profile:
        return profile
    if ref.isdigit():
        return store.get_by_id(int(ref))
    return None


def _json_response(handler: BaseHTTPRequestHandler, code: int, payload: Any) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _read_json(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", 0))
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8"))


class ClarityHandler(BaseHTTPRequestHandler):
    server_version = "ClarityIME/0.4"

    def log_message(self, fmt: str, *args) -> None:  # noqa: ARG002
        return  # quiet by default

    def _check_auth(self, path: str, method: str) -> bool:
        if not requires_auth(path, method):
            return True
        token = self.headers.get("X-ClarityIME-Token")
        if validate_request_token(token):
            return True
        audit("auth_rejected", {"path": path, "method": method})
        _json_response(self, 401, {"error": "unauthorized", "hint": "X-ClarityIME-Token"})
        return False

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/v1/health":
            _json_response(
                self,
                200,
                {"ok": True, "service": "clarityime", "integrated": "ime-shells", "version": "0.4"},
            )
            return
        if path == "/v1/security/status":
            _json_response(
                self,
                200,
                {
                    "loopback_only": True,
                    "key_backend": key_backend_label(),
                    "local_token_required": True,
                    "encryption": "CIM1",
                    "cerome_tags": True,
                },
            )
            return
        if path == "/v1/settings":
            _json_response(self, 200, load_settings())
            return
        if path == "/v1/consent":
            _json_response(self, 200, load_consent())
            return
        if path == "/v1/contacts/export":
            qs = parse_qs(urlparse(self.path).query)
            name = (qs.get("name") or [None])[0]
            if not name or not str(name).strip():
                _json_response(self, 400, {"error": "name_required"})
                return
            try:
                bundle = export_contact_bundle_by_name(str(name).strip())
            except ValueError as exc:
                _json_response(self, 404, {"error": str(exc)})
                return
            _json_response(self, 200, bundle)
            return
        if path == "/v1/contacts":
            store = ContactStore()
            rows = [
                {
                    "id": c.id,
                    "name": c.name,
                    "relationship": c.relationship,
                    "style_notes": c.style_notes,
                    "comprehension_notes": c.comprehension_notes,
                    "cerome": cerome_from_contact(c).public_export(),
                }
                for c in store.list_contacts()
            ]
            _json_response(self, 200, {"contacts": rows})
            return
        if path == "/v1/speaker":
            p = SpeakerStore().get()
            _json_response(self, 200, p.__dict__)
            return
        if path.startswith("/v1/bundles/"):
            bundle_id = path[len("/v1/bundles/") :].strip("/")
            if not bundle_id or "/" in bundle_id:
                _json_response(self, 400, {"error": "invalid_bundle_id"})
                return
            bundle = load_bundle(bundle_id)
            if bundle is None:
                _json_response(self, 404, {"error": "not_found"})
                return
            _json_response(self, 200, bundle)
            return
        _json_response(self, 404, {"error": "not_found"})

    def do_DELETE(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not self._check_auth(path, "DELETE"):
            return
        qs = parse_qs(urlparse(self.path).query)
        if path == "/v1/contacts":
            name = (qs.get("name") or [None])[0]
            if not name:
                _json_response(self, 400, {"error": "name_required"})
                return
            store = ContactStore()
            profile = store.get_by_name(name)
            if not profile or profile.id is None:
                _json_response(self, 404, {"error": "not_found"})
                return
            store.delete(profile.id)
            _json_response(self, 200, {"ok": True, "deleted": name})
            return
        _json_response(self, 404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not self._check_auth(path, "POST"):
            return
        try:
            body = _read_json(self)
        except json.JSONDecodeError:
            _json_response(self, 400, {"error": "invalid_json"})
            return

        if path == "/v1/clarify":
            self._handle_clarify(body)
            return
        if path == "/v1/candidates":
            self._handle_candidates(body)
            return
        if path == "/v1/feedback":
            self._handle_feedback(body)
            return
        if path == "/v1/bundles":
            self._handle_bundles_post(body)
            return
        if path == "/v1/settings":
            s = load_settings()
            s.update(body)
            save_settings(s)
            _json_response(self, 200, s)
            return
        if path == "/v1/consent":
            from clarityime.consent import save_consent

            c = load_consent()
            if "cloud_sync" in body:
                c["cloud_sync"] = bool(body["cloud_sync"])
            if "aggregate_research" in body:
                c["aggregate_research"] = bool(body["aggregate_research"])
            saved = save_consent(
                cloud_sync=c["cloud_sync"],
                aggregate_research=c["aggregate_research"],
            )
            _json_response(self, 200, saved)
            return
        if path == "/v1/contacts/import":
            try:
                saved = import_contact_bundle(body)
            except ValueError as exc:
                _json_response(self, 400, {"error": str(exc)})
                return
            _json_response(
                self,
                200,
                {
                    "ok": True,
                    "id": saved.id,
                    "name": saved.name,
                    "relationship": saved.relationship,
                    "style": saved.style_notes,
                    "comprehension": saved.comprehension_notes,
                },
            )
            return
        if path == "/v1/contacts":
            name = (body.get("name") or "").strip()
            if not name:
                _json_response(self, 400, {"error": "name_required"})
                return
            store = ContactStore()
            existing = store.get_by_name(name)
            profile = ContactProfile(
                id=existing.id if existing else None,
                name=name,
                style_notes=body.get("style_notes") or body.get("style") or "",
                preferred_words=body.get("preferred_words") or body.get("words") or "",
                relationship=body.get("relationship") or "",
                age_hint=body.get("age_hint") or body.get("age") or "",
                comprehension_notes=body.get("comprehension_notes")
                or body.get("comprehension")
                or "",
                extra=dict(existing.extra if existing else {}),
            )
            if isinstance(body.get("cerome"), dict):
                profile = merge_cerome_into_contact(
                    profile,
                    CeromeHumanProfile.from_dict(body["cerome"]),
                    write_legacy=True,
                )
            saved = store.upsert(profile)
            audit("contact_upsert", {"name": saved.name})
            _json_response(
                self,
                200,
                {
                    "id": saved.id,
                    "name": saved.name,
                    "relationship": saved.relationship,
                    "style_notes": saved.style_notes,
                    "comprehension_notes": saved.comprehension_notes,
                    "cerome": cerome_from_contact(saved).public_export(),
                },
            )
            return
        _json_response(self, 404, {"error": "not_found"})

    def _handle_clarify(self, body: dict) -> None:
        text = (body.get("text") or "").strip()
        if not text:
            _json_response(self, 400, {"error": "text_required"})
            return
        mode = parse_audience_mode(body.get("mode", "default"))
        nbest = body.get("nbest") or [text]
        contact = _resolve_contact(body.get("contact"))
        asr = AsrResult(
            candidates=[AsrCandidate(text=t, confidence=1.0 - i * 0.1) for i, t in enumerate(nbest)],
            backend="ime",
        )
        result = clarify(
            ClarifyRequest(
                asr=asr,
                mode=mode,
                contact=contact,
                speaker=SpeakerStore().get(),
            ),
            listener_preset=body.get("listener_preset"),
        )
        _json_response(
            self,
            200,
            {
                "raw": result.raw_primary,
                "original": result.original,
                "for_listener": result.for_listener,
                "clarified": result.clarified,
                "mode": result.mode.value,
                "used_network": result.used_network,
                "notes": result.notes,
            },
        )

    def _handle_candidates(self, body: dict) -> None:
        text = (body.get("text") or "").strip()
        if not text:
            _json_response(self, 400, {"error": "text_required"})
            return
        mode = parse_audience_mode(body.get("mode", "default"))
        contact = _resolve_contact(body.get("contact"))
        opts = clarify_candidates(
            text,
            mode=mode,
            nbest=body.get("nbest"),
            contact=contact,
            speaker=SpeakerStore().get(),
            listener_preset=body.get("listener_preset"),
        )
        original = next((c["text"] for c in opts if c["label"] in ("original", "standard")), text)
        for_listener = next((c["text"] for c in opts if c["label"] == "for_listener"), original)
        _json_response(
            self,
            200,
            {
                "raw": text,
                "original": original,
                "for_listener": for_listener,
                "candidates": opts,
            },
        )

    def _handle_feedback(self, body: dict) -> None:
        raw = body.get("raw", "")
        preferred = body.get("preferred", "")
        if not raw or not preferred:
            _json_response(self, 400, {"error": "raw_and_preferred_required"})
            return
        SpeakerStore().log_correction(raw, preferred)
        resp: dict[str, Any] = {"ok": True, "logged": True}
        nbest = body.get("nbest")
        if nbest is not None:
            mode = str(body.get("mode", "default"))
            candidates = body.get("candidates") or []
            bundle = save_utterance_bundle(
                raw,
                nbest,
                candidates,
                mode,
                picked=preferred,
            )
            host = self.server.server_address[0]  # type: ignore[union-attr]
            port = self.server.server_address[1]  # type: ignore[union-attr]
            resp["bundle_id"] = bundle["bundle_id"]
            resp["bundle_url"] = bundle_local_url(bundle["bundle_id"], host=host, port=port)
            resp["timestamp"] = bundle["timestamp"]
        # Future: if consent aggregate_research, queue de-identified stats only
        _json_response(self, 200, resp)

    def _handle_bundles_post(self, body: dict) -> None:
        raw = (body.get("raw") or "").strip()
        if not raw:
            _json_response(self, 400, {"error": "raw_required"})
            return
        nbest = body.get("nbest") or [raw]
        candidates = body.get("candidates") or []
        mode = str(body.get("mode", "default"))
        picked = body.get("picked")
        try:
            bundle = create_bundle(raw, nbest, candidates, mode, picked=picked)
            save_bundle(bundle)
        except ValueError as exc:
            _json_response(self, 400, {"error": str(exc)})
            return
        host = self.server.server_address[0]  # type: ignore[union-attr]
        port = self.server.server_address[1]  # type: ignore[union-attr]
        _json_response(
            self,
            200,
            {
                **bundle,
                "url": bundle_local_url(bundle["bundle_id"], host=host, port=port),
            },
        )


def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    host = normalize_loopback_host(host)
    ensure_local_api_token()
    httpd = ThreadingHTTPServer((host, port), ClarityHandler)
    print(f"ClarityIME core listening on http://{host}:{port} (IME shells connect here)")
    httpd.serve_forever()


def run_server_background(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> threading.Thread:
    t = threading.Thread(target=run_server, args=(host, port), daemon=True)
    t.start()
    return t


if __name__ == "__main__":
    run_server()
