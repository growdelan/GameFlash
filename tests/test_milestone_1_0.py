import unittest

import main
from tests.fakes import FakeWorksheet


class MilestoneOneTests(unittest.TestCase):
    def test_load_config_uses_ppe_defaults(self):
        original_load_dotenv = main.load_dotenv
        original_env = dict(main.os.environ)
        try:
            main.load_dotenv = lambda: None
            main.os.environ.clear()
            main.os.environ.update(
                {
                    "GEMINI_API_KEY": "test",
                    "SMTP_SERVER": "smtp.gmail.com",
                    "SENDER_MAIL": "sender@example.com",
                    "SENDER_PASS": "pass",
                    "RECIPIENTS": "receiver@example.com",
                }
            )

            config = main.load_config()

            self.assertEqual("https://www.ppe.pl/gry", config["URL"])
            self.assertEqual(
                "1N82WxjskvsIyjlfwh8CxlhHJB9LEUMwbAdCI8w0J_yk",
                config["GOOGLE_SHEET_ID"],
            )
            self.assertEqual("Sheet1", config["GOOGLE_SHEET_WORKSHEET"])
        finally:
            main.load_dotenv = original_load_dotenv
            main.os.environ.clear()
            main.os.environ.update(original_env)

    def test_fetch_and_process_news_uses_sheets_for_deduplication(self):
        worksheet = FakeWorksheet(values=[["Links"], ["https://example.com/existing"]])

        original_authenticate = main.google_sheets.authenticate_gspread
        original_open_sheet = main.google_sheets.open_sheet
        original_fetch_listing = main.listing.fetch_listing_html
        try:
            main.google_sheets.authenticate_gspread = lambda _: object()
            main.google_sheets.open_sheet = lambda gc, spreadsheet_id, worksheet_title: (
                object(),
                worksheet,
            )
            main.listing.fetch_listing_html = lambda url: """
            <a href="https://example.com/existing">Existing</a>
            <a href="https://example.com/new">New</a>
            <a href="https://example.com/new">New duplicate</a>
            """

            new_links = main.fetch_and_process_news(
                {
                    "GSPREAD_SERVICE_ACCOUNT_FILE": "service_account.json",
                    "GOOGLE_SHEET_ID": "sheet-id",
                    "GOOGLE_SHEET_WORKSHEET": "Sheet1",
                    "URL": "https://www.ppe.pl/gry",
                }
            )

            self.assertEqual([], new_links)
        finally:
            main.google_sheets.authenticate_gspread = original_authenticate
            main.google_sheets.open_sheet = original_open_sheet
            main.listing.fetch_listing_html = original_fetch_listing

    def test_fetch_and_process_news_uses_html_parser_without_llm(self):
        worksheet = FakeWorksheet(
            values=[["Links"], ["https://www.ppe.pl/news/416200/existing.html"]]
        )

        original_authenticate = main.google_sheets.authenticate_gspread
        original_open_sheet = main.google_sheets.open_sheet
        original_fetch_listing = main.listing.fetch_listing_html
        original_run_model = main.gemini.run_gemini_model
        try:
            main.google_sheets.authenticate_gspread = lambda _: object()
            main.google_sheets.open_sheet = lambda gc, spreadsheet_id, worksheet_title: (
                object(),
                worksheet,
            )
            main.listing.fetch_listing_html = lambda url: """
            <a href="/news/416200/existing.html">Existing</a>
            <a href="/news/416201/new.html">New</a>
            <a href="/gry/sample-game/123">Game</a>
            <a href="/news/416201/new.html">New duplicate</a>
            """
            main.gemini.run_gemini_model = lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("LLM nie powinien byc wywolywany dla listingu")
            )

            new_links = main.fetch_and_process_news(
                {
                    "GSPREAD_SERVICE_ACCOUNT_FILE": "service_account.json",
                    "GOOGLE_SHEET_ID": "sheet-id",
                    "GOOGLE_SHEET_WORKSHEET": "Sheet1",
                    "URL": "https://www.ppe.pl/gry",
                }
            )

            self.assertEqual(["https://www.ppe.pl/news/416201/new.html"], new_links)
            self.assertEqual(
                "pending",
                worksheet.record("https://www.ppe.pl/news/416201/new.html")["status"],
            )
        finally:
            main.google_sheets.authenticate_gspread = original_authenticate
            main.google_sheets.open_sheet = original_open_sheet
            main.gemini.run_gemini_model = original_run_model
            main.listing.fetch_listing_html = original_fetch_listing

    def test_fetch_and_process_news_normalizes_links_with_configured_url(self):
        worksheet = FakeWorksheet(values=[["Links"]])

        original_authenticate = main.google_sheets.authenticate_gspread
        original_open_sheet = main.google_sheets.open_sheet
        original_fetch_listing = main.listing.fetch_listing_html
        try:
            main.google_sheets.authenticate_gspread = lambda _: object()
            main.google_sheets.open_sheet = lambda gc, spreadsheet_id, worksheet_title: (
                object(),
                worksheet,
            )
            main.listing.fetch_listing_html = lambda url: """
            <a href="/news/416204/from-config.html">From config</a>
            """

            new_links = main.fetch_and_process_news(
                {
                    "GSPREAD_SERVICE_ACCOUNT_FILE": "service_account.json",
                    "GOOGLE_SHEET_ID": "sheet-id",
                    "GOOGLE_SHEET_WORKSHEET": "Sheet1",
                    "URL": "https://www.ppe.pl/gry",
                }
            )

            self.assertEqual(
                ["https://www.ppe.pl/news/416204/from-config.html"], new_links
            )
            self.assertEqual(1, len(worksheet.appended_rows))
        finally:
            main.google_sheets.authenticate_gspread = original_authenticate
            main.google_sheets.open_sheet = original_open_sheet
            main.listing.fetch_listing_html = original_fetch_listing

    def test_fetch_and_process_news_skips_link_when_append_fails(self):
        worksheet = FakeWorksheet(
            values=[["Links"]],
            append_fail_for={"https://www.ppe.pl/news/416202/fail.html"},
        )

        original_authenticate = main.google_sheets.authenticate_gspread
        original_open_sheet = main.google_sheets.open_sheet
        original_fetch_listing = main.listing.fetch_listing_html
        try:
            main.google_sheets.authenticate_gspread = lambda _: object()
            main.google_sheets.open_sheet = lambda gc, spreadsheet_id, worksheet_title: (
                object(),
                worksheet,
            )
            main.listing.fetch_listing_html = lambda url: """
            <a href="/news/416202/fail.html">Fail</a>
            <a href="/news/416203/success.html">Success</a>
            """

            new_links = main.fetch_and_process_news(
                {
                    "GSPREAD_SERVICE_ACCOUNT_FILE": "service_account.json",
                    "GOOGLE_SHEET_ID": "sheet-id",
                    "GOOGLE_SHEET_WORKSHEET": "Sheet1",
                    "URL": "https://www.ppe.pl/gry",
                }
            )

            self.assertEqual(["https://www.ppe.pl/news/416203/success.html"], new_links)
            self.assertEqual(1, len(worksheet.appended_rows))
        finally:
            main.google_sheets.authenticate_gspread = original_authenticate
            main.google_sheets.open_sheet = original_open_sheet
            main.listing.fetch_listing_html = original_fetch_listing


if __name__ == "__main__":
    unittest.main()
