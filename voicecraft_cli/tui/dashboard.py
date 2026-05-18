"""
TUI Dashboard module.

Provides a simple terminal-based dashboard for monitoring TTS engine
status, batch synthesis progress, and audio information. Uses ANSI
escape codes for terminal formatting (no curses dependency required).

The dashboard is designed to be lightweight and work in any terminal
that supports basic ANSI escape sequences.
"""

import sys
import os
import time
import threading
from typing import Optional, Dict, Any, List

from voicecraft_cli.utils.logger import get_logger

logger = get_logger(__name__)


class Dashboard:
    """Terminal-based dashboard for VoiceCraft-CLI.

    Displays real-time information about:
    - Active TTS engine and its configuration
    - Batch synthesis progress (progress bar, task counts)
    - Audio file information
    - System status

    Uses ANSI escape codes for colors and cursor control.
    Falls back to plain text on terminals without ANSI support.

    Usage:
        dash = Dashboard()
        dash.set_engine_info({"name": "espeak", "available": True})
        dash.update_progress(5, 10)
        dash.render()
    """

    # ANSI color codes
    COLORS = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "dim": "\033[2m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "bg_blue": "\033[44m",
        "bg_green": "\033[42m",
        "bg_red": "\033[41m",
    }

    # Progress bar characters
    BAR_FILLED = "="
    BAR_EMPTY = "-"
    BAR_HEAD = ">"
    BAR_WIDTH = 40

    def __init__(self, use_colors: bool = True) -> None:
        """Initialize the dashboard.

        Args:
            use_colors: Whether to use ANSI color codes (auto-detected if None).
        """
        if use_colors is None:
            use_colors = self._detect_color_support()

        self.use_colors = use_colors
        self._engine_info: Dict[str, Any] = {}
        self._progress_total: int = 0
        self._progress_completed: int = 0
        self._progress_failed: int = 0
        self._progress_current: str = ""
        self._audio_info: Dict[str, Any] = {}
        self._status_message: str = "Ready"
        self._status_type: str = "info"  # info, success, warning, error
        self._lines_rendered: int = 0
        self._lock = threading.Lock()

    def _detect_color_support(self) -> bool:
        """Detect whether the terminal supports ANSI colors.

        Returns:
            True if colors are likely supported.
        """
        # Check for NO_COLOR environment variable
        if os.environ.get("NO_COLOR"):
            return False

        # Check if stdout is a TTY
        if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
            return True

        # Check common terminal emulators
        term = os.environ.get("TERM", "")
        if term in ("dumb", ""):
            return False

        return True

    def _color(self, text: str, color_name: str) -> str:
        """Apply a color to text.

        Args:
            text: The text to colorize.
            color_name: Name of the color from COLORS dict.

        Returns:
            Colorized text string (or plain text if colors disabled).
        """
        if not self.use_colors:
            return text
        code = self.COLORS.get(color_name, "")
        reset = self.COLORS["reset"]
        return f"{code}{text}{reset}"

    def set_engine_info(self, info: Dict[str, Any]) -> None:
        """Set the TTS engine information to display.

        Args:
            info: Dictionary with engine details (name, available, rate, etc.).
        """
        with self._lock:
            self._engine_info = info

    def update_progress(self, completed: int, total: int,
                        failed: int = 0, current: str = "") -> None:
        """Update the batch progress display.

        Args:
            completed: Number of completed tasks.
            total: Total number of tasks.
            failed: Number of failed tasks.
            current: Description of the currently processing task.
        """
        with self._lock:
            self._progress_completed = completed
            self._progress_total = total
            self._progress_failed = failed
            self._progress_current = current

    def set_audio_info(self, info: Dict[str, Any]) -> None:
        """Set audio file information to display.

        Args:
            info: Dictionary with audio details (duration, sample_rate, etc.).
        """
        with self._lock:
            self._audio_info = info

    def set_status(self, message: str, status_type: str = "info") -> None:
        """Set the status bar message.

        Args:
            message: Status message text.
            status_type: Type of status ('info', 'success', 'warning', 'error').
        """
        with self._lock:
            self._status_message = message
            self._status_type = status_type

    def _build_progress_bar(self, percent: float) -> str:
        """Build a text-based progress bar.

        Args:
            percent: Progress percentage (0.0 - 100.0).

        Returns:
            String representation of the progress bar.
        """
        width = self.BAR_WIDTH
        filled = int(width * percent / 100)

        if filled >= width:
            bar = self.BAR_FILLED * width
        elif filled > 0:
            bar = self.BAR_FILLED * (filled - 1) + self.BAR_HEAD + self.BAR_EMPTY * (width - filled)
        else:
            bar = self.BAR_EMPTY * width

        return bar

    def _format_duration(self, seconds: float) -> str:
        """Format seconds into a human-readable duration string.

        Args:
            seconds: Duration in seconds.

        Returns:
            Formatted string (e.g., "1m 23s" or "45s").
        """
        if seconds < 60:
            return f"{seconds:.0f}s"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"

    def render(self) -> str:
        """Render the dashboard and return as a string.

        Returns:
            The rendered dashboard as a string.
        """
        with self._lock:
            lines = []
            lines.append(self._render_header())
            lines.append("")
            lines.append(self._render_engine_section())
            lines.append("")
            lines.append(self._render_progress_section())
            lines.append("")
            lines.append(self._render_audio_section())
            lines.append("")
            lines.append(self._render_status_bar())

            # Join and ensure no trailing whitespace on lines
            return "\n".join(line.rstrip() for line in lines)

    def _render_header(self) -> str:
        """Render the dashboard header.

        Returns:
            Header string.
        """
        title = self._color(" VoiceCraft-CLI Dashboard ", "bg_blue") + " " + self._color("white", "white")
        version = self._color("v1.0.0", "dim")
        return f"  {title} {version}"

    def _render_engine_section(self) -> str:
        """Render the engine information section.

        Returns:
            Engine info string.
        """
        label = self._color("  [Engine]", "bold")
        if not self._engine_info:
            return f"{label}  No engine information available"

        info = self._engine_info
        name = info.get("name", "unknown")
        available = info.get("available", False)

        if available:
            status = self._color("ONLINE", "green")
        else:
            status = self._color("OFFLINE", "red")

        rate = info.get("rate", 1.0)
        volume = info.get("volume", 1.0)
        pitch = info.get("pitch", 1.0)
        voice = info.get("voice_id", "default")

        lines = [
            f"{label}  {self._color(name, 'cyan')} [{status}]",
            f"          Rate: {rate:.1f}x  |  Volume: {volume:.0%}  |  Pitch: {pitch:.1f}x  |  Voice: {voice}",
        ]
        return "\n".join(lines)

    def _render_progress_section(self) -> str:
        """Render the batch progress section.

        Returns:
            Progress section string.
        """
        label = self._color("  [Progress]", "bold")

        if self._progress_total == 0:
            return f"{label}  No tasks in queue"

        percent = (self._progress_completed + self._progress_failed) / self._progress_total * 100
        bar = self._build_progress_bar(percent)

        # Color the progress bar
        if percent >= 100:
            bar = self._color(bar, "green")
        elif self._progress_failed > 0:
            bar = self._color(bar, "yellow")
        else:
            bar = self._color(bar, "cyan")

        completed_str = self._color(str(self._progress_completed), "green")
        failed_str = self._color(str(self._progress_failed), "red") if self._progress_failed > 0 else "0"
        total_str = str(self._progress_total)

        lines = [
            f"{label}  [{bar}] {percent:.0f}%",
            f"          Completed: {completed_str}  |  Failed: {failed_str}  |  Total: {total_str}",
        ]

        if self._progress_current:
            lines.append(f"          Current: {self._color(self._progress_current, 'dim')}")

        return "\n".join(lines)

    def _render_audio_section(self) -> str:
        """Render the audio information section.

        Returns:
            Audio info string.
        """
        label = self._color("  [Audio]", "bold")

        if not self._audio_info:
            return f"{label}  No audio information available"

        info = self._audio_info
        parts = []

        if "duration" in info:
            parts.append(f"Duration: {self._format_duration(info['duration'])}")

        if "sample_rate" in info:
            parts.append(f"Rate: {info['sample_rate']}Hz")

        if "bit_depth" in info:
            parts.append(f"Depth: {info['bit_depth']}bit")

        if "nchannels" in info:
            ch = "Mono" if info["nchannels"] == 1 else f"{info['nchannels']}ch"
            parts.append(f"Channels: {ch}")

        if "file_size_mb" in info:
            parts.append(f"Size: {info['file_size_mb']}MB")

        if "peak_db" in info:
            parts.append(f"Peak: {info['peak_db']}dB")

        return f"{label}  {'  |  '.join(parts)}"

    def _render_status_bar(self) -> str:
        """Render the status bar at the bottom.

        Returns:
            Status bar string.
        """
        color_map = {
            "info": "blue",
            "success": "green",
            "warning": "yellow",
            "error": "red",
        }
        color = color_map.get(self._status_type, "white")
        msg = self._color(f"  > {self._status_message}", color)
        return msg

    def print_dashboard(self) -> None:
        """Render and print the dashboard to stdout."""
        output = self.render()
        print(output)

    def print_simple_progress(self, completed: int, total: int,
                              failed: int = 0) -> None:
        """Print a simple single-line progress update.

        Useful for non-interactive contexts where a full dashboard
        is too verbose.

        Args:
            completed: Number of completed tasks.
            total: Total number of tasks.
            failed: Number of failed tasks.
        """
        percent = (completed + failed) / total * 100 if total > 0 else 0
        bar = self._build_progress_bar(percent)

        status = f"\r  [{bar}] {percent:.0f}% ({completed}/{total}"
        if failed > 0:
            status += f", {failed} failed"
        status += ")"

        print(status, end="", flush=True)

        if completed + failed >= total:
            print()  # New line when complete

    def print_engine_list(self, engines: List[Dict[str, Any]]) -> None:
        """Print a formatted list of available engines.

        Args:
            engines: List of engine info dictionaries.
        """
        print(self._color("  Available TTS Engines:", "bold"))
        for eng in engines:
            name = eng.get("name", "unknown")
            available = eng.get("available", False)
            if available:
                marker = self._color("[OK]", "green")
            else:
                marker = self._color("[--]", "dim")
            print(f"    {marker} {name}")

    def print_voice_list(self, voices: Dict[str, List[Dict[str, Any]]]) -> None:
        """Print a formatted list of available voices.

        Args:
            voices: Dictionary mapping engine names to voice lists.
        """
        print(self._color("  Available Voices:", "bold"))
        for engine_name, voice_list in voices.items():
            print(f"    {self._color(engine_name, 'cyan')}:")
            for v in voice_list[:10]:  # Limit to 10 voices per engine
                vid = v.get("id", "?")
                vname = v.get("name", "Unknown")
                vlang = v.get("lang", "?")
                print(f"      - {vid}: {vname} ({vlang})")
            if len(voice_list) > 10:
                print(f"      ... and {len(voice_list) - 10} more")
