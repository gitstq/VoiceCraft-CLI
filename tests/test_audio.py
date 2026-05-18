"""
Unit tests for audio processing modules.

Tests the AudioProcessor, AudioConverter, and WaveUtils classes.
"""

import unittest
import sys
import os
import tempfile
import struct

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voicecraft_cli.audio.processor import AudioProcessor
from voicecraft_cli.audio.converter import AudioConverter
from voicecraft_cli.audio.wave_utils import WaveUtils


class TestAudioProcessor(unittest.TestCase):
    """Tests for the AudioProcessor class."""

    def setUp(self):
        """Create a test processor and sample data."""
        self.processor = AudioProcessor(sample_width=2, sample_rate=22050, channels=1)
        # Create a simple sine-like wave pattern for testing
        self.samples = [int(16000 * (i % 100) / 100) for i in range(1000)]

    def test_adjust_volume_up(self):
        """Volume increase scales samples correctly."""
        result = self.processor.adjust_volume(self.samples, 2.0)
        for i in range(len(self.samples)):
            expected = min(32767, self.samples[i] * 2)
            self.assertEqual(result[i], expected)

    def test_adjust_volume_down(self):
        """Volume decrease scales samples correctly."""
        result = self.processor.adjust_volume(self.samples, 0.5)
        for i in range(len(self.samples)):
            self.assertEqual(result[i], self.samples[i] // 2)

    def test_adjust_volume_zero(self):
        """Zero volume produces silence."""
        result = self.processor.adjust_volume(self.samples, 0.0)
        self.assertTrue(all(s == 0 for s in result))

    def test_normalize(self):
        """Normalization brings peak to target level."""
        result = self.processor.normalize(self.samples, target_db=-3.0)
        self.assertEqual(len(result), len(self.samples))
        # Peak should be close to target
        peak = max(abs(s) for s in result)
        self.assertGreater(peak, 0)

    def test_normalize_empty(self):
        """Normalizing empty samples returns empty."""
        result = self.processor.normalize([])
        self.assertEqual(result, [])

    def test_normalize_silent(self):
        """Normalizing all-silent samples returns silent."""
        silent = [0] * 100
        result = self.processor.normalize(silent)
        self.assertTrue(all(s == 0 for s in result))

    def test_fade_in(self):
        """Fade-in starts at zero and increases."""
        result = self.processor.fade_in(self.samples, duration_ms=100)
        self.assertEqual(len(result), len(self.samples))
        # First sample should be near zero
        self.assertEqual(result[0], 0)

    def test_fade_out(self):
        """Fade-out ends at zero."""
        result = self.processor.fade_out(self.samples, duration_ms=100)
        self.assertEqual(len(result), len(self.samples))
        # Last sample should be near zero
        self.assertEqual(result[-1], 0)

    def test_fade_zero_duration(self):
        """Zero duration fade returns original samples."""
        result = self.processor.fade_in(self.samples, 0)
        self.assertEqual(result, self.samples)

    def test_resample_down(self):
        """Downsampling reduces sample count."""
        result = self.processor.resample(self.samples, 11025)
        self.assertLess(len(result), len(self.samples))

    def test_resample_up(self):
        """Upsampling increases sample count."""
        result = self.processor.resample(self.samples, 44100)
        self.assertGreater(len(result), len(self.samples))

    def test_resample_same_rate(self):
        """Same rate returns original samples."""
        result = self.processor.resample(self.samples, 22050)
        self.assertEqual(result, self.samples)

    def test_trim_silence(self):
        """Silence trimming removes leading/trailing zeros."""
        samples_with_silence = [0, 0, 0] + self.samples + [0, 0, 0]
        result = self.processor.trim_silence(samples_with_silence)
        self.assertLess(len(result), len(samples_with_silence))
        self.assertNotEqual(result[0], 0)

    def test_generate_silence(self):
        """Silence generation produces correct number of zeros."""
        silence = self.processor.generate_silence(100)
        self.assertEqual(len(silence), 2205)  # 22050 * 0.1
        self.assertTrue(all(s == 0 for s in silence))

    def test_concatenate(self):
        """Concatenation combines segments."""
        seg1 = [1, 2, 3]
        seg2 = [4, 5, 6]
        result = self.processor.concatenate([seg1, seg2])
        self.assertEqual(result, [1, 2, 3, 4, 5, 6])

    def test_get_duration_seconds(self):
        """Duration calculation is correct."""
        # 1000 samples at 22050 Hz
        duration = self.processor.get_duration_seconds(self.samples)
        self.assertAlmostEqual(duration, 1000 / 22050, places=4)

    def test_get_audio_info(self):
        """Audio info returns correct metadata."""
        info = self.processor.get_audio_info(self.samples)
        self.assertEqual(info["sample_count"], 1000)
        self.assertEqual(info["sample_rate"], 22050)
        self.assertEqual(info["sample_width"], 2)
        self.assertEqual(info["channels"], 1)
        self.assertGreater(info["peak_amplitude"], 0)


class TestAudioConverter(unittest.TestCase):
    """Tests for the AudioConverter class."""

    def setUp(self):
        """Create a test converter."""
        self.converter = AudioConverter()

    def test_bytes_to_samples_16bit(self):
        """16-bit LE bytes convert to samples correctly."""
        samples = [100, -200, 30000]
        data = struct.pack("<3h", *samples)
        result = self.converter.bytes_to_samples(data, AudioConverter.PCM_S16LE)
        self.assertEqual(result, samples)

    def test_samples_to_bytes_16bit(self):
        """Samples convert to 16-bit LE bytes correctly."""
        samples = [100, -200, 30000]
        data = self.converter.samples_to_bytes(samples, AudioConverter.PCM_S16LE)
        result = struct.unpack("<3h", data)
        self.assertEqual(list(result), samples)

    def test_roundtrip_16bit(self):
        """16-bit samples survive a roundtrip conversion."""
        original = [0, 100, -100, 32767, -32768, 12345]
        data = self.converter.samples_to_bytes(original, AudioConverter.PCM_S16LE)
        recovered = self.converter.bytes_to_samples(data, AudioConverter.PCM_S16LE)
        self.assertEqual(recovered, original)

    def test_convert_bit_depth_16_to_8(self):
        """16-bit to 8-bit conversion works."""
        samples_16 = [0, 1000, -1000, 32767, -32768]
        result = self.converter.convert_bit_depth(samples_16, 16, 8)
        self.assertEqual(len(result), len(samples_16))
        for s in result:
            self.assertGreaterEqual(s, -128)
            self.assertLessEqual(s, 127)

    def test_convert_bit_depth_same(self):
        """Same bit depth returns original."""
        samples = [100, 200, 300]
        result = self.converter.convert_bit_depth(samples, 16, 16)
        self.assertEqual(result, samples)

    def test_pcm_to_wav_bytes(self):
        """PCM to WAV conversion produces valid WAV data."""
        samples = [0, 1000, -1000, 500, -500]
        wav_data = self.converter.pcm_to_wav_bytes(samples, 22050, 2, 1)
        # WAV files start with "RIFF"
        self.assertTrue(wav_data.startswith(b"RIFF"))
        # Check file size is reasonable
        self.assertGreater(len(wav_data), 44)  # WAV header is 44 bytes

    def test_get_format_description(self):
        """Format description returns non-empty strings."""
        for fmt in range(8):
            desc = self.converter.get_format_description(fmt)
            self.assertIsInstance(desc, str)
            self.assertTrue(len(desc) > 0)

    def test_empty_input(self):
        """Empty input produces empty output."""
        result = self.converter.bytes_to_samples(b"", AudioConverter.PCM_S16LE)
        self.assertEqual(result, [])
        result = self.converter.samples_to_bytes([], AudioConverter.PCM_S16LE)
        self.assertEqual(result, b"")


class TestWaveUtils(unittest.TestCase):
    """Tests for the WaveUtils class."""

    def setUp(self):
        """Create test fixtures."""
        self.wave_utils = WaveUtils()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_write_and_read_wav(self):
        """WAV write and read roundtrip preserves data."""
        filepath = os.path.join(self.temp_dir, "test.wav")
        samples = [i * 100 for i in range(-100, 101)]

        success = self.wave_utils.write_wav(filepath, samples, 22050, 2, 1)
        self.assertTrue(success)
        self.assertTrue(os.path.isfile(filepath))

        info = self.wave_utils.read_wav(filepath)
        self.assertIsNotNone(info)
        self.assertEqual(len(info["samples"]), len(samples))
        # Samples may have minor differences due to 8-bit unsigned conversion
        # but for 16-bit they should be exact
        for orig, read in zip(samples, info["samples"]):
            self.assertEqual(orig, read)

    def test_write_wav_creates_directory(self):
        """write_wav creates output directory if needed."""
        filepath = os.path.join(self.temp_dir, "sub", "dir", "test.wav")
        samples = [100, -100, 200, -200]

        success = self.wave_utils.write_wav(filepath, samples)
        self.assertTrue(success)
        self.assertTrue(os.path.isfile(filepath))

    def test_read_nonexistent_file(self):
        """Reading a nonexistent file returns None."""
        info = self.wave_utils.read_wav("/nonexistent/path.wav")
        self.assertIsNone(info)

    def test_get_wav_info(self):
        """get_wav_info returns correct metadata."""
        filepath = os.path.join(self.temp_dir, "info_test.wav")
        samples = [0] * 22050  # 1 second of silence

        self.wave_utils.write_wav(filepath, samples, 44100, 2, 1)
        info = self.wave_utils.get_wav_info(filepath)

        self.assertIsNotNone(info)
        self.assertEqual(info["framerate"], 44100)
        self.assertEqual(info["sampwidth"], 2)
        self.assertEqual(info["nchannels"], 1)
        self.assertAlmostEqual(info["duration"], 0.5, places=1)

    def test_concatenate_wav_files(self):
        """WAV concatenation produces correct output."""
        file1 = os.path.join(self.temp_dir, "part1.wav")
        file2 = os.path.join(self.temp_dir, "part2.wav")
        output = os.path.join(self.temp_dir, "combined.wav")

        samples1 = [100, 200, 300]
        samples2 = [400, 500, 600]

        self.wave_utils.write_wav(file1, samples1)
        self.wave_utils.write_wav(file2, samples2)

        success = self.wave_utils.concatenate_wav_files([file1, file2], output)
        self.assertTrue(success)

        info = self.wave_utils.read_wav(output)
        self.assertIsNotNone(info)
        self.assertEqual(len(info["samples"]), 6)

    def test_concatenate_empty_list(self):
        """Concatenating empty file list returns False."""
        success = self.wave_utils.concatenate_wav_files([], "out.wav")
        self.assertFalse(success)

    def test_get_wav_info_nonexistent(self):
        """get_wav_info returns None for nonexistent file."""
        info = self.wave_utils.get_wav_info("/nonexistent.wav")
        self.assertIsNone(info)


if __name__ == "__main__":
    unittest.main()
