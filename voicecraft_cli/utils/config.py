"""
Configuration management module.

Manages VoiceCraft-CLI configuration with support for:
- Default configuration values
- Configuration file loading (INI-style)
- Environment variable overrides
- Runtime configuration updates
"""

import os
import configparser
from typing import Any, Dict, Optional

from voicecraft_cli.utils.logger import get_logger

logger = get_logger(__name__)

# Default configuration values
DEFAULTS = {
    "engine": {
        "name": "auto",          # Auto-detect best engine
        "rate": "1.0",           # Speech rate multiplier
        "volume": "1.0",         # Volume (0.0 - 1.0)
        "pitch": "1.0",          # Pitch multiplier
        "voice": "",             # Voice ID (empty = default)
    },
    "audio": {
        "format": "wav",         # Output format
        "sample_rate": "22050",  # Sample rate in Hz
        "sample_width": "2",     # Bytes per sample
        "channels": "1",         # Number of channels
    },
    "output": {
        "directory": ".",        # Default output directory
        "filename_template": "output_{index:04d}",  # Filename template
    },
    "logging": {
        "level": "WARNING",      # Log level
        "file": "",              # Log file path (empty = stderr only)
    },
}


class Config:
    """Configuration manager for VoiceCraft-CLI.

    Manages hierarchical configuration with defaults, file-based
    overrides, and environment variable support.

    Configuration lookup order (highest priority first):
        1. Environment variables (VOICECRAFT_<SECTION>_<KEY>)
        2. Configuration file values
        3. Default values

    Usage:
        config = Config()
        config.load_file("~/.voicecraft.ini")
        rate = config.get("engine", "rate", default=1.0)
    """

    # Environment variable prefix
    ENV_PREFIX = "VOICECRAFT_"

    def __init__(self) -> None:
        """Initialize configuration with default values."""
        self._data: Dict[str, Dict[str, str]] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default configuration values."""
        for section, values in DEFAULTS.items():
            self._data[section] = dict(values)

    def load_file(self, filepath: str) -> bool:
        """Load configuration from an INI-style file.

        Args:
            filepath: Path to the configuration file.

        Returns:
            True if the file was loaded successfully.
        """
        # Expand ~ and environment variables in path
        filepath = os.path.expanduser(filepath)
        filepath = os.path.expandvars(filepath)

        if not os.path.isfile(filepath):
            logger.debug(f"Config file not found: {filepath}")
            return False

        try:
            parser = configparser.ConfigParser()
            parser.read(filepath, encoding="utf-8")

            for section in parser.sections():
                if section not in self._data:
                    self._data[section] = {}
                for key, value in parser.items(section):
                    self._data[section][key] = value

            logger.info(f"Loaded configuration from {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to load config file {filepath}: {e}")
            return False

    def get(self, section: str, key: str, default: Any = None) -> str:
        """Get a configuration value.

        Checks environment variables first, then file values,
        then defaults.

        Args:
            section: Configuration section name.
            key: Configuration key name.
            default: Default value if not found.

        Returns:
            Configuration value as string.
        """
        # Check environment variable first
        env_key = f"{self.ENV_PREFIX}{section.upper()}_{key.upper()}"
        env_value = os.environ.get(env_key)
        if env_value is not None:
            return env_value

        # Check loaded configuration
        if section in self._data and key in self._data[section]:
            return self._data[section][key]

        # Return default
        if default is not None:
            return str(default)

        return ""

    def get_float(self, section: str, key: str, default: float = 0.0) -> float:
        """Get a configuration value as float.

        Args:
            section: Configuration section name.
            key: Configuration key name.
            default: Default value if conversion fails.

        Returns:
            Configuration value as float.
        """
        try:
            return float(self.get(section, key, str(default)))
        except (ValueError, TypeError):
            return default

    def get_int(self, section: str, key: str, default: int = 0) -> int:
        """Get a configuration value as integer.

        Args:
            section: Configuration section name.
            key: Configuration key name.
            default: Default value if conversion fails.

        Returns:
            Configuration value as integer.
        """
        try:
            return int(self.get(section, key, str(default)))
        except (ValueError, TypeError):
            return default

    def set(self, section: str, key: str, value: str) -> None:
        """Set a configuration value at runtime.

        Args:
            section: Configuration section name.
            key: Configuration key name.
            value: Value to set.
        """
        if section not in self._data:
            self._data[section] = {}
        self._data[section][key] = value

    def get_section(self, section: str) -> Dict[str, str]:
        """Get all values in a configuration section.

        Args:
            section: Configuration section name.

        Returns:
            Dictionary of key-value pairs.
        """
        return dict(self._data.get(section, {}))

    def save_file(self, filepath: str) -> bool:
        """Save current configuration to an INI-style file.

        Args:
            filepath: Output file path.

        Returns:
            True if the file was saved successfully.
        """
        filepath = os.path.expanduser(filepath)
        filepath = os.path.expandvars(filepath)

        try:
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)

            parser = configparser.ConfigParser()
            for section, values in self._data.items():
                parser[section] = values

            with open(filepath, "w", encoding="utf-8") as f:
                parser.write(f)

            logger.info(f"Configuration saved to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to save config file {filepath}: {e}")
            return False

    def get_all(self) -> Dict[str, Dict[str, str]]:
        """Get the complete configuration dictionary.

        Returns:
            Nested dictionary of all configuration values.
        """
        return dict(self._data)
