---
name: baldor-weekly-safety-update
description: "Build the BNY Weekly Safety Performance Update sent Monday 11am — incident dashboard, true-up, significant events, top-3 observations, owner-and-date action items, safety messages, and recognition."
---

# Weekly Safety Performance Update

The Monday 11am company update covering Warehouse and Transportation.
Deliver **two files**: a `.docx` and a plain-text copy-paste block with identical content.

## Counting rules — these are not negotiable

1. **Accidents: collapse sub-records.** Group by the claim number before the hyphen (`2026001219-2` → `2026001219`). One base number = one accident; preventable if ANY row in the family is coded Yes. Do NOT just drop hyphenated rows — 6 accidents in 2026 exist only as suffixed rows.
2. **Injuries: count every person.** Each `-002`/`-003` is a different injured person. Never collapse.
3. **Transportation injuries: employees only.** Exclude `Injured non-employee`.
4. **Warehouse: exclude ADMIN from both sides** — out of injury counts AND the man-hour denominator. Location codes containing `ADM`.
5. **Rate base is 200,000** (100 employees × 40 hrs × 50 weeks), per OSHA/BLS. Not 250,000. RIR uses OSHA-recordable counts; all-reported-injury rates run ~3× higher and must be labelled.
6. **Weeks are Monday–Sunday.** Week 32 of 2026 = Aug 3–9. `Avg/Week = YTD ÷ week number`.
7. **Undetermined preventability is its own bucket** — blank or Pending is neither preventable nor not. Report the count and export for classification.

## Steps

### 1. Fix the week
State the week number and date range before computing anything.

### 2. Dashboard — five rows in this order

| Metric | Target |
|---|---|
| Injuries - Transportation | ≤ 4 |
| Injuries - Warehouse* | ≤ 5 |
| Near Misses | ≥ 16 |
| Preventable Accidents - Transportation | ≤ 4 |
| DOT Recordable | 0 |

Columns: Metric · Week N · Prev. Week · YTD · Average Per Week · Weekly Target** · Rate per 200,000 hrs · Week Trend.

Near Misses are a **leading** indicator — up is good there, bad everywhere else.

Footnotes verbatim:
- `* All warehouse accidents are deemed preventable through elimination, engineering, administrative, and PPE controls.`
- `** Weekly target rate/manhours will be available with the rollout of the PowerBI dashboard.`

### 3. True up before publishing
Origami keeps coding records after the Monday pull, so every week publishes low. Re-pull, compare the last 3–4 weeks against what was sent, and show Published / Corrected / Change / Why. Never carry forward silently.

### 4. Check the denominator
Sum the man-hours detail and compare to the file's own Total row. Exports have capped at 3,500 rows, hiding a third of company hours. If they disagree, mark the rates provisional and raise a re-export action item.

### 5. Significant events
Two or three, numbered. What happened, why it matters, then `Video and Details: Origami Risk - Name (claim#)` with a highlighted `[LINK - FILL IN]`.

Lead with a cluster, the most severe single injury, or a real directional move. Tie clusters to a YTD denominator so the reader knows pattern from bad week.

### 6. Trends and learnings
Top 3 Warehouse and Top 3 Transportation, each grounded in a count plus YTD context. Add an `Additional note:` with tenure distribution and the spread of injured roles. Leave warehouse leadership commentary as a highlighted placeholder — it is not the sender's to write.

### 7. Leadership focus — four sections, every item owned and dated
`Warehouse Ops` · `Transportation` · `Warehouse Safety` · `Transportation Safety`

Format: `<action>  Owner: <name>   Due: MM/DD/YY`

Pull candidates from the Notion task tracker and unresolved items in last week's update. Highlight any owner you cannot name — never invent one.

### 8. Safety messages
One Warehouse, one Transportation. Written to the crew: short sentences, concrete actions, tied to what happened this week.

### 9. Verify
Re-run every figure programmatically against the raw export and confirm each matches the document. Render to PDF and look at the pages.

## Style

Match the established format exactly — it is a running series and readers scan for position. Highlight every field the sender must supply in yellow.