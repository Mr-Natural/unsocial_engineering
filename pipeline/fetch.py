"""Fetch a URL and reduce it to plain article text.

Shared by the writer (to ground drafts in real source content) and the editor
(to verify claims). Extracts the main/article content and drops nav/chrome so
callers see body text, not sidebar headlines. TLS goes through truststore
(injected by pipeline.config), so this works behind the local Norton inspection.
"""

from __future__ import annotations

import html
import logging
import re

log = logging.getLogger("fetch")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
DEFAULT_MAX_CHARS = 3000


def strip_html(raw: str) -> str:
    """Reduce an HTML page to its main article text."""
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
            tag.decompose()
        main = soup.find("main") or soup.find("article") or soup.body or soup
        text = main.get_text(separator=" ")
    except Exception:
        # Fallback to a plain tag strip if parsing fails.
        text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
        text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def fetch_text(url: str, max_chars: int = DEFAULT_MAX_CHARS) -> str:
    """Fetch `url` and return a plain-text excerpt. Returns '' on any failure."""
    import httpx  # lazy import

    try:
        resp = httpx.get(url, headers={"User-Agent": USER_AGENT}, timeout=20, follow_redirects=True)
        resp.raise_for_status()
        return strip_html(resp.text)[:max_chars]
    except Exception as exc:
        log.warning("Could not fetch %s (%s)", url, exc)
        return ""
