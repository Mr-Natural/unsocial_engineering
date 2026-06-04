"""Social agent — generates platform-specific posts for published articles.

For each published article that has no social posts yet, asks Claude (via a forced
`emit_social` tool) for an X/Twitter post, a Reddit-style summary, and a longer
Facebook/LinkedIn post, then inserts them into social_posts with status='pending'.
Actual posting is a later phase; this only generates and stores the content.

Standalone:
    python pipeline/social.py
    python pipeline/social.py --article-id <uuid> --dry-run
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Allow running as a standalone script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.config import config, get_anthropic, get_supabase  # noqa: E402

log = logging.getLogger("social")

SYSTEM_PROMPT = """\
You write social media posts for UnsocialEngineering.com, a scam-awareness site.
Given an article, produce posts that drive people to read it and stay safe.

Rules (apply to every platform):
- Authoritative but accessible, empowering not fear-mongering.
- No em dashes; do not use "crucial", "vital", "landscape", or "navigate".
- Always include the article link where indicated.
- Do not invent facts beyond the article's title and summary.

Return the posts only by calling the emit_social tool."""


def _emit_social_tool() -> dict:
    return {
        "name": "emit_social",
        "description": "Return platform-specific social posts for the article.",
        "input_schema": {
            "type": "object",
            "properties": {
                "twitter": {
                    "type": "string",
                    "description": "X/Twitter post, 280 characters max INCLUDING the link. Hook + link.",
                },
                "reddit": {
                    "type": "string",
                    "description": "Reddit-style summary for manual posting to a relevant subreddit. A few sentences, plain and helpful, ending with the link.",
                },
                "facebook": {
                    "type": "string",
                    "description": "Longer Facebook/LinkedIn post with more context and a clear call to read, ending with the link.",
                },
            },
            "required": ["twitter", "reddit", "facebook"],
        },
    }


def _articles_needing_social(client, article_id: str | None) -> list[dict]:
    if article_id:
        rows = client.table("articles").select("*").eq("id", article_id).execute().data or []
        return rows
    published = (
        client.table("articles")
        .select("*")
        .eq("status", "published")
        .order("published_at", desc=True)
        .execute()
        .data
        or []
    )
    existing = client.table("social_posts").select("article_id").execute().data or []
    have = {r["article_id"] for r in existing}
    return [a for a in published if a["id"] not in have]


def _generate(article: dict) -> dict | None:
    link = f"{config.site_url}/scams/{article['slug']}"
    content = (
        f"Title: {article['title']}\n"
        f"Summary: {article.get('summary') or ''}\n"
        f"Article link: {link}"
    )
    response = get_anthropic().messages.create(
        model=config.claude_model,
        max_tokens=1500,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        tools=[_emit_social_tool()],
        tool_choice={"type": "tool", "name": "emit_social"},
        messages=[{"role": "user", "content": content}],
    )
    tool_use = next((b for b in response.content if b.type == "tool_use"), None)
    return tool_use.input if tool_use else None


def run(article_id: str | None = None, limit: int | None = None, dry_run: bool = False) -> int:
    client = get_supabase()
    articles = _articles_needing_social(client, article_id)
    if limit:
        articles = articles[:limit]
    log.info("%d published article(s) need social posts", len(articles))

    created = 0
    for article in articles:
        posts = _generate(article)
        if not posts:
            log.warning("no social posts generated for %s", article["id"])
            continue

        # facebook content is reused for LinkedIn (same long-form post).
        rows = [
            {"article_id": article["id"], "platform": "twitter", "content": posts["twitter"], "status": "pending"},
            {"article_id": article["id"], "platform": "reddit", "content": posts["reddit"], "status": "pending"},
            {"article_id": article["id"], "platform": "facebook", "content": posts["facebook"], "status": "pending"},
            {"article_id": article["id"], "platform": "linkedin", "content": posts["facebook"], "status": "pending"},
        ]
        if dry_run:
            log.info("[dry-run] would insert %d post(s) for %s", len(rows), article["slug"])
            log.info("[dry-run] twitter (%d chars): %s", len(posts["twitter"]), posts["twitter"])
        else:
            client.table("social_posts").insert(rows).execute()
            log.info("inserted %d social post(s) for %s", len(rows), article["slug"])
        created += len(rows)

    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate social posts for published articles.")
    parser.add_argument("--article-id", help="generate for a single article")
    parser.add_argument("--limit", type=int, help="cap how many articles to process")
    parser.add_argument("--dry-run", action="store_true", help="do not write to the database")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    run(article_id=args.article_id, limit=args.limit, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
