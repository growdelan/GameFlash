import unittest

from storage import google_sheets


class FakeWorksheet:
    def __init__(self, values=None, append_error=None):
        self.values = values or [["Links"]]
        self.appended_rows = []
        self.append_error = append_error

    def get_all_values(self):
        return self.values

    def append_row(self, row, value_input_option="RAW"):
        if self.append_error:
            raise self.append_error
        self.appended_rows.append((row, value_input_option))


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

        google_sheets.append_link(ws, "https://example.com/new")

        self.assertEqual(
            [(["https://example.com/new"], "RAW")],
            ws.appended_rows,
        )


if __name__ == "__main__":
    unittest.main()
