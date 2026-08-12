"""Optional dependency checks with actionable install hints."""

from __future__ import annotations

ASR_HINT = 'pip install "clarityime[asr]"'
DESKTOP_HINT = 'pip install "clarityime[desktop]"'


class OptionalDependencyError(RuntimeError):
    """Raised when a command needs extras that are not installed."""


def require_asr(feature: str = "Microphone capture and local ASR") -> None:
    missing: list[str] = []
    for name in ("numpy", "sounddevice"):
        try:
            __import__(name)
        except ImportError:
            missing.append(name)
    try:
        __import__("faster_whisper")
    except ImportError:
        missing.append("faster-whisper")
    if missing:
        raise OptionalDependencyError(
            f"{feature} needs the asr extra: {ASR_HINT}"
        )


def require_desktop(feature: str = "Hotkey mode and clipboard paste") -> None:
    for name, label in (("keyboard", "keyboard"), ("pyperclip", "pyperclip")):
        try:
            __import__(name)
        except ImportError as exc:
            raise OptionalDependencyError(
                f"{feature} needs the desktop extra: {DESKTOP_HINT}"
            ) from exc
        except Exception as exc:
            raise OptionalDependencyError(
                f"{feature} needs the desktop extra ({DESKTOP_HINT}). "
                f"Failed to load {label}: {exc}"
            ) from exc
