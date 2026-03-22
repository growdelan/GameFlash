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


class MilestoneOneTests(unittest.TestCase):
    def test_fetch_and_process_news_uses_sheets_for_deduplication(self):
        worksheet = FakeWorksheet(values=[["Links"], ["https://example.com/existing"]])

        original_authenticate = main.google_sheets.authenticate_gspread
        original_open_sheet = main.google_sheets.open_sheet
        original_jina_scraper = main.jina.jina_scraper
        original_model_options = main.groq.model_options
        original_run_model = main.groq.run_groq_model
        original_current_year_month = main.utils.current_yera_and_month
        try:
            main.google_sheets.authenticate_gspread = lambda _: object()
            main.google_sheets.open_sheet = lambda gc, spreadsheet_id, worksheet_title: (
                object(),
                worksheet,
            )
            main.jina.jina_scraper = lambda url: "news-body"
            main.utils.current_yera_and_month = lambda: (2026, "03")
            main.groq.model_options = lambda prompt, temperature, max_tokens: {
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            main.groq.run_groq_model = lambda groq_api_key, model, options: (
                '{"links": ['
                '"https://example.com/existing", '
                '"https://example.com/new", '
                '"https://example.com/new"'
                "]}"
            )

            new_links = main.fetch_and_process_news(
                {
                    "GSPREAD_SERVICE_ACCOUNT_FILE": "service_account.json",
                    "GOOGLE_SHEET_ID": "sheet-id",
                    "GOOGLE_SHEET_WORKSHEET": "Arkusz1",
                    "URL": "https://konsolowe.info/playstation/ps5/",
                    "GROQ_API": "test",
                    "LLM_MODEL": "model",
                }
            )

            self.assertEqual(["https://example.com/new"], new_links)
            self.assertEqual(
                [("https://example.com/new", "RAW")],
                worksheet.appended_links,
            )
        finally:
            main.google_sheets.authenticate_gspread = original_authenticate
            main.google_sheets.open_sheet = original_open_sheet
            main.jina.jina_scraper = original_jina_scraper
            main.groq.model_options = original_model_options
            main.groq.run_groq_model = original_run_model
            main.utils.current_yera_and_month = original_current_year_month

    def test_fetch_and_process_news_skips_link_when_append_fails(self):
        worksheet = FakeWorksheet(
            values=[["Links"]],
            append_fail_for={"https://example.com/fail"},
        )

        original_authenticate = main.google_sheets.authenticate_gspread
        original_open_sheet = main.google_sheets.open_sheet
        original_jina_scraper = main.jina.jina_scraper
        original_model_options = main.groq.model_options
        original_run_model = main.groq.run_groq_model
        original_current_year_month = main.utils.current_yera_and_month
        try:
            main.google_sheets.authenticate_gspread = lambda _: object()
            main.google_sheets.open_sheet = lambda gc, spreadsheet_id, worksheet_title: (
                object(),
                worksheet,
            )
            main.jina.jina_scraper = lambda url: "news-body"
            main.utils.current_yera_and_month = lambda: (2026, "03")
            main.groq.model_options = lambda prompt, temperature, max_tokens: {
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            main.groq.run_groq_model = lambda groq_api_key, model, options: (
                '{"links": ['
                '"https://example.com/fail", '
                '"https://example.com/success"'
                "]}"
            )

            new_links = main.fetch_and_process_news(
                {
                    "GSPREAD_SERVICE_ACCOUNT_FILE": "service_account.json",
                    "GOOGLE_SHEET_ID": "sheet-id",
                    "GOOGLE_SHEET_WORKSHEET": "Arkusz1",
                    "URL": "https://konsolowe.info/playstation/ps5/",
                    "GROQ_API": "test",
                    "LLM_MODEL": "model",
                }
            )

            self.assertEqual(["https://example.com/success"], new_links)
            self.assertEqual(
                [("https://example.com/success", "RAW")],
                worksheet.appended_links,
            )
        finally:
            main.google_sheets.authenticate_gspread = original_authenticate
            main.google_sheets.open_sheet = original_open_sheet
            main.jina.jina_scraper = original_jina_scraper
            main.groq.model_options = original_model_options
            main.groq.run_groq_model = original_run_model
            main.utils.current_yera_and_month = original_current_year_month


if __name__ == "__main__":
    unittest.main()
