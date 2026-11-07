import json
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch, MagicMock

import httpx2
import openai
import main
from llms import openai_summary as llm

COMPLETE = "Tytuł: Nowa gra\n\nPodsumowanie: Studio zapowiedzialo nowa gre. Premiera w grudniu."


def api_error(status, headers=None, code=None):
    response = httpx2.Response(
        status,
        headers=headers,
        request=httpx2.Request("POST", "https://api.openai.com/v1/responses"),
    )
    return openai.APIStatusError(
        "secret-http-body", response=response, body={"code": code}
    )


class OpenAISummaryTests(unittest.TestCase):
    def run_model(self, side_effect=None, status="completed", text=COMPLETE):
        client = MagicMock()
        client.__enter__.return_value = client
        client.responses.create.side_effect = side_effect
        client.responses.create.return_value = SimpleNamespace(
            status=status, output_text=text
        )
        with patch.object(llm, "OpenAI", return_value=client) as factory:
            result = llm.run_openai_model(
                "test-key", llm.DEFAULT_MODEL, {"prompt": "article", "effort": "medium"}
            )
        return result, client, factory

    def test_model_config_defaults_and_override(self):
        with (
            patch.object(main, "load_dotenv"),
            patch.dict(os.environ, {"RECIPIENTS": "a@example.com"}, clear=True),
        ):
            config = main.load_config()
            self.assertEqual("gpt-6-luna", config["OPENAI_MODEL"])
            self.assertEqual("medium", config["OPENAI_REASONING_EFFORT"])
            os.environ["OPENAI_MODEL"] = "custom-model"
            self.assertEqual("custom-model", main.load_config()["OPENAI_MODEL"])

    def test_responses_contract_and_bounded_client(self):
        result, client, factory = self.run_model()
        self.assertEqual(COMPLETE, result)
        factory.assert_called_once_with(api_key="test-key", timeout=60, max_retries=0)
        client.responses.create.assert_called_once_with(
            model="gpt-6-luna",
            input="article",
            reasoning={"effort": "medium"},
            max_output_tokens=4096,
            store=False,
        )
        client.__exit__.assert_called_once()

    def test_transient_rate_limit_retries_once(self):
        with patch.object(llm.time, "sleep") as sleep:
            result, client, _ = self.run_model(
                [
                    api_error(429, {"retry-after": "2"}),
                    SimpleNamespace(status="completed", output_text=COMPLETE),
                ]
            )
        self.assertEqual(COMPLETE, result)
        self.assertEqual(2, client.responses.create.call_count)
        sleep.assert_called_once_with(2.0)

    def test_hour_long_rate_limit_does_not_sleep(self):
        with patch.object(llm.time, "sleep") as sleep:
            with self.assertRaisesRegex(llm.SummaryError, "dlugiej przerwy"):
                self.run_model([api_error(429, {"retry-after": "86264"})])
        sleep.assert_not_called()

    def test_quota_error_does_not_retry(self):
        with patch.object(llm.time, "sleep") as sleep:
            with self.assertRaisesRegex(llm.SummaryError, "HTTP 429"):
                self.run_model([api_error(429, code="insufficient_quota")])
        sleep.assert_not_called()

    def test_transient_server_errors_have_bounded_attempts(self):
        with patch.object(llm.time, "sleep") as sleep:
            with self.assertRaisesRegex(llm.SummaryError, "HTTP 503"):
                self.run_model([api_error(503)] * 3)
        self.assertEqual(2, sleep.call_count)

    def test_timeout_has_bounded_attempts(self):
        with patch.object(llm.time, "sleep") as sleep:
            with self.assertRaisesRegex(llm.SummaryError, "connection"):
                self.run_model(
                    [
                        openai.APITimeoutError(
                            request=httpx2.Request("POST", "https://api.openai.com")
                        )
                    ]
                    * 3
                )
        self.assertEqual(2, sleep.call_count)

    def test_auth_error_does_not_include_http_body(self):
        with self.assertRaises(llm.SummaryError) as error:
            self.run_model([api_error(401)])
        self.assertNotIn("secret-http-body", str(error.exception))

    def test_incomplete_response_is_rejected_even_when_text_ends_with_period(self):
        with self.assertRaisesRegex(llm.SummaryError, "nie zostala ukonczona"):
            self.run_model(status="incomplete")

    def test_empty_response_is_rejected(self):
        with self.assertRaisesRegex(llm.SummaryError, "pusta odpowiedz"):
            self.run_model(text="")

    def test_missing_key_is_rejected_before_request(self):
        with patch.object(llm, "OpenAI") as factory:
            with self.assertRaisesRegex(llm.SummaryError, "Brak OPENAI_API_KEY"):
                llm.run_openai_model("", "gpt-6-luna", {})
        factory.assert_not_called()

    def test_sanitize_removes_reasoning_blocks(self):
        self.assertEqual(
            COMPLETE,
            llm.sanitize_model_response(
                "<think>ukryta analiza</think>" + COMPLETE + "<think>ucięte"
            ),
        )

    def test_invalid_retry_header_falls_back_and_milliseconds_are_supported(self):
        self.assertEqual(
            2, llm.retry_delay_seconds(api_error(429, {"retry-after": "broken"}), 1)
        )
        self.assertEqual(
            0.5, llm.retry_delay_seconds(api_error(429, {"retry-after-ms": "500"}), 0)
        )


@unittest.skipUnless(
    os.environ.get("RUN_LIVE_OPENAI_VALIDATION") == "1",
    "Live OpenAI validation is opt-in.",
)
class OpenAILiveValidationTests(unittest.TestCase):
    def test_real_summary_without_sheets_or_smtp(self):
        config = main.load_config()
        text = "Studio zapowiedzialo gre wyscigowa. Premiera odbedzie sie w grudniu na PC. Gra bedzie miala tryb dla dwoch graczy. Cena nie zostala jeszcze ogloszona."
        result = llm.run_openai_model(
            config["OPENAI_API_KEY"],
            config["OPENAI_MODEL"],
            {
                "prompt": llm.summary_prompt(text),
                "effort": config["OPENAI_REASONING_EFFORT"],
            },
        )
        self.assertTrue(main.is_complete_summary_result(result))
        self.assertIn("grud", result.lower())
        self.assertLessEqual(len(result.split()), 110)
