"""
System TTS engine adapter.

Interfaces with native OS speech synthesis commands:
- macOS: 'say' command (NSSpeechSynthesizer)
- Windows: PowerShell SAPI COM object via 'powershell'
- Linux: Falls back to 'spd-say' (speech-dispatcher)

This engine requires no Python packages -- only system utilities.
"""

import os
import sys
import subprocess
import shutil
import tempfile
from typing import List, Optional, Dict, Any

from voicecraft_cli.engines.base import TTSEngine
from voicecraft_cli.utils.logger import get_logger

logger = get_logger(__name__)


class SystemEngine(TTSEngine):
    """TTS engine using native OS speech commands.

    Automatically detects the platform and uses the appropriate
    system command for speech synthesis.
    """

    def __init__(self) -> None:
        """Initialize the system engine adapter."""
        super().__init__()
        self.name = "system"
        self._platform = sys.platform
        self._cmd = self._detect_command()
        self._available = self.detect()

    def _detect_command(self) -> Optional[str]:
        """Detect the appropriate system TTS command.

        Returns:
            Path to the system TTS command, or None if unavailable.
        """
        if self._platform == "darwin":
            # macOS 'say' command
            path = shutil.which("say")
            if path:
                return path
        elif self._platform == "win32":
            # Windows PowerShell with SAPI
            path = shutil.which("powershell")
            if path:
                return path
        else:
            # Linux: try speech-dispatcher
            path = shutil.which("spd-say")
            if path:
                return path
        return None

    def detect(self) -> bool:
        """Check if a system TTS command is available.

        Returns:
            bool: True if a system command was found.
        """
        if self._cmd:
            self._available = True
            logger.info(f"System TTS engine detected: {self._cmd} ({self._platform})")
            return True
        self._available = False
        logger.debug("No system TTS command found")
        return False

    def _build_say_args(self, text: str, output_path: Optional[str] = None) -> List[str]:
        """Build arguments for the macOS 'say' command.

        Args:
            text: Text to speak.
            output_path: Optional file output path.

        Returns:
            List of command-line arguments.
        """
        args = [self._cmd]

        # Rate: 'say' uses words per minute (default ~175)
        rate = int(175 * self.rate)
        args.extend(["-r", str(rate)])

        # Volume: 'say' uses 0.0-1.0 (we already use this scale)
        args.extend(["-v", f"{self.volume:.1f}"])

        # Voice selection
        if self.voice_id:
            args.extend(["-v", self.voice_id])

        # Output to file
        if output_path:
            args.extend(["-o", output_path])

        args.append(text)
        return args

    def _build_spd_say_args(self, text: str) -> List[str]:
        """Build arguments for the Linux 'spd-say' command.

        Args:
            text: Text to speak.

        Returns:
            List of command-line arguments.
        """
        args = [self._cmd]

        # Rate: -i for integer rate (-100 to 100, 0 = normal)
        rate = int((self.rate - 1.0) * 100)
        args.extend(["-i", str(rate)])

        # Volume: -P for percentage (0-100)
        volume = int(self.volume * 100)
        args.extend(["-P", str(volume)])

        # Pitch: -p for percentage (-100 to 100, 0 = normal)
        pitch = int((self.pitch - 1.0) * 100)
        args.extend(["-p", str(pitch)])

        # Voice / language
        if self.voice_id:
            args.extend(["-l", self.voice_id])

        args.append(text)
        return args

    def _build_powershell_args(self, text: str, output_path: Optional[str] = None) -> List[str]:
        """Build arguments for Windows PowerShell SAPI.

        Args:
            text: Text to speak.
            output_path: Not supported on Windows via this method.

        Returns:
            List of command-line arguments.
        """
        # Escape single quotes in text
        escaped = text.replace("'", "''")
        rate = int(self.rate * 100)
        volume = int(self.volume * 100)

        script = (
            f"Add-Type -AssemblyName System.Speech; "
            f"$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$synth.Rate = {rate}; "
            f"$synth.Volume = {volume}; "
            f"$synth.Speak('{escaped}')"
        )

        return [
            self._cmd,
            "-NoProfile",
            "-Command",
            script,
        ]

    def speak(self, text: str) -> bool:
        """Speak text aloud using the system TTS command.

        Args:
            text: The text to speak.

        Returns:
            bool: True if speech was successful.
        """
        if not self._available:
            logger.error("Cannot speak: system TTS not available")
            return False
        try:
            if self._platform == "darwin":
                args = self._build_say_args(text)
            elif self._platform == "win32":
                args = self._build_powershell_args(text)
            else:
                args = self._build_spd_say_args(text)

            result = subprocess.run(
                args,
                capture_output=True,
                timeout=120,
            )
            if result.returncode == 0:
                logger.info("Speech completed via system engine")
                return True
            else:
                logger.error(
                    f"System TTS failed: {result.stderr.decode('utf-8', errors='replace')}"
                )
                return False
        except Exception as e:
            logger.error(f"System TTS speak failed: {e}")
            return False

    def synthesize_to_file(self, text: str, output_path: str,
                           format: str = "wav") -> bool:
        """Synthesize text and save to an audio file.

        Only macOS 'say' supports direct file output. On other platforms,
        this method is not supported.

        Args:
            text: The text to synthesize.
            output_path: Destination file path.
            format: Output format (only "wav" supported on macOS).

        Returns:
            bool: True if file was written successfully.
        """
        if not self._available:
            logger.error("Cannot synthesize: system TTS not available")
            return False

        if self._platform == "darwin":
            try:
                args = self._build_say_args(text, output_path=output_path)
                result = subprocess.run(
                    args,
                    capture_output=True,
                    timeout=120,
                )
                if result.returncode == 0 and os.path.exists(output_path):
                    logger.info(f"Audio saved to {output_path} via macOS say")
                    return True
                else:
                    logger.error("macOS say file output failed")
                    return False
            except Exception as e:
                logger.error(f"macOS say synthesize_to_file failed: {e}")
                return False
        else:
            logger.warning(
                "File output is only supported on macOS with 'say' command. "
                "Use pyttsx3 or espeak for file output on other platforms."
            )
            return False

    def get_voices(self) -> List[Dict[str, Any]]:
        """List available system voices.

        Returns:
            List of voice dictionaries.
        """
        if not self._available:
            return []

        voices = []

        if self._platform == "darwin":
            try:
                result = subprocess.run(
                    [self._cmd, "-v", "?"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split("\n"):
                        parts = line.strip().split(None, 2)
                        if len(parts) >= 2:
                            voices.append({
                                "id": parts[0],
                                "name": parts[1],
                                "lang": parts[0].split("_")[0] if "_" in parts[0] else parts[0],
                            })
            except Exception as e:
                logger.error(f"Failed to get macOS voices: {e}")

        elif self._platform == "win32":
            try:
                script = (
                    "Add-Type -AssemblyName System.Speech; "
                    "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    "$synth.GetInstalledVoices() | "
                    "ForEach-Object { $_.VoiceInfo.Name + '|' + $_.VoiceInfo.Culture.Name }"
                )
                result = subprocess.run(
                    [self._cmd, "-NoProfile", "-Command", script],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split("\n"):
                        if "|" in line:
                            name, lang = line.split("|", 1)
                            voices.append({
                                "id": name.strip(),
                                "name": name.strip(),
                                "lang": lang.strip(),
                            })
            except Exception as e:
                logger.error(f"Failed to get Windows voices: {e}")

        else:
            # spd-say does not have a simple voice listing command
            voices.append({
                "id": "default",
                "name": "Default (speech-dispatcher)",
                "lang": "en",
            })

        return voices

    def set_voice(self, voice_id: str) -> bool:
        """Select a system voice by its identifier.

        Args:
            voice_id: The voice identifier.

        Returns:
            bool: True if the voice ID was accepted.
        """
        self.voice_id = voice_id
        logger.info(f"System voice set to {voice_id}")
        return True
