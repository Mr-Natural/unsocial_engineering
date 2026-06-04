"""Lead de-duplication shared by the source scrapers.

Two leads are considered duplicates if they share a `source_url` (exact) or if
their titles match above a fuzzy threshold (rapidfuzz token-sort ratio). The
threshold of 85 tolerates minor wording/punctuation differences across reposts
and cross-posts while keeping genuinely distinct stories apart.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from rapidfuzz import fuzz

DEFAULT_THRESHOLD = 85


def fetch_recent_leads(client, since_days: int = 14, limit: int = 5000) -> list[dict[str, Any]]:
    """Return recent leads (title + source_url only) to dedupe against.

    Bounded by time and row count so the in-memory fuzzy comparison stays cheap.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat()
    resp = (
        client.table("leads")
        .select("title,source_url")
        .gte("scraped_at", cutoff)
        .limit(limit)
        .execute()
    )
    return list(resp.data or [])


def _title_is_duplicate(title: str, existing_titles: list[str], threshold: int) -> bool:
    return any(t and fuzz.token_sort_ratio(title, t) >= threshold for t in existing_titles)


def deduplicate(
    candidates: list[dict[str, Any]],
    existing: list[dict[str, Any]],
    threshold: int = DEFAULT_THRESHOLD,
) -> list[dict[str, Any]]:
    """Return the candidate leads that are not duplicates of `existing` leads or
    of one another. `existing` is a list of dicts with `title`/`source_url` keys.
    """
    seen_urls = {e["source_url"] for e in existing if e.get("source_url")}
    seen_titles = [e["title"] for e in existing if e.get("title")]

    unique: list[dict[str, Any]] = []
    for candidate in candidates:
        url = candidate.get("source_url")
        title = candidate.get("title") or ""

        if url and url in seen_urls:
            continue
        if title and _title_is_duplicate(title, seen_titles, threshold):
            continue

        unique.append(candidate)
        if url:
            seen_urls.add(url)
        if title:
            seen_titles.append(title)

    return unique
