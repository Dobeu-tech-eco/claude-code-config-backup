---
name: ikram-deferred-prod-secrets
description: "ikram-meme-and-co production secrets still missing (Stripe, Resend, admin) as of 2026-07-15"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6d9999a1-5a3a-4426-854e-f5623abab1ec
---

As of 2026-07-15 the ikram-meme-and-co production storefront was intentionally shipped
"Supabase-only" (catalog browsable). These required env vars are **still absent** in Vercel
Production and must be added before checkout / email / admin work:

- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` — checkout + webhook are non-functional without them.
- `RESEND_API_KEY`, `RESEND_FROM_EMAIL` — order-confirmation emails won't send.
- `ADMIN_EMAILS` — admin dashboard login denies everyone until set (magic-link email allowlist).

`NEXT_PUBLIC_SITE_URL` WAS set (to https://www.dobeu.store). When adding the Stripe webhook secret,
also register the Vercel webhook endpoint in Stripe. See [[ikram-supabase-vercel-deploy]].
