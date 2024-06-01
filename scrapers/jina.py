"""Scraper"""

import requests  # type: ignore


def jina_scraper(url: str):
    """Scrapowanie za pomocą JINA AI"""
    jina_ai = "https://r.jina.ai/"
    news = requests.get(f"{jina_ai}{url}")
    return str(news.content)
