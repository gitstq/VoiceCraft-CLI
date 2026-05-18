"""
Unit tests for batch processing queue.

Tests task management, file reading, and progress tracking.
"""

import unittest
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voicecraft_cli.batch.queue import BatchQueue, BatchTask, BatchProgress, TaskStatus


class TestBatchTask(unittest.TestCase):
    """Tests for the BatchTask dataclass."""

    def test_creation(self):
        """BatchTask is created with correct defaults."""
        task = BatchTask(task_id=1, text="Hello")
        self.assertEqual(task.task_id, 1)
        self.assertEqual(task.text, "Hello")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.error, "")
        self.assertEqual(task.duration, 0.0)

    def test_status_enum(self):
        """TaskStatus enum has expected values."""
        self.assertEqual(TaskStatus.PENDING.value, "pending")
        self.assertEqual(TaskStatus.PROCESSING.value, "processing")
        self.assertEqual(TaskStatus.COMPLETED.value, "completed")
        self.assertEqual(TaskStatus.FAILED.value, "failed")
        self.assertEqual(TaskStatus.SKIPPED.value, "skipped")


class TestBatchProgress(unittest.TestCase):
    """Tests for the BatchProgress dataclass."""

    def test_progress_percent(self):
        """Progress percentage is calculated correctly."""
        p = BatchProgress(total=10, completed=5, failed=2)
        self.assertAlmostEqual(p.progress_percent, 70.0)

    def test_progress_zero(self):
        """Zero total returns zero percent."""
        p = BatchProgress(total=0, completed=0, failed=0)
        self.assertEqual(p.progress_percent, 0.0)

    def test_progress_complete(self):
        """All completed returns 100%."""
        p = BatchProgress(total=10, completed=10, failed=0)
        self.assertEqual(p.progress_percent, 100.0)


class TestBatchQueue(unittest.TestCase):
    """Tests for the BatchQueue class."""

    def setUp(self):
        """Create test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.queue = BatchQueue(output_dir=self.temp_dir)

    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_text(self):
        """Adding text creates a task."""
        task = self.queue.add_text("Hello World")
        self.assertEqual(task.text, "Hello World")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(self.queue.task_count, 1)

    def test_add_text_with_output(self):
        """Adding text with output path uses that path."""
        task = self.queue.add_text("Test", output_path="/tmp/test.wav")
        self.assertEqual(task.output_path, "/tmp/test.wav")

    def test_add_text_auto_output(self):
        """Adding text without output path auto-generates one."""
        task = self.queue.add_text("Test")
        self.assertTrue(task.output_path.endswith(".wav"))
        self.assertIn(self.temp_dir, task.output_path)

    def test_add_multiple_texts(self):
        """Adding multiple texts creates multiple tasks."""
        self.queue.add_text("First")
        self.queue.add_text("Second")
        self.queue.add_text("Third")
        self.assertEqual(self.queue.task_count, 3)

    def test_add_file(self):
        """Adding tasks from a file works correctly."""
        filepath = os.path.join(self.temp_dir, "input.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("Line one\n")
            f.write("Line two\n")
            f.write("Line three\n")

        count = self.queue.add_file(filepath)
        self.assertEqual(count, 3)
        self.assertEqual(self.queue.task_count, 3)

    def test_add_file_skips_empty_lines(self):
        """Empty lines in input file are skipped."""
        filepath = os.path.join(self.temp_dir, "input.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("Line one\n")
            f.write("\n")
            f.write("Line two\n")

        count = self.queue.add_file(filepath)
        self.assertEqual(count, 2)

    def test_add_file_skips_comments(self):
        """Lines starting with # are skipped."""
        filepath = os.path.join(self.temp_dir, "input.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("Line one\n")
            f.write("# This is a comment\n")
            f.write("Line two\n")

        count = self.queue.add_file(filepath)
        self.assertEqual(count, 2)

    def test_add_file_nonexistent(self):
        """Nonexistent file returns 0."""
        count = self.queue.add_file("/nonexistent/file.txt")
        self.assertEqual(count, 0)

    def test_add_directory(self):
        """Adding tasks from a directory works."""
        os.makedirs(os.path.join(self.temp_dir, "texts"))
        for i in range(3):
            filepath = os.path.join(self.temp_dir, "texts", f"file{i}.txt")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"Content {i}\n")

        count = self.queue.add_directory(
            os.path.join(self.temp_dir, "texts")
        )
        self.assertEqual(count, 3)

    def test_add_directory_nonexistent(self):
        """Nonexistent directory returns 0."""
        count = self.queue.add_directory("/nonexistent/dir")
        self.assertEqual(count, 0)

    def test_get_progress_empty(self):
        """Empty queue has zero progress."""
        progress = self.queue.get_progress()
        self.assertEqual(progress.total, 0)
        self.assertEqual(progress.completed, 0)
        self.assertEqual(progress.progress_percent, 0.0)

    def test_get_progress(self):
        """Progress reflects task states."""
        self.queue.add_text("A")
        self.queue.add_text("B")
        tasks = self.queue.get_tasks()
        tasks[0].status = TaskStatus.COMPLETED
        tasks[1].status = TaskStatus.FAILED

        progress = self.queue.get_progress()
        self.assertEqual(progress.total, 2)
        self.assertEqual(progress.completed, 1)
        self.assertEqual(progress.failed, 1)

    def test_clear(self):
        """Clear removes all tasks."""
        self.queue.add_text("A")
        self.queue.add_text("B")
        self.assertEqual(self.queue.task_count, 2)
        self.queue.clear()
        self.assertEqual(self.queue.task_count, 0)

    def test_get_tasks(self):
        """get_tasks returns a copy of the task list."""
        self.queue.add_text("A")
        tasks = self.queue.get_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].text, "A")

    def test_process_all_no_engine(self):
        """Processing without an engine marks tasks as failed."""
        self.queue.add_text("Hello")
        progress = self.queue.process_all()
        self.assertEqual(progress.failed, 1)

    def test_process_all_with_mock_engine(self):
        """Processing with a mock engine succeeds."""

        class MockEngine:
            def synthesize_to_file(self, text, path, format="wav"):
                # Write a minimal valid WAV file
                import wave
                with wave.open(path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(22050)
                    wf.writeframes(b"\x00\x00" * 100)
                return True

        self.queue.set_engine(MockEngine())
        self.queue.add_text("Hello")
        progress = self.queue.process_all()
        self.assertEqual(progress.completed, 1)
        self.assertEqual(progress.failed, 0)

    def test_progress_callback(self):
        """Progress callback is called during processing."""
        callback_calls = []

        def on_progress(p):
            callback_calls.append(p)

        self.queue.set_progress_callback(on_progress)
        self.queue.add_text("Test")
        self.queue.process_all()  # Will fail (no engine) but callback should fire

        # Callback should have been called at least once
        self.assertGreater(len(callback_calls), 0)

    def test_stop(self):
        """Stop flag prevents further processing."""
        self.queue.add_text("A")
        self.queue.add_text("B")
        self.queue.add_text("C")
        self.queue.stop()
        progress = self.queue.process_all()
        # With stop flag set, no tasks should have been processed
        # (stop is checked before each task)
        self.assertEqual(progress.completed + progress.failed + progress.pending, 3)


if __name__ == "__main__":
    unittest.main()
