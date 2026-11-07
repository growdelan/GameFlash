import os
import unittest
from unittest.mock import patch

from utils.security import safe_error


class SecurityTests(unittest.TestCase):
    def test_env_secrets_and_openai_key_patterns_are_redacted(self):
        with patch.dict(
            os.environ,
            {"SENDER_PASS": "smtp-private", "OPENAI_API_KEY": "sk-test-private"},
        ):
            result = safe_error(
                RuntimeError("smtp-private sk-test-private sk-another-private HTTP 429")
            )
        self.assertNotIn("smtp-private", result)
        self.assertNotIn("sk-", result)
        self.assertIn("HTTP 429", result)
