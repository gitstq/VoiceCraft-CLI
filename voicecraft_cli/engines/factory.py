"""
TTS Engine Factory.

Automatically discovers available TTS engines on the current system
and provides the best available engine based on a priority order.
"""

import sys
from typing import List, Optional, Type, Dict, Any

from voicecraft_cli.engines.base import TTSEngine
from voicecraft_cli.utils.logger import get_logger

logger = get_logger(__name__)


class EngineFactory:
    """Factory for creating and managing TTS engine instances.

    The factory maintains a registry of engine classes and automatically
    detects which ones are available. Engines are prioritized in the
    following order:
        1. pyttsx3 (cross-platform, most feature-rich)
        2. espeak (Linux, lightweight)
        3. system (macOS say, Windows SAPI, Linux spd-say)

    Usage:
        factory = EngineFactory()
        engine = factory.get_engine()       # Best available
        engine = factory.get_engine("espeak")  # Specific engine
        voices = factory.list_all_voices()  # All voices from all engines
    """

    # Priority order: higher index = lower priority
    ENGINE_REGISTRY: List[Dict[str, Any]] = [
        {"name": "pyttsx3", "module": "voicecraft_cli.engines.pyttsx3_engine", "class": "Pyttsx3Engine"},
        {"name": "espeak", "module": "voicecraft_cli.engines.espeak_engine", "class": "EspeakEngine"},
        {"name": "system", "module": "voicecraft_cli.engines.system_engine", "class": "SystemEngine"},
    ]

    def __init__(self) -> None:
        """Initialize the factory and discover available engines."""
        self._engines: Dict[str, TTSEngine] = {}
        self._discover_engines()

    def _discover_engines(self) -> None:
        """Scan the registry and instantiate all available engines.

        Each engine class is imported and instantiated. Engines that
        report themselves as unavailable are still stored but marked.
        """
        for entry in self.ENGINE_REGISTRY:
            try:
                module = __import__(entry["module"], fromlist=[entry["class"]])
                engine_class = getattr(module, entry["class"])
                engine = engine_class()
                self._engines[entry["name"]] = engine
                status = "available" if engine.available else "not available"
                logger.info(f"Engine '{entry['name']}': {status}")
            except Exception as e:
                logger.warning(f"Failed to load engine '{entry['name']}': {e}")

    def get_engine(self, name: Optional[str] = None) -> Optional[TTSEngine]:
        """Get a TTS engine instance.

        If no name is specified, returns the first available engine
        based on priority order. If a name is given, returns that
        specific engine (or None if not found/available).

        Args:
            name: Optional engine name ('pyttsx3', 'espeak', 'system').

        Returns:
            A TTSEngine instance, or None if no suitable engine found.
        """
        if name:
            engine = self._engines.get(name)
            if engine and engine.available:
                return engine
            logger.warning(f"Engine '{name}' is not available")
            return None

        # Return first available engine by priority
        for entry in self.ENGINE_REGISTRY:
            engine = self._engines.get(entry["name"])
            if engine and engine.available:
                logger.info(f"Selected engine: {entry['name']}")
                return engine

        logger.warning("No TTS engines available on this system")
        return None

    def list_engines(self) -> List[Dict[str, Any]]:
        """List all registered engines with their availability status.

        Returns:
            List of dictionaries with 'name' and 'available' keys.
        """
        result = []
        for entry in self.ENGINE_REGISTRY:
            engine = self._engines.get(entry["name"])
            result.append({
                "name": entry["name"],
                "available": engine.available if engine else False,
            })
        return result

    def list_all_voices(self) -> Dict[str, List[Dict[str, Any]]]:
        """List voices from all available engines.

        Returns:
            Dictionary mapping engine names to their voice lists.
        """
        all_voices = {}
        for name, engine in self._engines.items():
            if engine.available:
                voices = engine.get_voices()
                if voices:
                    all_voices[name] = voices
        return all_voices

    def get_available_engine_names(self) -> List[str]:
        """Get names of all available engines.

        Returns:
            List of engine name strings.
        """
        return [
            name for name, engine in self._engines.items()
            if engine.available
        ]
