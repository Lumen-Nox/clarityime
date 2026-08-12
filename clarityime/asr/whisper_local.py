"""Local ASR via faster-whisper with N-best style multi-hypothesis."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from clarityime.models import AsrCandidate, AsrResult
from clarityime.optional_deps import require_asr


class WhisperLocalAsr:
    """Offline ASR — default backend. No network unless model download on first run."""

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def _load(self):
        if self._model is None:
            require_asr("Local Whisper ASR")
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self._model

    def transcribe_file(self, audio_path: Path, language: str = "zh") -> AsrResult:
        model = self._load()
        segments, info = model.transcribe(
            str(audio_path),
            language=language,
            beam_size=5,
            best_of=3,
            temperature=[0.0, 0.2, 0.4],
        )
        primary_text = "".join(s.text for s in segments).strip()
        candidates = self._multi_hypothesis(model, audio_path, language, primary_text)
        return AsrResult(
            candidates=candidates,
            language=language,
            backend=f"faster-whisper:{self.model_size}",
            used_network=False,
        )

    def transcribe_array(
        self,
        audio: Any,
        sample_rate: int = 16000,
        language: str | None = None,
    ) -> AsrResult:
        model = self._load()
        lang_kw = {} if language is None else {"language": language}
        segments, info = model.transcribe(
            audio,
            beam_size=5,
            best_of=3,
            temperature=[0.0, 0.2, 0.4],
            **lang_kw,
        )
        detected = language or getattr(info, "language", None) or "auto"
        primary_text = "".join(s.text for s in segments).strip()
        alt_segments, _ = model.transcribe(
            audio,
            beam_size=1,
            temperature=0.6,
            **lang_kw,
        )
        alt_text = "".join(s.text for s in alt_segments).strip()
        candidates = _pack_candidates([primary_text, alt_text])
        return AsrResult(
            candidates=candidates,
            language=str(detected),
            backend=f"faster-whisper:{self.model_size}",
            used_network=False,
        )

    def _multi_hypothesis(
        self, model, audio_path: Path, language: str, primary: str
    ) -> list[AsrCandidate]:
        texts = [primary]
        for temp in (0.2, 0.5):
            segs, _ = model.transcribe(
                str(audio_path),
                language=language,
                beam_size=1,
                temperature=temp,
            )
            texts.append("".join(s.text for s in segs).strip())
        return _pack_candidates(texts)


def _pack_candidates(texts: list[str]) -> list[AsrCandidate]:
    seen: set[str] = set()
    out: list[AsrCandidate] = []
    for i, t in enumerate(texts):
        t = t.strip()
        if not t or t in seen:
            continue
        seen.add(t)
        conf = max(0.35, 0.95 - i * 0.15)
        out.append(AsrCandidate(text=t, confidence=conf, source="whisper"))
    return out[:3]
