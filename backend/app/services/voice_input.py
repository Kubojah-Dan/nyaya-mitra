"""Voice input adapter for NyayaMitra intake.

Provides:
- A stub/mock speech-to-text adapter for local dev and testing.
- An interface contract for future integration with Google Cloud Speech-to-Text
  or Bhashini Vakyansh (ULCA) for Indian language ASR.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass
class TranscriptionResult:
    text: str
    confidence: float
    detected_language: str
    is_fallback: bool = False
    error: str = ""


class VoiceInputAdapter(abc.ABC):
    """Abstract voice input adapter interface."""

    @abc.abstractmethod
    async def transcribe(self, audio_bytes: bytes, language_hint: str = "hi-IN") -> TranscriptionResult:
        """Transcribe raw audio bytes to text."""
        pass


class MockVoiceInputAdapter(VoiceInputAdapter):
    """Mock adapter for testing — returns provided text verbatim."""

    def __init__(self, mock_text: str = "मेरे मकान मालिक ने मुझे बिना नोटिस के खाली करने को कहा है।") -> None:
        self._mock_text = mock_text

    async def transcribe(self, audio_bytes: bytes, language_hint: str = "hi-IN") -> TranscriptionResult:
        return TranscriptionResult(
            text=self._mock_text,
            confidence=0.95,
            detected_language=language_hint.split("-")[0],
            is_fallback=True,
        )


class TextFallbackAdapter(VoiceInputAdapter):
    """Text passthrough adapter — used when voice is unavailable."""

    async def transcribe(self, audio_bytes: bytes, language_hint: str = "en-IN") -> TranscriptionResult:
        try:
            text = audio_bytes.decode("utf-8").strip()
        except Exception:
            text = ""
        return TranscriptionResult(
            text=text,
            confidence=1.0,
            detected_language="en",
            is_fallback=True,
            error="" if text else "Empty text input",
        )
