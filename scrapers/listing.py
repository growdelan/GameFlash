"""Pobieranie i parsowanie listingu newsow."""

from bs4 import BeautifulSoup
import requests


def fetch_listing_html(url: str) -> str:
    """Pobiera surowy HTML strony listingu newsow."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def extract_news_links(html: str, year: int, month: str) -> list[str]:
    """Wyciaga linki do artykulow dla biezacego roku i miesiaca."""
    prefix = f"https://konsolowe.info/{year}/{month}/"
    soup = BeautifulSoup(html, "html.parser")
    links = []
    seen = set()

    for anchor in soup.select(f'a[href^="{prefix}"]'):
        link = str(anchor.get("href", "")).strip()
        if not link or link in seen:
            continue
        seen.add(link)
        links.append(link)

    return links
