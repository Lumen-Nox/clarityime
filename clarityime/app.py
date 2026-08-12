"""ClarityIME application — IME-integrated voice clarification layer."""

from __future__ import annotations

import threading
from pathlib import Path

import keyboard
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from clarityime.apply.inject import apply_text
from clarityime.asr.whisper_local import WhisperLocalAsr
from clarityime.audio import record_until_silence, save_wav
from clarityime.clarify.engine import clarify
from clarityime.models import AudienceMode, ClarifyRequest, parse_audience_mode
from clarityime.settings import load_settings
from clarityime.storage.contacts import ContactStore
from clarityime.storage.speaker import SpeakerStore

console = Console()


class ClarityApp:
    def __init__(
        self,
        mode: AudienceMode | None = None,
        contact_name: str | None = None,
        model_size: str | None = None,
    ) -> None:
        self.settings = load_settings()
        raw_audience = self.settings.get("default_audience", "default")
        self.mode = mode or parse_audience_mode(raw_audience)
        self.contact_name = contact_name or self.settings.get("default_contact")
        self.hotkey = self.settings.get("hotkey", "ctrl+shift+space")
        self.asr = WhisperLocalAsr(
            model_size=model_size or self.settings.get("whisper_model", "base")
        )
        self.contacts = ContactStore()
        self.speaker = SpeakerStore()
        self._busy = False
        self._record_dir = Path(__file__).resolve().parents[1] / "data" / "recordings"

    def _resolve_contact(self):
        if self.mode != AudienceMode.CONTACT:
            return None
        name = self.contact_name
        if not name:
            raise ValueError("CONTACT mode needs --contact NAME or settings default_contact")
        c = self.contacts.get_by_name(name)
        if not c:
            raise ValueError(f"Unknown contact: {name}")
        return c

    def run_once(self) -> None:
        if self._busy:
            console.print("[yellow]Still processing…[/]")
            return
        self._busy = True
        try:
            console.print("[cyan]🎤 Listening… (pause to finish)[/]")
            audio = record_until_silence()
            if audio.size == 0:
                console.print("[red]No audio captured.[/]")
                return

            save_wav(audio, self._record_dir / "last.wav")
            lang_setting = self.settings.get("asr_language", "auto")
            if lang_setting == "auto":
                asr_result = self.asr.transcribe_array(audio)
            else:
                asr_result = self.asr.transcribe_array(audio, language=lang_setting)

            result = clarify(
                ClarifyRequest(
                    asr=asr_result,
                    mode=self.mode,
                    contact=self._resolve_contact(),
                    speaker=self.speaker.get(),
                )
            )
            self._show_result(asr_result, result)

            apply_mode = self.settings.get("apply_mode", "auto")
            method = apply_text(
                result.clarified,
                mode=apply_mode,
                restore_clipboard=self.settings.get("restore_clipboard_after_apply", True),
            )
            console.print(f"[green]Applied via {method} (IME caret insert, no manual Ctrl+C/V).[/]")
        finally:
            self._busy = False

    def _show_result(self, asr_result, clarify_result) -> None:
        table = Table(title="ClarityIME — Raw vs Clarified", show_header=True)
        table.add_column("Field", style="cyan")
        table.add_column("Content")
        table.add_row("Mode (面向对象)", clarify_result.mode.value)
        table.add_row("ASR", asr_result.backend)
        table.add_row("Network", "yes" if clarify_result.used_network else "no — offline")
        table.add_row("Raw", clarify_result.raw_primary)
        if len(asr_result.candidates) > 1:
            alts = "\n".join(
                f"  {i+1}. [{c.confidence:.2f}] {c.text}"
                for i, c in enumerate(asr_result.candidates)
            )
            table.add_row("N-best", alts)
        table.add_row("Clarified", f"[bold green]{clarify_result.clarified}[/]")
        if clarify_result.notes:
            table.add_row("Notes", ", ".join(clarify_result.notes))
        console.print(Panel(table, border_style="magenta"))

    def run_hotkey_loop(self) -> None:
        console.print(
            Panel(
                f"[bold]ClarityIME[/] — 意思清晰化层（非润色输入法）\n"
                f"Hotkey: [cyan]{self.hotkey}[/] → speak → clarify → auto-apply\n"
                f"Audience: [yellow]{self.mode.value}[/]"
                + (f" → [yellow]{self.contact_name}[/]" if self.contact_name else "")
                + "\n[dim]Esc to quit[/]",
                title="Practice project — local-first",
            )
        )

        def on_hotkey():
            threading.Thread(target=self.run_once, daemon=True).start()

        keyboard.add_hotkey(self.hotkey, on_hotkey)
        keyboard.wait("esc")
