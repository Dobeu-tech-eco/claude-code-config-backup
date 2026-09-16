---
name: baldor-ppt
description: "Transform any PowerPoint presentation into a Baldor Specialty Foods branded deck. Use this skill whenever the user asks to rebrand, restyle, or convert a PowerPoint (.pptx) to Baldor branding — including applying Baldor colors, fonts, layouts, and corporate identity. Also trigger when the user mentions 'Baldor presentation', 'Baldor deck', 'Baldor slides', 'brand a deck for Baldor', 'Baldor PowerPoint', or wants to create a new presentation that follows Baldor brand guidelines. This skill applies to ALL PowerPoint work involving the Baldor Specialty Foods brand."
---

# Baldor Specialty Foods — PowerPoint Branding Skill

Transform any presentation into a Baldor-branded deck that follows the official brand guidelines extracted from the Baldor Introduction General template (April 2026).

## When to Use

- User uploads a `.pptx` and wants it rebranded to Baldor style
- User asks to create a new Baldor-branded presentation
- User wants to apply Baldor brand guidelines to slides
- User mentions "Baldor deck", "Baldor presentation", or "Baldor slides"

## Prerequisites

Before doing anything, read:
1. This SKILL.md (you're here)
2. `references/brand-guide.md` — the full color palette, font rules, layout patterns, and do/don't rules

Also read the pptx skill at `/mnt/skills/public/pptx/SKILL.md` for PowerPoint creation/editing mechanics.

## Workflow: Rebrand an Existing Deck

### Step 1: Extract Content from Source

```bash
extract-text input.pptx
```

Parse all slide text, speaker notes, and structure. Identify:
- Title slides vs content slides vs section dividers vs closing slides
- Key headings, body text, bullet points, image placeholders
- Any charts, tables, or data that must be preserved

### Step 2: Read the Brand Guide

```bash
cat /path/to/baldor-ppt/references/brand-guide.md
```

Load the full Baldor brand specifications into context.

### Step 3: Build the Branded Deck

Read `/mnt/skills/public/pptx/pptxgenjs.md` and create the deck from scratch using PptxGenJS. Follow these rules precisely:

#### Slide Dimensions
- **Widescreen 16:9** (the standard — `13.333 x 7.5 inches`)
- The template uses an oversized 26.67 x 15.00 canvas; for generated decks use standard 16:9

#### Font Assignments (with fallbacks)

Baldor uses proprietary fonts. Since they may not be installed on the rendering system, always use this fallback chain:

| Role | Primary (Baldor) | Fallback 1 | Fallback 2 |
|------|-----------------|------------|------------|
| **Headers/Titles** | Ruder Plakat LL VIP High 900 | Impact | Arial Black |
| **Subheads/Body** | Herbik | Georgia | Cambria |
| **Captions/Bullets** | FT Polar Semibold | Trebuchet MS | Calibri |

**Font rules:**
- Headers: sentence case OR ALL CAPS — both are valid
- Body text (Herbik/Georgia): Regular and Italic versions OK
- Captions/bullets (FT Polar/Trebuchet): ALWAYS ALL CAPS in PowerPoint
- Wordmark footer text: always FT Polar / Trebuchet, ALL CAPS

#### Color Palette

Use ONLY Baldor theme colors. Never introduce off-palette colors.

**Base Tones (use the most — backgrounds, large areas):**

| Name | Hex | Usage |
|------|-----|-------|
| Cream | `FAF8F3` | Default slide background, light surfaces |
| Wheat | `D4D0C5` | Alternate neutral background |
| Shale | `9A9D9E` | Secondary neutral, muted text |
| Charcoal | `2C3133` | Dark backgrounds, dark text |

**Primary & Secondary Greens (bold backgrounds, text on base tones):**

| Name | Hex | Usage |
|------|-----|-------|
| Evergreen | `20491D` | Primary brand green — bold backgrounds, section headers |
| Olive | `20280B` | Darker green — title slides, dark sections |
| Lime | `B3CF44` | Secondary green — accents, highlights, subheads |

**Tertiary (use sparingly — pops of color, small accents only, NEVER solid backgrounds):**

| Name | Hex | Usage |
|------|-----|-------|
| Cranberry | `8D4223` | Small accent |
| Caramel | `F2A813` | Small accent |
| Orange | `E34430` | Small accent, links |
| Yolk | `FFC000` | Small accent |
| Salmon | `EE8B84` | Small accent |
| Cabbage | `B3CC45` | Small accent (close to Lime) |
| Eggplant | `5C4E72` | Small accent |
| Spirulina | `79B0C8` | Small accent |

#### Slide Structure

Every Baldor deck should follow this general structure:

1. **Cover Slide** — Evergreen or Olive background, left half has title text (Cream/Lime colored), right half has full-bleed food photography placeholder. Baldor logo positioned on the image.

2. **Section Divider** — Evergreen background with large centered heading in Cream. Optional subtitle in Lime.

3. **Content Slides** — Cream (`FAF8F3`) background. Title in Evergreen. Body in Charcoal. Accent elements in Lime. Footer with page number and `CONFIDENTIAL & PROPRIETARY` in small caps.

4. **Quote/Testimonial Slides** — Wheat background. Large italic quote in Charcoal or Evergreen. Attribution in Lime or Shale.

5. **Data/Stats Slides** — Cream background. Large stat numbers in Evergreen or Lime. Supporting text in Charcoal.

6. **Closing Slide** — Evergreen or Olive background. "Thank You." in large Cream text. Copyright line: `(C) 2024 BALDOR SPECIALTY FOODS` in small Cream text.

#### Footer Pattern

Every content slide includes:
- Bottom-center: `CONFIDENTIAL & PROPRIETARY` in FT Polar/Trebuchet, ALL CAPS, 8pt, Shale color
- Bottom-right: slide number in matching style

#### Image Placeholders

When the source deck has images, add a placeholder rectangle with:
- Wheat (`D4D0C5`) fill
- Centered text: `PLACE IMAGE HERE` in FT Polar/Trebuchet, ALL CAPS, Shale color
- The user replaces these after generation

### Step 4: QA

Follow the standard pptx skill QA process:
1. `extract-text output.pptx` — verify content integrity
2. Convert to images and visually inspect
3. Check for: color compliance, font consistency, layout alignment, text overflow
4. Fix issues and re-verify

### Step 5: Deliver

Present the file to the user with:
- The branded `.pptx` file
- A summary of what was changed
- Notes about any content that needs manual attention (image replacements, data updates)

## Workflow: Create a New Baldor Deck

Same as above, but skip Step 1. Instead, work with the user to outline the content, then build directly following the brand guide.

## Critical Rules

1. **ONLY use Baldor theme colors.** Never use Standard Colors, Recent Colors, or any off-palette hex values.
2. **Font hierarchy is strict.** Headers → Ruder/Impact. Body → Herbik/Georgia. Captions → FT Polar/Trebuchet ALL CAPS.
3. **Cream (`FAF8F3`) is the default background** for content slides, not white.
4. **Tertiary colors are for small accents only** — never use them as full slide backgrounds.
5. **"CONFIDENTIAL & PROPRIETARY" footer** appears on every slide except cover and closing.
6. **Food-forward aesthetic** — the brand is warm, premium, and food-centric. Avoid generic corporate clip art. Prefer photographic placeholders over icons.
7. **Respect the Baldor logo** — the oval Baldor wordmark should appear on cover slides. Do not distort, recolor, or place on busy backgrounds without a solid backing panel.
