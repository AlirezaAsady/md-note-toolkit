# Rules for study notes (Markdown) and code comments

This file is one example style preset for md-note-toolkit: it tells an AI how to write a study note. In this file, "I", "me" and "my" always mean the user who owns the note, never the AI. The marker syntax (`^^`, `!!`, `^!` / `!^`, superscript glosses) is fixed by the tool and described in `SPEC.md`; everything else here is a personal choice you can rewrite. Give this file together with `SPEC.md` to the AI. Where the two disagree: this file decides content, structure and wording, `SPEC.md` decides the marker grammar and what the tool generates, because it mirrors the code.

## Priorities

1. The reader understands the topic, including the hard parts.
2. The content is correct and complete for what the note promises.
3. The note is easy to scan and the important things stand out.
4. Token cost.

Never cut a needed explanation, marker, Persian NOTE or gloss to save tokens. Save tokens only by removing repetition - the same content twice, restated questions, re-printed data - and by linking or referring back instead of restating.

Existing notes are not restyled by this file: they are the exception, not a backlog. Restyle a note only when the user asks for it.

Judgment beats quotas. Where a number appears it is a guide: exceed it by a small amount when that truly helps understanding, never by default. One number is hard, because it is a measurement and not a style choice: the recap trigger in section B, three marks in a section. Length is never a fixed number - it is bound to what the content needs. If something important does not fit, trim prose and repetition first, not the important thing.

Length: no hard line cap (about 700 lines is fine). If a topic risks token or context limits, split it into several notes.

## Language

- Main language: simple English (B2). Lists and tables may use keyword style. When the reasoning matters (because, so, unless, only if), write the connecting words instead of dropping them.
- Persian is the support language: questions and exercise prompts, plus the two tools of "Persian support" - the footnote gloss and the Persian NOTE.
- Never put Persian inside code. Code comments are English only (the script does not process code fences, so markers do not render there). Comments may carry footnote tokens.
- Symbols allowed in prose and comments: ✅ ❌ ⚠️ → (example: `WHERE drops NULL rows → LEFT = INNER`).
- NEVER use the zero-width non-joiner (the Persian half-space, U+200C) anywhere in Persian text - it breaks heading anchor links. Write a normal space instead ("میشود" as one word, "فایل ها" with a normal space). Never output that character itself, not even as an example; describe it in words.
- Digits are always ASCII 0-9, never Persian digits (U+06F0 to U+06F9) - they render wrong in some viewers and force a whole English paragraph into right-to-left. This holds inside Persian text too.

## Quality over quantity

- Fewer sections explained well beat many thin ones. Do not add a section, an example or a list item for coverage.
- A concept is explained in the order that fits it; a good default is the idea (and why it exists) → a minimal example → why the result is what it is → the trap or limit. Skip any step that adds nothing.
- The first note on a subject, and the first appearance of a hard concept, deserve real explanation. Easy material deserves less.
- Setup data contains only what the examples actually use. No unused rows, columns or tables. Prefer a short Setup (about 30 lines or less); when it must be longer, say why in one line.

## Persian support

The English text stays the main text. Persian helps the reader understand it; it does not replace it. Depth follows difficulty: an easy point gets nothing, a hard idea gets a real explanation.

| What is hard | Tool |
|---|---|
| one word or phrase | footnote gloss with a superscript token |
| an idea, a reason, a relationship, a trap | Persian `> [!NOTE]` at the end of the section |

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
- The same token text may appear more than once in a section (the inline use, the definition line, a pointer in a recap). Each occurrence is its own token with its own spaces.
- Example:

```
- Row versioning (MVCC) → readers read an old committed copy ¹ , no waiting

¹ خواننده یک نسخه قدیمی commit شده را میخواند، بدون انتظار
```

#### Chain and back-reference tokens (one term, several sections)

A term that comes back in later sections does not need its explanation repeated. The token then carries a separator and a second digit. There are two separators and the digits mean something different in each. Both forms are still one token, one colored span, and the space rules do not change. The tool treats every form as an ordinary gloss token (a superscript followed by non-space characters, see `SPEC.md` section 2.3) and only colors it: the meaning of the compound forms is a convention of this file.

Preference, in this order, and every step needs a reason:

1. Plain `N` - the default. Explain the term where it first appears, once, with no separator. This is the cheapest shape: one explanation, nothing to track.
2. Back-reference `S^N` - the term comes back and the explanation above is still enough. Use it only to avoid writing the same explanation twice: the saving is a whole definition line, the cost is two characters.
3. Chain `CᵛN` / `Cᵛ` - only when one explanation genuinely cannot serve the whole note: the reader needs something here, but the full story belongs later because the context to understand it does not exist yet.

Explaining early and referencing later beats deferring: it costs less and reads better, so the chain is the exception, not a style. A compound token with no second occurrence in the note is a mistake - delete the separator.

Back-reference with a caret, `S^N` - the explanation is already above:

- `S` is the section number and `N` is that section's own token number, so the reader is sent to one exact place. Both digits are already known, so there is nothing to track.
- Write no definition line here. The missing definition is the mark that says "look above".
- Use it when one plain gloss is enough and the term simply comes back later.

Chain with a superscript v (U+1D5B), `CᵛN` and bare `Cᵛ` - the explanation is built up in steps:

- `ᵛ` is the single character U+1D5B. Copy it exactly; never type a plain `v` in its place.
- `CᵛN` - the term has a local explanation here, so its definition line is `CᵛN ...`. `C` is the chain id and `N` the local number in this section, shared with the plain tokens.
- Bare `Cᵛ` with no definition line - a pointer. Nothing is explained here; the reader looks at the chain.
- Bare `Cᵛ` with a definition line `Cᵛ ...` - the HOME of the chain: the one complete explanation. Exactly one home per chain, in whichever section it belongs, not necessarily the last one.
- Chain ids run ¹, ², ³ ... in order of first appearance, so the highest id in a note says how many terms needed a fuller explanation. If no fuller explanation is ever written, the first one is the home and the chain closes there.
- A chain id is not a plain token. The chain id counter and the plain token counter are separate: the id appears only in the compound form (`CᵛN` or `Cᵛ`), a plain `¹` is always a local token number.

Numbering, both forms: the right digit is relative to the `##` section it stands in and restarts there (see the restart rule above), so the same chain can be `Cᵛ³` in one section and `Cᵛ¹` in the next, and it can be ¹⁰ in a long section. Numbers increase in reading order. A bare pointer takes no number and makes no gap.

Search: in the raw note, `Cᵛ` at the start of a line finds only the home definition. In the rendered note, `"g s22">Cᵛ<` finds the same span. Searching `Cᵛ` anywhere lists every use of the term, and searching `S^` lists every back-reference to section `S`.

Example (one term in five sections: explained once, referenced twice, then a chain with a partial and its home):

```
## 1. Sort keys

... a tie-breaker ¹ decides the order of equal rows ...

¹ کلیدی که ترتیب سطرهای هم رده را مشخص می کند

## 3. Order by

... the same tie-breaker ¹^¹ , no new explanation here ...

## 4. Ties

... the tie-breaker ¹^¹ again, still nothing new here ...

## 7. Stable order

... the tie-breaker ¹ᵛ¹ fixes the order across pages ...

¹ᵛ¹ کلیدی که ترتیب سطرهای هم رده را در صفحه های بعدی هم ثابت نگه می دارد

## 12. Cheat Sheet

... always give the query one tie-breaker ¹ᵛ ...

¹ᵛ وقتی دو سطر در همه کلیدهای مرتب سازی برابر باشند، این کلید ترتیب نهایی را ثابت نگه می دارد
```

### B. Persian NOTE

A Persian `> [!NOTE]` callout, blank line before and after. This type is reserved for the two passages below and for nothing else, so a NOTE always proves one of these two rules fired. An explanation of the content is written only as one of these two; bare Persian prose stays for questions and exercise prompts.

#### What counts as a mark

A mark is one `^^...^^` pair, one `!!...!!` pair, or a footnote token that has its own definition line. A pair counts as ONE mark (the open and the close together): `^^NULL^^` is one mark. Not a mark: `**bold**`, a back-reference `S^N`, a bare pointer `Cᵛ`, and anything inside a table, a code fence, a math block, a collapsible block or a callout. The definition line itself is not a mark - only the inline use counts, so one gloss is one mark.

#### Trigger for a section recap

Count the marks in every `##` section. Three or more means the section is hard and gets a recap at its end. Structural sections are never counted and never get one: TOC, Setup, Cleanup, Exercises, Cheat Sheet, Summary, Sources.

Count before writing the recap, because the recap carries footnote tokens of its own and must not feed the count.

#### What the recap says

The general concept of the section: what it is really about and why it behaves the way it does. Not word level notes - words are the footnote's job. If a term in the section already has a footnote token, the recap points at it with the same token instead of defining it again. Repeating a token number there is allowed: it is an inline use (space before and after), not a second definition.

Add what the English does not show (the reason, the intuition, the connection, the consequence). Do not translate the English paragraph sentence by sentence.

#### How long

Bound to what the concept needs, not to a fixed number. One line is common and often enough; a concept with several parts may take up to about six body lines. Never pad - a line the concept does not need is deleted. Past about six lines it has stopped being a recap and become a second explanation: cut it, or the section should have been split. A concept that really is a mechanism of separate steps may become a numbered list, one line per step.

#### Topic preview

Decided from the list of `##` headings, never from reading the body. Plan the headings first, decide the preview from that list, then write the sections. Nothing new is printed and no heading is written twice: the headings stay where they always were, and the TOC - optional, links, important sections only - is a separate thing (see TOC).

If every heading is structural (the list above), write no preview. Otherwise put a preview before section 1, after the TOC when the note has one (order: TOC → preview → section 1), written for a reader who has never met the topic:

1. One sentence: what this note is about and why the topic exists.
2. The parts or methods the note covers, named only - never how they work, never their trade-offs. Each part is explained in its own section.

Length follows the number of parts, never the depth of explanation: two lines when the note has two or three parts, up to about five when it has many, and then the second sentence becomes a short list of names. Explaining a part in the preview is a mistake, because its own section then has to repeat it.

Example:

````markdown
> [!NOTE]
> صفحه بندی یعنی داده ها را در تکه های کوچک تر نشان بدهی نه در یک لیست بلند، چون هم خواندنش برای کاربر راحت تر است و هم هزینه اش برای سرور کمتر.
> این جزوه دو روش را پوشش می دهد: OFFSET و Keyset.
````

#### Form

Every body line starts with `> `. The body may use `^^` and `!!` and may contain English terms (see Bidi). A footnote definition never goes inside a NOTE: definitions stay at column 0 in the section body, and the NOTE only points at them with the token. A NOTE body line that starts with a Persian word is not a definition line.

## Tables

- Use a table when comparing. A table is never explained on its own.
- Most columns English → the whole table is English; mark hard cells with a footnote and explain below it.
- Only one or two English columns (terms) and the rest Persian → a "Persian table", no footnotes.
- RTL lock: if any cell contains code that breaks when right-aligned, the entire table MUST be English (explanations as footnotes or a Persian NOTE below).

## Code blocks and comments

- Comments stay English (hard rule) and may carry footnote tokens with the same spacing rule (space before and after the token).
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
- Renaming a heading → in the `important` and `full` TOC modes update every `](#...)` TOC link in the same edit; in the `empty` mode leave the TOC body untouched (see TOC).

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

Section order (soft): TOC → topic preview (not a heading, see B) → Setup → Intro → Syntax → concepts, Examples → Best Practices → Pitfalls → Troubleshooting → Performance → Exercises → Cleanup → Cheat Sheet → Summary → Equivalents → Sources. Every section is optional; include only what the note needs. Numbers stay consecutive from `1.` over the sections that exist.

## TOC

This section is personalized: its default below fits the workspace where I read my notes, and another reader of this ruleset may need another mode. So an AI that receives this ruleset says at the beginning that the TOC is personalized here, and asks once, before writing the first note, which mode to use in this context; the answer holds until I change it. The modes:

- `empty` (the default in my workspace): write only the `## TOC (فهرست)` heading and leave the body empty. The list is mine, not the AI's: the Markdown All in One extension in my VS Code (`toc.levels` = 1..2) creates and refreshes it with a shortcut. An empty body is intended - not a bug, not a forgotten step - so the AI never writes or edits the list, also not after renaming a heading.
- `important`: one short list at the top with the important top-level `##` sections only (10 headings, 6 important → list those 6).
- `full`: every top-level `##` section.

In the `important` and `full` modes, anchors match the heading text exactly (`## 16. Exercises (تمرین ها)` → `#16-exercises-تمرین-ها`); verify them before sending. Short notes skip the TOC heading entirely, in every mode.

## Emphasis (color markers)

Only two markers exist: `^^red^^` and `!!highlight!!`. They label meaning, not hue. The reader recolors the classes by hand afterwards, so never think about a specific color.

- `^^x^^` = wrong, danger, trap, contrast, "this differs from that", a limit or an exception.
- `!!x!!` = key term, definition, the right way, a condition or value to remember.

### How to decide

There is no quota in either direction: one line may carry five marks, and ten lines of narrative may carry none.

- Keep a mark only if removing it would make the reader lose something: a term to learn, a rule, a condition, a distinction, a trap, a role. Otherwise drop it.
- A whole concept area that needs it can be marked densely: several marks in one line, one after another, or side by side (`!!LEFT JOIN!! keeps all left rows, the rest become ^^NULL^^`). Marks are never nested.
- When one sentence holds a contrast, a key point and an emphasis, mark each one separately. Do not fall back on `**bold**` for the second one.
- A right/wrong pair: mark both sides, wrong with `^^`, right with `!!`.
- Mark a term where it is defined or where it matters, not every time it appears.
- Marked text is a short phrase. Mark a whole clause only when that clause is the rule to memorize. Never color a whole paragraph.
- Plain text, lists, tables and callouts are enough for narrative, transitions and background.
- `**bold**` is only a label (the first words of a list item, `**Ex 1**`): it stays black, so it never stands in for a color mark. No `*italic*` at all. `` `code` `` means an identifier, command or keyword, so it is never decoration.
- If everything is marked, nothing is. Test: could a reader who skims only the colored parts recover the key terms and the traps?

### Mechanics

- A marker pair opens and closes on the same line (a table cell or a list item is fine).
- Never in headings, code fences, inline code or math (`$$`, `$`).
- Never write `^^` or `!!` as ordinary text (for example "Wow!!"); an odd number of markers on a line is left unprocessed and reported.
- Never write `<span>`, `class=` or inline styles; the processing generates them.
- Footnote tokens are never wrapped in markers (see Persian support).

## Hand-colored notes (keep my classes)

The AI writes only `^^` and `!!`; it never writes a class. I recolor by hand afterwards: I change a span's class in the styled note. The risk: running `reverse` and the color stage again maps every unknown class back to `^^` or `!!` (see `SPEC.md` section 4), so a hand color is lost. The AI protects my colors like this:

- Prefer not to reprocess at all. A small change (one line, one color) goes straight into the styled note: no reverse, no reprocess, wrapper lines untouched.
- If the note must go through reverse and the color stage again, check first whether the note is inside a git repository.
  - Git available: after reprocessing, compare with the committed version, find the spans whose class changed, and apply my classes to those spans again.
  - No git: before reversing, save the hand-colored spans (the span text and its class) to a temporary file outside the note. After reprocessing, re-apply only the classes from that list, then delete the temporary file.
- Re-applying changes classes only. Text, markers and wrappers stay exactly as the processing produced them.
- Never invent a class or a color. Which class goes where is my decision.
- No question is asked about this before writing a note.

## Math

Use KaTeX `$$...$$` only when a formula is really needed. The markers do not work inside math, so color formula parts with `\textcolor{name}{...}`.

- Color by role: each part of a formula that plays a different role gets its own color (input, result, condition, constant). Use only the names red, blue, green, orange, purple. One role keeps one color across the whole note.
- Put a one-line legend directly under the formula (`blue = center shift, red = discriminant, green = scale`).
- Around the formula, mark the same terms in the text with `!!` or `^^` as usual.
- Not every formula needs color. Color only when the parts mean different things.

## Callouts

Standard GitHub set only: `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]`. No custom types. The marker line is bare (`> [!TIP]` only); the title and body start on the next lines, each beginning with `>`.

There is no fixed cap. Use one wherever a reader could lose data or time, or must not miss a rule:

- `WARNING`: destructive, irreversible or risky actions, silent wrong results.
- `CAUTION`: severe consequences (data loss, security).
- `IMPORTANT`: a rule that everything after it depends on.
- `TIP`: a faster or safer way.
- `NOTE`: reserved for the two Persian passages of section B - the section recap and the topic preview. Never for English side information, which is a `TIP` or an `IMPORTANT`.

The main explanation never lives only inside a callout, and a callout does not replace marking the key phrase in the text. The one exception is `NOTE` (see B).

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
- The question line is Persian. The only exception is a prompt that is self-evident without words (for example `A = ?`, or one that is mostly identifiers and code). The AI treats every phrase as obvious and writes English, so that exception is narrower than it looks.
- Answers are short (code and one key comment). Point out common pitfalls and failure patterns at each stage.
- If a topic would clearly benefit from practice, say so in one line in the reply (not in the note) and offer an exercise note.

## Forbidden

- `<div dir="rtl">` and `<div dir="ltr">` (the script adds them).
- `<details>` and `<summary>` (use `^!` / `!^`).
- `<span>`, inline styles, hand-written classes, and new color definitions. Exceptions: the shared Mermaid palette, the five KaTeX color names, and re-applying my own classes under the rules of "Hand-colored notes".
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

> [!NOTE]
> مشتری های بدون سفارش در نتیجه می مانند ¹ ، ولی شرطِ WHERE همان ردیف ها را حذف می کند ² و کوئری بی صدا به یک INNER JOIN تبدیل می شود. جای درستِ شرط، ON است.
````

Six marks in this section (each `^^...^^` or `!!...!!` pair counts once, each footnote token with a definition counts once), so the recap is required. It sits at the end of the section as a `NOTE` and points at ¹ and ² instead of defining them again.

### 2. A right/wrong pair

````markdown
- ❌ ^^no column list^^ → the view breaks when a column is added
- ✅ !!explicit column list!! → the result shape stays stable
````

### 3. Plain prose, and the topic preview

````markdown
SQL started in the 1970s as a research language at IBM and was standardized in the 1980s. Most database vendors added their own extensions, so code written for one database often needs small changes for another. The next sections use the common core that works almost everywhere.

> [!NOTE]
> اس کیو ال یک زبان استاندارد برای کار با دیتابیس های رابطه ای است، و چون هر دیتابیس کمی تفاوت دارد، در این جزوه فقط بخش مشترک را یاد میگیریم.
> این جزوه سه قسمت را پوشش می دهد: SELECT, JOIN, WHERE.
````

Nothing here is a term to learn, a rule or a trap, and the section carries no mark, so no recap is required - the trigger counts marks, not paragraphs. The NOTE is the topic preview: one sentence on what the topic is and why it exists, one naming the parts.

### 4. A formula colored by role

````markdown
$$x = \frac{\textcolor{blue}{-b} \pm \sqrt{\textcolor{red}{b^2 - 4ac}}}{\textcolor{green}{2a}}$$

blue = center shift, red = discriminant (decides how many roots exist), green = scale

The !!discriminant!! decides how many roots exist: negative gives none, zero gives one, positive gives two.
````

The formula and its legend carry no mark and the sentence below carries one, so this section needs no recap.

## Self-check before sending

- Does every section with three or more marks have its recap at the end, and does that recap point at the footnote tokens instead of defining them again?
- Does a note with a real topic have its preview after the TOC (if any) and before section 1, decided from the list of headings? Is every recap and preview a `> [!NOTE]`, and is no `NOTE` used for anything else?
- Does a term that comes back in a later section use a back-reference or a chain token instead of a second full explanation?
- Does every compound token have a reason - a real second occurrence, or a real explanation that had to be deferred? A separator with no second use is deleted.
- Are the contrasts, traps, terms and conditions marked, and both sides of every right/wrong pair?
- Are there exercises that were not asked for? Move them out.
- Is the Setup limited to what the examples use?
- If the note was hand-colored and had to be reprocessed, did you follow "Hand-colored notes" (git comparison or a temporary list) before and after?
- Is every question line Persian unless it is self-evident, and is there no `*italic*` anywhere?
- Hard rules: no U+200C, ASCII digits, a space before and after every footnote token, definition lines start with the token, no Persian inside code, no markers in headings, code or math, headings follow the formula and canonical names, TOC anchors match.
