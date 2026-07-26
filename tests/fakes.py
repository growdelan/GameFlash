class FakeWorksheet:
    def __init__(self, values=None, append_error=None, append_fail_for=None):
        self.values = [list(row) for row in (values or [["Links"]])]
        self.appended_rows = []
        self.append_error = append_error
        self.append_fail_for = set(append_fail_for or [])

    def get_all_values(self):
        return [list(row) for row in self.values]

    def update_cell(self, row, column, value):
        while len(self.values) < row:
            self.values.append([])
        while len(self.values[row - 1]) < column:
            self.values[row - 1].append("")
        self.values[row - 1][column - 1] = str(value)

    def append_row(self, row, value_input_option="RAW"):
        header = [str(value).strip().lower() for value in self.values[0]]
        link_index = header.index("links")
        link = row[link_index]
        if self.append_error:
            raise self.append_error
        if link in self.append_fail_for:
            raise RuntimeError("append failed")
        appended_row = list(row)
        self.values.append(appended_row)
        self.appended_rows.append((appended_row, value_input_option))

    def record(self, link):
        header = [str(value).strip().lower() for value in self.values[0]]
        link_index = header.index("links")
        for row in self.values[1:]:
            if link_index < len(row) and row[link_index] == link:
                return {
                    name: row[index] if index < len(row) else ""
                    for index, name in enumerate(header)
                }
        raise AssertionError(f"Brak rekordu dla linku: {link}")
