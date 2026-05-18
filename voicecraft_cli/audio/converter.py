"""
Audio format converter module.

Handles conversion between different audio formats. Since this project
has zero external dependencies, conversions are limited to formats
supported by Python's built-in wave module (WAV/PCM). The converter
also provides raw PCM data serialization utilities.
"""

import struct
import io
from typing import Optional, Tuple, List

from voicecraft_cli.utils.logger import get_logger

logger = get_logger(__name__)


class AudioConverter:
    """Audio format converter for PCM/WAV data.

    Supports conversion between different PCM bit depths, endianness,
    and channel layouts. All operations are pure Python using the
    struct module for binary data handling.
    """

    # PCM format constants
    PCM_S8 = 0       # 8-bit signed integer
    PCM_U8 = 1       # 8-bit unsigned integer
    PCM_S16LE = 2    # 16-bit signed, little-endian
    PCM_S16BE = 3    # 16-bit signed, big-endian
    PCM_S32LE = 4    # 32-bit signed, little-endian
    PCM_S32BE = 5    # 32-bit signed, big-endian
    PCM_F32LE = 6    # 32-bit float, little-endian
    PCM_F32BE = 7    # 32-bit float, big-endian

    # Format info: (struct format char, bytes per sample, signed)
    FORMAT_INFO = {
        PCM_S8:    ("b", 1, True),
        PCM_U8:    ("B", 1, False),
        PCM_S16LE: ("<h", 2, True),
        PCM_S16BE: (">h", 2, True),
        PCM_S32LE: ("<i", 4, True),
        PCM_S32BE: (">i", 4, True),
        PCM_F32LE: ("<f", 4, True),
        PCM_F32BE: (">f", 4, True),
    }

    def __init__(self) -> None:
        """Initialize the audio converter."""
        pass

    def bytes_to_samples(self, data: bytes, fmt: int = PCM_S16LE) -> List[int]:
        """Convert raw PCM bytes to a list of integer samples.

        Args:
            data: Raw PCM byte data.
            fmt: PCM format constant (default: 16-bit signed LE).

        Returns:
            List of integer sample values.
        """
        if fmt not in self.FORMAT_INFO:
            logger.error(f"Unsupported format: {fmt}")
            return []

        fmt_char, width, signed = self.FORMAT_INFO[fmt]
        if len(data) % width != 0:
            logger.warning("Data length is not aligned to sample width")

        samples = []
        for i in range(0, len(data) - width + 1, width):
            chunk = data[i:i + width]
            value = struct.unpack(fmt_char, chunk)[0]
            samples.append(int(value))

        return samples

    def samples_to_bytes(self, samples: List[int], fmt: int = PCM_S16LE) -> bytes:
        """Convert a list of integer samples to raw PCM bytes.

        Args:
            samples: List of integer sample values.
            fmt: PCM format constant (default: 16-bit signed LE).

        Returns:
            Raw PCM byte data.
        """
        if fmt not in self.FORMAT_INFO:
            logger.error(f"Unsupported format: {fmt}")
            return b""

        fmt_char, width, signed = self.FORMAT_INFO[fmt]
        result = bytearray()

        for s in samples:
            # Clamp value to valid range for the format
            if width == 1:
                s = max(-128 if signed else 0, min(127 if signed else 255, s))
            elif width == 2:
                s = max(-32768, min(32767, s))
            elif width == 4:
                s = max(-2147483648, min(2147483647, s))
            result.extend(struct.pack(fmt_char, s))

        return bytes(result)

    def convert_bit_depth(self, samples: List[int], from_bits: int,
                          to_bits: int) -> List[int]:
        """Convert samples between different bit depths.

        Args:
            samples: List of integer samples in the source bit depth.
            from_bits: Source bit depth (8, 16, or 32).
            to_bits: Target bit depth (8, 16, or 32).

        Returns:
            List of integer samples in the target bit depth.
        """
        if from_bits == to_bits:
            return samples

        # Use signed range for all bit depths
        max_from = (2 ** (from_bits - 1)) - 1
        max_to = (2 ** (to_bits - 1)) - 1

        result = []
        for s in samples:
            # Normalize to -1.0..1.0 range, then scale to target
            normalized = s / max_from if max_from != 0 else 0
            new_val = int(normalized * max_to)
            # Clamp
            new_val = max(-max_to - 1, min(max_to, new_val))
            result.append(new_val)

        logger.debug(f"Converted {len(samples)} samples from {from_bits}-bit to {to_bits}-bit")
        return result

    def pcm_to_wav_bytes(self, samples: List[int], sample_rate: int = 22050,
                         sample_width: int = 2, channels: int = 1) -> bytes:
        """Convert PCM samples to WAV format bytes in memory.

        Creates a complete WAV file in memory using Python's wave module
        via a BytesIO buffer.

        Args:
            samples: List of integer PCM samples.
            sample_rate: Sample rate in Hz.
            sample_width: Bytes per sample (1, 2, or 4).
            channels: Number of channels.

        Returns:
            Complete WAV file as bytes.
        """
        import wave

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)

            # Convert samples to bytes
            if sample_width == 1:
                fmt_char = "B"  # unsigned 8-bit for WAV
                data = bytearray()
                for s in samples:
                    data.append(max(0, min(255, s + 128)))  # offset to unsigned
                wf.writeframes(bytes(data))
            elif sample_width == 2:
                data = self.samples_to_bytes(samples, self.PCM_S16LE)
                wf.writeframes(data)
            elif sample_width == 4:
                data = self.samples_to_bytes(samples, self.PCM_S32LE)
                wf.writeframes(data)

        return buf.getvalue()

    def get_format_description(self, fmt: int) -> str:
        """Get a human-readable description of a PCM format.

        Args:
            fmt: PCM format constant.

        Returns:
            Descriptive string.
        """
        descriptions = {
            self.PCM_S8: "8-bit signed PCM",
            self.PCM_U8: "8-bit unsigned PCM",
            self.PCM_S16LE: "16-bit signed PCM (little-endian)",
            self.PCM_S16BE: "16-bit signed PCM (big-endian)",
            self.PCM_S32LE: "32-bit signed PCM (little-endian)",
            self.PCM_S32BE: "32-bit signed PCM (big-endian)",
            self.PCM_F32LE: "32-bit float PCM (little-endian)",
            self.PCM_F32BE: "32-bit float PCM (big-endian)",
        }
        return descriptions.get(fmt, "Unknown format")
