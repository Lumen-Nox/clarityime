"""CLI entry for ClarityIME."""

from __future__ import annotations

import argparse
import json
import sys

from rich.console import Console
from rich.markup import escape

from clarityime import __version__
from clarityime.clarify.engine import clarify
from clarityime.clarify.local_rules import clarify_default
from clarityime.consent import load_consent, save_consent
from clarityime.models import AsrCandidate, AsrResult, AudienceMode, ClarifyRequest, ContactProfile, parse_audience_mode
from clarityime.settings import load_settings, save_settings
from clarityime.storage.contacts import ContactStore
from clarityime.storage.speaker import SpeakerStore

console = Console()

MODE_CHOICES = ["default", "contact", "structured", "ai"]


def cmd_demo(_args: argparse.Namespace) -> int:
    from clarityime.cerome.listener_presets import get_listener_preset
    from clarityime.clarify.listener_adapt import adapt_with_report

    raw = (
        "嗯那个 就是我想说一下这个方案吧 "
        "因为上次联调的时候大文件上传老是超时 "
        "所以我觉得可能得先改重试那块 "
        "但是我不太确定会不会影响别的接口 你觉得呢"
    )
    default_out, _ = clarify_default(raw, None)

    console.print("[cyan]Raw (ASR)[/]")
    console.print(raw)
    console.print("")
    console.print("[cyan]Clarified · default (speaker-faithful)[/]")
    console.print(default_out)
    console.print("")

    for preset_key, label in (
        ("analytical", "Adapted · analytical"),
        ("warm_flow", "Adapted · warm_flow"),
    ):
        preset = get_listener_preset(preset_key)
        assert preset is not None
        adapted, notes, cost_before, cost_after = adapt_with_report(default_out, preset)
        ops_line = next((n for n in notes if n.startswith("ops:")), "")
        op_tags = ops_line.removeprefix("ops:")
        console.print(f"[green]{label}[/]")
        console.print(adapted)
        console.print(
            f"[dim]  cost: {cost_before.total} -> {cost_after.total}[/]"
        )
        console.print(f"[dim]  ops: {op_tags}[/]")
        console.print("")

    console.print(
        "[dim]Same propositions · no summarization · fully offline[/]"
    )
    return 0


def cmd_clarify_text(args: argparse.Namespace) -> int:
    mode = parse_audience_mode(args.mode)
    contact = ContactStore().get_by_name(args.contact) if args.contact else None
    asr = AsrResult(candidates=[AsrCandidate(text=args.text, confidence=1.0)], backend="text")
    result = clarify(
        ClarifyRequest(
            asr=asr,
            mode=mode,
            contact=contact,
            speaker=SpeakerStore().get(),
        )
    )
    console.print(f"[dim]Raw:[/] {result.raw_primary}")
    console.print(f"[green]Clarified ({result.mode.value}):[/] {result.clarified}")
    return 0


def cmd_contacts(args: argparse.Namespace) -> int:
    store = ContactStore()
    if args.action == "list":
        for c in store.list_contacts() or []:
            console.print(f"- [{c.id}] {c.name} ({c.relationship}) tags: {c.style_notes}")
        return 0
    if args.action == "add":
        saved = store.upsert(
            ContactProfile(
                id=None,
                name=args.name,
                style_notes=args.style or "",
                preferred_words=args.words or "",
                relationship=args.relationship or "",
                age_hint=args.age or "",
                comprehension_notes=args.comprehension or "",
            )
        )
        console.print(f"Saved audience object #{saved.id}: {saved.name}")
        return 0
    if args.action == "export":
        from pathlib import Path

        store.export_profile(args.name, Path(args.out))
        console.print(f"Exported → {args.out}")
        return 0
    if args.action == "import":
        from pathlib import Path

        p = store.import_profile(Path(args.path))
        console.print(f"Imported: {p.name}")
        return 0
    return 1


def cmd_speaker(args: argparse.Namespace) -> int:
    store = SpeakerStore()
    if args.action == "show":
        p = store.get()
        console.print(json.dumps(p.__dict__, ensure_ascii=False, indent=2))
        return 0
    if args.action == "set":
        p = store.get()
        if args.patterns:
            p.oral_patterns = args.patterns
        if args.vague:
            p.vague_phrases = args.vague
        if args.length:
            p.preferred_length = args.length
        store.update(p)
        console.print("Speaker profile updated (local only).")
        return 0
    return 1


def cmd_consent(args: argparse.Namespace) -> int:
    if args.show or (args.cloud_sync is None and args.aggregate_research is None):
        console.print(json.dumps(load_consent(), ensure_ascii=False, indent=2))
        return 0
    c = load_consent()
    if args.cloud_sync is not None:
        c["cloud_sync"] = args.cloud_sync == "on"
    if args.aggregate_research is not None:
        c["aggregate_research"] = args.aggregate_research == "on"
    save_consent(
        cloud_sync=c["cloud_sync"],
        aggregate_research=c["aggregate_research"],
    )
    console.print("Consent saved (default: all off).")
    return 0


def cmd_settings(args: argparse.Namespace) -> int:
    if args.show or not any(
        [args.hotkey, args.apply_mode, args.audience, args.language, args.model]
    ):
        console.print(json.dumps(load_settings(), ensure_ascii=False, indent=2))
        return 0
    s = load_settings()
    if args.hotkey:
        s["hotkey"] = args.hotkey
    if args.apply_mode:
        s["apply_mode"] = args.apply_mode
    if args.audience:
        s["default_audience"] = args.audience
    if args.language:
        s["asr_language"] = args.language
    if args.model:
        s["whisper_model"] = args.model
    save_settings(s)
    console.print("Settings saved.")
    return 0


def cmd_capture(args: argparse.Namespace) -> int:
    """Record + ASR only; JSON stdout for platform shells (Windows tray, etc.)."""
    import json

    from clarityime.optional_deps import OptionalDependencyError, require_asr

    try:
        require_asr("capture")
        from clarityime.asr.whisper_local import WhisperLocalAsr
        from clarityime.audio import record_fixed, record_until_silence
    except OptionalDependencyError as exc:
        console.print(f"[red]Error:[/] {escape(str(exc))}")
        return 1

    from clarityime.settings import load_settings

    settings = load_settings()
    if args.seconds > 0:
        audio = record_fixed(seconds=args.seconds)
    else:
        audio = record_until_silence()
    if audio.size == 0:
        print(
            json.dumps(
                {"error": "no_audio", "raw": "", "nbest": []},
                ensure_ascii=False,
            )
        )
        return 1
    lang = settings.get("asr_language", "auto")
    asr = WhisperLocalAsr(model_size=settings.get("whisper_model", "base"))
    if lang == "auto":
        result = asr.transcribe_array(audio)
    else:
        result = asr.transcribe_array(audio, language=lang)
    nbest = result.top_n(3) if result.candidates else []
    payload = {
        "raw": result.primary,
        "nbest": nbest,
        "language": result.language,
        "backend": result.backend,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    from clarityime.app import ClarityApp

    console.print(
        "[yellow]Tip: production use → `clarityime serve` + platform IME keyboard.[/]"
    )
    app = ClarityApp(
        mode=parse_audience_mode(args.mode),
        contact_name=args.contact,
        model_size=args.model,
    )
    if args.once:
        app.run_once()
    else:
        app.run_hotkey_loop()
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from clarityime.security import normalize_loopback_host
    from clarityime.server import DEFAULT_HOST, DEFAULT_PORT, run_server

    host = normalize_loopback_host(args.host or DEFAULT_HOST)
    port = args.port or DEFAULT_PORT
    console.print(
        f"[green]ClarityIME core[/] for IME shells → http://{host}:{port}\n"
        "[dim]Install Android/Windows/macOS/Linux keyboard from platforms/[/]"
    )
    run_server(host=host, port=port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="clarityime",
        description="ClarityIME — audience comprehension inside the input method",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("demo").set_defaults(func=cmd_demo)

    srv = sub.add_parser("serve", help="Core API for integrated IME keyboards")
    srv.add_argument("--host", default=None)
    srv.add_argument("--port", type=int, default=None)
    srv.set_defaults(func=cmd_serve)

    run = sub.add_parser("run", help="[dev] standalone hotkey overlay")
    run.add_argument("--mode", choices=MODE_CHOICES, default="default")
    run.add_argument("--contact")
    run.add_argument("--model", default="base")
    run.add_argument("--once", action="store_true")
    run.set_defaults(func=cmd_run)

    cl = sub.add_parser("clarify", help="Clarify text (no ASR)")
    cl.add_argument("text")
    cl.add_argument("--mode", choices=MODE_CHOICES, default="default")
    cl.add_argument("--contact")
    cl.set_defaults(func=cmd_clarify_text)

    pol = sub.add_parser("polish", help="Alias for clarify")
    pol.add_argument("text")
    pol.add_argument("--mode", choices=MODE_CHOICES, default="default")
    pol.add_argument("--contact")
    pol.set_defaults(func=cmd_clarify_text)

    ct = sub.add_parser("contacts", help="Audience objects — local SQLite")
    ct_sub = ct.add_subparsers(dest="action", required=True)
    ct_sub.add_parser("list").set_defaults(func=cmd_contacts)
    add = ct_sub.add_parser("add")
    add.add_argument("--name", required=True)
    add.add_argument("--style", default="")
    add.add_argument("--words", default="")
    add.add_argument("--relationship", default="")
    add.add_argument("--age", default="")
    add.add_argument("--comprehension", default="", help="How they misunderstand you")
    add.set_defaults(func=cmd_contacts)
    exp = ct_sub.add_parser("export")
    exp.add_argument("--name", required=True)
    exp.add_argument("--out", required=True)
    exp.set_defaults(func=cmd_contacts)
    imp = ct_sub.add_parser("import")
    imp.add_argument("path")
    imp.set_defaults(func=cmd_contacts)

    sp = sub.add_parser("speaker", help="Speaker modeling (how I talk)")
    sp_sub = sp.add_subparsers(dest="action", required=True)
    sp_sub.add_parser("show").set_defaults(func=cmd_speaker)
    sp_set = sp_sub.add_parser("set")
    sp_set.add_argument("--patterns", default="")
    sp_set.add_argument("--vague", default="")
    sp_set.add_argument("--length", default="")
    sp_set.set_defaults(func=cmd_speaker)

    cn = sub.add_parser("consent", help="Data sharing toggles")
    cn.add_argument("--show", action="store_true")
    cn.add_argument("--cloud-sync", choices=["on", "off"])
    cn.add_argument("--aggregate-research", choices=["on", "off"])
    cn.set_defaults(func=cmd_consent)

    st = sub.add_parser("settings", help="Hotkey, apply mode, language")
    st.add_argument("--show", action="store_true")
    st.add_argument("--hotkey")
    st.add_argument("--apply-mode", choices=["auto", "paste", "clipboard_only"])
    st.add_argument("--audience", choices=MODE_CHOICES)
    st.add_argument("--language", help="auto | zh | en | …")
    st.add_argument("--model", help="Whisper size")
    st.set_defaults(func=cmd_settings)

    cap = sub.add_parser("capture", help="Record+ASR → JSON (for IME shells)")
    cap.add_argument("--seconds", type=int, default=0, help="Fixed duration; 0=silence-detect")
    cap.set_defaults(func=cmd_capture)

    return p


def main(argv: list[str] | None = None) -> int:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/]")
        return 130
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Error:[/] {escape(str(exc))}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
