---
name: ikram-supabase-vercel-deploy
description: "How ikram-meme-and-co is deployed on Vercel + hosted Supabase, and the gotchas that broke it"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6d9999a1-5a3a-4426-854e-f5623abab1ec
---

"Arab Stickers Co." (ikram-meme-and-co) production runs on Vercel team `dobeutechnology`
(project `prj_HXhMza5hoe0Oj4GHbbNBVN9Akpar`), domain **https://www.dobeu.store** (+ the
`ikram-meme-and-co-dobeutechnology.vercel.app` alias). Deploy protection (SSO) was turned OFF
so the storefront is publicly reachable (`vercel project protection disable ikram-meme-and-co --sso`).

Hosted DB is **Supabase via the Vercel Marketplace integration**, project ref
`jgvpornjuogveltufvle`, region **us-east-1**. Gotchas that bit us (2026-07-15):

1. The integration provisions `SUPABASE_URL` / `SUPABASE_ANON_KEY` / `SUPABASE_SECRET_KEY`, but the
   app reads `NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_ANON_KEY` / `SUPABASE_SERVICE_ROLE_KEY`.
   Those NEXT_PUBLIC_* names must be set explicitly. They are **build-time inlined** — after setting
   them you MUST redeploy; the old build had empty strings → `Error: Your project's URL and Key are
   required to create a Supabase client!` on every `[locale]` page.
2. The integration does NOT run repo migrations. The DB was empty (PostgREST `PGRST205 Could not find
   the table 'public.products'`). Apply with:
   `npx supabase db push --db-url "postgresql://postgres.jgvpornjuogveltufvle:<PW>@aws-0-us-east-1.pooler.supabase.com:5432/postgres" --include-seed`
   The direct host `db.<ref>.supabase.co` does NOT resolve — use the **session pooler** (port 5432,
   user `postgres.<ref>`). Local `supabase db push`/`db:types` also need Docker Desktop running, which
   was down on this machine.
3. Diagnose prod errors with the Vercel MCP `get_runtime_errors` / `get_runtime_logs`. `vercel env pull`
   returns EMPTY values for the integration's vars because they are marked **Sensitive** (write-only) —
   don't conclude "empty in prod" from a blank pull; check the live app instead.

See [[ikram-deferred-prod-secrets]].
