"""Editor agent — fact-checks a draft, scores confidence, flags risk.

Fetches each source URL client-side (so it works without a model-side web tool),
passes the excerpts to Claude via a forced `emit_review` tool, then sets the
article's status based on the returned confidence:

  confidence >= threshold  -> 'review' (owner approval is always required)
  confidence <  threshold  -> 'flagged'   (with editor_notes)

Standalone:
    python pipeline/editor.py                  # edits the oldest draft
    python pipeline/editor.py --article-id <uuid> --dry-run
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running as a standalone script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.config import config, get_anthropic, get_supabase  # noqa: E402
from pipeline.fetch import fetch_text  # noqa: E402

log = logging.getLogger("editor")

SYSTEM_PROMPT = """\
You are the fact-checking editor for UnsocialEngineering.com. You review draft \
scam-awareness articles before publication.

Do all of the following, then return your review by calling the emit_review tool:
1. Verify the article's factual claims against the supplied source excerpts. Note \
any claim that the sources do not support.
2. Check for AI writing tells: em dashes; the words "crucial", "vital", \
"landscape", "navigate"; and listicle padding or filler. If you find any, return a \
cleaned-up revised_body_html and revised_summary with them removed. If the prose is \
already clean, leave those fields empty.
3. Assign ai_confidence from 0 to 100 based on source quality and how well the \
article's claims are verifiable from the sources. Be conservative when sources are \
thin, missing, or unreachable.
4. Flag legal or defamation risk: naming individuals not in public court records, \
or stating accusations as fact rather than attributing them to a source.

Report every issue you find with its severity; do not silently drop concerns."""


def _emit_review_tool() -> dict:
    return {
        "name": "emit_review",
        "description": "Return the editorial review of the draft article.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ai_confidence": {"type": "integer", "description": "0-100 confidence score."},
                "revised_body_html": {"type": "string", "description": "Cleaned HTML if AI tells were fixed, else empty."},
                "revised_summary": {"type": "string", "description": "Cleaned 2-sentence summary if revised, else empty."},
                "legal_risk": {"type": "boolean", "description": "True if any defamation/legal risk was found."},
                "issues": {"type": "array", "items": {"type": "string"}, "description": "Each issue found, with severity."},
                "editor_notes": {"type": "string", "description": "Short rationale for the score and decision."},
            },
            "required": ["ai_confidence", "legal_risk", "issues", "editor_notes"],
        },
    }


def _build_user_content(article: dict, sources: dict[str, str]) -> str:
    parts = [
        "Review this draft article.\n",
        f"TITLE: {article.get('title')}",
        f"SUMMARY: {article.get('summary')}",
        "BODY_HTML:",
        article.get("body_html") or "",
        "\nSOURCES:",
    ]
    if not sources:
        parts.append("(no source URLs were provided)")
    for url, text in sources.items():
        parts.append(f"\n[{url}]")
        parts.append(text if text else "(could not be fetched)")
    return "\n".join(parts)


def _fetch_draft(client, article_id: str | None) -> dict | None:
    query = client.table("articles").select("*").eq("status", "draft")
    if article_id:
        rows = query.eq("id", article_id).limit(1).execute().data
    else:
        rows = query.order("created_at").limit(1).execute().data
    return rows[0] if rows else None


def run(article_id: str | None = None, dry_run: bool = False) -> dict | None:
    client = get_supabase()
    article = _fetch_draft(client, article_id)
    if not article:
        log.info("No draft article to edit.")
        return None
    log.info("Editing article %s (%s)", article["id"], article.get("slug"))

    sources = {url: fetch_text(url) for url in (article.get("source_urls") or [])}

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    date_note = (
        f"Today's date is {today}. Sources dated on or before today are current. "
        "Do not treat recent dates as implausible or 'from the future', and do not "
        "lower confidence solely because a source is more recent than you expect."
    )

    anthropic_client = get_anthropic()
    response = anthropic_client.messages.create(
        model=config.claude_model,
        max_tokens=4096,
        system=[
            {"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": date_note},
        ],
        tools=[_emit_review_tool()],
        tool_choice={"type": "tool", "name": "emit_review"},
        messages=[{"role": "user", "content": _build_user_content(article, sources)}],
    )

    tool_use = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_use is None:
        log.error("Model did not return an emit_review tool call.")
        return None
    review = tool_use.input

    confidence = int(review.get("ai_confidence", 0))
    notes = review.get("editor_notes", "")
    if review.get("issues"):
        notes = notes + "\n\nIssues:\n- " + "\n- ".join(review["issues"])
    if review.get("legal_risk"):
        notes = "[LEGAL RISK]\n" + notes

    update: dict = {"ai_confidence": confidence, "editor_notes": notes}
    # Apply any cleaned-up prose.
    if review.get("revised_body_html"):
        update["body_html"] = review["revised_body_html"]
    if review.get("revised_summary"):
        update["summary"] = review["revised_summary"]

    if confidence >= config.confidence_threshold and not review.get("legal_risk"):
        update["status"] = "review"
    else:
        update["status"] = "flagged"

    log.info(
        "Confidence %d (threshold %d), legal_risk=%s -> status=%s",
        confidence, config.confidence_threshold, bool(review.get("legal_risk")), update["status"],
    )

    if dry_run:
        log.info("[dry-run] would update article with: %s", {k: v for k, v in update.items() if k != "body_html"})
        return update

    client.table("articles").update(update).eq("id", article["id"]).eq("status", "draft").execute()
    log.info("Updated article %s -> %s", article["id"], update["status"])
    return update


def main() -> None:
    parser = argparse.ArgumentParser(description="Fact-check and score a draft article.")
    parser.add_argument("--article-id", help="edit a specific draft")
    parser.add_argument("--dry-run", action="store_true", help="do not write to the database")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    run(article_id=args.article_id, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
