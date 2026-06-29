"""Pobieranie i parsowanie listingu newsow."""

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import requests

PPE_BASE_URL = "https://www.ppe.pl"
PPE_NEWS_PATH_RE = re.compile(r"^/news/\d+/[^/]+\.html$")


def fetch_listing_html(url: str) -> str:
    """Pobiera surowy HTML strony listingu newsow."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def extract_news_links(html: str, base_url: str = PPE_BASE_URL) -> list[str]:
    """Wyciaga linki do newsow PPE z listingu i normalizuje je do pelnych URL."""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    seen = set()

    for anchor in soup.select("a[href]"):
        href = str(anchor.get("href", "")).strip()
        if not href:
            continue

        link = urljoin(base_url, href)
        parsed_link = urlparse(link)
        parsed_base = urlparse(base_url)
        if parsed_link.netloc != parsed_base.netloc:
            continue
        if not PPE_NEWS_PATH_RE.match(parsed_link.path):
            continue

        normalized_link = f"{parsed_base.scheme}://{parsed_base.netloc}{parsed_link.path}"
        if normalized_link in seen:
            continue
        seen.add(normalized_link)
        links.append(normalized_link)

    return links
