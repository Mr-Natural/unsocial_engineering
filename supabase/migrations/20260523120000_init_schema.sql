-- UnsocialEngineering.com — initial schema
-- Tables: categories, leads, articles, social_posts
-- Row Level Security: public (anon) read of published articles + all categories.
-- The pipeline writes using the service_role key, which bypasses RLS entirely,
-- so no write policies are defined for anon/authenticated.

-- gen_random_uuid() is provided natively by Postgres 13+ (and by pgcrypto on Supabase).

-- ---------------------------------------------------------------------------
-- categories
-- ---------------------------------------------------------------------------
create table if not exists public.categories (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  slug        text not null unique,
  description text,
  icon        text
);

-- ---------------------------------------------------------------------------
-- leads — raw story leads from scrapers
-- ---------------------------------------------------------------------------
create table if not exists public.leads (
  id              uuid primary key default gen_random_uuid(),
  source          text not null,
  source_url      text,
  raw_text        text,
  relevance_score integer,
  status          text not null default 'new',
  scraped_at      timestamptz not null default now(),
  cluster_id      uuid
);

create index if not exists leads_status_idx     on public.leads (status);
create index if not exists leads_cluster_id_idx on public.leads (cluster_id);
create index if not exists leads_scraped_at_idx on public.leads (scraped_at desc);

-- ---------------------------------------------------------------------------
-- articles — published content
-- ---------------------------------------------------------------------------
create table if not exists public.articles (
  id            uuid primary key default gen_random_uuid(),
  title         text not null,
  slug          text not null unique,
  body_html     text,
  summary       text,
  category_id   uuid references public.categories (id) on delete set null,
  source_urls   text[] not null default '{}',
  ai_confidence integer,
  status        text not null default 'draft',
  created_at    timestamptz not null default now(),
  published_at  timestamptz
);

create index if not exists articles_status_published_idx
  on public.articles (status, published_at desc);
create index if not exists articles_category_id_idx on public.articles (category_id);

-- ---------------------------------------------------------------------------
-- social_posts — generated social content linked to an article
-- ---------------------------------------------------------------------------
create table if not exists public.social_posts (
  id         uuid primary key default gen_random_uuid(),
  article_id uuid references public.articles (id) on delete cascade,
  platform   text not null,
  content    text,
  posted_at  timestamptz,
  status     text not null default 'pending'
);

create index if not exists social_posts_article_id_idx on public.social_posts (article_id);
create index if not exists social_posts_status_idx     on public.social_posts (status);

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------
alter table public.categories   enable row level security;
alter table public.leads        enable row level security;
alter table public.articles     enable row level security;
alter table public.social_posts enable row level security;

-- Categories are public reference data: anyone may read them.
create policy "Public can read categories"
  on public.categories
  for select
  to anon, authenticated
  using (true);

-- Articles are public only once published.
create policy "Public can read published articles"
  on public.articles
  for select
  to anon, authenticated
  using (status = 'published');

-- leads and social_posts have RLS enabled with no anon/authenticated policy,
-- so they are not readable or writable by public clients. The pipeline accesses
-- them with the service_role key, which bypasses RLS.
