"""Microphone capture for hotkey workflow."""

from __future__ import annotations

import time
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd


def record_until_silence(
    sample_rate: int = 16000,
    max_seconds: float = 30.0,
    silence_threshold: float = 0.015,
    silence_duration: float = 1.2,
) -> np.ndarray:
    """Record from default mic; stop after sustained silence or max duration."""
    block = int(sample_rate * 0.1)
    max_blocks = int(max_seconds / 0.1)
    chunks: list[np.ndarray] = []
    silent_blocks = 0
    needed_silent = int(silence_duration / 0.1)

    for _ in range(max_blocks):
        data = sd.rec(block, samplerate=sample_rate, channels=1, dtype="float32")
        sd.wait()
        chunks.append(data.flatten())
        rms = float(np.sqrt(np.mean(data**2)))
        if rms < silence_threshold:
            silent_blocks += 1
            if len(chunks) > 5 and silent_blocks >= needed_silent:
                break
        else:
            silent_blocks = 0

    if not chunks:
        return np.array([], dtype=np.float32)
    return np.concatenate(chunks)


def save_wav(audio: np.ndarray, path: Path, sample_rate: int = 16000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(audio, -1.0, 1.0)
    pcm16 = (pcm * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16.tobytes())


def record_fixed(seconds: float = 5.0, sample_rate: int = 16000) -> np.ndarray:
    frames = int(seconds * sample_rate)
    data = sd.rec(frames, samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()
    return data.flatten()
