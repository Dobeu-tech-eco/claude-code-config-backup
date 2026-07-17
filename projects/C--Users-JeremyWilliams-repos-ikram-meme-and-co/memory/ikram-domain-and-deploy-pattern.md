---
name: ikram-domain-and-deploy-pattern
description: Real prod domain is dobeu.store (not dobeu.shop); how deploys actually happen for this Vercel project
metadata: 
  node_type: memory
  type: project
  originSessionId: 138c3f28-3802-42cc-8b62-0ebf00b8b2c8
---

Production domain for the Ikram & Co. store is **www.dobeu.store / dobeu.store** — NOT dobeu.shop
(the user sometimes calls it dobeu.shop, but that host isn't attached to the project and returns 525).

Vercel project: `ikram-meme-and-co` (`prj_HXhMza5hoe0Oj4GHbbNBVN9Akpar`), team `dobeutechnology`
(`team_8K43hpr1Nzs0UsjjUCGh8OBK`).

**Deploy mechanics (non-obvious):** GitHub push-triggered deploys are auto-CANCELED on this project
(they show state CANCELED with 0 build logs). Real production builds are done via the Vercel CLI
(`vercel --prod`) — those carry an `actor` field. So pushing a branch is not enough to update the site.

In auto/permission mode, `vercel --prod` and `vercel env pull --environment=production` are BLOCKED
(production deploy / production-secrets reads) — the user must run those themselves. Preview deploys
(`vercel` with no --prod) ARE allowed and build with working Supabase env. See [[ikram-supabase-vercel-deploy]]
and [[ikram-deferred-prod-secrets]].
