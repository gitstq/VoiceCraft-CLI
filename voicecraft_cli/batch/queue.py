"""
Batch synthesis queue module.

Manages batch text-to-speech operations with support for reading
from files, directories, and inline text lists. Provides progress
tracking and callback hooks for UI integration.
"""

import os
import threading
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from voicecraft_cli.utils.logger import get_logger

logger = get_logger(__name__)


class TaskStatus(Enum):
    """Status of a batch synthesis task."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class BatchTask:
    """A single task in the batch synthesis queue.

    Attributes:
        task_id: Unique task identifier.
        text: Text content to synthesize.
        source: Source file path or description.
        output_path: Output audio file path.
        status: Current task status.
        error: Error message if the task failed.
        duration: Processing time in seconds.
    """
    task_id: int
    text: str
    source: str = ""
    output_path: str = ""
    status: TaskStatus = TaskStatus.PENDING
    error: str = ""
    duration: float = 0.0


@dataclass
class BatchProgress:
    """Progress information for the batch queue.

    Attributes:
        total: Total number of tasks.
        completed: Number of completed tasks.
        failed: Number of failed tasks.
        processing: Number of currently processing tasks.
        pending: Number of pending tasks.
    """
    total: int = 0
    completed: int = 0
    failed: int = 0
    processing: int = 0
    pending: int = 0

    @property
    def progress_percent(self) -> float:
        """Calculate completion percentage.

        Returns:
            Float from 0.0 to 100.0.
        """
        if self.total == 0:
            return 0.0
        return (self.completed + self.failed) / self.total * 100.0


class BatchQueue:
    """Batch text-to-speech synthesis queue.

    Manages a queue of synthesis tasks with support for:
    - Reading text from individual files or entire directories
    - Inline text lists
    - Progress tracking with callbacks
    - Threaded processing

    Usage:
        queue = BatchQueue(engine)
        queue.add_text("Hello world", output="hello.wav")
        queue.add_file("input.txt", output_dir="output/")
        queue.process_all()
    """

    def __init__(self, engine=None, output_dir: str = ".",
                 output_format: str = "wav") -> None:
        """Initialize the batch queue.

        Args:
            engine: TTS engine instance to use for synthesis.
            output_dir: Default output directory for generated files.
            output_format: Default output audio format.
        """
        self._engine = engine
        self._output_dir = output_dir
        self._output_format = output_format
        self._tasks: List[BatchTask] = []
        self._next_id = 0
        self._lock = threading.Lock()
        self._progress_callback: Optional[Callable[[BatchProgress], None]] = None
        self._task_callback: Optional[Callable[[BatchTask], None]] = None
        self._stop_flag = False

    def set_engine(self, engine) -> None:
        """Set the TTS engine for synthesis.

        Args:
            engine: TTS engine instance.
        """
        self._engine = engine

    def set_progress_callback(self, callback: Callable[[BatchProgress], None]) -> None:
        """Set a callback function for progress updates.

        Args:
            callback: Function accepting a BatchProgress argument.
        """
        self._progress_callback = callback

    def set_task_callback(self, callback: Callable[[BatchTask], None]) -> None:
        """Set a callback function for individual task completion.

        Args:
            callback: Function accepting a BatchTask argument.
        """
        self._task_callback = callback

    def add_text(self, text: str, output_path: str = "",
                 source: str = "inline") -> BatchTask:
        """Add a text synthesis task to the queue.

        Args:
            text: Text content to synthesize.
            output_path: Output file path (auto-generated if empty).
            source: Description of the text source.

        Returns:
            The created BatchTask.
        """
        with self._lock:
            task_id = self._next_id
            self._next_id += 1

            if not output_path:
                ext = f".{self._output_format}" if self._output_format else ".wav"
                output_path = os.path.join(
                    self._output_dir,
                    f"task_{task_id:04d}{ext}"
                )

            task = BatchTask(
                task_id=task_id,
                text=text,
                source=source,
                output_path=output_path,
            )
            self._tasks.append(task)
            logger.debug(f"Added task {task_id}: {text[:50]}...")
            return task

    def add_file(self, filepath: str, output_dir: str = "") -> int:
        """Add tasks from a text file (one utterance per line).

        Args:
            filepath: Path to the input text file.
            output_dir: Output directory (uses default if empty).

        Returns:
            Number of tasks added.
        """
        if not os.path.isfile(filepath):
            logger.error(f"File not found: {filepath}")
            return 0

        out_dir = output_dir or self._output_dir
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        count = 0

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue  # Skip empty lines and comments

                    ext = f".{self._output_format}" if self._output_format else ".wav"
                    output_path = os.path.join(
                        out_dir,
                        f"{base_name}_{line_num:04d}{ext}"
                    )
                    self.add_text(line, output_path, source=filepath)
                    count += 1

            logger.info(f"Added {count} tasks from {filepath}")
            return count

        except Exception as e:
            logger.error(f"Failed to read file {filepath}: {e}")
            return 0

    def add_directory(self, dirpath: str, output_dir: str = "",
                      extensions: Optional[List[str]] = None) -> int:
        """Add tasks from all text files in a directory.

        Args:
            dirpath: Path to the directory containing text files.
            output_dir: Output directory (uses default if empty).
            extensions: List of file extensions to include (default: ['.txt']).

        Returns:
            Number of tasks added.
        """
        if not os.path.isdir(dirpath):
            logger.error(f"Directory not found: {dirpath}")
            return 0

        if extensions is None:
            extensions = [".txt"]

        total = 0
        for filename in sorted(os.listdir(dirpath)):
            filepath = os.path.join(dirpath, filename)
            if os.path.isfile(filepath):
                _, ext = os.path.splitext(filename)
                if ext.lower() in extensions:
                    total += self.add_file(filepath, output_dir)

        logger.info(f"Added {total} tasks from directory {dirpath}")
        return total

    def get_progress(self) -> BatchProgress:
        """Get current batch progress.

        Returns:
            BatchProgress object with current statistics.
        """
        completed = 0
        failed = 0
        processing = 0
        pending = 0

        for task in self._tasks:
            if task.status == TaskStatus.COMPLETED:
                completed += 1
            elif task.status == TaskStatus.FAILED:
                failed += 1
            elif task.status == TaskStatus.PROCESSING:
                processing += 1
            else:
                pending += 1

        return BatchProgress(
            total=len(self._tasks),
            completed=completed,
            failed=failed,
            processing=processing,
            pending=pending,
        )

    def _notify_progress(self) -> None:
        """Send progress update to callback if registered."""
        if self._progress_callback:
            try:
                self._progress_callback(self.get_progress())
            except Exception as e:
                logger.error(f"Progress callback error: {e}")

    def _notify_task(self, task: BatchTask) -> None:
        """Send task update to callback if registered."""
        if self._task_callback:
            try:
                self._task_callback(task)
            except Exception as e:
                logger.error(f"Task callback error: {e}")

    def process_all(self) -> BatchProgress:
        """Process all pending tasks sequentially.

        Returns:
            Final BatchProgress after all tasks are processed.
        """
        self._stop_flag = False
        logger.info(f"Starting batch processing: {len(self._tasks)} tasks")

        for task in self._tasks:
            if self._stop_flag:
                logger.info("Batch processing stopped by user")
                break

            if task.status != TaskStatus.PENDING:
                continue

            self._process_task(task)
            self._notify_progress()

        progress = self.get_progress()
        logger.info(
            f"Batch complete: {progress.completed}/{progress.total} succeeded, "
            f"{progress.failed} failed"
        )
        return progress

    def stop(self) -> None:
        """Signal the batch processor to stop."""
        self._stop_flag = True
        logger.info("Stop requested")

    def _process_task(self, task: BatchTask) -> None:
        """Process a single synthesis task.

        Args:
            task: The BatchTask to process.
        """
        task.status = TaskStatus.PROCESSING
        start_time = time.time()

        try:
            if self._engine is None:
                raise RuntimeError("No TTS engine configured")

            # Ensure output directory exists
            out_dir = os.path.dirname(task.output_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)

            success = self._engine.synthesize_to_file(
                task.text,
                task.output_path,
                format=self._output_format,
            )

            task.duration = time.time() - start_time

            if success:
                task.status = TaskStatus.COMPLETED
                logger.info(
                    f"Task {task.task_id} completed: {task.output_path} "
                    f"({task.duration:.2f}s)"
                )
            else:
                task.status = TaskStatus.FAILED
                task.error = "Engine synthesis failed"
                logger.warning(f"Task {task.task_id} failed: engine error")

        except Exception as e:
            task.duration = time.time() - start_time
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"Task {task.task_id} failed: {e}")

        self._notify_task(task)

    def get_tasks(self) -> List[BatchTask]:
        """Get all tasks in the queue.

        Returns:
            List of all BatchTask objects.
        """
        return list(self._tasks)

    def clear(self) -> None:
        """Remove all tasks from the queue."""
        self._tasks.clear()
        self._next_id = 0
        logger.info("Batch queue cleared")

    @property
    def task_count(self) -> int:
        """Get the number of tasks in the queue.

        Returns:
            Number of tasks.
        """
        return len(self._tasks)
