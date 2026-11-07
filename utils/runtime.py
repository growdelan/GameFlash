"""Blokada pojedynczego procesu i twardy limit przebiegu na Unix."""

import fcntl
import os
from pathlib import Path
import signal

MAX_RUNTIME_SECONDS = 1800
LOCK_PATH = Path(__file__).resolve().parents[1] / ".gameflash.lock"


class RunTimeout(BaseException):
    """Nie jest przechwytywany przez retry pojedynczego artykulu."""


def _timeout(signum, frame):
    raise RunTimeout()


def run_exclusive(callback, *, lock_path=LOCK_PATH, timeout=MAX_RUNTIME_SECONDS):
    os.umask(0o077)
    with open(lock_path, "a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("GameFlash: inny przebieg jest aktywny.")
            return 75
        previous_handler = signal.signal(signal.SIGALRM, _timeout)
        signal.alarm(timeout)
        try:
            callback()
            return 0
        except RunTimeout:
            print("GameFlash: przekroczono limit czasu przebiegu.")
            return 124
        except Exception as exc:
            # Wyjatki integracji moga zawierac klucze lub fragmenty HTTP.
            print(f"GameFlash: przebieg zakonczony bledem ({type(exc).__name__}).")
            return 1
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, previous_handler)
