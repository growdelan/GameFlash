import unittest

import main


class FakeWorksheet:
    def __init__(self, values=None, append_fail_for=None):
        self.values = values or [["Links"]]
        self.appended_links = []
        self.append_fail_for = set(append_fail_for or [])

    def get_all_values(self):
        return self.values

    def append_row(self, row, value_input_option="RAW"):
        link = row[0]
        if link in self.append_fail_for:
            raise RuntimeError("append failed")
        self.appended_links.append((link, value_input_option))


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.original_load_config = main.load_config
        self.original_authenticate = main.google_sheets.authenticate_gspread
        self.original_open_sheet = main.google_sheets.open_sheet
        self.original_fetch_listing = main.listing.fetch_listing_html
        self.original_current_year_month = main.utils.current_yera_and_month
        self.original_fetch_article = main.jina.fetch_article_text
        self.original_run_model = main.groq.run_groq_model
        self.original_send_email = main.gmail.send_email

    def tearDown(self):
        main.load_config = self.original_load_config
        main.google_sheets.authenticate_gspread = self.original_authenticate
        main.google_sheets.open_sheet = self.original_open_sheet
        main.listing.fetch_listing_html = self.original_fetch_listing
        main.utils.current_yera_and_month = self.original_current_year_month
        main.jina.fetch_article_text = self.original_fetch_article
        main.groq.run_groq_model = self.original_run_model
        main.gmail.send_email = self.original_send_email

    def _configure_common(self, worksheet, listing_html):
        sent_messages = []

        main.load_config = lambda: {
            "GSPREAD_SERVICE_ACCOUNT_FILE": "service_account.json",
            "GOOGLE_SHEET_ID": "sheet-id",
            "GOOGLE_SHEET_WORKSHEET": "Arkusz1",
            "URL": "https://konsolowe.info/playstation/ps5/",
            "GROQ_API": "test",
            "LLM_MODEL": "model",
            "SMTP_SERVER": "smtp.gmail.com",
            "SENDER_MAIL": "sender@example.com",
            "SENDER_PASS": "pass",
            "RECIPIENTS": ["receiver@example.com"],
        }
        main.google_sheets.authenticate_gspread = lambda _: object()
        main.google_sheets.open_sheet = lambda gc, spreadsheet_id, worksheet_title: (
            object(),
            worksheet,
        )
        main.listing.fetch_listing_html = lambda url: listing_html
        main.utils.current_yera_and_month = lambda: (2026, "03")
        main.gmail.send_email = lambda **kwargs: sent_messages.append(kwargs)

        return sent_messages

    def test_main_processes_new_link_and_sends_email(self):
        worksheet = FakeWorksheet(values=[["Links"]])
        sent_messages = self._configure_common(
            worksheet,
            '<a href="https://konsolowe.info/2026/03/new-article/">New</a>',
        )
        main.jina.fetch_article_text = lambda url: "article-body"

        def fake_run_model(groq_api_key, model, options):
            prompt = options["prompt"]
            if "proofreading" in prompt:
                return "Tytul: New\n\nPodsumowanie: gotowe.\n\nLink: https://konsolowe.info/2026/03/new-article/"
            return "Tytul: New\n\nPodsumowanie: szkic."

        main.groq.run_groq_model = fake_run_model

        main.main()

        self.assertEqual(
            [("https://konsolowe.info/2026/03/new-article/", "RAW")],
            worksheet.appended_links,
        )
        self.assertEqual(1, len(sent_messages))
        self.assertIn("gotowe", sent_messages[0]["news_to_send"][0])

    def test_main_skips_existing_link_without_email(self):
        worksheet = FakeWorksheet(
            values=[["Links"], ["https://konsolowe.info/2026/03/existing/"]]
        )
        sent_messages = self._configure_common(
            worksheet,
            '<a href="https://konsolowe.info/2026/03/existing/">Existing</a>',
        )
        fetch_calls = []
        main.jina.fetch_article_text = lambda url: fetch_calls.append(url) or "article-body"
        main.groq.run_groq_model = lambda *args, **kwargs: "unused"

        main.main()

        self.assertEqual([], worksheet.appended_links)
        self.assertEqual([], sent_messages)
        self.assertEqual([], fetch_calls)

    def test_append_failure_stops_processing_link(self):
        worksheet = FakeWorksheet(
            values=[["Links"]],
            append_fail_for={"https://konsolowe.info/2026/03/fail/"},
        )
        sent_messages = self._configure_common(
            worksheet,
            '<a href="https://konsolowe.info/2026/03/fail/">Fail</a>',
        )
        fetch_calls = []
        main.jina.fetch_article_text = lambda url: fetch_calls.append(url) or "article-body"
        main.groq.run_groq_model = lambda *args, **kwargs: "unused"

        main.main()

        self.assertEqual([], worksheet.appended_links)
        self.assertEqual([], sent_messages)
        self.assertEqual([], fetch_calls)

    def test_fetch_failure_after_append_does_not_send_email(self):
        worksheet = FakeWorksheet(values=[["Links"]])
        sent_messages = self._configure_common(
            worksheet,
            '<a href="https://konsolowe.info/2026/03/fetch-fail/">Fail</a>',
        )
        main.jina.fetch_article_text = lambda url: (_ for _ in ()).throw(
            RuntimeError("fetch failed")
        )
        main.groq.run_groq_model = lambda *args, **kwargs: "unused"

        main.main()

        self.assertEqual(
            [("https://konsolowe.info/2026/03/fetch-fail/", "RAW")],
            worksheet.appended_links,
        )
        self.assertEqual([], sent_messages)

    def test_no_new_links_does_not_send_email(self):
        worksheet = FakeWorksheet(values=[["Links"]])
        sent_messages = self._configure_common(worksheet, "<html></html>")
        main.jina.fetch_article_text = lambda url: "article-body"
        main.groq.run_groq_model = lambda *args, **kwargs: "unused"

        main.main()

        self.assertEqual([], worksheet.appended_links)
        self.assertEqual([], sent_messages)


if __name__ == "__main__":
    unittest.main()
