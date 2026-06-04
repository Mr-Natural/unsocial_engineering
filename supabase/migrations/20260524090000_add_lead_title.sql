-- Leads need a dedicated title for fuzzy de-duplication (rapidfuzz) and for
-- display in the review queue. The full body stays in raw_text.

alter table public.leads add column if not exists title text;
