"""
Batch processing package.

Provides batch text-to-speech synthesis with queue management,
file/directory scanning, and progress tracking.
"""

from voicecraft_cli.batch.queue import BatchQueue

__all__ = ["BatchQueue"]
