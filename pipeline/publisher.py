"""Publisher — promotes an approved article to published status in Supabase.

STUB: foundation only. Planned: set status='published', stamp published_at,
ensure slug uniqueness in the form {category}-{title-slug}-{YYYYMMDD}.
"""

from __future__ import annotations

import argparse


def run(article_id: str | None = None) -> None:
    raise NotImplementedError("publisher is implemented in a later phase")


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish an approved article.")
    parser.add_argument("--article-id", help="article to publish")
    args = parser.parse_args()
    run(article_id=args.article_id)


if __name__ == "__main__":
    main()
