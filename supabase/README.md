# Supabase

Schema and Row Level Security live in `migrations/`. These are plain SQL and can
be applied either with the Supabase CLI (recommended) or by pasting into the SQL
editor in the dashboard.

## Migrations

| File | Purpose |
| --- | --- |
| `20260523120000_init_schema.sql` | Tables (`categories`, `leads`, `articles`, `social_posts`), indexes, and RLS policies. |
| `20260523120100_seed_categories.sql` | Seeds the 10 scam categories (idempotent). |

## Applying with the CLI

The CLI is not installed in this repo by default. Once you have it
(`scoop install supabase`, `brew install supabase/tap/supabase`, or the
[release binaries](https://github.com/supabase/cli/releases)):

```bash
supabase login
supabase link --project-ref <your-project-ref>   # from the dashboard URL
supabase db push                                  # applies migrations/ in order
```

`supabase init` is optional — only needed if you want a local `config.toml` for
running Supabase locally. It will not touch the existing `migrations/` folder.

## Row Level Security summary

- `categories` — public `SELECT` (reference data).
- `articles` — public `SELECT` only where `status = 'published'`.
- `leads`, `social_posts` — RLS on, no public policy; reachable only via the
  `service_role` key (which bypasses RLS), used by the pipeline.
