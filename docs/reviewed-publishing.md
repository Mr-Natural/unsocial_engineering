# Reviewed publishing pilot

This is a locally tested destination adapter for SavvyHub. It has not been connected
to the central worker, applied to hosted Supabase, or deployed. No article is approved
by this implementation, and no social account is connected.

## Contract and lifecycle

`pipeline.publisher.Publisher` exposes `stage`, `review`, `approve`, `publish` and
`social_draft`. The CLI exposes those actions separately, plus `revoke`. It has no
default action and never imports the legacy service-role configuration.

1. SavvyHub supplies a stable external ID, immutable slug, structured article and
   current base hash (null for a new article). Stage validates and safely renders it.
2. The destination hashes the complete JSONB envelope, including external ID, slug,
   base revision, article, sources, social copy, renderer version and final HTML.
   Use this returned hash, not a client-side JSON hash or the old preview manifest hash.
3. Shaun reviews the returned envelope and explicitly approves its ID and hash using
   an authenticated identity assigned `editor`. Writers must never call approval.
4. A separately restricted identity assigned `publisher` delivers that same ID/hash.
   Publication, receipt and held social draft commit in one database transaction.
5. Public readers see the resulting row through the existing published-only RLS
   policy and `/scams/{slug}` route. The site's existing ISR interval is 300 seconds;
   a database receipt is not proof of successful public website delivery.
6. A correction stages from the current published hash and needs new approval. The
   original publication date remains; revised_at records the correction. Older social
   drafts become superseded. Retries return a receipt without rolling back content.

Evidence classification is an editorial assertion, separate from publication
approval. The schema requires an explicit region, UTC research cutoff, source trail,
inline references and practical actions. It cannot verify that a source supports a
claim; the reviewer must do that. International advice and country-specific recovery
steps must remain clearly distinguished.

The article object has exactly these keys:

```
title, summary, author_credit, category_slug, stream, region,
evidence_label, evidence_note, research_as_of, sections, sources, actions, social_copy
```

`sections`: heading and paragraphs; each paragraph has text and source_ids.
`sources`: id, title, publisher and plain HTTPS url. `actions`: strings.
`research_as_of`: YYYY-MM-DDTHH:MM:SSZ. See `tests/publishing/test_database.py` for
synthetic examples. No unapproved real content belongs in this public repository.

CLI commands, to use only after the target and identity have been configured:

```text
python -m pipeline.publisher stage private-article.json --external-id ue:01 --slug why-smart-people-fall-for-scams
python -m pipeline.publisher review REVISION_UUID
python -m pipeline.publisher approve REVISION_UUID --hash DATABASE_HASH
python -m pipeline.publisher publish REVISION_UUID --hash DATABASE_HASH
python -m pipeline.publisher social-draft REVISION_UUID
```

Set UE_SUPABASE_URL, UE_SUPABASE_PUBLIC_KEY and UE_EDITORIAL_ACCESS_TOKEN in the
calling process using the relevant identity's authenticated session. Never put the
token in CLI arguments, public bundles, committed files or shared logs. The adapter
does not obtain/refresh tokens; the hosting integration must implement that lifecycle.
It refuses redirects and redacts remote error bodies. Review output contains drafts.

## Access and limitations

The new private schema has no client table access. Security-definer RPCs have an
empty search_path, explicit grants and role checks based on auth.uid()/auth.role().
Membership records are provisioned only by the database administrator; migration
creates no users or memberships. An identity may have only the role it needs. A
publisher can stage and deliver but cannot approve. The owner can review without
requiring a second human. See [Supabase function security guidance](https://supabase.com/docs/guides/database/functions).

The migration does **not** remove existing service-role credentials or privileged
database owners. Those can still write to legacy public tables. This is a known
release blocker for claiming an exclusive publishing boundary: inventory consumers,
migrate writes, test replacement identities, then restrict/revoke old access within
approved scope. Do not revoke working credentials blindly. Removing a reviewer
membership prevents their unconsumed approvals being used; it does not unpublish
already released content. Emergency takedowns need a separate reviewed procedure.

Source links are rendered, not fetched, by the publishing RPC. The existing legacy
source fetcher, writer, orchestrator and model-generated HTML are outside this
adapter's trust boundary and are not approved for unattended production use. The
legacy editor has been changed to hold high-score results for review.

No workflow or account policy is added in this change. Existing package locks are
preserved; older Python requirements remain loosely bounded. New adapter/tests use
the standard library. Native GitHub and Vercel gates, secret scopes, dependency
review, actionlint/zizmor CI and hosted acceptance remain release-readiness work.

## Local verification

Run `python -m unittest discover -s tests/publishing -v` with UE_TEST_PG_BIN pointing
to an already trusted PostgreSQL bin folder and UE_TEST_WORKDIR to scratch space.
Without both, database tests are explicitly skipped, which is **not** a full pass.
Tests create a fresh loopback-only password-protected database, apply migrations to
synthetic data, and stop it. No hosted database, production credentials or .env is read.

Coverage includes unauthorised access, private drafts, forged hashes, revoked
approvals, removed reviewer access, safe HTML rendering, legacy slug conflicts,
corrections, stale writes, repeat/concurrent delivery and held social drafts.
Auth claims are simulated: these tests do not verify real JWT issuance, PostgREST
exposure, deployed page rendering, provider release controls or identity separation.

## Next release steps (pending)

1. Verify the chosen Vercel project's actual team/project ID, repo/ref/root, domain,
   protection, plan support and environment names. qvkt is a provisional recommendation.
2. Verify the linked Supabase project, actual schema/roles and credential consumers;
   rehearse migration and identity provisioning in a separate non-production project.
3. Wire SavvyHub's reviewed editorial queue to this adapter with separate editor and
   publisher sessions, preserved external IDs, receipts and error handling. Keep
   private review records out of public previews and CI logs.
4. Integrate the accepted visual pilot with live published-only data; verify browser
   → public page → data plus unpublished-content isolation. The static preview is
   still a separate artifact and its six drafts are not imported by this migration.
5. Establish supported owner-controlled source release gates, CI and dependency
   checks before pushing/deploying. Refresh the first article's evidence and present
   its exact revision for review. Then run one preview publishing cycle and verify
   website delivery before requesting a specific production release decision.
6. Keep social account setup and any recurring source mining as separate decisions.

Owner of pending implementation checks: Codex. Owner of account access, project
choice, editorial decisions and production release: Shaun. No exception is accepted.
