# Rules for study notes (Markdown) and code comments

This file is one example style preset for md-note-toolkit: it tells an AI how to write a study note. The marker syntax (`^^`, `!!`, `^!` / `!^`, superscript glosses) is fixed by the tool and described in `SPEC.md`; everything else here is a personal choice you can rewrite. Give this file together with `SPEC.md` to the AI. Where the two disagree: this file decides content, structure and wording, `SPEC.md` decides the marker grammar and what the tool generates, because it mirrors the code.

## Priorities

1. The reader understands the topic, including the hard parts.
2. The content is correct and complete for what the note promises.
3. The note is easy to scan and the important things stand out.
4. Token cost.

Never cut a needed explanation, marker, Persian explanation or gloss to save tokens. Save tokens only by removing repetition (the same content twice, restated questions, re-printed data).

Existing notes are not restyled by this file: they are the exception, not a backlog. Restyle a note only when the user asks for it.

Judgment beats quotas. These rules contain very few hard numbers. Where a number appears it is a guide: exceed it by a small amount when that truly helps understanding, never by default. If something important does not fit, trim prose and repetition first, not the important thing.

Length: no hard line cap (about 700 lines is fine). If a topic risks token or context limits, split it into several notes.

## Language

- Main language: simple English (B2). Lists and tables may use keyword style. When the reasoning matters (because, so, unless, only if), write the connecting words instead of dropping them.
- Persian is the support language: questions, exercise prompts, the intro of a new topic, and complex points. See "Persian support" for the two tools: the footnote gloss and the Persian explanation paragraph.
- Never put Persian inside code. Code comments are English only (the script does not process code fences, so markers do not render there). Comments may carry footnote tokens.
- Symbols allowed in prose and comments: ✅ ❌ ⚠️ → (example: `WHERE drops NULL rows → LEFT = INNER`).
- NEVER use the zero-width non-joiner (the Persian half-space, Unicode U+200C) anywhere in Persian text. Always write a normal space instead (examples: "میشود" as one word, "فایل ها" with a normal space). It breaks heading anchor links. Never output that character itself, not even as an example; describe it in words.
- Digits are always ASCII 0-9, never Persian digits (U+06F0 to U+06F9); they render wrong in some viewers and force a whole English paragraph into right-to-left. ASCII digits inside Persian text are fine, even preferred. When unsure, use ASCII.

## Quality over quantity

- Fewer sections explained well beat many thin ones. Do not add a section, an example or a list item for coverage.
- A concept is explained in the order that fits it. A good default: the idea (and why it exists) → a minimal example → why the result is what it is → the trap or limit. This is a guide, not a template; skip steps that add nothing.
- The first note on a subject, and the first appearance of a hard concept, deserve real explanation. Easy material deserves less. Spend the length on what is hard.
- No repeated content. Link or refer back instead of restating.
- Setup data contains only what the examples actually use. No unused rows, columns or tables. Prefer a short Setup (about 30 lines or less); when it must be longer, say why in one line.

## Persian support

The English text stays the main text. Persian helps the reader understand it; it does not replace it. Depth follows difficulty: an easy point gets nothing, a hard idea gets a real explanation.

| What is hard | Tool |
|---|---|
| one word or phrase | footnote gloss with a superscript token |
| an idea, a reason, a relationship, a trap | Persian explanation paragraph under the English |

The two are often used together.

### A. Footnote gloss

Keep the English phrase and mark only the hard phrase with a sequential superscript token: ¹ ² ³ ⁴ ⁵ ⁶ ⁷ ⁸ ⁹ ⁰ ...

- Use it for phrasal verbs, idioms, abstract nouns, and technical terms on first use that a B2 reader who knows the topic may still pause on. When unsure whether a phrase is hard, gloss it.
- A space BEFORE and a space AFTER the token are both mandatory (the Python processing uses them as token boundaries, and they keep the mark distinct from an exponent).
  - ✅ `readers read an old committed copy ¹ , no waiting`
  - ❌ `copy¹ , no waiting` (no space before: looks like an exponent)
  - ❌ `copy ¹` at the end of a line without a trailing space
- A token is any listed superscript digit followed by non-space characters (`¹¹` or `¹*` is one token). It ends at the next literal space. A tab, a line end or a table pipe is not a substitute for that space. Punctuation must come after the separating space, otherwise it becomes part of the token.
- The surrounding spaces stay OUTSIDE the colored span; only the token is wrapped. Never wrap a token in `^^` or `!!` yourself, and never write a span by hand: the processing adds the color (inline tokens purple, definition tokens green; the classes are configurable). If `^^¹^^` or `!!¹!!` appears with the required spaces, the processing strips it and treats it as a bare token.
- Definition line: it starts with its token at the very beginning of its own line, then a mandatory space, then the Persian text. No leading space (it is a definition, not an inline marker).
  - ✅ `¹ خواننده یک نسخه قدیمی commit شده را میخواند`
  - ❌ `¹خواننده یک نسخه قدیمی commit شده را میخواند` (no space after the token)
- The definition is short: one or two key words or a clarifying phrase. Only the token is colored, not the explanation.
- Placement: the definition goes in a separate paragraph immediately after the specific table, paragraph or code block it belongs to, not collected at the end of the section.
- Numbering restarts from ¹ in every `##` section. If one section has several footnoted blocks, the numbers keep increasing inside that section, and each block's definitions go right after that block.
- Example:

```
- Row versioning (MVCC) → readers read an old committed copy ¹ , no waiting

¹ خواننده یک نسخه قدیمی commit شده را میخواند، بدون انتظار
```

### B. Persian explanation paragraph

A normal Persian paragraph placed directly under the English paragraph, example, table or code block it explains (blank line before and after). No token and no label.

Use it:
1. In the Intro of every new topic: 2 to 4 lines saying what it is and why it exists.
2. For a key concept that is hard to grasp: how it works, the intuition, an analogy, what to watch for.
3. After an example whose result is not obvious: why the output is what it is.
4. At a trap: why it happens and how to avoid it.

Size: one or two lines by default. A complex idea may take a longer explanation (up to about 8 lines, or a short list) when understanding needs it. Not every paragraph gets one; ten lines of easy material get none.

Content: add what the English does not show (the reason, the intuition, the connection, the consequence). Do not translate the English paragraph sentence by sentence.

Rules: Persian paragraphs may use `^^` and `!!` and may contain English terms (see Bidi). A paragraph that starts with a Persian word is not a footnote; footnote definitions are only lines that start with a superscript token. Under a table that has footnotes, put the footnote definitions first, then the explanation.

## Tables

- Most columns English → the whole table is English; mark hard cells with a footnote and explain below it.
- Only one or two English columns (terms) and the rest Persian → a "Persian table", no footnotes.
- RTL lock: if any cell contains code that breaks when right-aligned, the entire table MUST be English (explanations as footnotes or a Persian paragraph below).
- Use a table when comparing; use a Persian explanation paragraph below it when the difference is hard to see.

## Code blocks and comments

- Comments stay English (hard rule). They may use footnote markers with the same spacing rule (space before and after the token).
- The Persian explanation goes below the code block, never inside it.
- Short explanations go as comments next to the line. Mark good and bad lines with ✅ / ❌ in the comment. No comment on obvious lines.

## Bidi (mixed Persian and English)

This is a preference, not a hard rule (code comments in English only is the hard one). Notes render right-to-left: the script wraps blocks in `<div dir="rtl">` and handles mixed text. The risk: a Persian word BETWEEN two Latin tokens can reverse their order (`ROLLUP و CUBE` may show as `CUBE و ROLLUP`). There, use `,` / `VS` / `and` (`ROLLUP, CUBE`).

- Preferred shape: each language in one contiguous run, Persian at the EDGE of the Latin phrase.
- Latin inside Persian prose is fine (`از GROUP BY استفاده کن`).
- Never translate a technical term to satisfy this (`add`, `commit`, `merge`, `stage` stay English even mid-sentence: `دکمه add را بزن`).
- It matters most in headings, TOC links, table cells and list items; least in prose paragraphs (do not restructure a good sentence).

## Headings

- When a section's purpose matches a canonical name below, use that exact name. If none fits, create a new heading with the same formula. A note does not need every canonical section. Never rename a canonical section and never invent a fourth synonym for something listed.
- Formula: `## N. EnglishTerm[, EnglishTerm] (واژه فارسی)`. N = ASCII digits, a dot and one space (`## 7.`, never Persian digits). Numbering starts at `1.`, and `## 1.` is Setup only when the note has a Setup section. The body is English with at most ONE Persian keyword in parentheses at the end, only when the English alone is unclear (✅ `## 3. PIVOT Dynamic (پویا)`, ❌ `## ۳. PIVOT پویا (Dynamic)`). No U+200C in headings.
- Separators between parallel English terms:
  - ✅ `,` glued to the previous word with one space after (`## 6. GROUPING SETS, ROLLUP, CUBE` → `#6-grouping-sets-rollup-cube`)
  - ✅ uppercase `VS` with a space on both sides, only for a real comparison (`## 5. Git Rebase VS Reset`)
  - ❌ `و` or `،` (flips word order in right-to-left)
  - ❌ `&` and `/` (the slugger deletes them and leaves a double hyphen; `/` also reads as "or")
  - ❌ a space before the comma (breaks the anchor)
- Renaming a heading → update every `](#...)` TOC link in the same edit.

### Canonical section names

All numbered `## N.` except TOC.

| Name | Use |
|---|---|
| `## TOC (فهرست)` | unnumbered, top of the note |
| `## 1. Setup (Table 1)` | practice dataset; rename the parenthesis if there is no table |
| `Intro (مقدمه)` | what the topic is and why it exists |
| `Syntax` | grammar, clause order |
| `Examples` | worked examples |
| `X VS Y` | comparison; always the literal uppercase `VS`, never `و`, `در برابر` or `یا` |
| `Best Practices` | recommended habits |
| `Pitfalls (تله ها)` | traps and common mistakes, one section (not three) |
| `Troubleshooting` | "you hit error X, do Y" (Pitfalls = "do not do this") |
| `Performance (کارایی)` | speed and cost |
| `Exercises (تمرین ها)` | see "Exercises" below; rare |
| `Cleanup (پاک سازی)` | undo the setup |
| `Cheat Sheet` | code or command table to copy, no gloss |
| `Summary (خلاصه)` | prose wrap-up, gloss only when needed (a Cheat Sheet is not a Summary) |
| `Equivalents (معادل ها)` | the same thing in another tool; qualify only when it helps (`PostgreSQL, Django Equivalents (معادل ها)`) |
| `Sources (منابع)` | references |

The leading English keyword is the searchable token: `grep Pitfalls` or `grep Equivalents` must find that section in every note, whatever the subject. Subject-specific headings are free-form but keep the same formula and separators.

Section order (soft): TOC → Setup → Intro → Syntax → concepts, Examples → Best Practices → Pitfalls → Troubleshooting → Performance → Exercises → Cleanup → Cheat Sheet → Summary → Equivalents → Sources. Every section is optional; include only what the note needs. Numbers stay consecutive from `1.` over the sections that exist.

## TOC

Optional and judgment-based. Skip it for short notes. For a long note add it only when it helps navigation: one short list at the top with the important top-level `##` sections only (10 headings, 6 important → list those 6). Anchors match the heading text exactly (`## 16. Exercises (تمرین ها)` → `#16-exercises-تمرین-ها`); verify them before sending.

## Emphasis (color markers)

Only two markers exist: `^^red^^` and `!!highlight!!`. They label meaning, not hue. The reader recolors the classes by hand afterwards, so never think about a specific color.

- `^^x^^` = wrong, danger, trap, contrast, "this differs from that", a limit or an exception.
- `!!x!!` = key term, definition, the right way, a condition or value to remember.

### How to decide

Color is for meaning, not decoration. There is no quota in either direction: one line may carry five marks, and ten lines of narrative may carry none.

- Keep a mark only if removing it would make the reader lose something: a term to learn, a rule, a condition, a distinction, a trap, a role. Otherwise drop it.
- A whole concept area that needs it can be marked densely: several marks in one line, one after another, or side by side (`!!LEFT JOIN!! keeps all left rows, the rest become ^^NULL^^`). Marks are never nested.
- When one sentence holds a contrast, a key point and an emphasis, mark each one separately with the markers. Do not fall back to `**bold**` for the second one.
- A right/wrong pair: mark both sides, wrong with `^^`, right with `!!`.
- Mark a term where it is defined or where it matters, not every time it appears.
- Marked text is a short phrase. Mark a whole clause only when that clause is the rule to memorize. Never color a whole paragraph.
- Plain text, lists, tables and callouts are enough for narrative, transitions and background. `**bold**` is only a label (the first words of a list item, `**Ex 1**`): it stays black, so it never stands in for a color mark. No `*italic*` at all. `` `code` `` means an identifier, command or keyword, so it is never decoration.
- If everything is marked, nothing is. Test: could a reader who skims only the colored parts recover the key terms and the traps?

### Mechanics

- A marker pair opens and closes on the same line (a table cell or a list item is fine).
- Never in headings, code fences, inline code or math (`$$`, `$`).
- Never write `^^` or `!!` as ordinary text (for example "Wow!!"); an odd number of markers on a line is left unprocessed and reported.
- Never write `<span>`, `class=` or inline styles; the processing generates them.
- Footnote tokens are never wrapped in markers (see Persian support).

## Extra colors beyond the two markers (optional)

The two markers produce two classes: `^^` gives the red class, `!!` gives the yellow highlight. A third meaning needs a class written by hand, and that is opt-in, never the default.

- Default: two markers only. Recoloring is always safe because it happens in the stylesheet, not inside the note.
- A hand-written class is not round-trip safe: the reverse stage maps an unknown class back to `^^`, so a full reprocess loses that color.
- Roles worth a class when the user opts in: green = the right way, orange = a limit or a soft warning, a cyan highlight = output or result, a size class = a number or formula that anchors the eye.
- Ask in one line before writing a note: two markers only, or hand-written classes too? If the user does not care, use the two markers and spend no tokens on this.
- After a reverse and reprocess, restore what the reprocess removed. If the folder is under version control, its diff already points at those lines; otherwise list the hand-written classes and re-apply them. Both ways are optional.
- A minor change (one line, one color) goes straight into the styled file: no reverse, no reprocess, as long as the wrapper lines stay untouched.

## Math

Use KaTeX `$$...$$` only when a formula is really needed. The markers do not work inside math, so color formula parts with `\textcolor{name}{...}`.

- Color by role: each part of a formula that plays a different role gets its own color (input, result, condition, constant). Use only the names red, blue, green, orange, purple. One role keeps one color across the whole note.
- Put a one-line legend directly under the formula (`blue = center shift, red = discriminant, green = scale`), and a Persian explanation paragraph when the idea is hard.
- Around the formula, mark the same terms in the text with `!!` or `^^` as usual.
- Not every formula needs color. Color only when the parts mean different things.

## Callouts

Standard GitHub set only: `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]`. No custom types. The marker line is bare (`> [!TIP]` only); the title and body start on the next lines, each beginning with `>`.

There is no fixed cap. Use one wherever a reader could lose data or time, or must not miss a rule:

- `WARNING`: destructive, irreversible or risky actions, silent wrong results.
- `CAUTION`: severe consequences (data loss, security).
- `IMPORTANT`: a rule that everything after it depends on.
- `TIP`: a faster or safer way.
- `NOTE`: useful side information.

The main explanation never lives only inside a callout. A callout does not replace marking the key phrase in the text.

## Mermaid

Only when a chart replaces about 15 or more lines of prose. Keep it small (about 1 to 3 charts, at most about 10 nodes each); ask first for a large chart. Persian labels go inside `"..."`.

One shared palette: write the `classDef` lines once in the first chart (bad `fill:#fdd,stroke:#c00`, ok `fill:#dfd,stroke:#080`, key `fill:#ffd,stroke:#a80`); later charts only use `class X bad`.

## Collapsible sections

- Open with `^!` alone on its line and close with `!^` alone on its line; both are required.
- An answer block writes nothing after `^!`: the default label already says the same thing. Any other block gets a short title after `^!`, because that default label would mislabel it.
- Text, code and callouts are allowed inside. Never write `<details>` or `<summary>` directly.
- The marker lines are never inside code fences or inline code.
- Use it for readability, not for token saving.

## Exercises

A note does not contain exercises by default. Practice belongs in a separate exercise note that the user asks for.

- Exercise-only note: the whole note is `## 1. Exercises (تمرین ها)` (no empty Setup, Intro, TOC or Summary).
- A normal note may contain one or two exercises only when the topic cannot be understood without trying it. Never more unless the user asks.
- A dataset block ("Table 1") appears before the exercises only when they need data; otherwise skip it. When it exists, answers have no `CREATE` / `INSERT`, do not re-print Table 1 and do not restate the question.
- Shape: a bold `**Ex N** — question` line (Persian), a blank line, `^!`, a blank line, a code fence with ✅ / ⚠️ inline comments, a blank line, `!^`. The `^!` block itself is never wrapped in a fence; the answer's code goes in a normal fence inside it.
- The question line is Persian, about nine out of ten of them. The AI treats every phrase as obvious and writes English, so keep it Persian unless the prompt is self-evident without words (for example `A = ?`, or a prompt that is mostly identifiers and code).
- Answers are short (code and one key comment). Point out common pitfalls and failure patterns at each stage.
- If a topic would clearly benefit from practice, say so in one line in the reply (not in the note) and offer an exercise note.

## Forbidden

- `<div dir="rtl">` and `<div dir="ltr">` (the script adds them).
- `<details>` and `<summary>` (use `^!` / `!^`).
- `<span>`, inline styles, hand-written classes, and new color definitions. Exceptions: the shared Mermaid palette, the five KaTeX color names, and a class from the stylesheet when the user opted in (see Extra colors).
- Markers inside headings, code fences, inline code or math; markers used as ordinary text.
- U+200C anywhere; Persian digits.
- Persian inside code.

## Roadmap and skill-tree charts

A single unified graph, no subgraphs; the 10-node limit does not apply.

- Node color comes from `classDef` by category. Border thickness comes from a per-node `style` for importance (5px critical, 3px important, 2px normal). Apply the category class and the border style separately, not as multi-class on one node.
- Node shape by type: double circle = version-control tool, cylinder = database, hexagon = framework, diamond = security, trapezoid `[/../]` = infrastructure, deploy or API, rectangle = general skill, capsule = milestone.
- Node label = progress symbol (✔ known, ◐ learning, ○ future) + name + level tag `≼N≽` (`≼N.1≽` for optional or advanced items at that level) + difficulty stars up to 5.
- Use invisible tilde links (`~~~`) between same-level nodes for layout, with no extra visible links.
- Below the diagram always include: a color/category table, a shapes table, a symbols table and an explanation of the level tag.

## Examples of the intended density

### 1. A trap, with a gloss and a Persian explanation

````markdown
## 4. LEFT JOIN, WHERE Trap (تله)

!!LEFT JOIN!! keeps every row from the left table ¹ , even when nothing matches. The right-side columns are then ^^NULL^^.

¹ همه ردیف های جدول چپ در نتیجه میمانند

```sql
SELECT c.name, o.total
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
WHERE o.total > 100;   -- ❌ drops customers with no orders
```

^^WHERE on the right table^^ removes the NULL rows ² , so the query silently becomes an ^^INNER JOIN^^. ✅ Put the condition in `ON`.

² ردیف های NULL حذف میشوند

مشتری های بدون سفارش با LEFT JOIN نگه داشته میشوند و ستون های سفارش آنها NULL است. شرط WHERE روی ستون سفارش همین NULL ها را حذف میکند، پس آن مشتری ها ناپدید میشوند. برای نگه داشتنشان شرط را به ON ببر.
````

### 2. A right/wrong pair

````markdown
- ❌ ^^no column list^^ → the view breaks when a column is added
- ✅ !!explicit column list!! → the result shape stays stable
````

### 3. A dense line (five marks) and why that is fine

````markdown
Use `==` to compare !!values!! and `is` only to compare with !!None!!. ^^is with numbers or strings^^ is a trap: it may give ^^True^^ today and ^^False^^ on another interpreter.
````

Every mark carries a meaning (two rules, one trap, two results to contrast), so the density is justified here.

### 4. Plain prose with no marks

````markdown
SQL started in the 1970s as a research language at IBM and was standardized in the 1980s. Most database vendors added their own extensions, so code written for one database often needs small changes for another. The next sections use the common core that works almost everywhere.

اس کیو ال یک زبان استاندارد برای کار با دیتابیس های رابطه ای است. چون هر دیتابیس کمی تفاوت دارد، در این جزوه فقط بخش مشترک را یاد میگیریم.
````

Nothing here is a term to learn, a rule or a trap, so plain text is correct. The Persian paragraph is the intro of a new topic.

### 5. A formula colored by role

````markdown
$$x = \frac{\textcolor{blue}{-b} \pm \sqrt{\textcolor{red}{b^2 - 4ac}}}{\textcolor{green}{2a}}$$

blue = center shift, red = discriminant (decides how many roots exist), green = scale

عبارت !!زیر رادیکال!! تعیین میکند چند ریشه داریم: منفی یعنی ریشه حقیقی نداریم، صفر یعنی یک ریشه، و مثبت یعنی دو ریشه.
````

## Self-check before sending

Check these by judgment, not by counting:

- Does a new topic have a Persian intro? Is every hard idea explained, not only glossed?
- Are the contrasts, traps, terms and conditions marked, and both sides of every right/wrong pair?
- Is any mark pure decoration? Remove it.
- Are there exercises that were not asked for? Move them out.
- Is the Setup limited to what the examples use?
- Did you ask about hand-written classes, or default to the two markers without spending tokens on the question?
- Is every question line Persian unless it is self-evident, and is there no `*italic*` anywhere?
- Hard rules: no U+200C, ASCII digits, a space before and after every footnote token, definition lines start with the token, no Persian inside code, no markers in headings, code or math, headings follow the formula and canonical names, TOC anchors match.
