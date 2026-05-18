"""
Unit tests for TTS engine system.

Tests the base class, factory, and engine adapters.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voicecraft_cli.engines.base import TTSEngine
from voicecraft_cli.engines.factory import EngineFactory
from voicecraft_cli.engines.pyttsx3_engine import Pyttsx3Engine
from voicecraft_cli.engines.espeak_engine import EspeakEngine
from voicecraft_cli.engines.system_engine import SystemEngine


class TestTTSEngineBase(unittest.TestCase):
    """Tests for the TTSEngine abstract base class."""

    def test_cannot_instantiate_base(self):
        """TTSEngine is abstract and cannot be directly instantiated."""
        with self.assertRaises(TypeError):
            TTSEngine()

    def test_concrete_engine_inheritance(self):
        """Concrete engines properly inherit from TTSEngine."""
        # Create a minimal concrete implementation for testing
        class DummyEngine(TTSEngine):
            def detect(self): return False
            def speak(self, text): return False
            def synthesize_to_file(self, text, path, fmt="wav"): return False
            def get_voices(self): return []
            def set_voice(self, vid): return False

        engine = DummyEngine()
        self.assertIsInstance(engine, TTSEngine)
        self.assertFalse(engine.available)

    def test_set_rate_clamping(self):
        """Rate values are clamped to valid range."""
        class DummyEngine(TTSEngine):
            def detect(self): return False
            def speak(self, text): return False
            def synthesize_to_file(self, text, path, fmt="wav"): return False
            def get_voices(self): return []
            def set_voice(self, vid): return False

        engine = DummyEngine()
        engine.set_rate(5.0)
        self.assertEqual(engine.rate, 3.0)
        engine.set_rate(-1.0)
        self.assertEqual(engine.rate, 0.1)
        engine.set_rate(1.5)
        self.assertEqual(engine.rate, 1.5)

    def test_set_volume_clamping(self):
        """Volume values are clamped to 0.0-1.0."""
        class DummyEngine(TTSEngine):
            def detect(self): return False
            def speak(self, text): return False
            def synthesize_to_file(self, text, path, fmt="wav"): return False
            def get_voices(self): return []
            def set_voice(self, vid): return False

        engine = DummyEngine()
        engine.set_volume(2.0)
        self.assertEqual(engine.volume, 1.0)
        engine.set_volume(-0.5)
        self.assertEqual(engine.volume, 0.0)
        engine.set_volume(0.75)
        self.assertEqual(engine.volume, 0.75)

    def test_set_pitch_clamping(self):
        """Pitch values are clamped to valid range."""
        class DummyEngine(TTSEngine):
            def detect(self): return False
            def speak(self, text): return False
            def synthesize_to_file(self, text, path, fmt="wav"): return False
            def get_voices(self): return []
            def set_voice(self, vid): return False

        engine = DummyEngine()
        engine.set_pitch(5.0)
        self.assertEqual(engine.pitch, 2.0)
        engine.set_pitch(0.0)
        self.assertEqual(engine.pitch, 0.1)

    def test_get_info(self):
        """get_info returns correct engine configuration."""
        class DummyEngine(TTSEngine):
            def detect(self): return False
            def speak(self, text): return False
            def synthesize_to_file(self, text, path, fmt="wav"): return False
            def get_voices(self): return []
            def set_voice(self, vid): return False

        engine = DummyEngine()
        engine.name = "test"
        engine.set_rate(1.5)
        engine.set_volume(0.8)
        engine.set_pitch(1.2)

        info = engine.get_info()
        self.assertEqual(info["name"], "test")
        self.assertEqual(info["rate"], 1.5)
        self.assertEqual(info["volume"], 0.8)
        self.assertEqual(info["pitch"], 1.2)


class TestEngineFactory(unittest.TestCase):
    """Tests for the EngineFactory class."""

    def test_factory_creation(self):
        """EngineFactory can be created without errors."""
        factory = EngineFactory()
        self.assertIsInstance(factory, EngineFactory)

    def test_list_engines(self):
        """list_engines returns a list of engine entries."""
        factory = EngineFactory()
        engines = factory.list_engines()
        self.assertIsInstance(engines, list)
        self.assertGreater(len(engines), 0)
        for entry in engines:
            self.assertIn("name", entry)
            self.assertIn("available", entry)

    def test_get_engine_auto(self):
        """get_engine with no args returns an engine or None."""
        factory = EngineFactory()
        engine = factory.get_engine()
        # May be None if no engines are installed
        if engine is not None:
            self.assertTrue(engine.available)

    def test_get_engine_specific(self):
        """get_engine with a specific name returns that engine or None."""
        factory = EngineFactory()
        for name in ["pyttsx3", "espeak", "system"]:
            engine = factory.get_engine(name)
            if engine is not None:
                self.assertEqual(engine.name, name)

    def test_get_engine_invalid(self):
        """get_engine with invalid name returns None."""
        factory = EngineFactory()
        engine = factory.get_engine("nonexistent")
        self.assertIsNone(engine)

    def test_list_all_voices(self):
        """list_all_voices returns a dictionary."""
        factory = EngineFactory()
        voices = factory.list_all_voices()
        self.assertIsInstance(voices, dict)

    def test_get_available_engine_names(self):
        """get_available_engine_names returns a list."""
        factory = EngineFactory()
        names = factory.get_available_engine_names()
        self.assertIsInstance(names, list)


class TestPyttsx3Engine(unittest.TestCase):
    """Tests for the Pyttsx3Engine adapter."""

    def test_creation(self):
        """Pyttsx3Engine can be created without errors."""
        engine = Pyttsx3Engine()
        self.assertEqual(engine.name, "pyttsx3")

    def test_detect(self):
        """detect() returns a boolean."""
        engine = Pyttsx3Engine()
        result = engine.detect()
        self.assertIsInstance(result, bool)


class TestEspeakEngine(unittest.TestCase):
    """Tests for the EspeakEngine adapter."""

    def test_creation(self):
        """EspeakEngine can be created without errors."""
        engine = EspeakEngine()
        self.assertEqual(engine.name, "espeak")

    def test_detect(self):
        """detect() returns a boolean."""
        engine = EspeakEngine()
        result = engine.detect()
        self.assertIsInstance(result, bool)

    def test_build_args_basic(self):
        """_build_args produces correct argument list."""
        engine = EspeakEngine()
        engine._espeak_cmd = "espeak"
        args = engine._build_args("hello")
        self.assertIn("espeak", args)
        self.assertIn("hello", args)

    def test_build_args_with_output(self):
        """_build_args includes output path when provided."""
        engine = EspeakEngine()
        engine._espeak_cmd = "espeak"
        args = engine._build_args("hello", output_path="test.wav")
        self.assertIn("-w", args)
        idx = args.index("-w")
        self.assertEqual(args[idx + 1], "test.wav")


class TestSystemEngine(unittest.TestCase):
    """Tests for the SystemEngine adapter."""

    def test_creation(self):
        """SystemEngine can be created without errors."""
        engine = SystemEngine()
        self.assertEqual(engine.name, "system")

    def test_detect(self):
        """detect() returns a boolean."""
        engine = SystemEngine()
        result = engine.detect()
        self.assertIsInstance(result, bool)


if __name__ == "__main__":
    unittest.main()
