-- The editor agent records its rationale / flagged issues here, especially for
-- articles held at status='flagged' for human review.

alter table public.articles add column if not exists editor_notes text;
