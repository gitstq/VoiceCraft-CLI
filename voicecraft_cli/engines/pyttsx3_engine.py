"""
pyttsx3 TTS engine adapter.

Wraps the pyttsx3 library for cross-platform speech synthesis.
Falls back gracefully if pyttsx3 is not installed.
"""

import os
import sys
import subprocess
import tempfile
from typing import List, Optional, Dict, Any

from voicecraft_cli.engines.base import TTSEngine
from voicecraft_cli.utils.logger import get_logger

logger = get_logger(__name__)


class Pyttsx3Engine(TTSEngine):
    """TTS engine using the pyttsx3 Python library.

    pyttsx3 is a cross-platform text-to-speech library that wraps
    system speech engines (SAPI on Windows, NSSpeechSynthesizer on macOS,
    and espeak on Linux).

    This adapter detects pyttsx3 availability and provides a uniform
    interface for speech synthesis and file output.
    """

    def __init__(self) -> None:
        """Initialize the pyttsx3 engine adapter."""
        super().__init__()
        self.name = "pyttsx3"
        self._engine = None
        self._available = self.detect()

    def detect(self) -> bool:
        """Check if pyttsx3 is installed and importable.

        Returns:
            bool: True if pyttsx3 can be imported successfully.
        """
        try:
            import pyttsx3  # type: ignore
            self._available = True
            logger.info("pyttsx3 engine detected and available")
            return True
        except ImportError:
            self._available = False
            logger.debug("pyttsx3 is not installed")
            return False

    def _init_engine(self) -> bool:
        """Lazily initialize the pyttsx3 engine instance.

        Returns:
            bool: True if initialization succeeded.
        """
        if self._engine is not None:
            return True
        try:
            import pyttsx3  # type: ignore
            self._engine = pyttsx3.init()
            # Apply current settings
            self._engine.setProperty("rate", self._rate_to_wpm(self.rate))
            self._engine.setProperty("volume", self.volume)
            logger.info("pyttsx3 engine initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3: {e}")
            self._available = False
            return False

    @staticmethod
    def _rate_to_wpm(rate: float) -> int:
        """Convert a rate multiplier to words-per-minute for pyttsx3.

        Args:
            rate: Rate multiplier (1.0 = normal speed).

        Returns:
            int: Words per minute value.
        """
        # pyttsx3 default rate is typically 200 WPM
        return int(200 * rate)

    def speak(self, text: str) -> bool:
        """Speak text aloud using pyttsx3.

        Args:
            text: The text to speak.

        Returns:
            bool: True if speech was successful.
        """
        if not self._init_engine():
            logger.error("Cannot speak: pyttsx3 engine not available")
            return False
        try:
            self._engine.setProperty("rate", self._rate_to_wpm(self.rate))
            self._engine.setProperty("volume", self.volume)
            self._engine.say(text)
            self._engine.runAndWait()
            logger.info("Speech completed via pyttsx3")
            return True
        except Exception as e:
            logger.error(f"pyttsx3 speak failed: {e}")
            return False

    def synthesize_to_file(self, text: str, output_path: str,
                           format: str = "wav") -> bool:
        """Synthesize text and save to a WAV file.

        Note: pyttsx3 only supports WAV output natively. For other formats,
        use the audio converter module.

        Args:
            text: The text to synthesize.
            output_path: Destination file path.
            format: Output format (only "wav" is natively supported).

        Returns:
            bool: True if file was written successfully.
        """
        if not self._init_engine():
            logger.error("Cannot synthesize: pyttsx3 engine not available")
            return False
        try:
            self._engine.setProperty("rate", self._rate_to_wpm(self.rate))
            self._engine.setProperty("volume", self.volume)
            self._engine.save_to_file(text, output_path)
            self._engine.runAndWait()
            logger.info(f"Audio saved to {output_path} via pyttsx3")
            return True
        except Exception as e:
            logger.error(f"pyttsx3 synthesize_to_file failed: {e}")
            return False

    def get_voices(self) -> List[Dict[str, Any]]:
        """List available voices from pyttsx3.

        Returns:
            List of voice dictionaries with id, name, and language.
        """
        if not self._init_engine():
            return []
        try:
            voices = []
            for v in self._engine.getProperty("voices"):
                voices.append({
                    "id": v.id,
                    "name": v.name,
                    "lang": getattr(v, "languages", ["unknown"])[0]
                    if getattr(v, "languages", None) else "unknown",
                })
            return voices
        except Exception as e:
            logger.error(f"Failed to get pyttsx3 voices: {e}")
            return []

    def set_voice(self, voice_id: str) -> bool:
        """Select a pyttsx3 voice by its ID.

        Args:
            voice_id: The voice identifier string.

        Returns:
            bool: True if the voice was set successfully.
        """
        if not self._init_engine():
            return False
        try:
            self._engine.setProperty("voice", voice_id)
            self.voice_id = voice_id
            logger.info(f"Voice set to {voice_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to set voice {voice_id}: {e}")
            return False
