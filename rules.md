# Rules for study notes (Markdown) and code comments

Learning comes first. Save tokens where possible (no repeated content), but never cut needed content.

## Soft caps

- All caps in this file are soft.
- Exceed a cap by a small amount (e.g. 1–2 extra charts) only when it truly aids understanding. Never by default, never "just because".
- If a cap blocks something important: trim prose/repetition first (e.g. 5 small charts needed → shorten text, keep charts).

## Length

- No hard line cap (~700 lines is fine).
- If a topic risks token/context limits → split into several notes (use judgment).

## Language

- Explanations: simple English (B2), keyword style, not full sentences.
- Symbols: ✅ ❌ ⚠️ → (e.g. `WHERE drops NULL rows → LEFT = INNER`).
- Persian: for questions, exercise prompts, and complex points. Headings follow the Headings section (English body + at most one Persian keyword); if Language and Headings conflict, Headings wins. For inline explanations within English text, use the footnote system (see Persian explanations below). Never inside code.
- Persian text: NEVER use ZWNJ (U+200C, half-space). Always a normal space, e.g. میشود, فایل ها. ZWNJ breaks heading anchor links (TOC) and the user dislikes it.
- Code comments: English only (my script does not process code fences, so `^^` and `!!` markers will not render inside code). May use footnote markers (¹) — see Persian explanations.
- Digits: always ASCII `0-9`, never Persian digits (`U+06F0`–`U+06F9`) — they render wrong in some viewers/fonts. ASCII digits inside Persian text are fine, even preferred.
  - Only exception: a fully Persian sentence where the number is read as Persian prose, and there is a real reason. When unsure → ASCII.

## Persian explanations (footnotes)

When an English phrase is hard to parse or needs definition, keep it English and mark it:

- Mark only the hard phrase with a sequential superscript: `¹`, `²`, `³`, `⁴`, `⁵`, `⁶`, `⁷`, `⁸`, `⁹`, `⁰`...
- **Space BEFORE and AFTER the superscript are both mandatory.** The spaces are the token boundaries that the Python processing relies on, and they also keep it distinct from an exponent.
  - ✅ `readers read an old committed copy ¹ , no waiting`
  - ❌ `readers read an old committed copy¹ , no waiting` (no space before = looks like exponent)
  - ❌ `readers read an old committed copy ¹` (end of line without a trailing space)
- The token starts with any superscript digit listed above, followed by any non-space characters — so a two-digit mark (`¹¹`) or a custom mark (`¹*`) is one token. It **ends at the next literal space**. A tab, end of line, or table pipe is not a substitute for that space. Punctuation must follow the separating space, otherwise it becomes part of the token.
- The surrounding spaces stay OUTSIDE the colored span; only the token itself is wrapped.
- Never wrap the token yourself in `^^`/`!!` for emphasis — the processing adds the color span. If `^^¹^^` or `!!¹!!` appears with the required surrounding spaces, it is stripped and treated the same as bare `¹`, so the result must stay identical whether or not the markers were there.
- The Persian explanation line starts with its token (e.g. `¹ ` or `² `) at the very beginning of its own line. No leading space is needed for this definition; **the space after the token is mandatory.**
  - ✅ `¹ خواننده یک نسخه قدیمی commit شده را میخواند`
  - ❌ `¹خواننده یک نسخه قدیمی commit شده را میخواند` (no space after token)
- Inline tokens default to purple (`p`); definition tokens at the start of a line default to green (`g`). Only the token is colored, not the explanation text. Classes are configurable in the Python script; do not add spans manually.
- Persian explanation goes in a separate paragraph immediately after the specific table/paragraph/code block it belongs to — not collected at the end of the section.
- Numbering is per section (every `##` section starts again from `¹`), but each table/paragraph/code block's footnotes stay directly below it. If one section has several footnoted tables/blocks, the numbers keep increasing inside that section, and each block's explanations go right after that block.
- Explanation can be short: one or two key words, or a clarifying phrase. Goal: aid understanding of the English text, not replace it.

Example:

```text
- Row versioning (MVCC) → readers read an old committed copy ¹ , no waiting

¹ خواننده یک نسخه قدیمی commit شده را میخواند، بدون انتظار
```

### Tables

- Most columns English → entire table stays English; mark hard cells with `¹`, explain below.
- Only 1–2 English columns (terms), rest Persian → "Persian table", no footnotes needed.
- **RTL lock**: any cell with code that breaks when right-aligned → entire table MUST be English, even if other columns would be Persian. Explanations go below as footnotes.

### Code blocks

- Comments stay English (hard rule) but may use `¹` markers. Same spacing rule as everywhere (space before and after the token).
- Persian explanation goes below the code block, never inside.

## Bidi (mixed Persian, English) — preference, not a hard rule

Notes render RTL (my script wraps everything in `<div dir="rtl">` and already handles mixed text). Still, in an RTL run a Persian word sitting BETWEEN two Latin tokens can reverse their visual order.

- Worst case: `ROLLUP و CUBE` → may show as `CUBE و ROLLUP`. There `,` / `VS` / `and` is simply better → `ROLLUP, CUBE`.
- Preferred shape: each language in ONE contiguous run, Persian at the EDGE of the Latin phrase.
- ✅ Latin inside Persian prose is fine → `از GROUP BY استفاده کن`
- **Never translate a technical term to satisfy this rule.** `add`, `commit`, `merge`, `stage` stay English even mid-sentence → `دکمه add را بزن`. Meaning and searchability beat a pure run.
- Matters most in: headings, TOC links, table cells, list items — short lines with no surrounding context to fix the direction.
- Matters least in: prose paragraphs. Do not restructure a good sentence for this.
- Code comments: English only (see Language) — this one is hard, not a preference.

## Headings

When a section's purpose matches one of the canonical names below, you **MUST** use that exact canonical name. If no canonical name fits, create a new heading using the same formula. A note does not need all canonical sections — include only what the note needs. Never rename a canonical section, and never invent a 4th synonym for something already listed.

- Formula: `## N. EnglishTerm[, EnglishTerm] (واژه فارسی)`
- `N` = ASCII digits + `.` + one space → `## 7.`, never `## ۷.`. Number from `1.`; `## 1.` is Setup only when the note has a Setup section.
- Heading body in English. At most ONE Persian keyword, in parentheses, at the end — only when the English term alone is unclear.
  - ✅ `## 3. PIVOT Dynamic (پویا)` ❌ `## ۳. PIVOT پویا (Dynamic)`
- No ZWNJ in headings (see Language) — it breaks anchors.

Separators between parallel English terms:

- ✅ `,` — glued to the previous word, one space after: `## 6. GROUPING SETS, ROLLUP, CUBE` → `#6-grouping-sets-rollup-cube`
- ✅ `VS` — uppercase, space both sides, only for a real comparison: `## 5. Git Rebase VS Reset`
- ❌ `و` / `،` — a Persian conjunction inside an English heading flips word order in RTL
- ❌ `&` / `/` — the slugger deletes them → double hyphen (`#rollup--cube`); `/` also reads as "or"
- ❌ space before the comma (`ROLLUP , CUBE`) — breaks the anchor

Canonical section names:

| Purpose | Heading | Notes |
|---|---|---|
| Table of contents | `## TOC (فهرست)` | unnumbered, top of note |
| Practice dataset | `## 1. Setup (Table 1)` | rename the paren if there is no table |
| Intro | `## N. Intro (مقدمه)` | |
| Grammar, clause order | `## N. Syntax` | |
| Worked examples | `## N. Examples` | |
| Comparison of two things | `## N. X VS Y` | always literal uppercase `VS` so it stays searchable; never `و` / `در برابر` / `یا` |
| Recommended way | `## N. Best Practices` | |
| Traps + common mistakes | `## N. Pitfalls (تله ها)` | covers تله / دام / اشتباه رایج → one section, not three |
| Error, then fix | `## N. Troubleshooting` | different from Pitfalls: Pitfalls = "do not do this", Troubleshooting = "you hit error X, do Y" |
| Speed, plans, indexes | `## N. Performance (کارایی)` | |
| Questions + folded answers | `## N. Exercises (تمرین ها)` | |
| Drop practice objects | `## N. Cleanup (پاک سازی)` | |
| Table of commands, snippets | `## N. Cheat Sheet` | no gloss — a code/command table to copy |
| Wrap-up, conclusions | `## N. Summary (خلاصه)` | prose wrap-up (جمع بندی), gloss only when needed. Cheat Sheet is not a Summary |
| Same thing in another tool | `## N. Equivalents (معادل ها)` | qualify only when it helps: `## N. PostgreSQL, Django Equivalents (معادل ها)` |
| References | `## N. Sources (منابع)` | |

- The leading English keyword is the searchable token → `grep Pitfalls` or `grep Equivalents` must find that section in every note, whatever the subject (SQL, Git, Python...).
- Subject-specific headings are free-form, but keep the same formula and separators.
- Order (soft): `TOC` → `Setup` → `Intro` → `Syntax` → concepts, `Examples` → `Best Practices` → `Pitfalls` → `Troubleshooting` → `Performance` → `Exercises` → `Cleanup` → `Cheat Sheet` → `Summary` → `Equivalents` → `Sources`.
- Every section is optional. Include only what the note needs (e.g. an exercises-only note has just `## 1. Exercises (تمرین ها)`, no empty Setup, Intro, TOC or Summary). Numbers stay consecutive from `1.` over the sections that exist.
- Renaming a heading → update every `](#...)` TOC link in the same edit.

## Emphasis (only these two markers)

```text
^^red^^        = warning, error, difference
!!highlight!!  = key term, definition, memorize
```

- Open and close on the same line. Never nested. Never in headings, code fences, or inline code.
- Max 2–3 per section (~20 lines). Short phrases, not whole sentences.
- If everything is highlighted, nothing is.

## Callouts & diagrams (optional)

- Callouts (the standard GitHub set, no custom types): `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]` — max ~10 per note.
  - Marker line must be bare: `> [!TIP]` only, with nothing after it on the same line. Title or body starts on the next line(s), each beginning with `>`.
- Mermaid only when it replaces ≥ ~15 lines of prose.
  - Max ~1–3 small charts (≤ ~10 nodes). Ask first for large charts.
  - One shared palette. Write the `classDef` lines once, in the first chart. Later charts only use `class X bad`.
  - Persian labels inside `"..."`.

```text
classDef bad fill:#fdd,stroke:#c00
classDef ok  fill:#dfd,stroke:#080
classDef key fill:#ffd,stroke:#a80
```

- Tables for comparison. Fold extra content (answers, extra sections) with the `^!` block below — readability, not token saving.

## Collapsible sections

- Open with `^!` alone on its line; close with `!^` alone on its line. Both required, each on its own line.
- Answer block: write nothing after `^!`.
- Non-answer block (rare — extra explanation/example): write a short English title after `^!`.
- Text, code, callouts allowed inside.
- ❌ Never write `<details>` / `<summary>` directly.
- ❌ Marker lines never inside code fences or inline code.

## Navigation & math (optional)

- TOC: optional and judgment-based, never mandatory. Skip it for short notes. For a long note, add it only when it helps navigation.
  - List only the important main sections (top-level `##`), not every heading. Example: 10 headings, 6 important → list those 6.
  - One short list at the top. Cost ~10–20 lines: add only when worth it.
- TOC anchors: headings have no ZWNJ (see Language) → anchors match the heading text exactly (`## 16. Exercises (تمرین ها)` → `#16-exercises-تمرین-ها`). Verify anchors before shipping. Canonical section names and separators: see Headings.
- KaTeX `$$...$$`: only when a formula is really needed.

## Code

- Short explanations inside the code, as comments next to the line.
- Mark good/bad lines with ✅ / ❌ in the comment.
- No comment on obvious lines.

## Exercises

- Use one shared dataset block ("Table 1") before all exercises only when they need data; otherwise skip it. When it exists, answers have no `CREATE`/`INSERT`, no re-printing Table 1, no restating the question.
- Answers go in a collapsible block (`^!` … `!^`) written **raw** — never inside a code fence. The answer's own code still goes in a normal code fence inside the block; only the `^!` block itself is never wrapped in a fence.
- Answers can be short: code + 1 key comment.
- Point out common pitfalls / failure patterns at each stage.

Example (copy this shape, raw, no outer fence):

**Ex 1** — 2 سفارش آخر هر مشتری، با مشتری های بدون سفارش.

^!

```sql
SELECT c.Name, o.OrderID
FROM Customers c
OUTER APPLY (                      -- ✅ OUTER keeps Reza (no orders)
    SELECT TOP (2) OrderID
    FROM Orders
    WHERE Orders.CustomerID = c.CustomerID
    ORDER BY OrderDate DESC        -- ⚠️ TOP without ORDER BY = random rows
) o;
```

!^

## Forbidden

- `<div dir="rtl">` / `<div dir="ltr">` (my script adds them).
- `<details>` / `<summary>` (use the `^!` block instead).
- `<span>`, inline styles, new color definitions (except the shared Mermaid palette above).
- Exceeding the color cap, except via the soft-cap rule.
