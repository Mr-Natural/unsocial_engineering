"""Writer agent — drafts a scam-awareness article from a lead or lead cluster.

Calls the Claude API with a forced `emit_article` tool so the response is
structured JSON (reliable on every tool-capable model, including the configured
Sonnet). Inserts the result into `articles` with status='draft'.

Standalone:
    python pipeline/writer.py                 # writes from the top unprocessed lead
    python pipeline/writer.py --cluster-id <uuid>
    python pipeline/writer.py --lead-id <uuid> --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running as a standalone script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.config import config, get_anthropic, get_supabase  # noqa: E402
from pipeline.fetch import fetch_text  # noqa: E402

log = logging.getLogger("writer")

# The 10 seeded categories (see supabase/migrations seed). The model picks one
# slug; we resolve it to a category_id against the live table.
CATEGORY_SLUGS = [
    "phishing", "romance-scam", "crypto-fraud", "investment-scam", "impersonation",
    "tech-support", "marketplace-fraud", "employment-scam", "government-impersonation",
    "subscription-trap",
]

SYSTEM_PROMPT = """\
You are a scam-awareness writer for UnsocialEngineering.com. You turn raw reports \
of scams into clear, practical articles for everyday people.

Voice and rules (follow exactly):
- Authoritative but accessible. Empowering, not fear-mongering. Think consumer \
watchdog, not tabloid.
- Cite your sources. Reference the supplied source URLs in the body where claims \
come from them, and return them in source_urls.
- Do NOT name individual victims unless the information comes from public court \
records. Do not name accused individuals or companies as scammers as fact; \
attribute claims to the reporting source.
- Give no legal advice. Point readers to the relevant authority (ACCC/Scamwatch in \
Australia, FTC in the US, Action Fraud/NCSC in the UK) for reporting and help.
- Avoid AI writing tells: no em dashes (use commas, full stops, or parentheses); \
do not use the words "crucial", "vital", "landscape", or "navigate"; no listicle \
padding or filler.
- Ground the article in the supplied report details and source content. Do not \
invent statistics, company names, dates, or specifics that the sources do not \
support. If a source is thin, keep the article appropriately general rather than \
fabricating detail.
- Length: 400 to 800 words.
- body_html must be clean semantic HTML using <h2>, <h3>, <p>, <ul>/<li>, and \
<a href> for source links. No inline styles, no <html>/<body> wrapper.
- summary must be exactly two sentences.
- Pick the single best category slug for the scam.

Return your article only by calling the emit_article tool."""


def _emit_article_tool() -> dict:
    return {
        "name": "emit_article",
        "description": "Return the finished scam-awareness article.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Punchy, specific headline."},
                "slug": {"type": "string", "description": "Kebab-case slug derived from the title (no category or date)."},
                "body_html": {"type": "string", "description": "400-800 word article as semantic HTML."},
                "summary": {"type": "string", "description": "Exactly two sentences."},
                "category_slug": {"type": "string", "enum": CATEGORY_SLUGS},
                "source_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "URLs cited in the article.",
                },
            },
            "required": ["title", "slug", "body_html", "summary", "category_slug", "source_urls"],
        },
    }


def _slugify(text: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", text)[:80] or "scam"


def _compose_slug(category_slug: str, title: str) -> str:
    """Project slug convention: {category}-{title-slug}-{YYYYMMDD}."""
    date = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{category_slug}-{_slugify(title)}-{date}"


def _unique_slug(client, base: str) -> str:
    slug, n = base, 2
    while client.table("articles").select("id").eq("slug", slug).limit(1).execute().data:
        slug = f"{base}-{n}"
        n += 1
    return slug


def _fetch_leads(client, lead_id: str | None, cluster_id: str | None) -> list[dict]:
    query = client.table("leads").select("*")
    if cluster_id:
        return query.eq("cluster_id", cluster_id).execute().data or []
    if lead_id:
        return query.eq("id", lead_id).execute().data or []
    # Default: the highest-relevance lead not yet written.
    rows = (
        query.eq("status", "new")
        .order("relevance_score", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    return rows


def _category_id_for(client, slug: str) -> str | None:
    rows = client.table("categories").select("id").eq("slug", slug).limit(1).execute().data
    return rows[0]["id"] if rows else None


def _build_user_content(leads: list[dict], sources: dict[str, str]) -> str:
    parts = ["Write an article based on the following scam report(s):\n"]
    for i, lead in enumerate(leads, 1):
        parts.append(f"--- Report {i} (source: {lead.get('source')}) ---")
        if lead.get("title"):
            parts.append(f"Title: {lead['title']}")
        url = lead.get("source_url")
        if url:
            parts.append(f"Source URL: {url}")
        if lead.get("raw_text"):
            parts.append(f"Summary:\n{lead['raw_text'][:2000]}")
        # Full source content (fetched), so the model writes from real material.
        source_text = sources.get(url) if url else None
        if source_text:
            parts.append(f"Source content:\n{source_text}")
        parts.append("")
    return "\n".join(parts)


def run(lead_id: str | None = None, cluster_id: str | None = None, dry_run: bool = False) -> dict | None:
    client = get_supabase()
    leads = _fetch_leads(client, lead_id, cluster_id)
    if not leads:
        log.info("No leads to write about.")
        return None
    log.info("Writing from %d lead(s)", len(leads))

    # Fetch full source content so the draft is grounded in real material, not
    # just the (often thin) lead summary.
    sources = {
        url: fetch_text(url)
        for url in {l["source_url"] for l in leads if l.get("source_url")}
    }

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    date_note = (
        f"Today's date is {today}. The reports below describe current scams; treat "
        "their dates as present-day, not future-dated."
    )

    anthropic_client = get_anthropic()
    response = anthropic_client.messages.create(
        model=config.claude_model,
        max_tokens=4096,
        system=[
            {"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": date_note},
        ],
        tools=[_emit_article_tool()],
        tool_choice={"type": "tool", "name": "emit_article"},
        messages=[{"role": "user", "content": _build_user_content(leads, sources)}],
    )

    tool_use = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_use is None:
        log.error("Model did not return an emit_article tool call.")
        return None
    draft = tool_use.input

    category_id = _category_id_for(client, draft.get("category_slug", ""))
    # Source URLs: union of what the model cited and the leads' own URLs.
    lead_urls = [l["source_url"] for l in leads if l.get("source_url")]
    source_urls = list(dict.fromkeys((draft.get("source_urls") or []) + lead_urls))

    article = {
        "title": draft["title"],
        "body_html": draft["body_html"],
        "summary": draft["summary"],
        "category_id": category_id,
        "source_urls": source_urls,
        "status": "draft",
    }

    if dry_run:
        log.info("[dry-run] draft article: %s", json.dumps({**article, "body_html": f"<{len(article['body_html'])} chars>"}, indent=2))
        return article

    article["slug"] = _unique_slug(client, _compose_slug(draft.get("category_slug", "scam"), draft["title"]))
    inserted = client.table("articles").insert(article).execute().data[0]
    log.info("Inserted draft article %s (%s)", inserted["id"], inserted["slug"])

    # Mark the source leads as written.
    lead_ids = [l["id"] for l in leads]
    client.table("leads").update({"status": "written"}).in_("id", lead_ids).execute()
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Draft an article from a lead or cluster.")
    parser.add_argument("--lead-id", help="write from a single lead")
    parser.add_argument("--cluster-id", help="write from all leads in a cluster")
    parser.add_argument("--dry-run", action="store_true", help="do not write to the database")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    run(lead_id=args.lead_id, cluster_id=args.cluster_id, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
