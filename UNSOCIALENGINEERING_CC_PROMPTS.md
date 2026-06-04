# UnsocialEngineering.com — Claude Code Prompts

## PHASE 1: Project Scaffold & Database
Paste this first:

```
Read CLAUDE.md thoroughly. Then scaffold the project:

1. Init Next.js 15 with App Router, TypeScript, Tailwind, pnpm
2. Create the Supabase project (Sydney region) and set up these tables with migrations:
   - leads (id uuid, source text, source_url text, raw_text text, relevance_score int, status text default 'new', scraped_at timestamptz, cluster_id uuid nullable)
   - articles (id uuid, title text, slug text unique, body_html text, summary text, category_id uuid references categories, source_urls text[], ai_confidence int, status text default 'draft', created_at timestamptz, published_at timestamptz nullable)
   - categories (id uuid, name text, slug text unique, description text, icon text)
   - social_posts (id uuid, article_id uuid references articles, platform text, content text, posted_at timestamptz nullable, status text default 'pending')
3. Enable RLS: public SELECT on articles (where status='published') and categories. Service role for everything else.
4. Seed categories: phishing, romance-scam, crypto-fraud, investment-scam, impersonation, tech-support, marketplace-fraud, employment-scam, government-impersonation, subscription-trap
5. Create the pipeline/ directory structure per CLAUDE.md with config.py reading from .env
6. Set up Vercel project linked to GitHub repo

Don't build any pages yet — just the foundation.
```

---

## PHASE 2: Content Pipeline — Scrapers
```
Build the Reddit scraper in pipeline/sources/reddit_scraper.py:

- Use PRAW (Reddit API via reddit app credentials in .env)
- Monitor subreddits: r/Scams, r/phishing, r/fraud, r/personalfinance (scam-tagged), r/AusFinance (scam-tagged)
- For each post: extract title, selftext, url, score, num_comments, created_utc
- Only ingest posts from last 24 hours with score > 5 or num_comments > 3
- Insert into leads table with source='reddit', relevance_score based on engagement metrics
- Deduplicate against existing leads using fuzzy title matching (rapidfuzz, threshold 85)

Then build pipeline/sources/rss_scraper.py:
- Fetch RSS from: ACCC Scamwatch, FTC consumer alerts, Action Fraud UK, Snopes (scam tag)
- Parse with feedparser, insert as leads with source='rss'
- Same dedup logic

Skip Twitter/X for now — API costs are high. We'll add it later or use an alternative.

Each scraper should work standalone: `python pipeline/sources/reddit_scraper.py`
```

---

## PHASE 3: Content Pipeline — Writer & Editor Agents
```
Build the writer and editor agents:

pipeline/writer.py:
- Takes a lead (or cluster of related leads) from the leads table
- Calls Claude API (claude-sonnet-4-20250514) with a system prompt that produces a scam awareness article
- System prompt must enforce: cite sources, no victim naming, no legal advice, direct to authorities, no AI writing tells (no em dashes, no "crucial/landscape/navigate"), tone is authoritative but accessible
- Output: title, slug, body_html, summary (2 sentences), suggested category_id, source_urls array
- Article length: 400-800 words
- Insert into articles table with status='draft'

pipeline/editor.py:
- Takes a draft article from the articles table
- Calls Claude API with editor system prompt:
  - Verify claims against source URLs (fetch and cross-reference)
  - Check for AI writing tells and rewrite if found
  - Assign ai_confidence score (0-100) based on source quality and claim verifiability
  - Flag any potential defamation or legal risk
- If confidence >= 70: set status='review' (or 'published' if auto_publish=true in config)
- If confidence < 70: set status='flagged' with editor notes

pipeline/processor.py:
- Cluster related leads using TF-IDF + cosine similarity
- Score clusters by: number of leads, total engagement, source diversity, recency
- Feed top-scoring clusters to writer.py

Make each script runnable standalone with argparse.
```

---

## PHASE 4: Website Frontend
```
Build the Next.js frontend per CLAUDE.md structure:

Homepage (src/app/page.tsx):
- Hero section: "Don't Get Played" tagline, search bar for "Is this a scam?" checker
- Latest scams grid (6 cards) pulling from Supabase articles where status='published', ordered by published_at desc
- Trending scams sidebar (by category volume last 7 days)
- Alert banner component for breaking/urgent scams

Browse page (src/app/scams/page.tsx):
- Filterable by category, searchable, paginated
- Card shows: title, summary, category badge, confidence indicator, date

Article page (src/app/scams/[slug]/page.tsx):
- Full article with source citations
- "Report a Scam" CTA
- Related articles sidebar
- Share buttons

Category pages (src/app/categories/[slug]/page.tsx):
- Category description + filtered article list

Design: dark theme per CLAUDE.md brand guidelines. Use the warning amber/orange and teal/green accents. Mobile-first. Fast — aim for 95+ Lighthouse performance.
```

---

## PHASE 5: Orchestrator & Social
```
Build the orchestrator and social posting:

pipeline/orchestrator.py:
- Single entry point that runs the full pipeline in sequence:
  1. Run all scrapers (parallel with asyncio)
  2. Process & cluster leads
  3. Write articles for top N clusters (configurable, default 3)
  4. Edit all draft articles
  5. Generate social posts for newly published articles
- Support CLI flags: --source (single source), --write-only, --social-only, --dry-run
- Log everything to stdout with timestamps
- Designed to run as a cron job (e.g., every 6 hours)

pipeline/social.py:
- For each published article without social posts:
  - Generate Twitter/X post (280 chars, hook + link)
  - Generate Reddit-style summary (for manual posting to relevant subs)
  - Generate Facebook/LinkedIn post (longer, more context)
- Insert into social_posts table with status='pending'
- Actual posting integration is Phase 6 (for now just generates the content)

Add a simple /api/pipeline/status route that returns:
- Last run timestamp
- Counts: leads today, articles drafted, articles published
- Any flagged articles needing review
```

---

## PHASE 6: "Is This a Scam?" Checker Tool
```
Build the interactive scam checker at src/app/check/page.tsx:

- User pastes suspicious text (email, SMS, social media message, URL)
- Client sends to /api/check endpoint
- API calls Claude with a specialized system prompt:
  - Analyze the text for known scam patterns
  - Check for: urgency tactics, impersonation, too-good-to-be-true offers, suspicious URLs, requests for personal info/money
  - Return: risk_level (low/medium/high/critical), identified_patterns[], explanation, recommended_actions[]
- Display results with clear visual indicators (green/amber/red/flashing red)
- Show similar known scams from the articles database
- Include "Report This" button that creates a lead in the database

Rate limit: 10 checks per IP per hour (use Vercel KV or Supabase)
```

---

## Notes for Shaun
- **Twitter/X scraping:** Skipped initially due to API costs ($100/mo minimum for v2 search). Alternatives: Nitter instances (unreliable), or manual curation. Can revisit.
- **Auto-publish toggle:** Set `AUTO_PUBLISH=false` in .env initially. Review a few rounds manually before turning on.
- **Legal:** Add a disclaimer footer: "Information only. Not legal advice. If you've been scammed, contact [ACCC/local authority]."
- **SEO:** Each article page should have structured data (Article schema), OpenGraph tags, and a sitemap.xml generated from published articles.
- **Future additions:** Email newsletter (Resend API), browser extension for real-time URL checking, community reporting/voting system.
