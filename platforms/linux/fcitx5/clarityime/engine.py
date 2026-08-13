#!/usr/bin/env python3
"""ClarityIME Fcitx5 engine logic + CLI helper for the native addon."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

CORE = os.environ.get("CLARITYIME_CORE", "http://127.0.0.1:17800")
REPO = os.environ.get("CLARITYIME_ROOT", os.path.expanduser("~/code-ClarityIME"))


def http_get(path: str) -> dict | None:
    import urllib.error
    import urllib.request

    try:
        req = urllib.request.Request(f"{CORE.rstrip('/')}{path}", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def http_post(path: str, payload: dict) -> dict | None:
    import urllib.error
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
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def fetch_settings() -> dict:
    return http_get("/v1/settings") or {}


def auto_apply_top_enabled() -> bool:
    return bool(fetch_settings().get("auto_apply_top", False))


def offline_clarify(text: str, mode: str = "default") -> str:
    fillers = ("嗯", "啊", "呃", "那个", "就是", "然后")
    out = text.strip()
    for filler in fillers:
        if out.startswith(filler):
            out = out[len(filler) :]
    if mode == "ai":
        for greeting in ("你好", "您好", "请问"):
            if out.startswith(greeting):
                out = out[len(greeting) :].lstrip("，, ")
        return f"Intent: {out.rstrip('。！？')}"
    if out and out[-1] not in "。！？":
        out += "？" if any(x in out for x in ("吗", "么", "什么", "怎么")) else "。"
    return out


def candidates(
    text: str,
    mode: str = "default",
    contact: str | None = None,
    nbest: list[str] | None = None,
) -> list[dict[str, str]]:
    payload: dict = {"text": text, "mode": mode}
    if contact:
        payload["contact"] = contact
    if nbest:
        payload["nbest"] = nbest
    data = http_post("/v1/candidates", payload)
    if data and "candidates" in data:
        return [
            {"text": c["text"], "label": c.get("label", "option")}
            for c in data["candidates"]
        ]
    primary = offline_clarify(text, mode)
    return [{"text": primary, "label": "offline"}]


def capture_voice(seconds: int = 5) -> dict[str, object]:
    """Return ASR result: ``raw`` primary transcript and ``nbest`` alternates."""
    python = os.path.join(REPO, ".venv", "bin", "python")
    if not os.path.isfile(python):
        python = sys.executable
    try:
        out = subprocess.check_output(
            [python, "-m", "clarityime.main", "capture", "--seconds", str(seconds)],
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
        return {"raw": raw, "nbest": nbest}
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
        return {"raw": "", "nbest": []}


def send_feedback(
    raw: str,
    preferred: str,
    *,
    mode: str = "default",
    nbest: list[str] | None = None,
    candidates: list[dict[str, str]] | None = None,
) -> None:
    if raw and preferred and raw != preferred:
        payload: dict = {"raw": raw, "preferred": preferred}
        if nbest is not None:
            payload["nbest"] = nbest
            payload["mode"] = mode
            if candidates is not None:
                payload["candidates"] = candidates
        result = http_post("/v1/feedback", payload)
        if result and result.get("bundle_url"):
            print(result["bundle_url"], file=sys.stderr)


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ClarityIME Fcitx5 helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    offline_p = sub.add_parser("offline", help="Offline clarify fallback")
    offline_p.add_argument("text")
    offline_p.add_argument("mode", nargs="?", default="default")

    cand_p = sub.add_parser("candidates", help="Fetch candidate list JSON")
    cand_p.add_argument("--text", required=True)
    cand_p.add_argument("--mode", default="default")
    cand_p.add_argument("--contact", default="")
    cand_p.add_argument(
        "--nbest",
        default="",
        help='JSON array of ASR alternates, e.g. \'["嗯那个你好","你好"]\'',
    )

    sub.add_parser("capture", help="Capture voice; print {raw, nbest} JSON")

    sub.add_parser("settings", help="Fetch /v1/settings JSON")

    sub.add_parser("auto-apply-top", help="Print true/false from settings.auto_apply_top")

    fb_p = sub.add_parser("feedback", help="Send preferred candidate feedback")
    fb_p.add_argument("--raw", required=True)
    fb_p.add_argument("--preferred", required=True)
    fb_p.add_argument("--mode", default="default")
    fb_p.add_argument("--nbest", default="", help="JSON array of ASR alternates")
    fb_p.add_argument("--candidates", default="", help="JSON array of {text,label}")

    exp_p = sub.add_parser("export-contact", help="GET /v1/contacts/export → stdout or file")
    exp_p.add_argument("--name", required=True)
    exp_p.add_argument("--out", default="", help="Write JSON file (default: stdout)")

    imp_p = sub.add_parser("import-contact", help="POST /v1/contacts/import from JSON file")
    imp_p.add_argument("--path", required=True)

    bundle_p = sub.add_parser("get-bundle", help="GET /v1/bundles/{id} → stdout")
    bundle_p.add_argument("--id", required=True)

    args = parser.parse_args(argv)

    if args.cmd == "offline":
        print(offline_clarify(args.text, args.mode))
        return 0
    if args.cmd == "candidates":
        contact = args.contact or None
        nbest: list[str] | None = None
        if args.nbest.strip():
            parsed = json.loads(args.nbest)
            if isinstance(parsed, list):
                nbest = [str(x) for x in parsed if x]
        print(
            json.dumps(
                candidates(args.text, args.mode, contact, nbest),
                ensure_ascii=False,
            )
        )
        return 0
    if args.cmd == "capture":
        result = capture_voice()
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result.get("raw") else 1
    if args.cmd == "settings":
        print(json.dumps(fetch_settings(), ensure_ascii=False))
        return 0
    if args.cmd == "auto-apply-top":
        print("true" if auto_apply_top_enabled() else "false")
        return 0
    if args.cmd == "feedback":
        nbest: list[str] | None = None
        cands: list[dict[str, str]] | None = None
        if args.nbest.strip():
            parsed = json.loads(args.nbest)
            if isinstance(parsed, list):
                nbest = [str(x) for x in parsed if x]
        if args.candidates.strip():
            parsed = json.loads(args.candidates)
            if isinstance(parsed, list):
                cands = [
                    {"text": str(c.get("text", "")), "label": str(c.get("label", "option"))}
                    for c in parsed
                    if isinstance(c, dict)
                ]
        send_feedback(args.raw, args.preferred, mode=args.mode, nbest=nbest, candidates=cands)
        return 0
    if args.cmd == "export-contact":
        import urllib.parse

        q = urllib.parse.quote(args.name)
        data = http_get(f"/v1/contacts/export?name={q}")
        if not data:
            print("export failed", file=sys.stderr)
            return 1
        text = json.dumps(data, ensure_ascii=False, indent=2)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(text)
            print(args.out)
        else:
            print(text)
        return 0
    if args.cmd == "import-contact":
        with open(args.path, encoding="utf-8") as f:
            payload = json.load(f)
        if not http_post("/v1/contacts/import", payload):
            print("import failed", file=sys.stderr)
            return 1
        print("ok")
        return 0
    if args.cmd == "get-bundle":
        data = http_get(f"/v1/bundles/{args.id}")
        if not data:
            print("bundle not found", file=sys.stderr)
            return 1
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    if len(sys.argv) == 1:
        sample = offline_clarify("嗯那个你好", "default")
        print(f"offline test: {sample}")
        raise SystemExit(0)
    raise SystemExit(cli_main())
