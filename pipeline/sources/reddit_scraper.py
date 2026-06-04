"""Reddit scraper — ingests scam-related posts into the leads table.

Uses PRAW in read-only mode (app credentials from .env). Monitors the dedicated
scam subreddits plus scam-tagged posts in general finance subreddits, keeps only
recent, engaged posts, scores them by engagement, de-duplicates, and inserts new
leads with source='reddit'.

Standalone:
    python pipeline/sources/reddit_scraper.py
    python pipeline/sources/reddit_scraper.py --dry-run --since-hours 48
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running as a standalone script (adds the project root to sys.path so the
# `pipeline` package is importable when this file is executed directly).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline.config import config, get_supabase  # noqa: E402
from pipeline.dedup import DEFAULT_THRESHOLD, deduplicate, fetch_recent_leads  # noqa: E402

log = logging.getLogger("reddit_scraper")

# (subreddit, scam_only). For general-finance subs we only take scam-tagged posts.
SUBREDDITS: list[tuple[str, bool]] = [
    ("Scams", False),
    ("phishing", False),
    ("fraud", False),
    ("personalfinance", True),
    ("AusFinance", True),
]

SCAM_KEYWORDS = ("scam", "scammed", "scammer", "phish", "fraud")


def compute_relevance(score: int, num_comments: int) -> int:
    """Engagement-weighted relevance, clamped to 0-100. Comments are weighted 2x
    upvotes because discussion tends to signal corroboration and reach."""
    return max(0, min(100, score + 2 * num_comments))


def _is_scam_tagged(submission) -> bool:
    flair = (submission.link_flair_text or "").lower()
    title = (submission.title or "").lower()
    haystack = f"{flair} {title}"
    return any(keyword in haystack for keyword in SCAM_KEYWORDS)


def _build_reddit():
    config.require("reddit_client_id", "reddit_client_secret")
    import praw  # imported lazily so the module loads without PRAW present

    reddit = praw.Reddit(
        client_id=config.reddit_client_id,
        client_secret=config.reddit_client_secret,
        user_agent=config.reddit_user_agent,
    )
    reddit.read_only = True
    return reddit


def collect_candidates(
    reddit,
    since_hours: int = 24,
    min_score: int = 5,
    min_comments: int = 3,
    per_sub_limit: int = 200,
) -> list[dict]:
    cutoff = datetime.now(timezone.utc).timestamp() - since_hours * 3600
    candidates: list[dict] = []

    for name, scam_only in SUBREDDITS:
        try:
            count = 0
            # .new() is strictly reverse-chronological, so we can stop at the
            # first post older than the cutoff.
            for submission in reddit.subreddit(name).new(limit=per_sub_limit):
                if submission.created_utc < cutoff:
                    break
                if not (submission.score > min_score or submission.num_comments > min_comments):
                    continue
                if scam_only and not _is_scam_tagged(submission):
                    continue

                permalink = f"https://www.reddit.com{submission.permalink}"
                selftext = (submission.selftext or "").strip()
                body_parts = [selftext] if selftext else []
                # Link posts: keep the external URL in the body for the writer/editor.
                if not submission.is_self and submission.url and submission.url != permalink:
                    body_parts.append(f"Link: {submission.url}")

                candidates.append(
                    {
                        "source": "reddit",
                        "title": submission.title,
                        "source_url": permalink,
                        "raw_text": "\n\n".join(body_parts) or submission.title,
                        "relevance_score": compute_relevance(submission.score, submission.num_comments),
                        "status": "new",
                    }
                )
                count += 1
            log.info("r/%s: %d candidate(s)", name, count)
        except Exception as exc:  # a single failing subreddit must not abort the run
            log.warning("r/%s: skipped (%s)", name, exc)

    return candidates


def run(
    since_hours: int = 24,
    min_score: int = 5,
    min_comments: int = 3,
    per_sub_limit: int = 200,
    threshold: int = DEFAULT_THRESHOLD,
    dry_run: bool = False,
) -> list[dict]:
    reddit = _build_reddit()
    candidates = collect_candidates(reddit, since_hours, min_score, min_comments, per_sub_limit)
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
    parser = argparse.ArgumentParser(description="Scrape Reddit for scam leads.")
    parser.add_argument("--since-hours", type=int, default=24, help="only posts from the last N hours")
    parser.add_argument("--min-score", type=int, default=5, help="keep posts with score > this")
    parser.add_argument("--min-comments", type=int, default=3, help="...or num_comments > this")
    parser.add_argument("--limit", type=int, default=200, help="max posts fetched per subreddit")
    parser.add_argument("--dedup-threshold", type=int, default=DEFAULT_THRESHOLD, help="fuzzy title threshold")
    parser.add_argument("--dry-run", action="store_true", help="do not write to the database")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    run(
        since_hours=args.since_hours,
        min_score=args.min_score,
        min_comments=args.min_comments,
        per_sub_limit=args.limit,
        threshold=args.dedup_threshold,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
