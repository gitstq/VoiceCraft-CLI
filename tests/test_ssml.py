"""
Unit tests for SSML parser.

Tests parsing of various SSML tags and edge cases.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voicecraft_cli.ssml.parser import (
    SSMLParser, SSMLSegment, SSMLBreak, SSMLProsody, SSMLSayAs
)


class TestSSMLParser(unittest.TestCase):
    """Tests for the SSMLParser class."""

    def setUp(self):
        """Create a parser instance for testing."""
        self.parser = SSMLParser()

    def test_plain_text(self):
        """Plain text without SSML tags is returned as-is."""
        segments = self.parser.parse("Hello World")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].segment_type, "text")
        self.assertEqual(segments[0].text, "Hello World")

    def test_simple_speak(self):
        """Simple <speak> tag is parsed correctly."""
        segments = self.parser.parse("<speak>Hello</speak>")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].text, "Hello")

    def test_auto_wrap_speak(self):
        """Text without <speak> root is auto-wrapped."""
        segments = self.parser.parse("<break time='500ms'/>")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].segment_type, "break")

    def test_break_with_time(self):
        """<break> with time attribute is parsed correctly."""
        segments = self.parser.parse("<speak>Hello<break time='1000ms'/>World</speak>")
        self.assertEqual(len(segments), 3)
        self.assertEqual(segments[0].text, "Hello")
        self.assertEqual(segments[1].segment_type, "break")
        self.assertEqual(segments[1].break_info.duration_ms, 1000)
        self.assertEqual(segments[2].text, "World")

    def test_break_with_strength(self):
        """<break> with strength attribute uses correct duration."""
        segments = self.parser.parse("<speak>A<break strength='strong'/>B</speak>")
        self.assertEqual(len(segments), 3)
        self.assertEqual(segments[1].break_info.duration_ms, 500)
        self.assertEqual(segments[1].break_info.strength, "strong")

    def test_break_strength_xstrong(self):
        """<break strength='x-strong'> maps to 1000ms."""
        segments = self.parser.parse("<speak>A<break strength='x-strong'/>B</speak>")
        self.assertEqual(segments[1].break_info.duration_ms, 1000)

    def test_break_time_seconds(self):
        """<break time='1.5s'> converts to 1500ms."""
        segments = self.parser.parse("<speak>A<break time='1.5s'/>B</speak>")
        self.assertEqual(segments[1].break_info.duration_ms, 1500)

    def test_prosody_rate(self):
        """<prosody rate='fast'> is parsed correctly."""
        segments = self.parser.parse("<speak><prosody rate='fast'>Hello</prosody></speak>")
        self.assertEqual(len(segments), 3)
        self.assertEqual(segments[0].segment_type, "prosody_start")
        self.assertEqual(segments[0].prosody.rate, "fast")
        self.assertEqual(segments[1].text, "Hello")
        self.assertEqual(segments[2].segment_type, "prosody_end")

    def test_prosody_all_attrs(self):
        """<prosody> with all attributes is parsed correctly."""
        segments = self.parser.parse(
            "<speak><prosody rate='slow' pitch='low' volume='50'>Hi</prosody></speak>"
        )
        self.assertEqual(segments[0].prosody.rate, "slow")
        self.assertEqual(segments[0].prosody.pitch, "low")
        self.assertEqual(segments[0].prosody.volume, "50")

    def test_emphasis(self):
        """<emphasis> is parsed with correct level."""
        segments = self.parser.parse("<speak><emphasis level='strong'>Hello</emphasis></speak>")
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].segment_type, "emphasis")
        self.assertEqual(segments[0].emphasis_level, "strong")

    def test_emphasis_default_level(self):
        """<emphasis> without level defaults to 'moderate'."""
        segments = self.parser.parse("<speak><emphasis>Hello</emphasis></speak>")
        self.assertEqual(segments[0].emphasis_level, "moderate")

    def test_say_as(self):
        """<say-as> is parsed with interpret-as attribute."""
        segments = self.parser.parse(
            "<speak><say-as interpret-as='date'>2024-01-01</say-as></speak>"
        )
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].segment_type, "say_as")
        self.assertEqual(segments[0].say_as_info.interpret_as, "date")
        self.assertEqual(segments[0].text, "2024-01-01")

    def test_voice(self):
        """<voice> is parsed with name attribute."""
        segments = self.parser.parse("<speak><voice name='Alex'>Hello</voice></speak>")
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].segment_type, "voice")
        self.assertEqual(segments[0].voice_name, "Alex")

    def test_phoneme(self):
        """<phoneme> is parsed with ph attribute."""
        segments = self.parser.parse("<speak><phoneme ph='h&#x025B;lo&#x028A;'>hello</phoneme></speak>")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].segment_type, "phoneme")

    def test_sentence_tag(self):
        """<s> tag creates a sentence segment."""
        segments = self.parser.parse("<speak><s>Hello world</s></speak>")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].segment_type, "sentence")
        self.assertEqual(len(segments[0].children), 1)
        self.assertEqual(segments[0].children[0].text, "Hello world")

    def test_paragraph_tag(self):
        """<p> tag creates a paragraph segment."""
        segments = self.parser.parse("<speak><p>Paragraph text</p></speak>")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].segment_type, "paragraph")

    def test_nested_elements(self):
        """Nested SSML elements are parsed correctly."""
        segments = self.parser.parse(
            "<speak><prosody rate='fast'><emphasis>Hello <break time='200ms'/>World</emphasis></prosody></speak>"
        )
        # Should have: prosody_start, emphasis, text("Hello"), break, text("World"), prosody_end
        self.assertGreater(len(segments), 3)

    def test_mixed_content(self):
        """Mixed text and elements are parsed correctly."""
        segments = self.parser.parse(
            "<speak>Start <break time='100ms'/> Middle <break time='200ms'/> End</speak>"
        )
        texts = [s.text for s in segments if s.segment_type == "text"]
        breaks = [s for s in segments if s.segment_type == "break"]
        self.assertEqual(len(texts), 3)
        self.assertEqual(len(breaks), 2)

    def test_invalid_xml_fallback(self):
        """Invalid XML falls back to plain text."""
        segments = self.parser.parse("<broken<tag>")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].segment_type, "text")

    def test_segments_to_plain_text(self):
        """segments_to_plain_text extracts text content."""
        segments = self.parser.parse(
            "<speak>Hello<break time='500ms'/>World</speak>"
        )
        text = self.parser.segments_to_plain_text(segments)
        self.assertIn("Hello", text)
        self.assertIn("World", text)

    def test_extract_prosody_settings(self):
        """extract_prosody_settings finds prosody in segments."""
        segments = self.parser.parse(
            "<speak><prosody rate='fast' pitch='high'>Hello</prosody></speak>"
        )
        settings = self.parser.extract_prosody_settings(segments)
        self.assertEqual(settings["rate"], "fast")
        self.assertEqual(settings["pitch"], "high")

    def test_extract_prosody_none(self):
        """extract_prosody_settings returns None values when no prosody."""
        segments = self.parser.parse("<speak>Hello</speak>")
        settings = self.parser.extract_prosody_settings(segments)
        self.assertIsNone(settings["rate"])

    def test_empty_input(self):
        """Empty string produces empty segments."""
        segments = self.parser.parse("")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].text, "")

    def test_whitespace_handling(self):
        """Whitespace in text is trimmed."""
        segments = self.parser.parse("<speak>  Hello   World  </speak>")
        self.assertEqual(segments[0].text, "Hello   World")

    def test_mark_tag(self):
        """<mark> tag is parsed as a marker segment."""
        segments = self.parser.parse("<speak><mark name='start'/>Hello</speak>")
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].segment_type, "mark")
        self.assertEqual(segments[0].text, "start")


class TestSSMLTimeParsing(unittest.TestCase):
    """Tests for time string parsing."""

    def setUp(self):
        self.parser = SSMLParser()

    def test_milliseconds(self):
        """'500ms' converts to 500."""
        self.assertEqual(self.parser._parse_time_string("500ms"), 500)

    def test_seconds(self):
        """'1s' converts to 1000."""
        self.assertEqual(self.parser._parse_time_string("1s"), 1000)

    def test_fractional_seconds(self):
        """'1.5s' converts to 1500."""
        self.assertEqual(self.parser._parse_time_string("1.5s"), 1500)

    def test_bare_number(self):
        """Bare number defaults to milliseconds."""
        self.assertEqual(self.parser._parse_time_string("750"), 750)

    def test_invalid_string(self):
        """Invalid string returns default."""
        self.assertEqual(self.parser._parse_time_string("abc"), 250)


if __name__ == "__main__":
    unittest.main()
