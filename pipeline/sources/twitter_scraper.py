"""Twitter/X scraper.

DEFERRED: skipped initially due to API costs ($100/mo minimum for v2 search).
See the notes in UNSOCIALENGINEERING_CC_PROMPTS.md. Left as a placeholder so the
source layout matches CLAUDE.md.
"""

from __future__ import annotations

import argparse


def run() -> None:
    raise NotImplementedError("twitter_scraper is deferred — see project notes")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Twitter/X for scam leads (deferred).")
    parser.parse_args()
    run()


if __name__ == "__main__":
    main()
