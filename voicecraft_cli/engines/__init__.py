"""
TTS Engine package.

Provides abstract base class and concrete implementations for various
text-to-speech engines (pyttsx3, espeak, system commands).
"""

from voicecraft_cli.engines.base import TTSEngine
from voicecraft_cli.engines.factory import EngineFactory

__all__ = ["TTSEngine", "EngineFactory"]
