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
        original_fetch_listing = main.listing.fetch_listing_html
        original_current_year_month = main.utils.current_yera_and_month
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
            main.utils.current_yera_and_month = lambda: (2026, "03")

            new_links = main.fetch_and_process_news(
                {
                    "GSPREAD_SERVICE_ACCOUNT_FILE": "service_account.json",
                    "GOOGLE_SHEET_ID": "sheet-id",
                    "GOOGLE_SHEET_WORKSHEET": "Arkusz1",
                    "URL": "https://konsolowe.info/playstation/ps5/",
                }
            )

            self.assertEqual([], new_links)
        finally:
            main.google_sheets.authenticate_gspread = original_authenticate
            main.google_sheets.open_sheet = original_open_sheet
            main.listing.fetch_listing_html = original_fetch_listing
            main.utils.current_yera_and_month = original_current_year_month

    def test_fetch_and_process_news_uses_html_parser_without_llm(self):
        worksheet = FakeWorksheet(values=[["Links"], ["https://konsolowe.info/2026/03/existing/"]])

        original_authenticate = main.google_sheets.authenticate_gspread
        original_open_sheet = main.google_sheets.open_sheet
        original_fetch_listing = main.listing.fetch_listing_html
        original_current_year_month = main.utils.current_yera_and_month
        original_run_model = main.groq.run_groq_model
        try:
            main.google_sheets.authenticate_gspread = lambda _: object()
            main.google_sheets.open_sheet = lambda gc, spreadsheet_id, worksheet_title: (
                object(),
                worksheet,
            )
            main.listing.fetch_listing_html = lambda url: """
            <a href="https://konsolowe.info/2026/03/existing/">Existing</a>
            <a href="https://konsolowe.info/2026/03/new/">New</a>
            <a href="https://konsolowe.info/2026/02/old/">Old</a>
            <a href="https://konsolowe.info/2026/03/new/">New duplicate</a>
            """
            main.utils.current_yera_and_month = lambda: (2026, "03")
            main.groq.run_groq_model = lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("LLM nie powinien byc wywolywany dla listingu")
            )

            new_links = main.fetch_and_process_news(
                {
                    "GSPREAD_SERVICE_ACCOUNT_FILE": "service_account.json",
                    "GOOGLE_SHEET_ID": "sheet-id",
                    "GOOGLE_SHEET_WORKSHEET": "Arkusz1",
                    "URL": "https://konsolowe.info/playstation/ps5/",
                }
            )

            self.assertEqual(["https://konsolowe.info/2026/03/new/"], new_links)
            self.assertEqual(
                [("https://konsolowe.info/2026/03/new/", "RAW")],
                worksheet.appended_links,
            )
        finally:
            main.google_sheets.authenticate_gspread = original_authenticate
            main.google_sheets.open_sheet = original_open_sheet
            main.groq.run_groq_model = original_run_model
            main.listing.fetch_listing_html = original_fetch_listing
            main.utils.current_yera_and_month = original_current_year_month

    def test_fetch_and_process_news_skips_link_when_append_fails(self):
        worksheet = FakeWorksheet(
            values=[["Links"]],
            append_fail_for={"https://konsolowe.info/2026/03/fail/"},
        )

        original_authenticate = main.google_sheets.authenticate_gspread
        original_open_sheet = main.google_sheets.open_sheet
        original_fetch_listing = main.listing.fetch_listing_html
        original_current_year_month = main.utils.current_yera_and_month
        try:
            main.google_sheets.authenticate_gspread = lambda _: object()
            main.google_sheets.open_sheet = lambda gc, spreadsheet_id, worksheet_title: (
                object(),
                worksheet,
            )
            main.listing.fetch_listing_html = lambda url: """
            <a href="https://konsolowe.info/2026/03/fail/">Fail</a>
            <a href="https://konsolowe.info/2026/03/success/">Success</a>
            """
            main.utils.current_yera_and_month = lambda: (2026, "03")

            new_links = main.fetch_and_process_news(
                {
                    "GSPREAD_SERVICE_ACCOUNT_FILE": "service_account.json",
                    "GOOGLE_SHEET_ID": "sheet-id",
                    "GOOGLE_SHEET_WORKSHEET": "Arkusz1",
                    "URL": "https://konsolowe.info/playstation/ps5/",
                }
            )

            self.assertEqual(["https://konsolowe.info/2026/03/success/"], new_links)
            self.assertEqual(
                [("https://konsolowe.info/2026/03/success/", "RAW")],
                worksheet.appended_links,
            )
        finally:
            main.google_sheets.authenticate_gspread = original_authenticate
            main.google_sheets.open_sheet = original_open_sheet
            main.listing.fetch_listing_html = original_fetch_listing
            main.utils.current_yera_and_month = original_current_year_month


if __name__ == "__main__":
    unittest.main()
