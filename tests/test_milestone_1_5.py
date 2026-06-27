import unittest

import main
from scrapers import jina


ARTICLE_URL = "https://konsolowe.info/2026/06/test-artykul/"
JINA_URL = f"https://r.jina.ai/{ARTICLE_URL}"
WP_API_URL = "https://konsolowe.info/wp-json/wp/v2/posts/123"


class FakeResponse:
    def __init__(self, text="", status_code=200, headers=None, json_data=None):
        self.text = text
        self.status_code = status_code
        self.headers = headers or {}
        self._json_data = json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise jina.requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        if self._json_data is None:
            raise RuntimeError("no json")
        return self._json_data


class MilestoneOneFiveJinaTests(unittest.TestCase):
    def setUp(self):
        self.original_get = jina.requests.get

    def tearDown(self):
        jina.requests.get = self.original_get

    def test_validate_article_text_rejects_jina_403_body(self):
        with self.assertRaisesRegex(jina.ArticleContentError, "blad zrodla"):
            jina.validate_article_text(
                "Title: 403 Forbidden\n\n"
                f"URL Source: {ARTICLE_URL}\n\n"
                "Warning: Target URL returned error 403: Forbidden"
            )

    def test_jina_403_body_uses_wordpress_api_fallback(self):
        calls = []
        article_html = (
            "<html><head>"
            '<link rel="alternate" type="application/json" '
            'href="https://konsolowe.info/wp-json/wp/v2/posts/123">'
            "</head><body></body></html>"
        )
        article_text = (
            "To jest pelna tresc artykulu z WordPress REST API. "
            "Zawiera informacje o premierze gry, reakcjach graczy, wydaniu "
            "pudelkowym oraz szerszym kontekscie rynku. "
        ) * 4

        def fake_get(url, timeout=30):
            calls.append((url, timeout))
            if url == JINA_URL:
                return FakeResponse(
                    "Title: 403 Forbidden\nWarning: Target URL returned error 403"
                )
            if url == ARTICLE_URL:
                return FakeResponse(article_html)
            if url == WP_API_URL:
                return FakeResponse(
                    json_data={"content": {"rendered": f"<p>{article_text}</p>"}}
                )
            raise AssertionError(f"Unexpected URL: {url}")

        jina.requests.get = fake_get

        result = jina.fetch_article_text(ARTICLE_URL)

        self.assertIn("pelna tresc artykulu", result)
        self.assertNotIn("403 Forbidden", result)
        self.assertEqual(
            [(JINA_URL, 30), (ARTICLE_URL, 30), (WP_API_URL, 30)],
            calls,
        )

    def test_jina_http_error_uses_wordpress_api_fallback(self):
        calls = []
        article_html = (
            "<html><head>"
            '<link rel="alternate" type="application/json" '
            'href="https://konsolowe.info/wp-json/wp/v2/posts/123">'
            "</head><body></body></html>"
        )
        article_text = (
            "To jest pelna tresc artykulu pobrana po bledzie HTTP Jina. "
            "Zawiera opis wydarzen, kontekst rynkowy i informacje wystarczajace "
            "do przygotowania rzetelnego podsumowania. "
        ) * 4

        def fake_get(url, timeout=30):
            calls.append((url, timeout))
            if url == JINA_URL:
                return FakeResponse(status_code=503)
            if url == ARTICLE_URL:
                return FakeResponse(article_html)
            if url == WP_API_URL:
                return FakeResponse(
                    json_data={"content": {"rendered": f"<p>{article_text}</p>"}}
                )
            raise AssertionError(f"Unexpected URL: {url}")

        jina.requests.get = fake_get

        result = jina.fetch_article_text(ARTICLE_URL)

        self.assertIn("pobrana po bledzie HTTP Jina", result)
        self.assertEqual(
            [(JINA_URL, 30), (ARTICLE_URL, 30), (WP_API_URL, 30)],
            calls,
        )

    def test_jina_403_body_uses_direct_html_when_wordpress_api_fails(self):
        article_text = (
            "Bezposredni HTML zawiera realna tresc artykulu o grze, "
            "wydaniu pudelkowym, reakcji studia i konsekwencjach dla rynku. "
        ) * 4

        def fake_get(url, timeout=30):
            if url == JINA_URL:
                return FakeResponse(
                    "Title: 403 Forbidden\nWarning: Target URL returned error 403"
                )
            if url == ARTICLE_URL:
                return FakeResponse(
                    "<html><body><article><div id='entry'>"
                    f"<p>{article_text}</p>"
                    "</div></article></body></html>",
                    headers={"Link": '<https://konsolowe.info/wp-json/wp/v2/posts/123>; rel="alternate"'},
                )
            if url == WP_API_URL:
                return FakeResponse(status_code=500)
            raise AssertionError(f"Unexpected URL: {url}")

        jina.requests.get = fake_get

        result = jina.fetch_article_text(ARTICLE_URL)

        self.assertIn("Bezposredni HTML zawiera realna tresc", result)
        self.assertNotIn("403 Forbidden", result)

    def test_fetch_article_text_raises_when_all_sources_fail(self):
        def fake_get(url, timeout=30):
            if url == JINA_URL:
                return FakeResponse(
                    "Title: 403 Forbidden\nWarning: Target URL returned error 403"
                )
            if url == ARTICLE_URL:
                return FakeResponse("<html><body><article>Za krotko.</article></body></html>")
            raise AssertionError(f"Unexpected URL: {url}")

        jina.requests.get = fake_get

        with self.assertRaises(jina.ArticleContentError):
            jina.fetch_article_text(ARTICLE_URL)


class MilestoneOneFivePipelineTests(unittest.TestCase):
    def setUp(self):
        self.original_fetch_article = main.jina.fetch_article_text
        self.original_run_model = main.groq.run_groq_model

    def tearDown(self):
        main.jina.fetch_article_text = self.original_fetch_article
        main.groq.run_groq_model = self.original_run_model

    def test_fetch_error_prevents_403_body_from_reaching_summary_prompt(self):
        prompts = []
        main.jina.fetch_article_text = lambda url: (_ for _ in ()).throw(
            RuntimeError("Jina zwrocila blad zrodla zamiast tresci.")
        )

        def fake_run_model(groq_api_key, model, options):
            prompts.append(options["prompt"])
            return "unused"

        main.groq.run_groq_model = fake_run_model

        result = main.summarize_news(
            {"GROQ_API": "test", "LLM_MODEL": "model"},
            [ARTICLE_URL],
        )

        self.assertEqual([], result)
        self.assertEqual([], prompts)

    def test_incomplete_proofreading_result_is_not_sent(self):
        main.groq.run_groq_model = lambda groq_api_key, model, options: (
            "Tytuł: News\n\n"
            "Podsumowanie: Tekst jest uciety w polowie zdania\n\n"
            f"Link: {ARTICLE_URL}"
        )

        result = main.news_proofreading(
            {"GROQ_API": "test", "LLM_MODEL": "model"},
            [
                "Tytuł: News\n\n"
                "Podsumowanie: Szkic.\n\n"
                f"Link: {ARTICLE_URL}\n\n"
                "################################"
            ],
        )

        self.assertEqual([], result)

    def test_complete_proofreading_result_is_kept(self):
        main.groq.run_groq_model = lambda groq_api_key, model, options: (
            "Tytuł: News\n\n"
            "Podsumowanie: Tekst jest kompletny.\n\n"
            f"Link: {ARTICLE_URL}"
        )

        result = main.news_proofreading(
            {"GROQ_API": "test", "LLM_MODEL": "model"},
            [
                "Tytuł: News\n\n"
                "Podsumowanie: Szkic.\n\n"
                f"Link: {ARTICLE_URL}\n\n"
                "################################"
            ],
        )

        self.assertEqual(1, len(result))
        self.assertIn("Tekst jest kompletny.", result[0])

    def test_complete_proofreading_result_allows_closing_quote_after_sentence(self):
        main.groq.run_groq_model = lambda groq_api_key, model, options: (
            "Tytuł: News\n\n"
            "Podsumowanie: Tekst jest kompletny.”\n\n"
            f"Link: {ARTICLE_URL}"
        )

        result = main.news_proofreading(
            {"GROQ_API": "test", "LLM_MODEL": "model"},
            [
                "Tytuł: News\n\n"
                "Podsumowanie: Szkic.\n\n"
                f"Link: {ARTICLE_URL}\n\n"
                "################################"
            ],
        )

        self.assertEqual(1, len(result))
        self.assertIn("Tekst jest kompletny.”", result[0])


if __name__ == "__main__":
    unittest.main()
