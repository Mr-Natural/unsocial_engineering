# Setup — Phase 1 foundation

This documents what the scaffold created and the **cloud steps that require your
own login** (they can't be done headlessly).

## What's in place

- **Next.js 15** (App Router, TypeScript, Tailwind v4, pnpm) — pinned to `next@15`.
- **Supabase client wiring** in `src/lib/supabase/` (`client`, `server`, `admin`)
  and types in `src/lib/types.ts`.
- **Database migrations** in `supabase/migrations/` (schema + RLS + category seed).
- **Pipeline skeleton** in `pipeline/` with a working `config.py`; the agent
  modules are phase stubs (see `UNSOCIALENGINEERING_CC_PROMPTS.md`).
- **`.env.example`** listing every required variable.

## Local dev environment notes

- `pnpm` was installed via npm to the user prefix (`%APPDATA%\npm`). pnpm 9.x is
  pinned because pnpm 10+ requires Node 22 and this machine runs Node 20.
- **Norton SSL inspection:** Norton re-signs HTTPS with its own root CA, which
  Node/npm don't trust by default (causes `UNABLE_TO_VERIFY_LEAF_SIGNATURE`).
  Fixed by exporting that root to `C:\Users\shaun\.certs\norton-root.pem` and
  setting the user env var `NODE_EXTRA_CA_CERTS` to it. If npm/pnpm/network
  fetches start failing again, confirm that variable is still set.

## Cloud steps you need to run

These need interactive auth, so they're left for you.

### 1. Supabase project (Sydney region)

1. Create a project at https://supabase.com/dashboard and set the region to
   **Sydney (`ap-southeast-2`)** in the region picker, per project conventions.
2. Apply the schema (see `supabase/README.md`):
   ```bash
   supabase login
   supabase link --project-ref <project-ref>
   supabase db push
   ```
   Or paste the two files in `supabase/migrations/` into the dashboard SQL editor.
3. Copy the URL + anon key + service role key from Project Settings → API into
   `.env.local` (and `.env` for the pipeline). Use `.env.example` as the template.

### 2. Vercel + GitHub

1. `git init` here, commit, and push to a new GitHub repo (`gh repo create` once
   the GitHub CLI is installed and authed, or create it in the web UI).
2. Import the repo at https://vercel.com/new, framework auto-detects Next.js.
3. Add the same env vars in Vercel → Project → Settings → Environment Variables.
4. Deploy. `main` is production per the project conventions.

## Quick checks

```bash
pnpm dev                 # Next.js dev server on http://localhost:3000
python pipeline/config.py  # prints which env vars are set (no secrets shown)
```
