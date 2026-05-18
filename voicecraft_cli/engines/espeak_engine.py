"""
eSpeak TTS engine adapter.

Interfaces with the eSpeak command-line tool for speech synthesis.
eSpeak is a compact, open-source speech synthesizer available on most
Linux distributions and can be installed on macOS and Windows.
"""

import os
import subprocess
import shutil
from typing import List, Optional, Dict, Any

from voicecraft_cli.engines.base import TTSEngine
from voicecraft_cli.utils.logger import get_logger

logger = get_logger(__name__)


class EspeakEngine(TTSEngine):
    """TTS engine using the eSpeak command-line tool.

    eSpeak is a lightweight, open-source speech synthesizer that supports
    many languages and voices. This adapter invokes eSpeak via subprocess
    and handles its command-line arguments for rate, pitch, and volume.
    """

    # eSpeak speed: words per minute (default ~175)
    DEFAULT_SPEED = 175
    # eSpeak pitch: 0-99 (default 50)
    DEFAULT_PITCH = 50
    # eSpeak amplitude: 0-200 (default 100)
    DEFAULT_AMPLITUDE = 100

    def __init__(self) -> None:
        """Initialize the eSpeak engine adapter."""
        super().__init__()
        self.name = "espeak"
        self._espeak_cmd = self._find_espeak()
        self._available = self.detect()

    def _find_espeak(self) -> Optional[str]:
        """Locate the eSpeak executable on the system.

        Checks for 'espeak-ng' first (newer version), then falls back
        to 'espeak'.

        Returns:
            Path to the eSpeak executable, or None if not found.
        """
        for cmd in ["espeak-ng", "espeak"]:
            path = shutil.which(cmd)
            if path:
                logger.debug(f"Found eSpeak at: {path}")
                return path
        return None

    def detect(self) -> bool:
        """Check if eSpeak is available on the system.

        Returns:
            bool: True if eSpeak executable was found.
        """
        if self._espeak_cmd:
            self._available = True
            logger.info(f"eSpeak engine detected: {self._espeak_cmd}")
            return True
        self._available = False
        logger.debug("eSpeak is not installed")
        return False

    def _build_args(self, text: str, output_path: Optional[str] = None) -> List[str]:
        """Build the eSpeak command-line argument list.

        Args:
            text: The text to synthesize.
            output_path: If provided, write audio to this file instead of speaking.

        Returns:
            List of command-line arguments for the eSpeak subprocess.
        """
        args = [self._espeak_cmd]

        # Speed (words per minute)
        speed = int(self.DEFAULT_SPEED * self.rate)
        args.extend(["-s", str(speed)])

        # Pitch (0-99 scale)
        pitch = int(self.DEFAULT_PITCH * self.pitch)
        pitch = max(0, min(99, pitch))
        args.extend(["-p", str(pitch)])

        # Amplitude / volume (0-200 scale)
        amplitude = int(self.DEFAULT_AMPLITUDE * self.volume)
        amplitude = max(0, min(200, amplitude))
        args.extend(["-a", str(amplitude)])

        # Voice selection
        if self.voice_id:
            args.extend(["-v", self.voice_id])

        # Output to file
        if output_path:
            args.extend(["-w", output_path])

        # The text to speak (passed as final argument)
        args.append(text)

        return args

    def speak(self, text: str) -> bool:
        """Speak text aloud using eSpeak.

        Args:
            text: The text to speak.

        Returns:
            bool: True if speech was successful.
        """
        if not self._available:
            logger.error("Cannot speak: eSpeak not available")
            return False
        try:
            args = self._build_args(text)
            result = subprocess.run(
                args,
                capture_output=True,
                timeout=60,
            )
            if result.returncode == 0:
                logger.info("Speech completed via eSpeak")
                return True
            else:
                logger.error(f"eSpeak failed: {result.stderr.decode('utf-8', errors='replace')}")
                return False
        except FileNotFoundError:
            logger.error("eSpeak executable not found")
            self._available = False
            return False
        except subprocess.TimeoutExpired:
            logger.error("eSpeak timed out")
            return False
        except Exception as e:
            logger.error(f"eSpeak speak failed: {e}")
            return False

    def synthesize_to_file(self, text: str, output_path: str,
                           format: str = "wav") -> bool:
        """Synthesize text and save to a WAV file using eSpeak.

        eSpeak natively writes WAV files. For other formats, use the
        audio converter module.

        Args:
            text: The text to synthesize.
            output_path: Destination file path.
            format: Output format (only "wav" is natively supported).

        Returns:
            bool: True if file was written successfully.
        """
        if not self._available:
            logger.error("Cannot synthesize: eSpeak not available")
            return False
        try:
            args = self._build_args(text, output_path=output_path)
            result = subprocess.run(
                args,
                capture_output=True,
                timeout=120,
            )
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(f"Audio saved to {output_path} via eSpeak")
                return True
            else:
                logger.error(f"eSpeak file output failed: {result.stderr.decode('utf-8', errors='replace')}")
                return False
        except Exception as e:
            logger.error(f"eSpeak synthesize_to_file failed: {e}")
            return False

    def get_voices(self) -> List[Dict[str, Any]]:
        """List available eSpeak voices.

        Parses the output of 'espeak --voices' to extract voice information.

        Returns:
            List of voice dictionaries with id, name, and language.
        """
        if not self._available:
            return []
        try:
            result = subprocess.run(
                [self._espeak_cmd, "--voices"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return []

            voices = []
            for line in result.stdout.strip().split("\n")[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 5:
                    lang = parts[1] if len(parts) > 1 else "unknown"
                    voice_name = " ".join(parts[4:]) if len(parts) > 4 else parts[-1]
                    voices.append({
                        "id": lang,
                        "name": voice_name,
                        "lang": lang,
                    })
            return voices
        except Exception as e:
            logger.error(f"Failed to get eSpeak voices: {e}")
            return []

    def set_voice(self, voice_id: str) -> bool:
        """Select an eSpeak voice by language code.

        Args:
            voice_id: Language/voice identifier (e.g., 'en', 'zh').

        Returns:
            bool: True if the voice ID was accepted.
        """
        self.voice_id = voice_id
        logger.info(f"eSpeak voice set to {voice_id}")
        return True
