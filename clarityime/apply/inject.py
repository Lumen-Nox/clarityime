"""IME caret apply: write clarified text to focused field without manual Ctrl+C/V."""

from __future__ import annotations

import time

from clarityime.optional_deps import require_desktop


def apply_text(
    text: str,
    mode: str = "auto",
    *,
    restore_clipboard: bool = True,
    paste_delay_ms: int = 50,
) -> str:
    """
    Apply text at cursor.

    Returns method used: 'paste' | 'inject' | 'clipboard_only'.

    For CJK, reliable path is clipboard + synthetic Ctrl+V (standard IME inject fallback).
    """
    if not text:
        return "clipboard_only"

    require_desktop("Clipboard paste apply")
    import keyboard
    import pyperclip

    if mode == "clipboard_only":
        pyperclip.copy(text)
        return "clipboard_only"

    old_clip = pyperclip.paste() if restore_clipboard else None
    pyperclip.copy(text)
    time.sleep(paste_delay_ms / 1000.0)

    if mode in ("auto", "paste", "inject"):
        keyboard.send("ctrl+v")
        method = "paste"
    else:
        method = "clipboard_only"

    if restore_clipboard and old_clip is not None:
        time.sleep(paste_delay_ms / 1000.0)
        try:
            pyperclip.copy(old_clip)
        except Exception:
            pass

    return method
