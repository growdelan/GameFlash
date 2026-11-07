import fcntl
from pathlib import Path
import signal
import tempfile
import unittest
from unittest.mock import patch

from utils.runtime import run_exclusive


class RuntimeTests(unittest.TestCase):
    def test_second_instance_cannot_enter_and_lock_is_released(self):
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / "lock"
            entered = []

            def first():
                entered.append("first")
                self.assertEqual(
                    75, run_exclusive(lambda: entered.append("second"), lock_path=lock)
                )

            self.assertEqual(0, run_exclusive(first, lock_path=lock))
            self.assertEqual(["first"], entered)
            self.assertEqual(0, run_exclusive(lambda: None, lock_path=lock))

    def test_timeout_is_not_swallowed_by_article_exception_handler(self):
        with tempfile.TemporaryDirectory() as directory:

            def blocked():
                try:
                    signal.raise_signal(signal.SIGALRM)
                except Exception:
                    self.fail("Timeout swallowed")

            self.assertEqual(
                124, run_exclusive(blocked, lock_path=Path(directory) / "lock")
            )

    def test_unhandled_exception_does_not_print_its_secret_message(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("builtins.print") as output,
        ):

            def failing():
                raise RuntimeError("private credential")

            self.assertEqual(
                1, run_exclusive(failing, lock_path=Path(directory) / "lock")
            )
            self.assertNotIn("private credential", str(output.call_args_list))
