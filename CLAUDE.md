# UnsocialEngineering.com — Project Conventions

## Project Overview
Scam tracking and information resource website. AI-automated content pipeline discovers, writes, verifies, and publishes scam awareness stories. Target audience: everyday people who need practical, accessible scam awareness content.

## Tech Stack
- **Framework:** Next.js 15 (App Router, TypeScript, Tailwind CSS)
- **Database:** Supabase (Postgres) — hosted in Sydney region
- **Deployment:** Vercel
- **Content Pipeline:** Python scripts + Claude API
- **Package Manager:** pnpm

## Project Structure
```
unsocialengineering/
├── src/
│   ├── app/                  # Next.js App Router pages
│   │   ├── page.tsx          # Homepage — latest scams, trending, search
│   │   ├── scams/
│   │   │   ├── page.tsx      # Browse/filter all scams
│   │   │   └── [slug]/
│   │   │       └── page.tsx  # Individual scam article
│   │   ├── categories/       # Scam categories (phishing, romance, crypto, etc.)
│   │   ├── check/            # "Is this a scam?" interactive checker tool
│   │   └── api/              # API routes for pipeline webhooks
│   ├── components/           # Shared UI components
│   ├── lib/                  # Utilities, Supabase client, types
│   └── styles/               # Global styles
├── pipeline/                 # Python content automation
│   ├── config.py             # API keys, Supabase connection, settings
│   ├── sources/              # Source scrapers
│   │   ├── reddit_scraper.py # r/Scams, r/phishing, r/fraud, etc.
│   │   ├── twitter_scraper.py# Scam-related Twitter/X monitoring
│   │   └── rss_scraper.py    # News RSS feeds (FTC, ACCC, Action Fraud)
│   ├── processor.py          # Dedup, cluster, score story leads
│   ├── writer.py             # Claude API — draft article from lead
│   ├── editor.py             # Claude API — fact-check, tone, compliance
│   ├── publisher.py          # Push approved article to Supabase
│   ├── social.py             # Generate + post social media summaries
│   └── orchestrator.py       # Cron-driven pipeline controller
├── supabase/
│   └── migrations/           # Database migrations
└── CLAUDE.md                 # This file
```

## Database Schema (Supabase)
Key tables:
- `leads` — raw story leads from scrapers (source, url, raw_text, score, status)
- `articles` — published content (title, slug, body_html, category, source_urls, published_at, ai_confidence)
- `categories` — scam taxonomy (phishing, romance, crypto, investment, impersonation, etc.)
- `social_posts` — generated social media content linked to articles

## Content Pipeline Flow
```
Sources (Reddit/Twitter/RSS)
  → Scrape & ingest leads
  → Deduplicate & score relevance
  → Writer agent drafts article
  → Editor agent verifies facts, checks tone, flags issues
  → Owner reviews an immutable revision and explicitly approves its hash
  → Restricted publisher commits that exact revision to Supabase
  → Social copy remains a revision-linked review draft
```

## Design & Brand
- **Tone:** Authoritative but accessible. Not fear-mongering — empowering. Think consumer watchdog, not tabloid.
- **Palette:** Dark theme. Deep charcoal/navy base. Accent: warning amber/orange for alerts, teal/green for "safe" indicators.
- **Typography:** Clean sans-serif. Headlines bold and punchy. Body highly readable.
- **Logo concept:** Shield or lock motif — protection-oriented.

## AI Content Rules
- Every article MUST cite its source(s) with links
- Articles must NOT name individual victims unless from public court records
- Confidence scores are editorial suggestions, never permission to publish. Every revision requires owner approval.
- No legal advice — always direct to relevant authority (ACCC, FTC, Action Fraud, etc.)
- Avoid AI writing tells: no em dashes, no "crucial/vital/landscape/navigate", no listicle padding

## Key Commands
```bash
# Dev
pnpm dev                          # Next.js dev server
python pipeline/orchestrator.py   # Run full pipeline once
python pipeline/orchestrator.py --source reddit  # Single source

# Deploy
vercel --prod
```

## Environment Variables
```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
ANTHROPIC_API_KEY=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
TWITTER_BEARER_TOKEN=
```

## Conventions
- All Python scripts use `if __name__ == "__main__"` with argparse
- Supabase RLS enabled. New publishing uses restricted authenticated RPCs; legacy pipeline service-role access remains a migration risk. See AGENTS.md and docs/reviewed-publishing.md.
- Slug format: `{category}-{title-slug}-{YYYYMMDD}`
- All dates stored as UTC, displayed in user's local timezone
- Git: conventional commits, main branch is production
