import unittest

from storage import google_sheets
from tests.fakes import FakeWorksheet


class GoogleSheetsTests(unittest.TestCase):
    def test_read_registered_links_reads_links_column(self):
        ws = FakeWorksheet(
            values=[
                ["Links", "Other"],
                ["https://example.com/1", "x"],
                ["https://example.com/2", "y"],
                ["", "z"],
            ]
        )

        self.assertEqual(
            {
                "https://example.com/1",
                "https://example.com/2",
            },
            google_sheets.read_registered_links(ws),
        )

    def test_read_registered_links_requires_links_header(self):
        ws = FakeWorksheet(values=[["WrongHeader"]])

        with self.assertRaisesRegex(RuntimeError, "Links"):
            google_sheets.read_registered_links(ws)

    def test_append_link_appends_raw_row(self):
        ws = FakeWorksheet()
        google_sheets.ensure_state_schema(ws)

        google_sheets.append_pending_link(
            ws,
            "https://example.com/new",
            timestamp="2026-07-26T10:00:00+00:00",
        )

        record = ws.record("https://example.com/new")
        self.assertEqual("pending", record["status"])
        self.assertEqual("0", record["attempts"])
        self.assertEqual("2026-07-26T10:00:00+00:00", record["discoveredat"])
        self.assertEqual("RAW", ws.appended_rows[0][1])

    def test_ensure_state_schema_preserves_existing_columns(self):
        ws = FakeWorksheet(values=[["Other", "Links"], ["x", "https://old"]])

        google_sheets.ensure_state_schema(ws)

        self.assertEqual(["Other", "Links"], ws.values[0][:2])
        self.assertEqual(
            list(google_sheets.STATE_HEADERS),
            ws.values[0][2:],
        )

    def test_read_news_records_treats_legacy_blank_status_as_sent(self):
        ws = FakeWorksheet(values=[["Links"], ["https://example.com/legacy"]])

        records = google_sheets.read_news_records(ws)

        self.assertEqual(1, len(records))
        self.assertEqual("sent", records[0].status)
        self.assertEqual(2, records[0].row_number)


if __name__ == "__main__":
    unittest.main()
