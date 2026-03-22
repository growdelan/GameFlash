import unittest

from scrapers import listing


class ListingParserTests(unittest.TestCase):
    def test_extract_news_links_filters_current_month_and_deduplicates(self):
        html = """
        <html>
            <body>
                <a href="https://konsolowe.info/2026/03/alpha/">Alpha</a>
                <a href="https://konsolowe.info/2026/03/beta/">Beta</a>
                <a href="https://konsolowe.info/2026/02/old/">Old</a>
                <a href="https://example.com/other/">Other</a>
                <a href="https://konsolowe.info/2026/03/alpha/">Alpha duplicate</a>
            </body>
        </html>
        """

        self.assertEqual(
            [
                "https://konsolowe.info/2026/03/alpha/",
                "https://konsolowe.info/2026/03/beta/",
            ],
            listing.extract_news_links(html, 2026, "03"),
        )


if __name__ == "__main__":
    unittest.main()
