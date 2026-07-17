# Project Memory — ikram-meme-and-co (Ikram & Co. — renamed from "Arab Stickers Co." 2026-07-15)

- [Supabase + Vercel deploy](ikram-supabase-vercel-deploy.md) — prod on www.dobeu.store; NEXT_PUBLIC var mapping + build-time inlining gotcha; apply migrations via us-east-1 session pooler
- [Deferred prod secrets](ikram-deferred-prod-secrets.md) — Stripe/Resend/ADMIN_EMAILS still missing in Production
- [Domain & deploy pattern](ikram-domain-and-deploy-pattern.md) — prod is dobeu.store NOT dobeu.shop; git pushes auto-cancel, deploy via `vercel --prod` CLI; prod deploy/secret-pull gated in auto mode
