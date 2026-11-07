"""Redakcja sekretow przed logowaniem lub zapisem diagnostyki."""

import os
import re

KEY_RE = re.compile(r"sk-[A-Za-z0-9_-]+")


def safe_error(error: Exception) -> str:
    text = str(error)
    for name, value in os.environ.items():
        if (
            value
            and len(value) >= 4
            and any(
                marker in name.upper() for marker in ("KEY", "TOKEN", "PASS", "SECRET")
            )
        ):
            text = text.replace(value, "[REDACTED]")
    return KEY_RE.sub("[REDACTED]", text)
