"""
Abstract base class for all TTS engines.

Every engine implementation must inherit from TTSEngine and implement
all abstract methods. This ensures a uniform interface regardless of
the underlying speech synthesis backend.
"""

import abc
import os
from typing import List, Optional, Dict, Any


class TTSEngine(abc.ABC):
    """Abstract base class for Text-to-Speech engines.

    Subclasses must implement all abstract methods to provide a
    consistent interface for speech synthesis across different backends.

    Attributes:
        name (str): Human-readable engine name.
        rate (float): Speech rate multiplier (0.5 - 2.0, default 1.0).
        volume (float): Volume level (0.0 - 1.0, default 1.0).
        pitch (float): Pitch multiplier (0.5 - 2.0, default 1.0).
        voice_id (Optional[str]): Currently selected voice identifier.
    """

    def __init__(self) -> None:
        """Initialize the TTS engine with default parameters."""
        self.name: str = "base"
        self.rate: float = 1.0
        self.volume: float = 1.0
        self.pitch: float = 1.0
        self.voice_id: Optional[str] = None
        self._available: bool = False

    @property
    def available(self) -> bool:
        """Check if this engine is available on the current system.

        Returns:
            bool: True if the engine can be used, False otherwise.
        """
        return self._available

    @abc.abstractmethod
    def detect(self) -> bool:
        """Detect whether the engine backend is available.

        Returns:
            bool: True if the backend is installed and usable.
        """
        ...

    @abc.abstractmethod
    def speak(self, text: str) -> bool:
        """Speak the given text aloud through the audio output.

        Args:
            text: The text string to synthesize and speak.

        Returns:
            bool: True if synthesis succeeded, False otherwise.
        """
        ...

    @abc.abstractmethod
    def synthesize_to_file(self, text: str, output_path: str,
                           format: str = "wav") -> bool:
        """Synthesize text and save the audio to a file.

        Args:
            text: The text string to synthesize.
            output_path: Filesystem path for the output audio file.
            format: Output audio format (default "wav").

        Returns:
            bool: True if file was written successfully, False otherwise.
        """
        ...

    @abc.abstractmethod
    def get_voices(self) -> List[Dict[str, Any]]:
        """List all available voices for this engine.

        Returns:
            List of voice dictionaries, each containing at minimum:
                - 'id': Unique voice identifier string.
                - 'name': Human-readable voice name.
                - 'lang': Language code (e.g., 'en-US').
        """
        ...

    @abc.abstractmethod
    def set_voice(self, voice_id: str) -> bool:
        """Select a voice by its identifier.

        Args:
            voice_id: The voice identifier to activate.

        Returns:
            bool: True if the voice was set successfully, False otherwise.
        """
        ...

    def set_rate(self, rate: float) -> bool:
        """Set the speech rate.

        Args:
            rate: Speech rate multiplier (0.5 = half speed, 2.0 = double speed).

        Returns:
            bool: True if the rate was accepted.
        """
        self.rate = max(0.1, min(3.0, rate))
        return True

    def set_volume(self, volume: float) -> bool:
        """Set the output volume.

        Args:
            volume: Volume level from 0.0 (silent) to 1.0 (maximum).

        Returns:
            bool: True if the volume was accepted.
        """
        self.volume = max(0.0, min(1.0, volume))
        return True

    def set_pitch(self, pitch: float) -> bool:
        """Set the voice pitch.

        Args:
            pitch: Pitch multiplier (0.5 = low, 2.0 = high).

        Returns:
            bool: True if the pitch was accepted.
        """
        self.pitch = max(0.1, min(2.0, pitch))
        return True

    def get_info(self) -> Dict[str, Any]:
        """Get information about the current engine configuration.

        Returns:
            Dictionary containing engine name, availability, rate,
            volume, pitch, and selected voice.
        """
        return {
            "name": self.name,
            "available": self._available,
            "rate": self.rate,
            "volume": self.volume,
            "pitch": self.pitch,
            "voice_id": self.voice_id,
        }
