"""Pobieranie tresci artykulow przez mirror Jina."""

import requests


def fetch_article_text(url: str) -> str:
    """Pobiera tresc artykulu przez mirror Jina."""
    jina_ai = "https://r.jina.ai/"
    response = requests.get(f"{jina_ai}{url}", timeout=30)
    response.raise_for_status()
    return response.text
