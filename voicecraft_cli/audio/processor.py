"""
Audio processor module.

Pure-Python implementation for audio post-processing including
volume adjustment, sample rate conversion, and basic effects.
Operates on raw PCM audio data (lists/arrays of integers or floats).
"""

import math
import struct
from typing import List, Tuple, Optional

from voicecraft_cli.utils.logger import get_logger

logger = get_logger(__name__)


class AudioProcessor:
    """Pure-Python audio post-processing engine.

    Operates on raw PCM sample data for volume scaling, resampling,
    fading, normalization, and other basic audio manipulations.

    All processing is done in-memory using Python built-in types.
    Supports 8-bit, 16-bit, and 32-bit PCM formats.
    """

    # Maximum amplitude for different bit depths
    MAX_AMPLITUDE = {
        8: 127,
        16: 32767,
        32: 2147483647,
    }

    def __init__(self, sample_width: int = 2, sample_rate: int = 22050,
                 channels: int = 1) -> None:
        """Initialize the audio processor.

        Args:
            sample_width: Bytes per sample (1=8bit, 2=16bit, 4=32bit).
            sample_rate: Samples per second (e.g., 22050, 44100).
            channels: Number of audio channels (1=mono, 2=stereo).
        """
        self.sample_width = sample_width
        self.sample_rate = sample_rate
        self.channels = channels

    def adjust_volume(self, samples: List[int], volume: float) -> List[int]:
        """Scale audio sample amplitudes by a volume factor.

        Args:
            samples: List of integer PCM samples.
            volume: Volume multiplier (0.0 = silent, 1.0 = original, 2.0 = double).

        Returns:
            List of adjusted integer PCM samples.
        """
        max_amp = self.MAX_AMPLITUDE.get(self.sample_width * 8, 32767)
        result = []
        for s in samples:
            adjusted = int(s * volume)
            # Clamp to valid range
            adjusted = max(-max_amp - 1, min(max_amp, adjusted))
            result.append(adjusted)
        logger.debug(f"Volume adjusted by factor {volume:.2f}")
        return result

    def normalize(self, samples: List[int], target_db: float = -3.0) -> List[int]:
        """Normalize audio to a target peak level.

        Args:
            samples: List of integer PCM samples.
            target_db: Target peak level in decibels (default -3.0 dB).

        Returns:
            List of normalized integer PCM samples.
        """
        if not samples:
            return samples

        # Find current peak
        peak = max(abs(s) for s in samples)
        if peak == 0:
            return samples

        # Convert target dB to linear scale
        target_linear = 10 ** (target_db / 20.0)
        max_amp = self.MAX_AMPLITUDE.get(self.sample_width * 8, 32767)

        # Calculate gain factor
        gain = (max_amp * target_linear) / peak

        result = []
        for s in samples:
            adjusted = int(s * gain)
            adjusted = max(-max_amp - 1, min(max_amp, adjusted))
            result.append(adjusted)

        logger.debug(f"Audio normalized to {target_db} dB")
        return result

    def fade_in(self, samples: List[int], duration_ms: float) -> List[int]:
        """Apply a linear fade-in effect.

        Args:
            samples: List of integer PCM samples.
            duration_ms: Fade-in duration in milliseconds.

        Returns:
            List of samples with fade-in applied.
        """
        if not samples or duration_ms <= 0:
            return samples

        fade_samples = int(self.sample_rate * (duration_ms / 1000.0))
        fade_samples = min(fade_samples, len(samples))

        result = list(samples)
        for i in range(fade_samples):
            factor = i / fade_samples
            result[i] = int(result[i] * factor)

        logger.debug(f"Fade-in applied: {duration_ms}ms")
        return result

    def fade_out(self, samples: List[int], duration_ms: float) -> List[int]:
        """Apply a linear fade-out effect.

        Args:
            samples: List of integer PCM samples.
            duration_ms: Fade-out duration in milliseconds.

        Returns:
            List of samples with fade-out applied.
        """
        if not samples or duration_ms <= 0:
            return samples

        fade_samples = int(self.sample_rate * (duration_ms / 1000.0))
        fade_samples = min(fade_samples, len(samples))

        result = list(samples)
        total = len(result)
        for i in range(fade_samples):
            idx = total - fade_samples + i
            factor = 1.0 - ((i + 1) / fade_samples)
            result[idx] = int(result[idx] * factor)

        # Ensure the very last sample in the fade region is silent
        if fade_samples > 0 and fade_samples <= total:
            result[total - 1] = 0

        logger.debug(f"Fade-out applied: {duration_ms}ms")
        return result

    def resample(self, samples: List[int], new_rate: int) -> List[int]:
        """Resample audio to a new sample rate using linear interpolation.

        Note: This is a basic resampler. For high-quality resampling,
        consider using dedicated audio libraries.

        Args:
            samples: List of integer PCM samples.
            new_rate: Target sample rate in Hz.

        Returns:
            List of resampled integer PCM samples.
        """
        if new_rate == self.sample_rate or not samples:
            return samples

        ratio = self.sample_rate / new_rate
        new_length = int(len(samples) / ratio)
        result = []

        for i in range(new_length):
            src_pos = i * ratio
            src_idx = int(src_pos)
            frac = src_pos - src_idx

            if src_idx + 1 < len(samples):
                # Linear interpolation between adjacent samples
                interpolated = samples[src_idx] * (1 - frac) + samples[src_idx + 1] * frac
            else:
                interpolated = samples[src_idx] if src_idx < len(samples) else 0

            result.append(int(interpolated))

        logger.debug(
            f"Resampled from {self.sample_rate}Hz to {new_rate}Hz "
            f"({len(samples)} -> {len(result)} samples)"
        )
        self.sample_rate = new_rate
        return result

    def trim_silence(self, samples: List[int], threshold: float = 0.01) -> List[int]:
        """Remove leading and trailing silence from audio.

        Args:
            samples: List of integer PCM samples.
            threshold: Silence threshold as fraction of max amplitude (0.0-1.0).

        Returns:
            List of samples with silence trimmed.
        """
        if not samples:
            return samples

        max_amp = self.MAX_AMPLITUDE.get(self.sample_width * 8, 32767)
        abs_threshold = int(max_amp * threshold)

        # Find first non-silent sample
        start = 0
        for i, s in enumerate(samples):
            if abs(s) > abs_threshold:
                start = i
                break

        # Find last non-silent sample
        end = len(samples) - 1
        for i in range(len(samples) - 1, -1, -1):
            if abs(samples[i]) > abs_threshold:
                end = i
                break

        trimmed = samples[start:end + 1]
        logger.debug(f"Trimmed silence: {len(samples)} -> {len(trimmed)} samples")
        return trimmed

    def generate_silence(self, duration_ms: float) -> List[int]:
        """Generate a silence segment.

        Args:
            duration_ms: Duration of silence in milliseconds.

        Returns:
            List of zero-valued PCM samples.
        """
        num_samples = int(self.sample_rate * (duration_ms / 1000.0))
        return [0] * num_samples

    def concatenate(self, segments: List[List[int]]) -> List[int]:
        """Concatenate multiple audio segments into one.

        Args:
            segments: List of PCM sample lists.

        Returns:
            Combined list of PCM samples.
        """
        result = []
        for segment in segments:
            result.extend(segment)
        logger.debug(f"Concatenated {len(segments)} segments, total {len(result)} samples")
        return result

    def get_duration_seconds(self, samples: List[int]) -> float:
        """Calculate the duration of audio samples in seconds.

        Args:
            samples: List of PCM samples.

        Returns:
            Duration in seconds.
        """
        if self.sample_rate == 0:
            return 0.0
        return len(samples) / self.sample_rate

    def get_audio_info(self, samples: List[int]) -> dict:
        """Get information about an audio sample buffer.

        Args:
            samples: List of PCM samples.

        Returns:
            Dictionary with duration, sample count, peak level, etc.
        """
        peak = max(abs(s) for s in samples) if samples else 0
        max_amp = self.MAX_AMPLITUDE.get(self.sample_width * 8, 32767)
        peak_db = 20 * math.log10(peak / max_amp) if peak > 0 else float("-inf")

        return {
            "sample_count": len(samples),
            "duration_seconds": self.get_duration_seconds(samples),
            "sample_rate": self.sample_rate,
            "sample_width": self.sample_width,
            "channels": self.channels,
            "peak_amplitude": peak,
            "peak_db": round(peak_db, 2),
        }
