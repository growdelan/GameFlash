import unittest

from scrapers import listing


class ListingParserTests(unittest.TestCase):
    def test_extract_news_links_returns_ppe_news_links_and_deduplicates(self):
        html = """
        <html>
            <body>
                <a href="/news/416209/assetto-corsa-rally.html">Alpha</a>
                <a href="https://www.ppe.pl/news/416220/koei-tecmo.html">Beta</a>
                <a href="/promocje">Promocje</a>
                <a href="/promocje/gry/ps5">Promocje PS5</a>
                <a href="/gry/ranking">Ranking</a>
                <a href="/gry/the-path-of-the-warrior-art-of-fighting-3-r/20892">Game</a>
                <a href="/news.html">News index</a>
                <a href="/recenzje-gier.html">Recenzje</a>
                <a href="/publicystyka.html">Publicystyka</a>
                <a href="https://example.com/other/">Other</a>
                <a href="/news/416209/assetto-corsa-rally.html">Alpha duplicate</a>
            </body>
        </html>
        """

        self.assertEqual(
            [
                "https://www.ppe.pl/news/416209/assetto-corsa-rally.html",
                "https://www.ppe.pl/news/416220/koei-tecmo.html",
            ],
            listing.extract_news_links(html),
        )


if __name__ == "__main__":
    unittest.main()
