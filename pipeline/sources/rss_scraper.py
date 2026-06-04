"""RSS scraper — ingests scam alerts from authority/news feeds into leads.

Parses each feed with feedparser, keeps recent entries, and inserts new leads
using the same de-duplication logic. RSS items carry no engagement signal so
they get a fixed baseline relevance score.

Two feed groups are maintained:
  FEEDS        — authority/news sources, source='rss'
  REDDIT_FEEDS — subreddit RSS, source='reddit_rss' (fallback while PRAW creds
                 are unavailable; reddit_scraper.py takes over once they exist)

Standalone:
    python pipeline/sources/rss_scraper.py
    python pipeline/sources/rss_scraper.py --dry-run --since-days 30
"""

from __future__ import annotations

import argparse
import html
import logging
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote

# Allow running as a standalone script (see reddit_scraper for rationale).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline.config import get_supabase  # noqa: E402
from pipeline.dedup import DEFAULT_THRESHOLD, deduplicate, fetch_recent_leads  # noqa: E402
from pipeline.relevance import is_scam_relevant  # noqa: E402

log = logging.getLogger("rss_scraper")

# Authority and fact-check feeds (verified working). If a feed stops returning
# entries, verify the URL — outlets change these occasionally.
#
# ACCC Scamwatch and Action Fraud UK discontinued their public RSS feeds, so the
# closest national-government equivalents are used in their place: ASD's ACSC
# (Australia) and the NCSC (UK).
FEEDS: dict[str, str] = {
    "FTC Consumer Alerts": "https://consumer.ftc.gov/blog/rss",
    "Snopes (scams)": "https://www.snopes.com/tag/scams/feed/",
    "ACSC (Australia)": "https://www.cyber.gov.au/rss/news",
    "NCSC (UK)": "https://www.ncsc.gov.uk/api/1/services/v1/all-rss-feed.xml",
}

# Many of these sites reject the default feedparser user-agent with a block page,
# so present a browser-like UA.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Reddit enforces its own bot policy and returns 429 for generic UAs. Their
# API rules require a descriptive user-agent with contact info.
REDDIT_USER_AGENT = "UnsocialEngineering/1.0 (scam-tracker; +https://unsocialengineering.com)"

# Subreddit RSS feeds — fallback while PRAW credentials are unavailable.
# Uses source='reddit_rss' so pipeline logic can distinguish from PRAW leads.
REDDIT_FEEDS: dict[str, str] = {
    "r/Scams": "https://www.reddit.com/r/Scams/new/.rss",
    "r/phishing": "https://www.reddit.com/r/phishing/new/.rss",
    "r/fraud": "https://www.reddit.com/r/fraud/new/.rss",
    "r/AusFinance (scam)": "https://www.reddit.com/r/AusFinance/search/.rss?q=scam&restrict_sr=on&sort=new",
    "r/personalfinance (scam)": "https://www.reddit.com/r/personalfinance/search/.rss?q=scam&restrict_sr=on&sort=new",
}

# Authoritative sources, but no engagement metric to score on.
DEFAULT_RSS_RELEVANCE = 50


def _clean_title(raw: str) -> str:
    """Strip HTML tags/entities some feeds embed in <title> and collapse space."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", raw))).strip()


def _entry_text(entry) -> str:
    for key in ("summary", "description"):
        value = entry.get(key)
        if value:
            return value
    content = entry.get("content")
    if content:
        try:
            return content[0].get("value", "")
        except (AttributeError, IndexError, TypeError):
            pass
    return ""


def _entry_link(entry) -> str | None:
    """Return the entry's canonical URL.

    Some feeds (notably FTC) wrap the real article URL in an HTML anchor inside
    <link>, which feedparser percent-encodes, e.g.
    `https://consumer.ftc.gov/%3Ca%20href%3D%22<REAL>%22...%3E`. Decode and pull
    the inner href out. Well-formed feeds have no inner href and pass through.
    """
    raw = entry.get("link") or ""
    match = re.search(r'href=["\']([^"\']+)["\']', unquote(raw))
    return match.group(1) if match else (raw or None)


def _entry_datetime(entry):
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            return datetime.fromtimestamp(time.mktime(parsed), tz=timezone.utc)
    return None


def _collect_from_feeds(
    feeds: dict[str, str],
    user_agent: str,
    source: str,
    cutoff: datetime,
    per_feed_limit: int,
    relevance_filter: bool,
) -> tuple[list[dict], int]:
    """Fetch and filter one group of feeds. Returns (candidates, skipped_count)."""
    import feedparser  # lazy so the module loads without feedparser installed

    candidates: list[dict] = []
    skipped = 0

    for name, url in feeds.items():
        try:
            parsed = feedparser.parse(url, agent=user_agent)
            if parsed.bozo and not parsed.entries:
                log.warning("%s: feed error (%s)", name, getattr(parsed, "bozo_exception", "unknown"))
                continue

            count = 0
            for entry in parsed.entries[:per_feed_limit]:
                published = _entry_datetime(entry)
                if published and published < cutoff:
                    continue
                title = _clean_title(entry.get("title") or "")
                if not title:
                    continue

                raw_text = _entry_text(entry).strip() or title
                if relevance_filter and not is_scam_relevant(f"{title} {raw_text}"):
                    skipped += 1
                    continue

                candidates.append(
                    {
                        "source": source,
                        "title": title,
                        "source_url": _entry_link(entry),
                        "raw_text": raw_text,
                        "relevance_score": DEFAULT_RSS_RELEVANCE,
                        "status": "new",
                    }
                )
                count += 1
            log.info("%s: %d candidate(s)", name, count)
        except Exception as exc:  # one bad feed must not abort the run
            log.warning("%s: skipped (%s)", name, exc)

    return candidates, skipped


def collect_candidates(
    since_days: int = 7, per_feed_limit: int = 50, relevance_filter: bool = True
) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

    authority_leads, skipped_authority = _collect_from_feeds(
        FEEDS, USER_AGENT, "rss", cutoff, per_feed_limit, relevance_filter
    )
    reddit_leads, skipped_reddit = _collect_from_feeds(
        REDDIT_FEEDS, REDDIT_USER_AGENT, "reddit_rss", cutoff, per_feed_limit, relevance_filter
    )

    candidates = authority_leads + reddit_leads
    total_skipped = skipped_authority + skipped_reddit
    if relevance_filter and total_skipped:
        log.info("Filtered out %d non-scam entr(y/ies)", total_skipped)
    return candidates


def run(
    since_days: int = 7,
    per_feed_limit: int = 50,
    threshold: int = DEFAULT_THRESHOLD,
    relevance_filter: bool = True,
    dry_run: bool = False,
) -> list[dict]:
    candidates = collect_candidates(since_days, per_feed_limit, relevance_filter)
    log.info("Collected %d candidate lead(s) before dedup", len(candidates))
    if not candidates:
        return []

    client = get_supabase()
    existing = fetch_recent_leads(client)
    new_leads = deduplicate(candidates, existing, threshold)
    log.info(
        "%d new lead(s) after dedup (%d duplicate[s] dropped)",
        len(new_leads),
        len(candidates) - len(new_leads),
    )

    if dry_run:
        for lead in new_leads:
            log.info("[dry-run] would insert: %s", lead["title"])
        return new_leads

    if new_leads:
        client.table("leads").insert(new_leads).execute()
        log.info("Inserted %d lead(s)", len(new_leads))
    return new_leads


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape RSS feeds for scam leads.")
    parser.add_argument("--since-days", type=int, default=7, help="only entries from the last N days")
    parser.add_argument("--limit", type=int, default=50, help="max entries per feed")
    parser.add_argument("--dedup-threshold", type=int, default=DEFAULT_THRESHOLD, help="fuzzy title threshold")
    parser.add_argument("--no-relevance-filter", action="store_true", help="ingest non-scam entries too")
    parser.add_argument("--dry-run", action="store_true", help="do not write to the database")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    run(
        since_days=args.since_days,
        per_feed_limit=args.limit,
        threshold=args.dedup_threshold,
        relevance_filter=not args.no_relevance_filter,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
