---
name: backend-is-lovable-cloud
description: The backend is the Lovable Cloud database, not a Supabase project; never give Supabase dashboard/CLI instructions
metadata:
  type: feedback
---

The owner manages the backend through Lovable Cloud (Lovable MCP is connected: workspace "Dobeu Tech Solutions LLC", project "Chima"). Repo paths and packages named `supabase` (`supabase/migrations`, `src/integrations/supabase/*`, `@supabase/supabase-js`) are Lovable-generated/required, not a Supabase project.

**Why:** the owner corrected this twice ("this is a lovable backend not supabase", "its lovable cloud database") and asked to update all notes so no agent assumes a Supabase backend.

**How to apply:** say "Lovable Cloud database/auth/secrets" in prose; never tell the owner to use a Supabase dashboard or CLI; don't rename supabase-named paths without asking (Lovable sync). Unverified: whether Lovable applies hand-written migrations on GitHub sync and in what order vs code deploy; where secrets like GAME_SCORE_SALT are set; the auth redirect allow-list. Email confirmation is ON (owner confirmed 2026-10-06). See [[bun-not-on-windows-use-npx]] for other env notes.
