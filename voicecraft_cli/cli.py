"""
CLI argument parser and main entry point for VoiceCraft-CLI.

Provides comprehensive command-line interface with argparse,
supporting text synthesis, file output, batch processing,
engine management, and more.
"""

import argparse
import sys
import os
from typing import List, Optional

from voicecraft_cli import __version__
from voicecraft_cli.utils.logger import get_logger, setup_logging
from voicecraft_cli.utils.config import Config
from voicecraft_cli.engines.factory import EngineFactory
from voicecraft_cli.tui.dashboard import Dashboard
from voicecraft_cli.batch.queue import BatchQueue
from voicecraft_cli.ssml.parser import SSMLParser
from voicecraft_cli.audio.wave_utils import WaveUtils

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all CLI options.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="voicecraft-cli",
        description="VoiceCraft-CLI: Lightweight Terminal Speech Synthesis & Audio Processing Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Speak text aloud
  voicecraft-cli --text "Hello, World!"

  # Synthesize text to a WAV file
  voicecraft-cli --text "Hello" --output hello.wav

  # Use a specific engine with custom settings
  voicecraft-cli --text "Hello" --engine espeak --rate 1.5 --volume 0.8

  # Batch process a text file
  voicecraft-cli --batch input.txt --output-dir output/

  # Use SSML for fine control
  voicecraft-cli --ssml '<speak>Hello <break time="500ms"/> World</speak>'

  # List available engines and voices
  voicecraft-cli --list-engines
  voicecraft-cli --list-voices

  # Get audio file info
  voicecraft-cli --info audio.wav
        """,
    )

    # Input options
    input_group = parser.add_argument_group("Input Options")
    input_group.add_argument(
        "-t", "--text",
        type=str, default=None,
        help="Text to synthesize (use quotes for multi-word text)",
    )
    input_group.add_argument(
        "-f", "--file",
        type=str, default=None,
        help="Read text from a file",
    )
    input_group.add_argument(
        "--ssml",
        type=str, default=None,
        help="SSML markup to parse and synthesize",
    )
    input_group.add_argument(
        "--ssml-file",
        type=str, default=None,
        help="Read SSML markup from a file",
    )

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "-o", "--output",
        type=str, default=None,
        help="Output audio file path (e.g., output.wav)",
    )
    output_group.add_argument(
        "--output-dir",
        type=str, default=".",
        help="Output directory for batch processing (default: current directory)",
    )
    output_group.add_argument(
        "--format",
        type=str, default="wav",
        choices=["wav"],
        help="Output audio format (default: wav)",
    )

    # Engine options
    engine_group = parser.add_argument_group("Engine Options")
    engine_group.add_argument(
        "-e", "--engine",
        type=str, default=None,
        choices=["auto", "pyttsx3", "espeak", "system"],
        help="TTS engine to use (default: auto-detect)",
    )
    engine_group.add_argument(
        "--list-engines",
        action="store_true",
        help="List all available TTS engines and exit",
    )
    engine_group.add_argument(
        "--list-voices",
        action="store_true",
        help="List all available voices and exit",
    )

    # Voice parameters
    voice_group = parser.add_argument_group("Voice Parameters")
    voice_group.add_argument(
        "--voice",
        type=str, default=None,
        help="Voice identifier to use",
    )
    voice_group.add_argument(
        "-r", "--rate",
        type=float, default=None,
        help="Speech rate multiplier (0.5 = slow, 2.0 = fast, default: 1.0)",
    )
    voice_group.add_argument(
        "-v", "--volume",
        type=float, default=None,
        help="Volume level (0.0 = silent, 1.0 = max, default: 1.0)",
    )
    voice_group.add_argument(
        "-p", "--pitch",
        type=float, default=None,
        help="Pitch multiplier (0.5 = low, 2.0 = high, default: 1.0)",
    )

    # Batch options
    batch_group = parser.add_argument_group("Batch Processing")
    batch_group.add_argument(
        "-b", "--batch",
        type=str, default=None,
        help="Batch mode: process a text file (one utterance per line)",
    )
    batch_group.add_argument(
        "--batch-dir",
        type=str, default=None,
        help="Batch mode: process all .txt files in a directory",
    )

    # Audio processing options
    audio_group = parser.add_argument_group("Audio Processing")
    audio_group.add_argument(
        "--info",
        type=str, default=None,
        metavar="FILE",
        help="Display information about an audio file and exit",
    )
    audio_group.add_argument(
        "--concat",
        type=str, nargs="+", default=None,
        metavar="FILES",
        help="Concatenate multiple WAV files into one",
    )
    audio_group.add_argument(
        "--normalize",
        action="store_true",
        help="Normalize output audio volume",
    )

    # UI options
    ui_group = parser.add_argument_group("UI Options")
    ui_group.add_argument(
        "--dashboard",
        action="store_true",
        help="Show TUI dashboard during processing",
    )
    ui_group.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

    # General options
    general_group = parser.add_argument_group("General Options")
    general_group.add_argument(
        "--config",
        type=str, default=None,
        help="Path to configuration file",
    )
    general_group.add_argument(
        "--log-level",
        type=str, default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level (default: WARNING)",
    )
    general_group.add_argument(
        "--log-file",
        type=str, default=None,
        help="Write logs to a file",
    )
    general_group.add_argument(
        "--version",
        action="version",
        version=f"VoiceCraft-CLI {__version__}",
    )

    return parser


def cmd_list_engines(args: argparse.Namespace, factory: EngineFactory,
                     dashboard: Dashboard) -> int:
    """Handle the --list-engines command.

    Args:
        args: Parsed command-line arguments.
        factory: Engine factory instance.
        dashboard: Dashboard instance.

    Returns:
        Exit code (0 for success).
    """
    engines = factory.list_engines()
    dashboard.print_engine_list(engines)
    print()

    available = [e for e in engines if e["available"]]
    if available:
        print(f"  Active engine: {available[0]['name']}")
    else:
        print("  No engines available. Install pyttsx3, espeak, or use a system with TTS support.")

    return 0


def cmd_list_voices(args: argparse.Namespace, factory: EngineFactory,
                    dashboard: Dashboard) -> int:
    """Handle the --list-voices command.

    Args:
        args: Parsed command-line arguments.
        factory: Engine factory instance.
        dashboard: Dashboard instance.

    Returns:
        Exit code (0 for success).
    """
    voices = factory.list_all_voices()
    if not voices:
        print("  No voices available. No TTS engine is active.")
        return 1

    dashboard.print_voice_list(voices)
    return 0


def cmd_audio_info(args: argparse.Namespace) -> int:
    """Handle the --info command to display audio file information.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    filepath = args.info
    if not filepath or not os.path.isfile(filepath):
        print(f"  Error: File not found: {filepath}")
        return 1

    wave_utils = WaveUtils()
    info = wave_utils.get_wav_info(filepath)

    if info is None:
        print(f"  Error: Could not read audio file: {filepath}")
        return 1

    print(f"  File: {info['filepath']}")
    print(f"  Size: {info['file_size_mb']} MB ({info['file_size_bytes']} bytes)")
    print(f"  Duration: {info['duration']:.3f} seconds")
    print(f"  Sample Rate: {info['framerate']} Hz")
    print(f"  Bit Depth: {info['bit_depth']} bits")
    print(f"  Channels: {info['nchannels']}")
    print(f"  Frames: {info['nframes']}")
    if info["comptype"] != "NONE":
        print(f"  Compression: {info['compname']} ({info['comptype']})")

    return 0


def cmd_concat(args: argparse.Namespace) -> int:
    """Handle the --concat command to concatenate WAV files.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    files = args.concat
    if not files or len(files) < 2:
        print("  Error: --concat requires at least 2 WAV files")
        return 1

    for f in files:
        if not os.path.isfile(f):
            print(f"  Error: File not found: {f}")
            return 1

    output_path = args.output or "concatenated.wav"
    wave_utils = WaveUtils()

    print(f"  Concatenating {len(files)} files...")
    success = wave_utils.concatenate_wav_files(files, output_path)

    if success:
        info = wave_utils.get_wav_info(output_path)
        if info:
            print(f"  Output: {output_path} ({info['duration']:.2f}s)")
        return 0
    else:
        print("  Error: Concatenation failed")
        return 1


def get_text_input(args: argparse.Namespace) -> Optional[str]:
    """Resolve text input from CLI arguments.

    Checks --text, --file, --ssml, --ssml-file in order and returns
    the first available text content.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Text string, or None if no input was provided.
    """
    # Direct text
    if args.text:
        return args.text

    # Text from file
    if args.file:
        if not os.path.isfile(args.file):
            print(f"  Error: File not found: {args.file}")
            return None
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            print(f"  Error reading file: {e}")
            return None

    # SSML text
    if args.ssml:
        parser = SSMLParser()
        segments = parser.parse(args.ssml)
        return parser.segments_to_plain_text(segments)

    # SSML from file
    if args.ssml_file:
        if not os.path.isfile(args.ssml_file):
            print(f"  Error: SSML file not found: {args.ssml_file}")
            return None
        try:
            with open(args.ssml_file, "r", encoding="utf-8") as f:
                ssml_content = f.read().strip()
            parser = SSMLParser()
            segments = parser.parse(ssml_content)
            return parser.segments_to_plain_text(segments)
        except Exception as e:
            print(f"  Error reading SSML file: {e}")
            return None

    return None


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for VoiceCraft-CLI.

    Parses arguments, initializes components, and dispatches
    to the appropriate command handler.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Set up logging
    setup_logging(level=args.log_level, log_file=args.log_file)

    # Load configuration
    config = Config()
    if args.config:
        config.load_file(args.config)

    # Create dashboard
    dashboard = Dashboard(use_colors=not args.no_color)

    # Create engine factory
    factory = EngineFactory()

    # Handle --list-engines
    if args.list_engines:
        return cmd_list_engines(args, factory, dashboard)

    # Handle --list-voices
    if args.list_voices:
        return cmd_list_voices(args, factory, dashboard)

    # Handle --info
    if args.info:
        return cmd_audio_info(args)

    # Handle --concat
    if args.concat:
        return cmd_concat(args)

    # Check for input
    text = get_text_input(args)
    batch_mode = args.batch or args.batch_dir

    if not text and not batch_mode:
        parser.print_help()
        return 0

    # Get engine
    engine_name = args.engine or config.get("engine", "name", "auto")
    if engine_name == "auto":
        engine_name = None

    engine = factory.get_engine(engine_name)
    if engine is None:
        print("  Error: No TTS engine available.")
        print("  Please install pyttsx3, espeak, or use a system with TTS support.")
        return 1

    # Apply voice parameters
    rate = args.rate if args.rate is not None else config.get_float("engine", "rate", 1.0)
    volume = args.volume if args.volume is not None else config.get_float("engine", "volume", 1.0)
    pitch = args.pitch if args.pitch is not None else config.get_float("engine", "pitch", 1.0)

    engine.set_rate(rate)
    engine.set_volume(volume)
    engine.set_pitch(pitch)

    if args.voice:
        engine.set_voice(args.voice)

    # Update dashboard with engine info
    dashboard.set_engine_info(engine.get_info())

    # Handle batch mode
    if batch_mode:
        return handle_batch_mode(args, engine, dashboard, config)

    # Handle single text synthesis
    return handle_single_synthesis(args, engine, text, dashboard)


def handle_single_synthesis(args: argparse.Namespace, engine, text: str,
                            dashboard: Dashboard) -> int:
    """Handle single text-to-speech synthesis.

    Args:
        args: Parsed command-line arguments.
        engine: TTS engine instance.
        text: Text to synthesize.
        dashboard: Dashboard instance.

    Returns:
        Exit code.
    """
    if args.output:
        # Synthesize to file
        print(f"  Synthesizing to {args.output}...")
        success = engine.synthesize_to_file(text, args.output, format=args.format)

        if success:
            # Show file info
            wave_utils = WaveUtils()
            info = wave_utils.get_wav_info(args.output)
            if info:
                dashboard.set_audio_info(info)
                if args.dashboard:
                    dashboard.print_dashboard()
                else:
                    print(f"  Done: {args.output} ({info['duration']:.2f}s)")
            return 0
        else:
            print("  Error: Synthesis failed")
            return 1
    else:
        # Speak aloud
        if args.dashboard:
            dashboard.set_status("Speaking...", "info")
            dashboard.print_dashboard()

        print(f"  Speaking: {text[:80]}{'...' if len(text) > 80 else ''}")
        success = engine.speak(text)

        if success:
            dashboard.set_status("Speech completed", "success")
            return 0
        else:
            dashboard.set_status("Speech failed", "error")
            return 1


def handle_batch_mode(args: argparse.Namespace, engine, dashboard: Dashboard,
                      config: Config) -> int:
    """Handle batch text-to-speech synthesis.

    Args:
        args: Parsed command-line arguments.
        engine: TTS engine instance.
        dashboard: Dashboard instance.
        config: Configuration instance.

    Returns:
        Exit code.
    """
    output_dir = args.output_dir or config.get("output", "directory", ".")

    queue = BatchQueue(
        engine=engine,
        output_dir=output_dir,
        output_format=args.format,
    )

    # Add tasks
    if args.batch:
        count = queue.add_file(args.batch, output_dir)
        if count == 0:
            print(f"  Error: No tasks added from {args.batch}")
            return 1
        print(f"  Added {count} tasks from {args.batch}")

    if args.batch_dir:
        count = queue.add_directory(args.batch_dir, output_dir)
        if count == 0:
            print(f"  Error: No tasks added from {args.batch_dir}")
            return 1
        print(f"  Added {count} tasks from {args.batch_dir}")

    if queue.task_count == 0:
        print("  Error: No tasks to process")
        return 1

    # Set up progress callback
    def on_progress(progress):
        if args.dashboard:
            dashboard.update_progress(
                progress.completed, progress.total,
                progress.failed
            )
            # Clear screen and redraw dashboard
            print("\033[2J\033[H", end="")
            dashboard.print_dashboard()
        else:
            dashboard.print_simple_progress(
                progress.completed, progress.total, progress.failed
            )

    queue.set_progress_callback(on_progress)

    # Process all tasks
    print(f"  Processing {queue.task_count} tasks...")
    progress = queue.process_all()

    # Print summary
    print()
    if progress.failed > 0:
        print(f"  Completed: {progress.completed}/{progress.total} ({progress.failed} failed)")
        return 1
    else:
        print(f"  All {progress.completed} tasks completed successfully")
        return 0
