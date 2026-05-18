"""
SSML (Speech Synthesis Markup Language) parser.

Parses SSML tags and converts them into a structured representation
that can be used by TTS engines to control speech output.

Supported SSML tags:
    <speak>     - Root element
    <break>     - Pause/break in speech
    <prosody>   - Rate, pitch, volume control
    <emphasis>  - Emphasis level
    <say-as>    - Interpret text format (date, time, etc.)
    <phoneme>   - Phonetic pronunciation
    <voice>     - Voice selection
    <mark>      - Marker for navigation
    <s>         - Sentence
    <p>         - Paragraph
"""

import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from voicecraft_cli.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SSMLBreak:
    """Represents a pause/break in speech.

    Attributes:
        duration_ms: Break duration in milliseconds.
        strength: Break strength ('none', 'x-weak', 'weak', 'medium',
                  'strong', 'x-strong').
    """
    duration_ms: int = 500
    strength: str = "medium"


@dataclass
class SSMLProsody:
    """Represents prosody (rate, pitch, volume) settings.

    Attributes:
        rate: Speech rate multiplier or absolute value.
        pitch: Pitch multiplier or absolute value.
        volume: Volume level.
    """
    rate: Optional[str] = None
    pitch: Optional[str] = None
    volume: Optional[str] = None


@dataclass
class SSMLSayAs:
    """Represents a say-as interpretation hint.

    Attributes:
        interpret_as: Interpretation format (e.g., 'date', 'time', 'telephone').
        format: Format specification string.
    """
    interpret_as: str = ""
    format: str = ""


@dataclass
class SSMLSegment:
    """A segment of parsed SSML content.

    Each segment is either plain text or a control element.
    Segments are processed sequentially by the TTS engine.

    Attributes:
        text: The text content (empty for control segments).
        segment_type: Type of segment ('text', 'break', 'prosody_start',
                     'prosody_end', 'emphasis', 'say_as', 'voice', 'sentence',
                     'paragraph').
        prosody: Prosody settings (if applicable).
        break_info: Break information (if applicable).
        say_as_info: Say-as information (if applicable).
        emphasis_level: Emphasis level ('none', 'weak', 'moderate', 'strong').
        voice_name: Voice name (if applicable).
        children: Nested segments for container elements.
    """
    text: str = ""
    segment_type: str = "text"
    prosody: Optional[SSMLProsody] = None
    break_info: Optional[SSMLBreak] = None
    say_as_info: Optional[SSMLSayAs] = None
    emphasis_level: str = "moderate"
    voice_name: str = ""
    children: List["SSMLSegment"] = field(default_factory=list)


class SSMLParser:
    """Parser for SSML (Speech Synthesis Markup Language).

    Parses SSML input and produces a list of SSMLSegment objects
    that can be consumed by TTS engines for controlled speech output.

    Usage:
        parser = SSMLParser()
        segments = parser.parse("<speak>Hello <break time='500ms'/> World</speak>")
        for seg in segments:
            print(seg.segment_type, seg.text)
    """

    # Strength to duration mapping (in milliseconds)
    STRENGTH_DURATIONS = {
        "none": 0,
        "x-weak": 50,
        "weak": 100,
        "medium": 250,
        "strong": 500,
        "x-strong": 1000,
    }

    def __init__(self) -> None:
        """Initialize the SSML parser."""
        pass

    def parse(self, ssml_text: str) -> List[SSMLSegment]:
        """Parse SSML text into a list of segments.

        Args:
            ssml_text: SSML markup string.

        Returns:
            List of SSMLSegment objects representing the parsed content.
        """
        # Strip surrounding whitespace
        ssml_text = ssml_text.strip()

        # If no SSML tags, treat as plain text
        if not ssml_text.startswith("<"):
            return [SSMLSegment(text=ssml_text, segment_type="text")]

        try:
            # Ensure we have a root <speak> element
            if not ssml_text.startswith("<speak"):
                ssml_text = f"<speak>{ssml_text}</speak>"

            root = ET.fromstring(ssml_text)
            segments = self._parse_element(root)
            logger.debug(f"Parsed SSML into {len(segments)} segments")
            return segments

        except ET.ParseError as e:
            logger.error(f"SSML parse error: {e}")
            # Fall back to plain text, stripping tags
            clean_text = re.sub(r"<[^>]+>", "", ssml_text)
            return [SSMLSegment(text=clean_text, segment_type="text")]

    def _parse_element(self, element: ET.Element) -> List[SSMLSegment]:
        """Recursively parse an XML element into SSML segments.

        Args:
            element: XML element to parse.

        Returns:
            List of SSMLSegment objects.
        """
        segments = []
        tag = element.tag.lower() if element.tag else ""

        if tag == "speak":
            # Root element: parse children
            segments.extend(self._parse_children(element))

        elif tag == "break":
            # Break/pause element
            segments.append(self._parse_break(element))

        elif tag == "prosody":
            # Prosody control element
            segments.extend(self._parse_prosody(element))

        elif tag == "emphasis":
            # Emphasis element
            segments.extend(self._parse_emphasis(element))

        elif tag == "say-as":
            # Say-as interpretation element
            segments.extend(self._parse_say_as(element))

        elif tag == "voice":
            # Voice selection element
            segments.extend(self._parse_voice(element))

        elif tag == "phoneme":
            # Phonetic pronunciation
            ph = element.get("ph", "")
            if ph:
                segments.append(SSMLSegment(text=ph, segment_type="phoneme"))

        elif tag == "mark":
            # Marker element (informational, no audio effect)
            name = element.get("name", "")
            segments.append(SSMLSegment(text=name, segment_type="mark"))

        elif tag in ("s", "p"):
            # Sentence or paragraph container
            child_segments = self._parse_children(element)
            container = SSMLSegment(
                segment_type="sentence" if tag == "s" else "paragraph",
                children=child_segments,
            )
            segments.append(container)

        else:
            # Unknown tag: treat as container, parse children
            segments.extend(self._parse_children(element))

        return segments

    def _parse_children(self, element: ET.Element) -> List[SSMLSegment]:
        """Parse all children of an XML element.

        Handles both text content and child elements.

        Args:
            element: Parent XML element.

        Returns:
            List of SSMLSegment objects from children.
        """
        segments = []

        # Handle text content before first child
        if element.text and element.text.strip():
            segments.append(SSMLSegment(text=element.text.strip(), segment_type="text"))

        # Handle child elements
        for child in element:
            segments.extend(self._parse_element(child))

            # Handle text after each child (tail text)
            if child.tail and child.tail.strip():
                segments.append(SSMLSegment(text=child.tail.strip(), segment_type="text"))

        return segments

    def _parse_break(self, element: ET.Element) -> SSMLSegment:
        """Parse a <break> element.

        Args:
            element: The <break> XML element.

        Returns:
            SSMLSegment with break information.
        """
        time_str = element.get("time", "")
        strength = element.get("strength", "medium")

        # Parse time attribute (e.g., "500ms", "1s")
        duration_ms = self.STRENGTH_DURATIONS.get(strength, 250)

        if time_str:
            duration_ms = self._parse_time_string(time_str)

        return SSMLSegment(
            segment_type="break",
            break_info=SSMLBreak(duration_ms=duration_ms, strength=strength),
        )

    def _parse_prosody(self, element: ET.Element) -> List[SSMLSegment]:
        """Parse a <prosody> element.

        Creates a prosody_start segment, child segments, and prosody_end segment.

        Args:
            element: The <prosody> XML element.

        Returns:
            List of SSMLSegment objects.
        """
        prosody = SSMLProsody(
            rate=element.get("rate"),
            pitch=element.get("pitch"),
            volume=element.get("volume"),
        )

        segments = [SSMLSegment(segment_type="prosody_start", prosody=prosody)]
        segments.extend(self._parse_children(element))
        segments.append(SSMLSegment(segment_type="prosody_end"))
        return segments

    def _parse_emphasis(self, element: ET.Element) -> List[SSMLSegment]:
        """Parse an <emphasis> element.

        Args:
            element: The <emphasis> XML element.

        Returns:
            List of SSMLSegment objects.
        """
        level = element.get("level", "moderate")
        level = level.lower()

        segments = [SSMLSegment(segment_type="emphasis", emphasis_level=level)]
        segments.extend(self._parse_children(element))
        return segments

    def _parse_say_as(self, element: ET.Element) -> List[SSMLSegment]:
        """Parse a <say-as> element.

        Args:
            element: The <say-as> XML element.

        Returns:
            List of SSMLSegment objects.
        """
        say_as = SSMLSayAs(
            interpret_as=element.get("interpret-as", ""),
            format=element.get("format", ""),
        )

        text = (element.text or "").strip()
        if text:
            segments = [SSMLSegment(
                text=text,
                segment_type="say_as",
                say_as_info=say_as,
            )]
        else:
            segments = []

        return segments

    def _parse_voice(self, element: ET.Element) -> List[SSMLSegment]:
        """Parse a <voice> element.

        Args:
            element: The <voice> XML element.

        Returns:
            List of SSMLSegment objects.
        """
        voice_name = element.get("name", element.get("xml:lang", ""))

        segments = [SSMLSegment(segment_type="voice", voice_name=voice_name)]
        segments.extend(self._parse_children(element))
        return segments

    def _parse_time_string(self, time_str: str) -> int:
        """Parse a time string into milliseconds.

        Supports formats: "500ms", "1s", "1.5s", "1000"

        Args:
            time_str: Time string to parse.

        Returns:
            Duration in milliseconds.
        """
        time_str = time_str.strip().lower()

        # Match patterns like "500ms", "1.5s", "1000"
        match = re.match(r"^(\d+(?:\.\d+)?)\s*(ms|s)?$", time_str)
        if not match:
            return 250  # Default

        value = float(match.group(1))
        unit = match.group(2) or "ms"

        if unit == "s":
            return int(value * 1000)
        return int(value)

    def segments_to_plain_text(self, segments: List[SSMLSegment]) -> str:
        """Convert parsed SSML segments back to plain text.

        Strips all SSML markup and returns only the text content,
        with pauses represented as "..." and emphasis markers.

        Args:
            segments: List of SSMLSegment objects.

        Returns:
            Plain text string.
        """
        parts = []

        for seg in segments:
            if seg.segment_type == "text":
                parts.append(seg.text)
            elif seg.segment_type == "break":
                if seg.break_info:
                    parts.append("...")
            elif seg.segment_type == "emphasis":
                parts.append(self.segments_to_plain_text(seg.children))
            elif seg.segment_type in ("sentence", "paragraph"):
                parts.append(self.segments_to_plain_text(seg.children))
            elif seg.segment_type in ("prosody_start", "prosody_end", "voice"):
                pass  # Skip control segments

        return " ".join(p for p in parts if p)

    def extract_prosody_settings(self, segments: List[SSMLSegment]) -> Dict[str, Any]:
        """Extract the first prosody settings found in segments.

        Useful for applying SSML prosody to a TTS engine.

        Args:
            segments: List of SSMLSegment objects.

        Returns:
            Dictionary with 'rate', 'pitch', 'volume' keys (or None values).
        """
        for seg in segments:
            if seg.segment_type == "prosody_start" and seg.prosody:
                return {
                    "rate": seg.prosody.rate,
                    "pitch": seg.prosody.pitch,
                    "volume": seg.prosody.volume,
                }
        return {"rate": None, "pitch": None, "volume": None}
