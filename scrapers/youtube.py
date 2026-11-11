"""Linki YouTube z tresci artykulu, bez udzialu modelu."""

import re
from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup
import requests


def canonical_video_url(value):
    parsed = urlparse(value if not value.startswith("//") else "https:" + value)
    host = (parsed.hostname or "").lower()
    parts = parsed.path.strip("/").split("/")
    video_id = ""
    if host in {"youtu.be", "www.youtu.be"}:
        video_id = parts[0]
    elif host in {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtube-nocookie.com",
        "www.youtube-nocookie.com",
    }:
        if parts[0] == "watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif len(parts) == 2 and parts[0] in {"embed", "shorts", "live", "v"}:
            video_id = parts[1]
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        return "https://www.youtube.com/watch?v=" + video_id
    return None


def extract_video_links(html):
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one(
        '[itemprop="articleBody"], article .entry-content, article #entry, article, .entry-content'
    )
    if article is None:
        return []
    links = []
    for node in article.select("a, iframe, embed, object, [data-src], [data-video-id]"):
        candidates = [
            node.get(attr, "")
            for attr in ("href", "src", "data-src", "data-lazy-src", "data")
        ]
        for value in candidates:
            link = canonical_video_url(value)
            if link and link not in links:
                links.append(link)
    return links


def fetch_video_links(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return extract_video_links(response.text)
