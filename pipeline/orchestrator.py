"""Orchestrator — single entry point that runs the full pipeline in sequence.

  1. Scrape all sources (in parallel)
  2. Process & cluster leads, write articles for the top N clusters
  3. Edit every draft article
  4. Generate social posts for newly published articles

Designed to run unattended as a cron job (e.g. every 6 hours). Logs each stage to
stdout with timestamps.

    python pipeline/orchestrator.py                 # full run
    python pipeline/orchestrator.py --source reddit # only scrape reddit, then continue
    python pipeline/orchestrator.py --write-only     # skip scraping
    python pipeline/orchestrator.py --social-only     # only generate social posts
    python pipeline/orchestrator.py --dry-run         # no database writes
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

# Allow running as a standalone script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import editor, processor, social  # noqa: E402
from pipeline.config import config, get_supabase  # noqa: E402
from pipeline.sources import reddit_scraper, rss_scraper  # noqa: E402

log = logging.getLogger("orchestrator")

SOURCES = {"reddit": reddit_scraper, "rss": rss_scraper}


async def _scrape(source: str | None, dry_run: bool) -> None:
    """Run the selected scrapers concurrently (each is blocking I/O, so off-thread)."""
    names = [source] if source else list(SOURCES)
    jobs = {name: asyncio.to_thread(SOURCES[name].run, dry_run=dry_run) for name in names}
    results = await asyncio.gather(*jobs.values(), return_exceptions=True)
    for name, result in zip(jobs, results):
        if isinstance(result, Exception):
            log.warning("scraper %s failed: %s", name, result)
        else:
            log.info("scraper %s ingested %d new lead(s)", name, len(result or []))


def _edit_all_drafts(dry_run: bool) -> None:
    client = get_supabase()
    drafts = client.table("articles").select("id").eq("status", "draft").execute().data or []
    log.info("editing %d draft article(s)", len(drafts))
    for draft in drafts:
        try:
            editor.run(article_id=draft["id"], dry_run=dry_run)
        except Exception as exc:
            log.warning("editing %s failed: %s", draft["id"], exc)


def run(
    source: str | None = None,
    write_only: bool = False,
    social_only: bool = False,
    dry_run: bool = False,
    top: int | None = None,
) -> None:
    started = time.monotonic()
    top = top if top is not None else config.max_articles_per_run

    if social_only:
        log.info("== social only ==")
        social.run(dry_run=dry_run)
        log.info("done in %.1fs", time.monotonic() - started)
        return

    if not write_only:
        log.info("== stage 1: scrape ==")
        asyncio.run(_scrape(source, dry_run))

    log.info("== stage 2: process + write top %d cluster(s) ==", top)
    processor.run(write=True, top=top, dry_run=dry_run)

    log.info("== stage 3: edit drafts ==")
    _edit_all_drafts(dry_run)

    log.info("== stage 4: social ==")
    social.run(dry_run=dry_run)

    log.info("pipeline finished in %.1fs", time.monotonic() - started)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the UnsocialEngineering content pipeline.")
    parser.add_argument("--source", choices=list(SOURCES), help="scrape a single source, then continue")
    parser.add_argument("--write-only", action="store_true", help="skip scraping; process/write/edit/social")
    parser.add_argument("--social-only", action="store_true", help="only generate social posts")
    parser.add_argument("--top", type=int, help="clusters to write (default: MAX_ARTICLES_PER_RUN)")
    parser.add_argument("--dry-run", action="store_true", help="run without writing to the database")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    run(
        source=args.source,
        write_only=args.write_only,
        social_only=args.social_only,
        dry_run=args.dry_run,
        top=args.top,
    )


if __name__ == "__main__":
    main()
