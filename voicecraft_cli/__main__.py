"""
VoiceCraft-CLI entry point.

Allows running the CLI via: python -m voicecraft_cli
"""

import sys
from voicecraft_cli.cli import main

if __name__ == "__main__":
    sys.exit(main())
