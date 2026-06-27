"""Pobieranie tresci artykulow przez mirror Jina."""

import html
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import requests

JINA_AI_URL = "https://r.jina.ai/"
MIN_ARTICLE_TEXT_LENGTH = 200
JINA_ERROR_PATTERNS = (
    "Title: 403 Forbidden",
    "Warning: Target URL returned error 403",
)
WP_POST_RE = re.compile(r"/wp-json/wp/v2/posts/(\d+)")


class ArticleContentError(RuntimeError):
    """Sygnalizuje brak wiarygodnej tresci artykulu."""


def _normalize_text(value: str) -> str:
    """Porzadkuje biale znaki w tekscie artykulu."""
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


def validate_article_text(text: str) -> str:
    """Zwraca tekst artykulu albo zglasza blad dla odpowiedzi technicznych."""
    normalized_text = _normalize_text(text)
    for error_pattern in JINA_ERROR_PATTERNS:
        if error_pattern in normalized_text:
            raise ArticleContentError("Jina zwrocila blad zrodla zamiast tresci.")

    if len(normalized_text) < MIN_ARTICLE_TEXT_LENGTH:
        raise ArticleContentError("Pobrana tresc artykulu jest zbyt krotka.")

    return normalized_text


def _is_konsolowe_url(url: str) -> bool:
    """Sprawdza, czy link prowadzi do obslugiwanego zrodla WordPress."""
    hostname = urlparse(url).hostname or ""
    return hostname == "konsolowe.info" or hostname.endswith(".konsolowe.info")


def _extract_post_id(response: requests.Response) -> str | None:
    """Wyciaga ID posta WordPress z naglowka Link albo HTML."""
    header_link = response.headers.get("Link", "")
    header_match = WP_POST_RE.search(header_link)
    if header_match:
        return header_match.group(1)

    soup = BeautifulSoup(response.text, "html.parser")
    wp_link = soup.find("link", attrs={"rel": "alternate", "type": "application/json"})
    if wp_link:
        href = str(wp_link.get("href", ""))
        href_match = WP_POST_RE.search(href)
        if href_match:
            return href_match.group(1)

    return None


def _clean_html_text(html_content: str) -> str:
    """Oczyszcza HTML artykulu do tekstu dla LLM."""
    soup = BeautifulSoup(html_content, "html.parser")
    for element in soup(["script", "style", "noscript", "iframe"]):
        element.decompose()
    return _normalize_text(soup.get_text(" "))


def _article_text_from_direct_html(html_content: str) -> str:
    """Wyciaga glowna tresc artykulu z bezposredniego HTML."""
    soup = BeautifulSoup(html_content, "html.parser")
    for element in soup(["script", "style", "noscript", "iframe"]):
        element.decompose()

    article_node = soup.select_one(
        "article .entry-content, article #entry, article, #entry, .entry-content, main"
    )
    if article_node is None:
        article_node = soup.body or soup

    return _normalize_text(article_node.get_text(" "))


def _fetch_from_wordpress_api(url: str, post_id: str) -> str:
    """Pobiera tresc posta przez WordPress REST API."""
    parsed_url = urlparse(url)
    api_url = f"{parsed_url.scheme}://{parsed_url.netloc}/wp-json/wp/v2/posts/{post_id}"
    response = requests.get(api_url, timeout=30)
    response.raise_for_status()
    post_data = response.json()
    rendered_content = post_data.get("content", {}).get("rendered", "")
    return validate_article_text(_clean_html_text(rendered_content))


def _fetch_article_fallback(url: str) -> str:
    """Pobiera tresc artykulu z fallbackow dla konsolowe.info."""
    if not _is_konsolowe_url(url):
        raise ArticleContentError("Brak fallbacku dla tego zrodla.")

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    post_id = _extract_post_id(response)
    if post_id:
        try:
            return _fetch_from_wordpress_api(url, post_id)
        except Exception as exc:
            print(f"Nie udalo sie pobrac tresci przez WordPress REST API: {url} ({exc})")

    return validate_article_text(_article_text_from_direct_html(response.text))


def fetch_article_text(url: str) -> str:
    """Pobiera tresc artykulu przez Jina z fallbackiem dla zrodel WordPress."""
    try:
        response = requests.get(f"{JINA_AI_URL}{url}", timeout=30)
        response.raise_for_status()
        return validate_article_text(response.text)
    except ArticleContentError:
        return _fetch_article_fallback(url)
    except requests.RequestException as exc:
        print(f"Nie udalo sie pobrac tresci przez Jina: {url} ({exc})")
        return _fetch_article_fallback(url)
