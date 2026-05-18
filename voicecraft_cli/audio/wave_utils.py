"""
WAV file utilities module.

Provides high-level operations for WAV files using Python's built-in
wave module. Includes reading, writing, appending, and metadata
extraction capabilities.
"""

import wave
import os
import io
from typing import Optional, Tuple, List, Dict, Any

from voicecraft_cli.utils.logger import get_logger

logger = get_logger(__name__)


class WaveUtils:
    """Utility class for WAV file operations.

    Wraps Python's wave module with a more convenient interface for
    common operations like reading, writing, concatenating, and
    extracting metadata from WAV files.
    """

    def __init__(self) -> None:
        """Initialize the WAV utilities."""
        pass

    def read_wav(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Read a WAV file and return its data and metadata.

        Args:
            filepath: Path to the WAV file.

        Returns:
            Dictionary containing:
                - 'samples': List of integer PCM samples.
                - 'params': Dict with nchannels, sampwidth, framerate, etc.
                - 'duration': Duration in seconds.
            Returns None if the file cannot be read.
        """
        try:
            with wave.open(filepath, "rb") as wf:
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()
                raw_data = wf.readframes(n_frames)

            # Convert raw bytes to samples
            samples = self._bytes_to_samples(raw_data, sampwidth)

            duration = n_frames / framerate if framerate > 0 else 0.0

            info = {
                "samples": samples,
                "params": {
                    "nchannels": n_channels,
                    "sampwidth": sampwidth,
                    "framerate": framerate,
                    "nframes": n_frames,
                    "comptype": wf.getcomptype(),
                    "compname": wf.getcompname(),
                },
                "duration": duration,
                "filepath": filepath,
            }

            logger.info(
                f"Read WAV: {filepath} ({duration:.2f}s, {framerate}Hz, "
                f"{sampwidth * 8}-bit, {n_channels}ch)"
            )
            return info

        except Exception as e:
            logger.error(f"Failed to read WAV file {filepath}: {e}")
            return None

    def write_wav(self, filepath: str, samples: List[int],
                  sample_rate: int = 22050, sample_width: int = 2,
                  channels: int = 1) -> bool:
        """Write PCM samples to a WAV file.

        Args:
            filepath: Output file path.
            samples: List of integer PCM samples.
            sample_rate: Sample rate in Hz.
            sample_width: Bytes per sample (1, 2, or 4).
            channels: Number of audio channels.

        Returns:
            True if the file was written successfully.
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)

            raw_data = self._samples_to_bytes(samples, sample_width)

            with wave.open(filepath, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(sample_rate)
                wf.writeframes(raw_data)

            duration = len(samples) / sample_rate if sample_rate > 0 else 0.0
            logger.info(
                f"Wrote WAV: {filepath} ({duration:.2f}s, {sample_rate}Hz, "
                f"{sample_width * 8}-bit, {channels}ch)"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to write WAV file {filepath}: {e}")
            return False

    def concatenate_wav_files(self, input_paths: List[str],
                              output_path: str) -> bool:
        """Concatenate multiple WAV files into one.

        All input files must have the same sample rate, bit depth,
        and channel count. If they differ, the parameters of the
        first file are used and others are converted.

        Args:
            input_paths: List of input WAV file paths.
            output_path: Output WAV file path.

        Returns:
            True if concatenation was successful.
        """
        if not input_paths:
            logger.error("No input files provided for concatenation")
            return False

        all_samples = []
        params = None

        for path in input_paths:
            info = self.read_wav(path)
            if info is None:
                logger.warning(f"Skipping unreadable file: {path}")
                continue

            if params is None:
                params = info["params"]

            all_samples.extend(info["samples"])

        if not all_samples or params is None:
            logger.error("No valid audio data to concatenate")
            return False

        return self.write_wav(
            output_path,
            all_samples,
            sample_rate=params["framerate"],
            sample_width=params["sampwidth"],
            channels=params["nchannels"],
        )

    def get_wav_info(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Extract metadata from a WAV file without reading all samples.

        Args:
            filepath: Path to the WAV file.

        Returns:
            Dictionary with file metadata, or None if unreadable.
        """
        try:
            with wave.open(filepath, "rb") as wf:
                n_frames = wf.getnframes()
                framerate = wf.getframerate()
                duration = n_frames / framerate if framerate > 0 else 0.0

                # Calculate file size
                file_size = os.path.getsize(filepath)

                return {
                    "filepath": filepath,
                    "file_size_bytes": file_size,
                    "file_size_mb": round(file_size / (1024 * 1024), 2),
                    "nchannels": wf.getnchannels(),
                    "sampwidth": wf.getsampwidth(),
                    "bit_depth": wf.getsampwidth() * 8,
                    "framerate": framerate,
                    "nframes": n_frames,
                    "duration": round(duration, 3),
                    "comptype": wf.getcomptype(),
                    "compname": wf.getcompname(),
                }
        except Exception as e:
            logger.error(f"Failed to get WAV info for {filepath}: {e}")
            return None

    def _bytes_to_samples(self, data: bytes, sample_width: int) -> List[int]:
        """Convert raw WAV bytes to a list of integer samples.

        Args:
            data: Raw PCM byte data from wave.readframes().
            sample_width: Bytes per sample.

        Returns:
            List of integer sample values.
        """
        import struct

        if sample_width == 1:
            # 8-bit WAV is unsigned (0-255), convert to signed (-128 to 127)
            return [b - 128 for b in data]
        elif sample_width == 2:
            fmt = "<" + "h" * (len(data) // 2)
            return list(struct.unpack(fmt, data))
        elif sample_width == 4:
            fmt = "<" + "i" * (len(data) // 4)
            return list(struct.unpack(fmt, data))
        else:
            logger.warning(f"Unsupported sample width: {sample_width}")
            return []

    def _samples_to_bytes(self, samples: List[int], sample_width: int) -> bytes:
        """Convert a list of integer samples to raw WAV bytes.

        Args:
            samples: List of integer sample values.
            sample_width: Bytes per sample.

        Returns:
            Raw PCM byte data suitable for wave.writeframes().
        """
        import struct

        if sample_width == 1:
            # 8-bit WAV is unsigned
            return bytes(max(0, min(255, s + 128)) for s in samples)
        elif sample_width == 2:
            fmt = "<" + "h" * len(samples)
            return struct.pack(fmt, *samples)
        elif sample_width == 4:
            fmt = "<" + "i" * len(samples)
            return struct.pack(fmt, *samples)
        else:
            logger.warning(f"Unsupported sample width: {sample_width}")
            return b""
