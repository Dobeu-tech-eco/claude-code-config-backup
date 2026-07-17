---
name: baldor-create-sop
description: "Create Baldor Specialty Foods SOP documents (.docx) using standardized corporate formatting — Aptos font, CONFIDENTIAL footer, versioned header, and structured sections (Purpose, Scope, Responsibilities, Procedure, Documentation & Records, Governance). Use this skill whenever the user mentions 'Baldor SOP', 'SOP for Baldor', 'standard operating procedure' in a Baldor context, 'Baldor document', 'Baldor policy', 'Baldor procedure', or asks to convert any content into a Baldor-formatted Word document. Also trigger when the user references /Baldor-Create-SOP or asks to create safety, compliance, training, or operational documents for Baldor Specialty Foods. This skill applies to ALL output surfaces — Claude.ai chat, Claude Code, Cowork, Claude for Word, and any environment with file-creation capability."
---

# Baldor SOP Document Creator

## Prerequisites

**Before writing any code, ALWAYS read the docx skill first:**

```
Read /mnt/skills/public/docx/SKILL.md
```

The docx skill defines the toolchain (docx-js via Node.js), validation pipeline, and critical rules that this skill builds on top of. Every Baldor SOP is a .docx file — the docx skill is the foundation, this skill is the template layer.

## When This Skill Triggers

This skill activates when the user wants to create any Baldor Specialty Foods document that follows the corporate SOP format. Common triggers:

- "Create a Baldor SOP for [topic]"
- "Turn this into a Baldor SOP"
- "Make a Baldor procedure document"
- "Format this as a Baldor SOP"
- "/Baldor-Create-SOP"
- Any request for a safety, compliance, training, HR, or operational document at Baldor

## Gathering Inputs

Before generating the document, collect or confirm:

1. **Document title** — the SOP name (e.g., "Driver Pre-Trip Inspection Procedure")
2. **Effective date** — use `"dd/mm/yyyy"` as placeholder if not provided
3. **Version number** — use `"#.##"` as placeholder if not provided
4. **Content** — the user may provide raw content to format, or ask you to draft content from scratch
5. **Language** — English by default; ask if bilingual (English/Spanish) is needed since many Baldor SOPs serve bilingual teams
6. **Additional sections** — beyond the standard six, the user may need appendices, forms, or checklists

## Document Specifications

### Page Layout
- **Paper:** US Letter (12240 x 15840 DXA)
- **Margins:** 1 inch all sides (1440 DXA each)
- **Orientation:** Portrait (default)

### Typography
- **Font:** Aptos for ALL text — no exceptions
- **Color:** Black (#000000) for all text — monochrome palette only
- **Title:** Aptos 12pt, bold, centered
- **Section headings:** Aptos 12pt, bold, left-aligned (no underline)
- **Body text:** Aptos 12pt, regular, left-aligned, spaceAfter 8pt (160 DXA)
- **Lists:** Hanging indent, leftIndent 36pt/72pt/108pt by nesting level (720/1440/2160 DXA)
- **Tables:** Bold centered headers, regular body cells, thin borders

### Header (every page)
Two lines, Aptos 12pt, left-aligned:
```
Effective date: dd/mm/yyyy
Version: #.##
```

### Footer (every page)
Three-part footer, Aptos 10pt:
```
Line 1: CONFIDENTIAL AND PROPRIETARY
        This document is the property of Baldor Specialty Foods and may not be
        reproduced or distributed without written consent.
Line 2: (c) Baldor Specialty Foods
Line 3: Page | [auto page number]
```

All footer text is centered.

### Standard SOP Sections

Every Baldor SOP follows this outline structure unless the user specifies otherwise:

1. **Purpose** — Why the SOP exists; what process or requirement it addresses
2. **Scope** — Who and what the SOP applies to (roles, branches, departments)
3. **Responsibilities** — Who is accountable for each aspect (typically a table)
4. **Procedure** — Step-by-step instructions for carrying out the process
5. **Documentation & Records** — What records must be kept, where, and for how long
6. **Governance** — Review cycle, approval authority, version history table

### Table of Contents

For SOPs longer than 3 pages, include an auto-generated Table of Contents after the title block. Use Heading 1 for main sections, Heading 2 for subsections. The TOC must use HeadingLevel and outlineLevel per the docx skill requirements.

## docx-js Template

Below is the canonical code pattern for generating a Baldor SOP. Adapt content as needed but preserve the formatting structure exactly.

```javascript
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, HeadingLevel,
  BorderStyle, WidthType, ShadingType, TableOfContents,
  PageNumber, PageBreak
} = require("docx");

// -- Configuration -----------------------------------------------------------
const EFFECTIVE_DATE = "dd/mm/yyyy";  // Replace with actual date
const VERSION = "#.##";              // Replace with actual version
const FONT = "Aptos";
const FONT_SIZE_12PT = 24;  // Half-points: 24 = 12pt
const FONT_SIZE_10PT = 20;  // Half-points: 20 = 10pt
const COLOR = "000000";
const MARGIN = 1440;  // 1 inch in DXA

// -- Helpers -----------------------------------------------------------------
const run = (text, opts = {}) =>
  new TextRun({ text, font: FONT, size: opts.size || FONT_SIZE_12PT,
    bold: opts.bold || false, color: COLOR, ...opts });

const bodyParagraph = (text) =>
  new Paragraph({
    spacing: { after: 160 },
    children: [run(text)]
  });

const sectionHeading = (text, level = HeadingLevel.HEADING_1) =>
  new Paragraph({ heading: level, children: [run(text, { bold: true })] });

// -- Header ------------------------------------------------------------------
const docHeader = new Header({
  children: [
    new Paragraph({ children: [run(`Effective date: ${EFFECTIVE_DATE}`)] }),
    new Paragraph({ children: [run(`Version: ${VERSION}`)] }),
  ]
});

// -- Footer ------------------------------------------------------------------
const docFooter = new Footer({
  children: [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 0 },
      children: [
        run("CONFIDENTIAL AND PROPRIETARY", { size: FONT_SIZE_10PT, bold: true }),
      ]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 0 },
      children: [
        run("This document is the property of Baldor Specialty Foods and may not be reproduced or distributed without written consent.", { size: FONT_SIZE_10PT }),
      ]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 0 },
      children: [run("\u00A9 Baldor Specialty Foods", { size: FONT_SIZE_10PT })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [
        run("Page ", { size: FONT_SIZE_10PT }),
        new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: FONT_SIZE_10PT, color: COLOR }),
      ]
    }),
  ]
});

// -- Title -------------------------------------------------------------------
const titleParagraph = new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 320 },
  children: [run("DOCUMENT TITLE HERE", { bold: true })]
});

// -- Document Assembly -------------------------------------------------------
const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: FONT, size: FONT_SIZE_12PT, color: COLOR }
      }
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: FONT_SIZE_12PT, bold: true, font: FONT, color: COLOR },
        paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 }
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: FONT_SIZE_12PT, bold: true, font: FONT, color: COLOR },
        paragraph: { spacing: { before: 180, after: 120 }, outlineLevel: 1 }
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: FONT_SIZE_12PT, bold: true, font: FONT, color: COLOR, italics: true },
        paragraph: { spacing: { before: 120, after: 80 }, outlineLevel: 2 }
      },
    ]
  },
  numbering: {
    config: [
      {
        reference: "sop-bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "\u2022",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }, {
          level: 1, format: LevelFormat.BULLET, text: "\u25E6",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 1440, hanging: 360 } } }
        }, {
          level: 2, format: LevelFormat.BULLET, text: "\u25AA",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 2160, hanging: 360 } } }
        }]
      },
      {
        reference: "sop-numbers",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }, {
          level: 1, format: LevelFormat.LOWER_LETTER, text: "%2.",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 1440, hanging: 360 } } }
        }]
      }
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN }
      }
    },
    headers: { default: docHeader },
    footers: { default: docFooter },
    children: [
      titleParagraph,
      // Uncomment TOC for documents over 3 pages:
      // new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" }),
      // new Paragraph({ children: [new PageBreak()] }),

      sectionHeading("1. Purpose"),
      bodyParagraph("[Describe the purpose of this SOP.]"),

      sectionHeading("2. Scope"),
      bodyParagraph("[Define who and what this SOP applies to.]"),

      sectionHeading("3. Responsibilities"),
      bodyParagraph("[Define roles and accountability. Use a table if multiple roles.]"),

      sectionHeading("4. Procedure"),
      bodyParagraph("[Step-by-step process instructions.]"),

      sectionHeading("5. Documentation & Records"),
      bodyParagraph("[What records are kept, where, and retention period.]"),

      sectionHeading("6. Governance"),
      bodyParagraph("[Review cycle, approval authority, and version history.]"),
    ]
  }]
});

// -- Write and Validate ------------------------------------------------------
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/home/claude/baldor-sop.docx", buffer);
  console.log("SOP generated successfully.");
});
```

After generating, **always validate:**

```bash
python /mnt/skills/public/docx/scripts/office/validate.py /home/claude/baldor-sop.docx
```

Then copy to outputs:

```bash
cp /home/claude/baldor-sop.docx /mnt/user-data/outputs/
```

## Responsibilities Table Pattern

Many Baldor SOPs include a RACI or simple responsibility matrix:

```javascript
const border = { style: BorderStyle.SINGLE, size: 1, color: "000000" };
const borders = { top: border, bottom: border, left: border, right: border };

const headerCell = (text, width) => new TableCell({
  borders, width: { size: width, type: WidthType.DXA },
  shading: { fill: "D9D9D9", type: ShadingType.CLEAR },
  margins: { top: 80, bottom: 80, left: 120, right: 120 },
  children: [new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [run(text, { bold: true })]
  })]
});

const bodyCell = (text, width) => new TableCell({
  borders, width: { size: width, type: WidthType.DXA },
  margins: { top: 80, bottom: 80, left: 120, right: 120 },
  children: [new Paragraph({ children: [run(text)] })]
});

// Example: 3-column responsibilities table (full content width = 9360 DXA)
new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [3120, 3120, 3120],
  rows: [
    new TableRow({ children: [
      headerCell("Role", 3120),
      headerCell("Responsibility", 3120),
      headerCell("Frequency", 3120),
    ]}),
    new TableRow({ children: [
      bodyCell("Transportation Safety Manager", 3120),
      bodyCell("Review and update SOP annually", 3120),
      bodyCell("Annual", 3120),
    ]}),
  ]
})
```

## Adapting Content

When the user provides raw content (notes, bullet points, existing documents):

1. **Map content to standard sections** — place each piece under the appropriate SOP heading
2. **Formalize language** — convert casual notes into directive SOP language ("The driver shall...", "Management must ensure...")
3. **Add structure** — numbered steps for procedures, tables for responsibilities, bullet lists for requirements
4. **Fill gaps** — if a standard section has no content, include a placeholder noting it needs completion
5. **Bilingual handling** — if requested, place English first followed by Spanish translation for each section, clearly separated by a subsection heading (e.g., "4. Procedure" then "4. Procedimiento")

## Cross-Platform Notes

This skill works across all Claude environments:

- **Claude.ai (chat):** Use bash_tool and docx-js to generate the .docx, validate, and present via present_files
- **Claude Code:** Same toolchain; run npm/node directly in the terminal
- **Cowork:** Same toolchain; subagents can handle parallel generation if producing multiple SOPs
- **Claude for Word (add-in):** When operating inside an existing Word environment, apply the formatting specs (font, sizes, margins, header/footer text) directly to the active document using the host application formatting capabilities rather than generating a new .docx from scratch. Match every spec from the Document Specifications section above.

The key principle: the **formatting spec is constant** across all surfaces. Only the mechanism for applying it changes.

## Checklist Before Delivery

- [ ] Aptos font on ALL text (no Arial, no Calibri, no fallbacks)
- [ ] All text black #000000
- [ ] Header shows effective date + version on every page
- [ ] Footer shows CONFIDENTIAL notice + copyright + page number on every page
- [ ] 1-inch margins all sides
- [ ] Title is bold, centered
- [ ] Section headings are bold, left-aligned, no underline
- [ ] Body text has spaceAfter 8pt (160 DXA)
- [ ] Lists use numbering config (never unicode bullet characters directly)
- [ ] Tables use DXA widths with dual width pattern (columnWidths + cell width)
- [ ] Document validated with validate.py
- [ ] File delivered to /mnt/user-data/outputs/
