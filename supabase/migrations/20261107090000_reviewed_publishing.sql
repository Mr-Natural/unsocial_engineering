-- Additive publishing pilot. No identities are provisioned and nothing is published.
-- Apply only after verifying the intended Supabase project and reviewing this migration.
begin;

alter table public.articles add column revised_at timestamptz;
alter table public.articles add column evidence_label text;
alter table public.articles add column editorial_stream text;
alter table public.articles add column region text;
alter table public.articles add column research_as_of timestamptz;
alter table public.articles add column author_credit text;

create schema ue_private;
revoke all on schema ue_private from public, anon, authenticated, service_role;

create table ue_private.members (
  user_id uuid not null unique,
  role text not null check (role in ('producer', 'editor', 'publisher')),
  primary key (user_id, role)
);
create table ue_private.destinations (
  external_id text primary key,
  slug text not null unique,
  article_id uuid unique references public.articles(id),
  current_hash text,
  withdrawn_at timestamptz,
  review_epoch integer not null default 0
);
create table ue_private.revisions (
  id uuid primary key default gen_random_uuid(),
  external_id text not null references ue_private.destinations(external_id),
  revision_hash text not null unique,
  envelope jsonb not null,
  created_by uuid not null,
  created_at timestamptz not null default now()
);
create table ue_private.approvals (
  revision_id uuid primary key references ue_private.revisions(id),
  approved_by uuid not null,
  approved_at timestamptz not null default now(),
  revoked_at timestamptz
);
create table ue_private.events (
  id bigint generated always as identity primary key,
  revision_id uuid not null references ue_private.revisions(id),
  action text not null,
  actor uuid not null,
  occurred_at timestamptz not null default now()
);
create table ue_private.receipts (
  revision_id uuid primary key references ue_private.revisions(id),
  article_id uuid not null references public.articles(id),
  published_at timestamptz not null default now(),
  published_by uuid not null,
  receipt jsonb not null
);
create table ue_private.withdrawals (
  revision_id uuid primary key references ue_private.revisions(id),
  withdrawn_by uuid not null,
  withdrawn_at timestamptz not null default now(),
  reason text not null,
  receipt jsonb not null
);
-- Separate from the legacy social queue: nothing here can be sent automatically.
create table ue_private.social_drafts (
  revision_id uuid primary key references ue_private.revisions(id),
  content text not null,
  status text not null default 'review_draft' check (status in ('review_draft', 'superseded', 'withdrawn'))
);
alter table ue_private.members enable row level security;
alter table ue_private.destinations enable row level security;
alter table ue_private.revisions enable row level security;
alter table ue_private.approvals enable row level security;
alter table ue_private.events enable row level security;
alter table ue_private.receipts enable row level security;
alter table ue_private.withdrawals enable row level security;
alter table ue_private.social_drafts enable row level security;
revoke all on all tables in schema ue_private from public, anon, authenticated, service_role;
revoke all on all sequences in schema ue_private from public, anon, authenticated, service_role;

insert into public.categories(name, slug, description) values
 ('The psychology of deception', 'psychology-of-deception', 'How manipulation works.'),
 ('Traditional threats, modern victims', 'traditional-threats', 'Recognising established scams.'),
 ('AI and the new generation of deception', 'ai-and-deception', 'Evidence and emerging risks.'),
 ('Your money, identity and digital life', 'money-identity-digital-life', 'Practical protection.'),
 ('The future of trust and security', 'future-of-trust', 'How trust and security are changing.')
on conflict (slug) do nothing;

create function ue_private.require_role(wanted text[]) returns uuid
language plpgsql security definer set search_path = '' as $$
declare actor uuid := auth.uid();
begin
  if auth.role() is distinct from 'authenticated' or actor is null then
    raise exception 'Authenticated editorial identity required' using errcode = '42501';
  end if;
  -- Lock membership until commit so concurrent removal cannot race publication.
  perform 1 from ue_private.members where user_id = actor and role = any(wanted) for share;
  if not found then raise exception 'Editorial role required' using errcode = '42501'; end if;
  return actor;
end $$;

create function ue_private.escape_html(value text) returns text
language sql immutable strict set search_path = '' as $$
 select replace(replace(replace(replace(replace(value, '&', '&amp;'), '<', '&lt;'), '>', '&gt;'), '"', '&quot;'), '''', '&#39;');
$$;

create function ue_private.required_text(value jsonb, max_length integer) returns text
language plpgsql immutable set search_path = '' as $$
begin
 if jsonb_typeof(value) is distinct from 'string' or length(btrim(value #>> '{}')) not between 1 and max_length then
   raise exception 'Missing, invalid or oversized text' using errcode = '22023';
 end if;
 return value #>> '{}';
end $$;

create function ue_private.require_array(value jsonb, min_length integer, max_length integer) returns void
language plpgsql immutable set search_path = '' as $$
begin
 if jsonb_typeof(value) is distinct from 'array' then
   raise exception 'Expected array' using errcode = '22023';
 end if;
 if jsonb_array_length(value) not between min_length and max_length then
   raise exception 'Invalid array size' using errcode = '22023';
 end if;
end $$;

-- This renderer is versioned in every envelope. All supplied text is escaped.
-- Links are HTTPS URLs with a hostname and no credentials, whitespace or delimiters.
create function ue_private.render_article(p jsonb) returns text
language plpgsql immutable set search_path = '' as $$
declare s jsonb; section jsonb; para jsonb; ref jsonb; action jsonb;
  ids text[] := '{}'; source_id text; url text; html text; cited integer := 0;
begin
 if jsonb_typeof(p) is distinct from 'object' or octet_length(p::text) > 200000 then
   raise exception 'Invalid or oversized article' using errcode = '22023';
 end if;
 if p - array['title','summary','category_slug','stream','region','evidence_label','evidence_note','research_as_of','sections','sources','actions','social_copy','author_credit'] <> '{}'::jsonb then
   raise exception 'Unknown article fields' using errcode = '22023';
 end if;
 perform ue_private.required_text(p->'title', 200);
 perform ue_private.required_text(p->'summary', 1000);
 perform ue_private.required_text(p->'author_credit', 200);
 perform ue_private.required_text(p->'social_copy', 2000);
 if p->>'category_slug' is null or p->>'category_slug' not in
 ('psychology-of-deception','traditional-threats','ai-and-deception','money-identity-digital-life','future-of-trust') then
   raise exception 'Unknown editorial pillar' using errcode = '22023';
 end if;
 if p->>'stream' is null or p->>'stream' not in ('evergreen_education','verified_threat_briefing') then
   raise exception 'Unknown stream' using errcode = '22023';
 end if;
 if p->>'evidence_label' is null or p->>'evidence_label' not in ('Confirmed Threat','Emerging Risk','Hypothetical Scenario') then
   raise exception 'Unknown evidence classification' using errcode = '22023';
 end if;
 -- Keep a literal UTC research cutoff, separate from publication time.
 if ue_private.required_text(p->'research_as_of', 20) !~ '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$' then
   raise exception 'Research cutoff must be UTC ISO time' using errcode = '22023';
 end if;
 perform (p->>'research_as_of')::timestamptz;
 html := '<p><strong>' || ue_private.escape_html(p->>'evidence_label') || '</strong> · '
   || ue_private.escape_html(ue_private.required_text(p->'region', 100)) || '</p><p>'
   || ue_private.escape_html(ue_private.required_text(p->'evidence_note', 2000)) || '</p><p>By '
   || ue_private.escape_html(p->>'author_credit') || '. Research as of '
   || ue_private.escape_html(p->>'research_as_of') || '.</p>';
 perform ue_private.require_array(p->'sources', 1, 50);
 for s in select value from jsonb_array_elements(p->'sources') loop
   if jsonb_typeof(s) <> 'object' or s - array['id','title','publisher','url'] <> '{}'::jsonb then
     raise exception 'Invalid source fields' using errcode = '22023';
   end if;
   source_id := ue_private.required_text(s->'id', 80);
   if source_id = any(ids) then raise exception 'Duplicate source ID' using errcode = '22023'; end if;
   ids := array_append(ids, source_id);
   perform ue_private.required_text(s->'title', 300);
   perform ue_private.required_text(s->'publisher', 200);
   url := ue_private.required_text(s->'url', 2048);
   if url !~ '^https://[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?(/[^[:space:]<>"\\]*)?$' then
     raise exception 'Source must be a plain HTTPS URL without credentials' using errcode = '22023';
   end if;
 end loop;
 perform ue_private.require_array(p->'sections', 1, 30);
 for section in select value from jsonb_array_elements(p->'sections') loop
   if jsonb_typeof(section) <> 'object' or section - array['heading','paragraphs'] <> '{}'::jsonb then
     raise exception 'Invalid section fields' using errcode = '22023';
   end if;
   html := html || '<h2>' || ue_private.escape_html(ue_private.required_text(section->'heading', 200)) || '</h2>';
   perform ue_private.require_array(section->'paragraphs', 1, 30);
   for para in select value from jsonb_array_elements(section->'paragraphs') loop
     if jsonb_typeof(para) <> 'object' or para - array['text','source_ids'] <> '{}'::jsonb then
       raise exception 'Invalid paragraph fields' using errcode = '22023';
     end if;
     html := html || '<p>' || ue_private.escape_html(ue_private.required_text(para->'text', 10000));
     perform ue_private.require_array(para->'source_ids', 0, 20);
     for ref in select value from jsonb_array_elements(para->'source_ids') loop
       source_id := ue_private.required_text(ref, 80);
       if not source_id = any(ids) then raise exception 'Unresolved source reference' using errcode = '22023'; end if;
       select value into s from jsonb_array_elements(p->'sources') where value->>'id' = source_id;
       html := html || ' <a rel="noopener noreferrer" href="' || ue_private.escape_html(s->>'url') || '">'
         || ue_private.escape_html(s->>'publisher') || '</a>';
       cited := cited + 1;
     end loop;
     html := html || '</p>';
   end loop;
 end loop;
 if cited = 0 then raise exception 'At least one inline citation required' using errcode = '22023'; end if;
 html := html || '<h2>What you can do</h2><ul>';
 perform ue_private.require_array(p->'actions', 1, 20);
 for action in select value from jsonb_array_elements(p->'actions') loop
   html := html || '<li>' || ue_private.escape_html(ue_private.required_text(action, 2000)) || '</li>';
 end loop;
 return html || '</ul>';
end $$;

create function public.ue_stage_revision(p_external_id text, p_slug text, p_base_hash text, p_article jsonb)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare actor uuid; d ue_private.destinations%rowtype; r ue_private.revisions%rowtype; envelope jsonb; hash text; body text;
begin
 actor := ue_private.require_role(array['producer','editor']);
 if p_external_id is null or p_external_id !~ '^[a-zA-Z0-9][a-zA-Z0-9:_-]{0,127}$'
   or p_slug is null or length(p_slug) > 180 or p_slug !~ '^[a-z0-9]+(-[a-z0-9]+)*$' then
   raise exception 'Invalid article identity or slug' using errcode = '22023';
 end if;
 if p_base_hash is not null and p_base_hash !~ '^[a-f0-9]{64}$' then
   raise exception 'Invalid base revision hash' using errcode = '22023';
 end if;
 body := ue_private.render_article(p_article);
 insert into ue_private.destinations(external_id, slug) values(p_external_id, p_slug) on conflict (external_id) do nothing;
 select * into strict d from ue_private.destinations where external_id = p_external_id for update;
 if d.slug <> p_slug then raise exception 'Article slug is immutable' using errcode = '22023'; end if;
 if d.current_hash is distinct from p_base_hash then raise exception 'Stale base revision' using errcode = '40001'; end if;
 if exists(select 1 from public.articles where slug = p_slug and id is distinct from d.article_id) then
   raise exception 'Slug belongs to an existing article' using errcode = '23505';
 end if;
 envelope := jsonb_build_object('schema_version', 'ue/1', 'renderer_version', 1, 'external_id', p_external_id,
   'slug', p_slug, 'base_hash', p_base_hash, 'review_epoch', d.review_epoch, 'article', p_article, 'body_html', body);
 hash := encode(sha256(convert_to(envelope::text, 'UTF8')), 'hex');
 insert into ue_private.revisions(external_id, revision_hash, envelope, created_by)
   values(p_external_id, hash, envelope, actor) on conflict (revision_hash) do nothing;
 select * into strict r from ue_private.revisions where revision_hash = hash;
 return jsonb_build_object('revision_id', r.id, 'revision_hash', hash, 'envelope', r.envelope);
end $$;

create function public.ue_review_revision(p_revision_id uuid) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare r ue_private.revisions%rowtype;
begin
 perform ue_private.require_role(array['producer','editor','publisher']);
 select * into strict r from ue_private.revisions where id = p_revision_id;
 return jsonb_build_object('revision_id', r.id, 'revision_hash', r.revision_hash, 'envelope', r.envelope,
   'approved', exists(select 1 from ue_private.approvals a join ue_private.members m on m.user_id = a.approved_by
       and m.role = 'editor' where a.revision_id = r.id and a.revoked_at is null),
   'receipt', (select receipt from ue_private.receipts where revision_id = r.id),
   'withdrawal', (select receipt from ue_private.withdrawals where revision_id = r.id),
   'is_current', exists(select 1 from ue_private.destinations where external_id = r.external_id
       and current_hash = r.revision_hash and withdrawn_at is null));
end $$;

create function public.ue_set_approval(p_revision_id uuid, p_revision_hash text, p_approved boolean) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare actor uuid; r ue_private.revisions%rowtype; d ue_private.destinations%rowtype;
begin
 actor := ue_private.require_role(array['editor']);
 select * into strict r from ue_private.revisions where id = p_revision_id for update;
 if p_revision_hash is distinct from r.revision_hash or p_approved is null then
   raise exception 'Exact revision hash and approval decision required' using errcode = '22023';
 end if;
 select * into strict d from ue_private.destinations where external_id = r.external_id for update;
 if (r.envelope->>'review_epoch')::integer is distinct from d.review_epoch then
   raise exception 'Revision predates withdrawal; stage it again for review' using errcode = '40001';
 end if;
 if exists(select 1 from ue_private.receipts where revision_id = r.id) then
   raise exception 'Already published; use a reviewed correction or separate takedown procedure' using errcode = '22023';
 end if;
 insert into ue_private.approvals(revision_id, approved_by, revoked_at)
 values(r.id, actor, case when p_approved then null else now() end)
 on conflict (revision_id) do update set approved_by = actor, approved_at = now(), revoked_at = excluded.revoked_at;
 insert into ue_private.events(revision_id, action, actor) values(r.id, case when p_approved then 'approved' else 'revoked' end, actor);
 return jsonb_build_object('revision_id', r.id, 'revision_hash', r.revision_hash, 'approved', p_approved);
end $$;

create function public.ue_publish_revision(p_revision_id uuid, p_revision_hash text) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare actor uuid; r ue_private.revisions%rowtype; d ue_private.destinations%rowtype;
  approval ue_private.approvals%rowtype; p jsonb; article_uuid uuid; category_uuid uuid; result jsonb;
begin
 actor := ue_private.require_role(array['publisher']);
 select * into strict r from ue_private.revisions where id = p_revision_id for update;
 if p_revision_hash is distinct from r.revision_hash then raise exception 'Exact revision hash required' using errcode = '22023'; end if;
 select * into strict d from ue_private.destinations where external_id = r.external_id for update;
 select receipt into result from ue_private.receipts where revision_id = r.id;
 if found then return result || jsonb_build_object('replayed', true,
   'is_current', d.current_hash = r.revision_hash and d.withdrawn_at is null,
   'withdrawn', d.current_hash = r.revision_hash and d.withdrawn_at is not null); end if;
 if (r.envelope->>'review_epoch')::integer is distinct from d.review_epoch then
   raise exception 'Revision predates withdrawal; stage it again for review' using errcode = '40001';
 end if;
 select * into approval from ue_private.approvals where revision_id = r.id and revoked_at is null for share;
 if not found then raise exception 'Revision has no active approval' using errcode = '42501'; end if;
 perform 1 from ue_private.members where user_id = approval.approved_by and role = 'editor' for share;
 if not found then raise exception 'Approver no longer has editorial access' using errcode = '42501'; end if;
 if d.current_hash is distinct from r.envelope->>'base_hash' then raise exception 'Stale base revision' using errcode = '40001'; end if;
 p := r.envelope->'article';
 select id into strict category_uuid from public.categories where slug = p->>'category_slug';
 if d.article_id is null then
   insert into public.articles(title, slug, summary, body_html, category_id, source_urls, status, published_at)
   values(p->>'title', d.slug, p->>'summary', r.envelope->>'body_html', category_uuid,
     array(select value->>'url' from jsonb_array_elements(p->'sources')), 'published', now()) returning id into article_uuid;
 else
   article_uuid := d.article_id;
   update public.articles set title = p->>'title', summary = p->>'summary', body_html = r.envelope->>'body_html',
     category_id = category_uuid, source_urls = array(select value->>'url' from jsonb_array_elements(p->'sources')),
     ai_confidence = null, status = 'published', revised_at = now() where id = article_uuid;
 end if;
 update public.articles set evidence_label = p->>'evidence_label', editorial_stream = p->>'stream',
   region = p->>'region', research_as_of = (p->>'research_as_of')::timestamptz,
   author_credit = p->>'author_credit' where id = article_uuid;
 update ue_private.destinations set article_id = article_uuid, current_hash = r.revision_hash,
   withdrawn_at = null where external_id = r.external_id;
 update ue_private.social_drafts set status = 'superseded' where revision_id in
   (select id from ue_private.revisions where external_id = r.external_id);
 insert into ue_private.social_drafts(revision_id, content)
 values(r.id, p->>'social_copy' || E'\n\nhttps://www.unsocialengineering.com/scams/' || d.slug);
 result := jsonb_build_object('revision_id', r.id, 'revision_hash', r.revision_hash, 'article_id', article_uuid,
   'path', '/scams/' || d.slug, 'published_at', now(), 'social_status', 'review_draft');
 insert into ue_private.receipts(revision_id, article_id, published_by, receipt) values(r.id, article_uuid, actor, result);
 insert into ue_private.events(revision_id, action, actor) values(r.id, 'published', actor);
 return result || jsonb_build_object('replayed', false, 'is_current', true);
end $$;

-- An editor explicitly withdraws the exact live revision. Never a worker action.
-- Retain the article/audit; public RLS hides its flagged row. Re-delivery cannot
-- restore it. Any replacement needs a fresh, unrevoked revision approval.
create function public.ue_withdraw_revision(p_revision_id uuid, p_revision_hash text, p_reason text)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare actor uuid; r ue_private.revisions%rowtype; d ue_private.destinations%rowtype; result jsonb;
begin
 actor := ue_private.require_role(array['editor']);
 perform ue_private.required_text(to_jsonb(p_reason), 2000);
 select * into strict r from ue_private.revisions where id = p_revision_id for update;
 if p_revision_hash is distinct from r.revision_hash then raise exception 'Exact revision hash required' using errcode = '22023'; end if;
 select * into strict d from ue_private.destinations where external_id = r.external_id for update;
 if d.current_hash is distinct from r.revision_hash or d.article_id is null then
   raise exception 'Only the current published revision can be withdrawn' using errcode = '40001';
 end if;
 select receipt into result from ue_private.withdrawals where revision_id = r.id;
 if found then return result || jsonb_build_object('replayed', true); end if;
 update public.articles set status = 'flagged' where id = d.article_id;
 update ue_private.destinations set withdrawn_at = now(), review_epoch = review_epoch + 1 where external_id = r.external_id;
 update ue_private.social_drafts set status = 'withdrawn' where revision_id in
   (select id from ue_private.revisions where external_id = r.external_id);
 -- A queued correction approved before withdrawal must not silently restore it.
 update ue_private.approvals set revoked_at = now() where revision_id in
   (select id from ue_private.revisions where external_id = r.external_id)
   and not exists(select 1 from ue_private.receipts rc where rc.revision_id = approvals.revision_id);
 result := jsonb_build_object('revision_id', r.id, 'revision_hash', r.revision_hash,
   'article_id', d.article_id, 'path', '/scams/' || d.slug, 'withdrawn_at', now(), 'status', 'withdrawn');
 insert into ue_private.withdrawals(revision_id, withdrawn_by, reason, receipt) values(r.id, actor, p_reason, result);
 insert into ue_private.events(revision_id, action, actor) values(r.id, 'withdrawn', actor);
 return result || jsonb_build_object('replayed', false);
end $$;

create function public.ue_social_draft(p_revision_id uuid) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare result jsonb;
begin
 perform ue_private.require_role(array['editor','publisher']);
 select jsonb_build_object('revision_id', revision_id, 'content', content, 'status', status)
   into strict result from ue_private.social_drafts where revision_id = p_revision_id;
 return result;
end $$;

-- Supabase default privileges may grant service_role/authenticated directly.
-- Revoke every new function explicitly before exposing only the narrow RPCs.
revoke all on all functions in schema ue_private from public, anon, authenticated, service_role;
revoke all on function public.ue_stage_revision(text,text,text,jsonb), public.ue_review_revision(uuid),
 public.ue_set_approval(uuid,text,boolean), public.ue_publish_revision(uuid,text), public.ue_social_draft(uuid),
 public.ue_withdraw_revision(uuid,text,text)
 from public, anon, authenticated, service_role;
grant execute on function public.ue_stage_revision(text,text,text,jsonb), public.ue_review_revision(uuid),
 public.ue_set_approval(uuid,text,boolean), public.ue_publish_revision(uuid,text), public.ue_social_draft(uuid),
 public.ue_withdraw_revision(uuid,text,text)
 to authenticated;
commit;
