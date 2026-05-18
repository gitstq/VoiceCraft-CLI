"""
SSML package.

Provides SSML (Speech Synthesis Markup Language) parsing capabilities.
"""

from voicecraft_cli.ssml.parser import SSMLParser, SSMLSegment, SSMLBreak, SSMLProsody

__all__ = ["SSMLParser", "SSMLSegment", "SSMLBreak", "SSMLProsody"]
