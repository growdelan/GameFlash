import os
from types import SimpleNamespace
import unittest

import main
from llms import gemini


GEMINI_MODEL = "gemini-3.5-flash"
VALIDATION_ARTICLE_URL = (
    "https://konsolowe.info/2024/10/oto-lista-wszystkich-gier-ulepszonych-na-ps5-pro/"
)
VALIDATION_ARTICLE_TEXT = """
Sony opublikowalo liste gier, ktore otrzymaja ulepszenia dla PlayStation 5 Pro.
Na liscie znalazly sie produkcje first-party oraz gry zewnetrznych wydawcow.
Aktualizacje maja poprawic jakosc obrazu, plynnosc animacji i wykorzystac nowe
mozliwosci konsoli, w tym PSSR. Dla graczy oznacza to lepsza oprawe bez
koniecznosci kupowania osobnych wersji gier.
"""


class MilestoneOneFourTests(unittest.TestCase):
    def setUp(self):
        self.original_load_dotenv = main.load_dotenv
        self.original_llm_model = os.environ.get("GEMINI_MODEL")
        self.original_recipients = os.environ.get("RECIPIENTS")

    def tearDown(self):
        main.load_dotenv = self.original_load_dotenv
        if self.original_llm_model is None:
            os.environ.pop("GEMINI_MODEL", None)
        else:
            os.environ["GEMINI_MODEL"] = self.original_llm_model
        if self.original_recipients is None:
            os.environ.pop("RECIPIENTS", None)
        else:
            os.environ["RECIPIENTS"] = self.original_recipients

    def test_load_config_uses_gemini_as_default_model(self):
        main.load_dotenv = lambda: None
        os.environ.pop("GEMINI_MODEL", None)
        os.environ["RECIPIENTS"] = "receiver@example.com"

        config = main.load_config()

        self.assertEqual(GEMINI_MODEL, config["GEMINI_MODEL"])

    def test_load_config_allows_model_override(self):
        main.load_dotenv = lambda: None
        os.environ["GEMINI_MODEL"] = "custom/model"
        os.environ["RECIPIENTS"] = "receiver@example.com"

        config = main.load_config()

        self.assertEqual("custom/model", config["GEMINI_MODEL"])

    def test_sanitize_model_response_removes_think_block(self):
        response = (
            "<think>analiza techniczna, ktora nie powinna trafic do maila</think>\n"
            "Tytuł: News\n\nPodsumowanie: Gotowy tekst."
        )

        sanitized = gemini.sanitize_model_response(response)

        self.assertEqual("Tytuł: News\n\nPodsumowanie: Gotowy tekst.", sanitized)
        self.assertNotIn("<think>", sanitized)
        self.assertNotIn("</think>", sanitized)

    def test_sanitize_model_response_removes_unclosed_think_block(self):
        response = (
            "Tytuł: News\n\nPodsumowanie: Gotowy tekst.\n\n"
            "<think>uciety proces rozumowania"
        )

        sanitized = gemini.sanitize_model_response(response)

        self.assertEqual("Tytuł: News\n\nPodsumowanie: Gotowy tekst.", sanitized)
        self.assertNotIn("<think>", sanitized)

    def test_sanitize_model_response_keeps_response_without_think_unchanged(self):
        response = "Tytuł: News\n\nPodsumowanie: Gotowy tekst."

        self.assertEqual(response, gemini.sanitize_model_response(response))

    def test_run_gemini_model_sends_prompt_and_generation_config(self):
        captured_request = {}
        original_client = gemini.gemini_client

        def fake_generate_content(**kwargs):
            captured_request.update(kwargs)
            return SimpleNamespace(text="Tytuł: News\n\nPodsumowanie: Gotowe.")

        fake_client = SimpleNamespace(
            models=SimpleNamespace(generate_content=fake_generate_content)
        )

        try:
            gemini.gemini_client = lambda _: fake_client
            result = gemini.run_gemini_model(
                gemini_api_key="test",
                model=GEMINI_MODEL,
                options=gemini.model_options(
                    prompt="prompt",
                    temperature=0.8,
                    max_tokens=1024,
                ),
            )
        finally:
            gemini.gemini_client = original_client

        self.assertEqual("Tytuł: News\n\nPodsumowanie: Gotowe.", result)
        self.assertEqual(GEMINI_MODEL, captured_request["model"])
        self.assertEqual(
            "prompt",
            captured_request["contents"][0].parts[0].text,
        )
        self.assertEqual(0.8, captured_request["config"].temperature)
        self.assertEqual(1024, captured_request["config"].max_output_tokens)

    def test_gemini_client_uses_request_timeout(self):
        captured_kwargs = {}
        original_client_class = gemini.genai.Client

        class FakeClient:
            def __init__(self, **kwargs):
                captured_kwargs.update(kwargs)

        try:
            gemini.genai.Client = FakeClient
            gemini.gemini_client("test-key")
        finally:
            gemini.genai.Client = original_client_class

        self.assertEqual("test-key", captured_kwargs["api_key"])
        self.assertEqual(
            gemini.GEMINI_REQUEST_TIMEOUT_MS,
            captured_kwargs["http_options"].timeout,
        )

    def test_run_gemini_model_raises_clear_error_for_empty_content(self):
        original_client = gemini.gemini_client

        def fake_generate_content(**kwargs):
            return SimpleNamespace(text=None)

        fake_client = SimpleNamespace(
            models=SimpleNamespace(generate_content=fake_generate_content)
        )

        try:
            gemini.gemini_client = lambda _: fake_client
            with self.assertRaisesRegex(RuntimeError, "pusta odpowiedz"):
                gemini.run_gemini_model(
                    gemini_api_key="test",
                    model=GEMINI_MODEL,
                    options=gemini.model_options(
                        prompt="prompt",
                        temperature=0.8,
                        max_tokens=1024,
                    ),
                )
        finally:
            gemini.gemini_client = original_client

    def test_run_gemini_model_retries_rate_limit_error(self):
        original_client = gemini.gemini_client
        original_sleep = gemini.time.sleep
        calls = []
        sleeps = []

        def fake_generate_content(**kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise RuntimeError("RESOURCE_EXHAUSTED retryDelay: '2s'")
            return SimpleNamespace(text="Tytuł: News\n\nPodsumowanie: Gotowe.")

        fake_client = SimpleNamespace(
            models=SimpleNamespace(generate_content=fake_generate_content)
        )

        try:
            gemini.gemini_client = lambda _: fake_client
            gemini.time.sleep = lambda delay: sleeps.append(delay)
            result = gemini.run_gemini_model(
                gemini_api_key="test",
                model=GEMINI_MODEL,
                options=gemini.model_options(
                    prompt="prompt",
                    temperature=0.8,
                    max_tokens=1024,
                ),
            )
        finally:
            gemini.gemini_client = original_client
            gemini.time.sleep = original_sleep

        self.assertEqual("Tytuł: News\n\nPodsumowanie: Gotowe.", result)
        self.assertEqual(2, len(calls))
        self.assertEqual([3.0], sleeps)

@unittest.skipUnless(
    os.environ.get("RUN_LIVE_GEMINI_VALIDATION") == "1",
    "Live Gemini validation is opt-in and does not run in normal tests.",
)
class GeminiLiveValidationTests(unittest.TestCase):
    def test_gemini_live_validation_returns_expected_output(self):
        from dotenv import load_dotenv

        load_dotenv(".env")
        api_key = os.getenv("GEMINI_API_KEY")
        self.assertTrue(api_key)

        summary = gemini.run_gemini_model(
            gemini_api_key=api_key,
            model=GEMINI_MODEL,
            options=gemini.model_options(
                prompt=gemini.summary_prompt(VALIDATION_ARTICLE_TEXT),
                temperature=0.8,
                max_tokens=1024,
            ),
            sanitize_response=False,
        )
        sanitized_response = gemini.sanitize_model_response(summary)

        print("Gemini live validation contains <think>:", "<think>" in summary.lower())
        self.assertIn("Tytu", sanitized_response)
        self.assertIn("Podsumowanie", sanitized_response)
        self.assertNotIn("<think>", sanitized_response.lower())
        self.assertNotIn("</think>", sanitized_response.lower())


if __name__ == "__main__":
    unittest.main()
