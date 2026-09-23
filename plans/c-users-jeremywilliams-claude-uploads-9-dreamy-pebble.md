# Plan: 60-second teaser — "THE WIND DOES NOT AIM"

## Context

You attached a VEGA workspace export (`chima_teaser_project.zip`) and a beat-sheet script, asking for a plan to generate a 60-second teaser.

**The archive cannot be rendered as-is.** It contains only project metadata — `brief.xml`, `recipe.yaml`, `draft.json`, `state.json`, `chima_teaser_script.md`. Every media file the timeline references is absent, because those lived in the VEGA sandbox, not the zip:

```
/workspace/user_uploads/{1,2,3,39,41,43,44,47}.mp4   ← 8 video clips, missing
/workspace/user_uploads/25.png                       ← title card, missing
/workspace/user_uploads/5.png                        ← Chima character card, missing
```

`state.json` also shows `"stage": "confirm"`, `"user_confirmed": false` — the project was never approved or rendered. This is a rebuild, not a re-render.

**Intended outcome:** a 60.0s, 1080×1920 (9:16) MP4 with narration, music, foley and a title card — visually consistent with the one piece of canonical Chima art that exists — plus the reusable shot assets behind it.

---

## What art actually exists (I looked at every file — the filenames mislead)

I opened the images rather than trusting the names. The result changes the plan materially.

### The one usable reference

**`C:\Users\JeremyWilliams\repos\chimacomics\public\art\chima.png`** (693 KB) — a **photoreal 3D-rendered** young grey wolf, three-quarter rear view, amber-brown eyes, standing in a **cream fleecy hooded onesie with a small gold bell** at the throat, bushy tail out. Transparent background.

This is the single cinematic-grade character asset in the repo, and it is the style target for the whole teaser: detailed fur, soft key light, believable fabric.

**It also validates `brief.xml`.** The brief describes CHARACTER_01 as wearing "a cream-colored fleecy onesie with a small gold bell" — that is this image, described exactly. The brief was written from this art, which raises my confidence in the rest of the brief.

### What the other 12 PNGs actually are — *not* what the file names imply

The `public\__l5e\assets-v1\` PNGs are **cartoon sticker art** in a completely different style (thick white die-cut outline, flat cel shading, Three Little Pigs comedy register). Critically:

| File | catalog.ts uses it as | What it actually depicts |
|---|---|---|
| `chima-pigs-question.png` | **Ada Okonjo's** character image | Cartoon Chima in a sheep hood holding a red fan, beside **three cartoon pigs**. No Ada. |
| `chima-book.png` | **Isaac "the Bellows"'** image | Cartoon Chima in a sheep hood reading a book titled "BIG BAD IDEAS". No Isaac. |
| `chima-fan.png` | The Industrial Fan | Cartoon Chima blowing a **wooden** house apart with a small **red handheld desk fan**. Not an industrial fan. |
| `chima-brickhouse.png` | Brick house | Cartoon brick cottage with three pigs in the window. |
| `chima-plan.png` | Blueprints | Cartoon Chima in a black bodysuit reading "HOW TO BE HUMAN". No blueprints. |

**Consequence:** there is **no likeness of Ada, no likeness of Isaac, and no industrial fan** anywhere on disk. Those must be designed fresh, anchored to `art\chima.png`'s rendering style. Feeding a sticker of a wolf-with-pigs to an image model as "Ada's face" would produce nonsense — so the plan does not do that.

### Design system — "Cold Press" (`src\styles.css`, ~line 340)

Semantic tokens only; the repo forbids hardcoded colour. Match these in the grade and title card:

- paper ground `oklch(0.973 0.004 250)` · ink `oklch(0.198 0.017 264)`
- **vermilion signal `oklch(0.532 0.192 28)`** ← brand accent, use for the title
- storm-blue night `oklch(0.232 0.028 262)`

**Fonts** (self-hosted woff2, `public\fonts\`): **Bricolage Grotesque** 600/700/800 display, Public Sans, Newsreader.
**Tagline** (`src\content\site.ts`): *"The wind does not aim. Only a creature aims."*
Ready-made copy: `src\content\chapter-seo.ts`, `src\components\interactive\CharacterDossier.tsx`.

### Canon facts worth using

From `src\content\catalog.ts` + `story.test.ts` (test-enforced):

- Chima Greaves, **sixteen**, warehouse cleaner. Great-great-great-**grandson** of Isaac "the Bellows" — a descendant, *never* the original Big Bad Wolf. (The brief agrees; this is a constraint to preserve, not a conflict.)
- **Ada Okonjo** — "the person the wind reached." Has a roof, **a gate**, and a son named **Tom**. Explicitly "not a plot device and not a pig in a rhyme."
- The fan is **"The Bellows II"**, mill salvage rebuilt over months, now under a tarp.

**One genuine open question — Chima's clothing.** `catalog.ts` says "White PPE coverall, **not a costume**." The hero art shows a cream fleecy onesie with a bell. These most likely reconcile (a cream/white fleecy *work* garment, read in-story as PPE rather than a sheep suit) — but the script's Scene 1 "**blue** industrial jumpsuit" matches neither the art nor the catalog. **Default taken: render the cream/white fleecy coverall from `art\chima.png` throughout, no blue.** Override if the blue jumpsuit is intended as a later-story change.

Also note Ada's **gate** makes script.md's Scene 4 (Chima repairing a wooden garden gate) clearly *Ada's* gate — a far stronger ending than brief.xml's "hang up the coverall." **script.md is treated as canon** where the two diverge; it is also newer (19:57 vs 17:52).

---

## Prerequisites — two hard blockers, both need you

1. **`belt` CLI is installed but not logged in** (`belt auth status` → `✗ not logged in`). Nothing downstream works — not generation, not even `belt app estimate`. It's interactive, so run it yourself:
   ```
   ! belt login
   ```
2. **ffmpeg is not installed** — needed for assembly, `drawtext` overlays and `ffprobe` verification:
   ```
   ! winget install Gyan.FFmpeg
   ```
   Fallback: the `remotion-render` skill (Node 24 present, Remotion bundles its own ffmpeg), or cloud `infsh/media-merger` — both make exact 60.0s timing and crisp text harder.

**No dollar figures appear in this plan on purpose** — they aren't knowable until login. Step 2 of execution is a `belt app estimate` pass reported to you for approval before anything is spent.

---

## Pipeline: keyframes first, then motion

Controlling idea: **identity is decided in the stills, not the clips.** Stills are cheap and re-rollable; clips are not. Generate and approve all 12 keyframes before one video call.

```
art\chima.png ──► keyframe still (1080×1920, cinematic) ──► i2v clip (5s) ──┐
                  gpt-image-2-5-sunburst (preserves subject)  seedance-2-0  │
                                                                            ├──► ffmpeg ──► teaser.mp4
narration (ElevenLabs, 2 voices) ───────────────────────────────────────────┤
music (elevenlabs-music) + foley (infsh/mmaudio per clip) ──────────────────┘
```

**Design-first sub-step:** before Scene 3, generate and approve a **character sheet for Ada** and a **hero render of The Bellows II**, both anchored to `art\chima.png`'s style. They have no existing art, so they need their own small approval beat — a drifting Ada is as damaging as a drifting Chima.

**Models** (primary → fallback; confirm 9:16 support via `belt app get <id>` after login):

| Stage | Primary | Fallback | Why |
|---|---|---|---|
| Keyframe stills | `openai/gpt-image-2-5-sunburst` | `bytedance/seedream-4-5` | Precise edits that *preserve subject and composition* — the character-lock requirement |
| New designs (Ada, fan) | `bytedance/seedream-4-5` | `google/gemini-3-pro-image` | Strong cinematic t2i for net-new subjects |
| Image→video | `bytedance/seedance-2-0` | `falai/wan-2-5-i2v` | 1080p, sync audio, 9:16 |
| Chima-heavy shots | `alibaba/happyhorse-1-0-r2v` | — | Reference-to-video, built for character preservation |
| Narration | `elevenlabs-tts` skill | `text-to-speech` skill | Two voices |
| Music | `elevenlabs-music` skill | licensed track | See audio note |
| Foley | `infsh/mmaudio` | — | Per-clip sound design |

---

## Shot list — 12 shots × 5s = 60.0s

Narration verbatim from `chima_teaser_script.md`. Chima: young male, thoughtful, slightly melancholic. Ada: adult female, warm and protective. Every Chima shot is seeded from `art\chima.png`.

### Scene 1 — The Legacy (0–15s)
| # | t | Shot |
|---|---|---|
| 1.1 | 0–5 | Vast shadowy warehouse at night. Chima — small, cream fleecy coverall, gold bell — walks away down a long aisle, floor scrubber beside him. Slow track behind; sodium shafts, deep vertical negative space. |
| 1.2 | 5–10 | Insert: an old children's picture book, page turning to an illustration of Isaac "the Bellows" — *new design*, an older, broader wolf, rendered as a painted storybook plate (deliberately a different medium, so no likeness is invented for live action). Dust in lamp light. |
| 1.3 | 10–15 | Close on Chima's face lit by a single work lamp, amber eyes lifting. Held, quiet. |

> **Chima (0.5–5.5s):** "They said I was too small. That I could never live up to the name."

### Scene 2 — The Build (15–30s)
| # | t | Shot |
|---|---|---|
| 2.1 | 15–20 | ECU: Chima's paws/hands on a fan hub with a wrench. Grease, metal grain, one spark. |
| 2.2 | 20–25 | Grease-stained blueprints pinned to a shed wall, corners lifting in a draft. Rack focus across the schematic — labelled **"THE BELLOWS II"**. |
| 2.3 | 25–30 | Wide, low angle: the completed towering industrial fan, Chima dwarfed at its base, backlit. *(Uses the new fan design, not the cartoon desk fan.)* |

> **Chima (16–22s):** "But I would prove them wrong. I would make the wind bend to my will."

### Scene 3 — The Consequence (30–45s)
| # | t | Shot |
|---|---|---|
| 3.1 | 30–35 | Dawn hilltop. Chima's hand on the switch — throws it. Blades accelerate, air distorts. |
| 3.2 | 35–40 | **Comic-strip stylisation:** the brick house detonates into red dust as a hard graphic panel burst — vermilion `oklch(0.532 0.192 28)` on paper white. The one deliberately non-photoreal beat, and the only place the sticker-art register belongs. |
| 3.3 | 40–45 | Ada — *new design*: a compassionate woman in her thirties, gentle face, pink cardigan — in her roofless kitchen, cradling Tom, cold blue winter sky where the ceiling was. She looks up. |

> **Ada (40.5–45s):** "Sleep my love, the wind will watch over us."

### Scene 4 — Resolution (45–60s)
| # | t | Shot |
|---|---|---|
| 4.1 | 45–50 | Dawn. Chima, somber, planing a board — repairing **Ada's** wooden garden gate. Hands working, no triumph. |
| 4.2 | 50–55 | The shed: the fan under a tarp, shape still menacing. Light clicks off. Slow fade toward black. |
| 4.3 | 55–60 | **Title card**: **THE WIND DOES NOT AIM** (Bricolage Grotesque 800, vermilion) / "A TALE IN EIGHT PARTS" / `chimacomics.shop` |

> **Chima (54–59s):** "The wind does not aim... but we do."

**Two assembly details that bite if ignored:**

- **Hard cuts, not crossfades.** 11 × 0.5s crossfades would eat 5.5s and blow the 60.0s target. Hard cuts also suit the fable register. If dissolves are wanted, generate each clip ~0.5s longer than its slot and overlap into the surplus.
- **Title card is composited in ffmpeg `drawtext`, not generated.** AI text rendering is unreliable and this frame must be pixel-crisp. FFmpeg's freetype often lacks brotli and **cannot read woff2** — convert Bricolage Grotesque to TTF (or pull the TTF from Google Fonts) first.

---

## Audio

Three defects in the existing `draft.json` that this fixes:

1. **Zero narration** — the draft carries only BGM and two text overlays despite four scripted lines. The TTS pass fills a load-bearing gap.
2. **Broken BGM path** — `"source": "/workspace/chima_teaser/https:/assets.mixkit.co/..."` is a URL mangled into a filesystem path. It would not have resolved.
3. **Unverified music licence** — that's a mixkit **preview** URL, not a licensed asset. For a commercial teaser on chimacomics.shop, that's a real risk. Default: generate an original bed via `elevenlabs-music` (epic/dramatic, sparse, industrial). Alternative: supply a licensed track.

Mix: narration −16 LUFS and always intelligible; music ducked to ≈−28 LUFS under speech, up to −20 in gaps; per-clip foley from `infsh/mmaudio` (warehouse hum and scrubber, wrench clank, fan spin-up roar, wind and debris, plane on wood, a switch click).

---

## Output layout

Standalone production workspace — keeps hundreds of MB of intermediates out of the site repo:

```
C:\Users\JeremyWilliams\repos\chima-teaser\
├── refs\          # art\chima.png + approved Ada / Bellows II designs
├── stills\        # 12 approved keyframes, 1080×1920
├── clips\         # 12 × 5s i2v renders
├── audio\         # vo-chima-*.wav, vo-ada-*.wav, music.wav, foley\
├── build\         # shots.json, concat lists, drawtext filters, fonts\*.ttf
└── out\           # teaser-9x16.mp4  ← deliverable
```

Execution runs in a git worktree (background-job rule). **Nothing is written to `repos\chimacomics` as part of this plan.** If the teaser should later live on the site, note two constraints from that repo's `CLAUDE.md`: images are referenced through `src\assets\*.asset.json` pointers, never imported as binaries; and the repo syncs with Lovable, so **published history must never be rewritten** — no force-push, rebase or amend.

---

## Execution order

1. **Prereqs** — you run `belt login` and `winget install Gyan.FFmpeg`.
2. **Estimate** — `belt app estimate` across chosen models; report totals, wait for your go-ahead.
3. **Scaffold** — create `repos\chima-teaser\`, copy `art\chima.png` into `refs\`, convert Bricolage Grotesque woff2 → TTF.
4. **Design gate** — generate Ada's character sheet and the Bellows II hero render. **Your approval before they enter any keyframe.**
5. **Keyframes** — 12 stills at 1080×1920, each seeded from its approved reference.
6. **★ Review gate** — contact sheet of all 12 stills. **No video spend before this passes.** Re-roll rejects; stills are cheap, clips are not.
7. **Motion** — 12 × 5s i2v renders, each spot-checked for character drift before the next.
8. **Audio** — 4 TTS lines (2 voices), music bed, per-clip foley.
9. **Assembly** — ffmpeg concat on exact boundaries, audio mix + ducking, `drawtext` title card.
10. **Verify** — below.

---

## Verification

Against `out\teaser-9x16.mp4`:

- `ffprobe -v error -show_entries format=duration:stream=width,height,codec_type` → **60.0s ±0.1**, **1080×1920**, one video + one audio stream, H.264/AAC.
- `ffmpeg -af ebur128` → integrated ≈ −16 LUFS, true peak < −1 dBTP.
- Frame grabs at **0, 5, 15, 30, 40, 45, 57s** — confirm Chima is the same wolf in every appearance: grey fur, amber eyes, **cream fleecy coverall with gold bell**, no blue jumpsuit, no sticker-style flattening outside shot 3.2.
- Ada at 40–45s matches her approved character sheet; the fan at 25–30s matches the approved Bellows II render and is clearly industrial, not a desk fan.
- Title-card grab at 57s — "THE WIND DOES NOT AIM" and `chimacomics.shop` legible at phone size; colour-sample the title to vermilion `oklch(0.532 0.192 28)`.
- Play with audio: all four narration lines land inside their scene windows and sit above the bed.
- Canon check: Chima reads as Isaac's descendant, not the original.

---

## Open decisions (defaults applied — override any of these)

| # | Decision | Default taken |
|---|---|---|
| 1 | Chima's clothing — art/catalog cream-white coverall vs script's blue jumpsuit | **Cream fleecy coverall + gold bell**, per `art\chima.png` |
| 2 | brief.xml vs script.md on Scenes 3–4 | **script.md wins** (newer; gate ending matches Ada's canon gate) |
| 3 | Ada / Isaac / industrial fan have no art | **Design fresh**, anchored to `art\chima.png` style, behind an approval gate |
| 4 | Spend cap | **Estimate first, you approve** before any generation |
| 5 | Music | **Generate original**; mixkit preview URL is not licence-cleared |
| 6 | Aspect ratio | **9:16 only** per brief (YouTube Shorts). A 16:9 cutdown for the site's `intro.mp4` is a follow-on, out of scope |
| 7 | Original VEGA uploads | Assumed **unavailable**. If you still have Videos 1–3 / Images 4–33, say so — real footage would replace generated shots and cut both cost and drift risk |

*(I raised 1, 2, 4 and the si-commands question as a prompt during planning; it was cancelled, so these are my documented defaults rather than your choices.)*

---

## Not in scope / noted

- The four `uv run si eval|optimize|promote|log repo-readme-author` lines at the end of your message look like a stray paste unrelated to the video — **not included, not run**. (If you do want them: `si promote` always writes state; there is no dry run.)
- `/resume` is a built-in Claude Code CLI command — I can't invoke it mid-turn; type it directly at the prompt.
- `repos\chimacomics` has a dangling og:image: `src\assets\chima-share-card.jpg.asset.json` declares a 1200×630 share card that isn't checked in. Unrelated, but a frame from this teaser would make a good replacement.
- Running `belt` during read-only checks triggered its auto-updater (v1.18.41 → v1.18.55). Harmless, but it was a write I didn't intend in plan mode.
