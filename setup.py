"""
Setup script for VoiceCraft-CLI.

Zero external dependencies -- only Python standard library required.
"""

from setuptools import setup, find_packages

# Read long description from README if available
long_description = """
VoiceCraft-CLI: Lightweight Terminal Speech Synthesis & Audio Processing Engine.

A pure-Python CLI tool for text-to-speech, audio processing, and batch synthesis.
Supports multiple TTS engines (pyttsx3, espeak, macOS say, Windows SAPI),
SSML markup, batch processing, and audio file operations.
"""

setup(
    name="voicecraft-cli",
    version="1.0.0",
    description="Lightweight Terminal Speech Synthesis & Audio Processing Engine",
    long_description=long_description.strip(),
    author="VoiceCraft-CLI Contributors",
    license="MIT",
    python_requires=">=3.7",
    packages=find_packages(exclude=["tests*"]),
    package_dir={"": "."},
    entry_points={
        "console_scripts": [
            "voicecraft-cli=voicecraft_cli.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Utilities",
    ],
)
