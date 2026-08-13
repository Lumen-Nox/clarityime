#!/usr/bin/env python3
"""IBus engine — ClarityIME integrated input method for Linux."""

from __future__ import annotations

import json
import os
import subprocess
import sys

CORE = os.environ.get("CLARITYIME_CORE", "http://127.0.0.1:17800")
REPO = os.environ.get("CLARITYIME_ROOT", os.path.expanduser("~/code-ClarityIME"))

try:
    import gi

    gi.require_version("IBus", "1.0")
    gi.require_version("GLib", "2.0")
    from gi.repository import GLib, IBus
except ImportError:
    IBus = None  # type: ignore
    GLib = None  # type: ignore


def _http_get(path: str) -> dict | None:
    import urllib.request

    try:
        req = urllib.request.Request(f"{CORE.rstrip('/')}{path}", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def _http_post(path: str, payload: dict) -> dict | None:
    import urllib.request

    try:
        req = urllib.request.Request(
            f"{CORE.rstrip('/')}{path}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def _fetch_settings() -> dict:
    return _http_get("/v1/settings") or {}


def _auto_apply_top_enabled() -> bool:
    return bool(_fetch_settings().get("auto_apply_top", False))


def _offline_clarify(text: str, mode: str) -> str:
    fillers = ("嗯", "啊", "呃", "那个", "就是", "然后")
    out = text.strip()
    for f in fillers:
        if out.startswith(f):
            out = out[len(f) :]
    if mode == "ai":
        for g in ("你好", "您好", "请问"):
            if out.startswith(g):
                out = out[len(g) :].lstrip("，, ")
        return f"Intent: {out.rstrip('。！？')}"
    if out and out[-1] not in "。！？":
        out += "？" if any(x in out for x in ("吗", "么", "什么", "怎么")) else "。"
    return out


def _candidates(
    text: str,
    mode: str,
    contact: str | None = None,
    nbest: list[str] | None = None,
) -> list[tuple[str, str]]:
    payload: dict = {"text": text, "mode": mode}
    if contact:
        payload["contact"] = contact
    if nbest:
        payload["nbest"] = nbest
    data = _http_post("/v1/candidates", payload)
    if data and "candidates" in data:
        return [(c["text"], c.get("label", "option")) for c in data["candidates"]]
    primary = _offline_clarify(text, mode)
    return [(primary, "offline")]


def _capture_voice() -> tuple[str, list[str]]:
    python = os.path.join(REPO, ".venv", "bin", "python")
    if not os.path.isfile(python):
        python = sys.executable
    try:
        out = subprocess.check_output(
            [python, "-m", "clarityime.main", "capture", "--seconds", "5"],
            cwd=REPO,
            text=True,
            timeout=120,
        )
        data = json.loads(out.strip())
        raw = str(data.get("raw") or "")
        nbest_raw = data.get("nbest") or []
        nbest = [str(x) for x in nbest_raw if x] if isinstance(nbest_raw, list) else []
        if raw and raw not in nbest:
            nbest = [raw, *[x for x in nbest if x != raw]]
        return raw, nbest
    except Exception:
        return "", []


def _format_candidate(index: int, text: str, label: str) -> str:
    if index == 0:
        return f"★ 推荐 · [{label}] {text}  (Enter/1)"
    return f"{index + 1}. [{label}] {text}"


if IBus is not None:

    MODES = ("default", "ai", "contact")
    KEY_F9 = 0xFFC6
    KEY_V = 0x0076
    MASK_CTRL = IBus.ModifierType.CONTROL_MASK
    MASK_SHIFT = IBus.ModifierType.SHIFT_MASK

    class ClarityEngine(IBus.Engine):
        def __init__(self):
            super().__init__()
            self.mode = "default"
            self.contact: str | None = None
            self._pending_raw = ""
            self._pending_nbest: list[str] = []
            self._pending_options: list[tuple[str, str]] = []
            self.register_property(self._make_mode_prop())

        def _make_mode_prop(self) -> IBus.PropList:
            return IBus.Property(
                key="mode",
                prop_type=IBus.PropType.MENU,
                label=f"ClarityIME [{self.mode}]",
                icon="input-keyboard",
                symbol=IBus.Text("🎤"),
                state=IBus.PropState.ENABLED,
                sub_props=self._mode_sub_props(),
            )

        def _mode_sub_props(self) -> IBus.PropList:
            subs = IBus.PropList()
            for m in MODES:
                subs.append(
                    IBus.Property(
                        key=f"mode-{m}",
                        prop_type=IBus.PropType.RADIO,
                        label=m,
                        state=IBus.PropState.CHECKED
                        if m == self.mode
                        else IBus.PropState.UNCHECKED,
                    )
                )
            subs.append(
                IBus.Property(
                    key="voice",
                    prop_type=IBus.PropType.NORMAL,
                    label="Voice clarify (F9)",
                    symbol=IBus.Text("🎤"),
                )
            )
            return subs

        def do_property_activate(self, prop_key: str, prop_state: int) -> bool:  # noqa: ARG002
            if prop_key.startswith("mode-"):
                self.mode = prop_key.replace("mode-", "")
                self.update_property(self._make_mode_prop())
                return True
            if prop_key == "voice":
                GLib.idle_add(self._run_voice_pipeline)
                return True
            return False

        def do_process_key_event(self, keyval, keycode, state):  # noqa: ARG002
            if keyval == KEY_F9 and not (state & (MASK_CTRL | MASK_SHIFT)):
                GLib.idle_add(self._run_voice_pipeline)
                return True
            if keyval == KEY_V and (state & MASK_CTRL) and (state & MASK_SHIFT):
                GLib.idle_add(self._run_voice_pipeline)
                return True
            if self._pending_options:
                if keyval in (0xFF0D, 0x0020):
                    self._apply_candidate(0)
                    return True
                if 0x0031 <= keyval <= 0x0039:
                    idx = keyval - 0x0031
                    if idx < len(self._pending_options):
                        self._apply_candidate(idx)
                        return True
                if keyval == 0xFF1B:
                    self._clear_lookup()
                    return True
                # Ctrl+Shift+B — none of the candidates fit (feedback)
                if keyval == 0x0062 and (state & MASK_CTRL) and (state & MASK_SHIFT):
                    self._send_user_feedback("keyboard shortcut")
                    return True
            return False

        def _run_voice_pipeline(self) -> bool:
            raw, nbest = _capture_voice()
            if not raw:
                return False
            self._show_candidates(raw, nbest)
            return False

        def _show_candidates(self, raw: str, nbest: list[str] | None = None) -> None:
            self._pending_raw = raw
            self._pending_nbest = list(nbest) if nbest else [raw]
            self._pending_options = _candidates(raw, self.mode, self.contact, nbest)
            if _auto_apply_top_enabled() or len(self._pending_options) == 1:
                self._apply_candidate(0)
                return
            table = IBus.LookupTable.new(
                page_size=9,
                cursor_pos=0,
                cursor_visible=True,
                round=True,
            )
            for i, (text, label) in enumerate(self._pending_options[:9]):
                table.append_candidate(
                    IBus.Text(_format_candidate(i, text, label)),
                    i,
                    IBus.Text(text),
                )
            self.update_lookup_table(table, True)

        def _apply_candidate(self, index: int) -> None:
            if not self._pending_options or index >= len(self._pending_options):
                self._clear_lookup()
                return
            text, _ = self._pending_options[index]
            self.commit_text(IBus.Text(text))
            if text != self._pending_raw:
                _http_post(
                    "/v1/feedback",
                    {
                        "raw": self._pending_raw,
                        "preferred": text,
                        "mode": self.mode,
                        "nbest": self._pending_nbest,
                        "candidates": [
                            {"text": t, "label": label}
                            for t, label in self._pending_options
                        ],
                    },
                )
            self._clear_lookup()

        def _send_user_feedback(self, note: str) -> None:
            if not self._pending_raw:
                return
            payload = {
                "raw": self._pending_raw,
                "preferred": f"[user_feedback] {note}",
                "mode": self.mode,
                "nbest": self._pending_nbest,
                "candidates": [
                    {"text": t, "label": label}
                    for t, label in self._pending_options
                ],
            }
            resp = _http_post("/v1/feedback", payload)
            if resp and resp.get("bundle_url"):
                print(f"ClarityIME bundle: {resp['bundle_url']}", file=sys.stderr)
            self._clear_lookup()

        def _clear_lookup(self) -> None:
            self._pending_raw = ""
            self._pending_nbest = []
            self._pending_options = []
            self.hide_lookup_table()

    class ClarityFactory(IBus.Factory):
        def create_engine(self, name):  # noqa: ARG002
            return ClarityEngine()

    def run_ibus() -> None:
        IBus.init()
        component = IBus.Component.new(
            "org.clarityime.ibus",
            "ClarityIME voice clarify input method",
            "0.3.0",
            "MIT",
            "Example User",
            "https://github.com/clarityime",
            "",
            "",
        )
        factory = ClarityFactory()
        component.add_engine(
            "clarityime",
            IBus.EngineDesc.new(
                "clarityime",
                "ClarityIME",
                "ClarityIME — voice clarify IME",
                "en",
                "MIT",
                "Example User",
                "input-keyboard",
                "default",
            ),
            factory,
        )
        IBus.bus.register_component(component)
        IBus.main()

    if __name__ == "__main__":
        run_ibus()

else:
    if __name__ == "__main__":
        print("Install: sudo apt install ibus python3-gi gir1.2-ibus-1.0")
        print("Offline test:", _offline_clarify("嗯那个你好", "default"))
