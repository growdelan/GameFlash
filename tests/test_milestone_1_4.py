import os
from types import SimpleNamespace
import unittest

import main
from llms import groq


QWEN_MODEL = "qwen/qwen3.6-27b"
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
        self.original_llm_model = os.environ.get("LLM_MODEL")
        self.original_recipients = os.environ.get("RECIPIENTS")

    def tearDown(self):
        main.load_dotenv = self.original_load_dotenv
        if self.original_llm_model is None:
            os.environ.pop("LLM_MODEL", None)
        else:
            os.environ["LLM_MODEL"] = self.original_llm_model
        if self.original_recipients is None:
            os.environ.pop("RECIPIENTS", None)
        else:
            os.environ["RECIPIENTS"] = self.original_recipients

    def test_load_config_uses_qwen_as_default_model(self):
        main.load_dotenv = lambda: None
        os.environ.pop("LLM_MODEL", None)
        os.environ["RECIPIENTS"] = "receiver@example.com"

        config = main.load_config()

        self.assertEqual(QWEN_MODEL, config["LLM_MODEL"])

    def test_load_config_allows_model_override(self):
        main.load_dotenv = lambda: None
        os.environ["LLM_MODEL"] = "custom/model"
        os.environ["RECIPIENTS"] = "receiver@example.com"

        config = main.load_config()

        self.assertEqual("custom/model", config["LLM_MODEL"])

    def test_sanitize_model_response_removes_think_block(self):
        response = (
            "<think>analiza techniczna, ktora nie powinna trafic do maila</think>\n"
            "Tytuł: News\n\nPodsumowanie: Gotowy tekst."
        )

        sanitized = groq.sanitize_model_response(response)

        self.assertEqual("Tytuł: News\n\nPodsumowanie: Gotowy tekst.", sanitized)
        self.assertNotIn("<think>", sanitized)
        self.assertNotIn("</think>", sanitized)

    def test_sanitize_model_response_removes_unclosed_think_block(self):
        response = (
            "Tytuł: News\n\nPodsumowanie: Gotowy tekst.\n\n"
            "<think>uciety proces rozumowania"
        )

        sanitized = groq.sanitize_model_response(response)

        self.assertEqual("Tytuł: News\n\nPodsumowanie: Gotowy tekst.", sanitized)
        self.assertNotIn("<think>", sanitized)

    def test_sanitize_model_response_keeps_response_without_think_unchanged(self):
        response = "Tytuł: News\n\nPodsumowanie: Gotowy tekst."

        self.assertEqual(response, groq.sanitize_model_response(response))

    def test_qwen_request_hides_reasoning_and_uses_minimum_token_budget(self):
        captured_request = {}
        original_client = groq.groq_client

        def fake_create(**kwargs):
            captured_request.update(kwargs)
            message = SimpleNamespace(content="Tytuł: News\n\nPodsumowanie: Gotowe.")
            choice = SimpleNamespace(message=message)
            return SimpleNamespace(choices=[choice])

        fake_client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
        )

        try:
            groq.groq_client = lambda _: fake_client
            result = groq.run_groq_model(
                groq_api_key="test",
                model=QWEN_MODEL,
                options=groq.model_options(
                    prompt="prompt",
                    temperature=0.8,
                    max_tokens=1024,
                ),
            )
        finally:
            groq.groq_client = original_client

        self.assertEqual("Tytuł: News\n\nPodsumowanie: Gotowe.", result)
        self.assertEqual("hidden", captured_request["reasoning_format"])
        self.assertEqual(groq.QWEN_MIN_MAX_TOKENS, captured_request["max_tokens"])

    def test_groq_client_uses_request_timeout(self):
        captured_kwargs = {}
        original_groq_class = groq.Groq

        class FakeGroq:
            def __init__(self, **kwargs):
                captured_kwargs.update(kwargs)

        try:
            groq.Groq = FakeGroq
            groq.groq_client("test-key")
        finally:
            groq.Groq = original_groq_class

        self.assertEqual("test-key", captured_kwargs["api_key"])
        self.assertEqual(
            groq.GROQ_REQUEST_TIMEOUT_SECONDS,
            captured_kwargs["timeout"],
        )

    def test_run_groq_model_raises_clear_error_for_empty_content(self):
        original_client = groq.groq_client

        def fake_create(**kwargs):
            message = SimpleNamespace(content=None)
            choice = SimpleNamespace(message=message)
            return SimpleNamespace(choices=[choice])

        fake_client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
        )

        try:
            groq.groq_client = lambda _: fake_client
            with self.assertRaisesRegex(RuntimeError, "pusta odpowiedz"):
                groq.run_groq_model(
                    groq_api_key="test",
                    model=QWEN_MODEL,
                    options=groq.model_options(
                        prompt="prompt",
                        temperature=0.8,
                        max_tokens=1024,
                    ),
                )
        finally:
            groq.groq_client = original_client

    def test_proofreading_keeps_source_link_when_model_omits_it(self):
        source_news = (
            "Tytuł: News\n\n"
            "Podsumowanie: Szkic.\n\n"
            f"Link: {VALIDATION_ARTICLE_URL}\n\n"
            "################################"
        )
        proofreading_news = "Tytuł: News\n\nPodsumowanie: Gotowy tekst."

        result = main.ensure_link_in_proofreading_result(proofreading_news, source_news)

        self.assertIn(f"Link: {VALIDATION_ARTICLE_URL}", result)


@unittest.skipUnless(
    os.environ.get("RUN_LIVE_GROQ_VALIDATION") == "1",
    "Live Groq validation is opt-in and does not run in normal tests.",
)
class QwenLiveValidationTests(unittest.TestCase):
    def test_qwen_live_validation_reports_reasoning_and_sanitizes_output(self):
        from dotenv import load_dotenv

        load_dotenv(".env")
        api_key = os.getenv("GROQ_API_KEY")
        self.assertTrue(api_key)

        summary = groq.run_groq_model(
            groq_api_key=api_key,
            model=QWEN_MODEL,
            options=groq.model_options(
                prompt=groq.summary_prompt(VALIDATION_ARTICLE_TEXT),
                temperature=0.8,
                max_tokens=1024,
            ),
            sanitize_response=False,
        )
        proofread = groq.run_groq_model(
            groq_api_key=api_key,
            model=QWEN_MODEL,
            options=groq.model_options(
                prompt=groq.proofreading_prompt(
                    f"{summary}\n\nLink: {VALIDATION_ARTICLE_URL}"
                ),
                temperature=1,
                max_tokens=1024,
            ),
            sanitize_response=False,
        )

        raw_response = f"{summary}\n{proofread}"
        sanitized_proofread = main.ensure_link_in_proofreading_result(
            groq.sanitize_model_response(proofread),
            f"{summary}\n\nLink: {VALIDATION_ARTICLE_URL}",
        )
        sanitized_response = f"{groq.sanitize_model_response(summary)}\n{sanitized_proofread}"

        print("Qwen live validation contains <think>:", "<think>" in raw_response.lower())
        self.assertIn("Tytu", sanitized_response)
        self.assertIn("Podsumowanie", sanitized_response)
        self.assertIn(VALIDATION_ARTICLE_URL, sanitized_response)
        self.assertNotIn("<think>", sanitized_response.lower())
        self.assertNotIn("</think>", sanitized_response.lower())


if __name__ == "__main__":
    unittest.main()
