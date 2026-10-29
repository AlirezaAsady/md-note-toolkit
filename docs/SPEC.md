# Note marker specification

This is the authoring spec for notes processed by this toolkit. It defines the
marker grammar, what the tool generates, and the contract the round trip relies
on. It is deliberately language-agnostic: nothing here assumes Persian, and
every rule that depends on your language is listed in section 7.

Hand this file to an AI along with your own style rules and it can write
conforming notes. [`rules.md`](../rules.md) is one complete worked example of
such a style - a preset, not a requirement.

---

## 1. The three layers

```
layer 1   raw note            markers only, no HTML        <- you write this
layer 2   colored note        spans + details              <- color stage
layer 3   styled note         + <div dir="rtl"> + <link>   <- RTL stage
```

Layer 1 is the source of truth. `reverse` walks back from layer 3 to layer 1, so
you can regenerate the styled note at any time and the raw file stays readable,
diffable and cheap for an AI to edit.

The round trip is **content-identical, not byte-identical**: blank lines and
wrapper positions are normalized on the way out. Never hand-edit a layer 2 or
layer 3 file - edit layer 1 and re-run.

---

## 2. Marker grammar

### 2.1 Emphasis and highlight

| Marker | Becomes | Intended meaning |
|---|---|---|
| `^^text^^` | `<span class="r">text</span>` | warning, error, difference |
| `!!text!!` | `<span class="hy">text</span>` | key term, definition |

- Open and close on the **same line**. Nesting is not supported.
- Non-greedy: `^^a^^ b ^^c^^` produces two spans, not one.
- An **odd** number of `^^` or `!!` on a line is left exactly as written and
  reported as a warning. The tool never guesses where you meant to close.
- The inner text passes through `html.escape`, so `<`, `>` and `&` survive as
  literal characters.

### 2.2 Collapsible block

```text
^! optional short title
anything: prose, tables, code fences, callouts
!^
```

- `^!` and `!^` each stand **alone on their own line**. Leading whitespace is
  allowed on the open marker, not on the close marker.
- Generated shape:

  ```html
  <details dir="rtl">
  <summary>title</summary>

  <div dir="ltr">

  ...block content, untouched...

  </div>
  </details>
  ```

- The title may itself contain `^^` and `!!`; they are converted.
- With no title, the summary falls back to `DEFAULT_SUMMARY` in
  `md_color_gui.py`. On `reverse`, a summary equal to that string becomes a bare
  `^!` again. **This default is currently Persian** - see section 5.
- Everything between the markers passes through raw. The RTL stage does not wrap
  text inside a fold block, exactly like inside a code fence.
- A missing `!^` is reported as a warning; nothing is closed for you.

### 2.3 Gloss token

A short superscript used as a pointer to a translation or definition written
elsewhere. It is the cheapest way to keep a technical phrase in the source
language without paying for an inline translation every time it appears.

Default alphabet (`FOOT_OPEN`): `¹²³⁴⁵⁶⁷⁸⁹⁰`

**Inline use - a space on both sides is mandatory:**

```text
readers read an old committed copy ¹ , no waiting
```

The token starts at the superscript character and ends at the next literal
space. A tab, end of line, or table pipe does not count as that space, so
punctuation written without it becomes part of the token. Both spaces stay
**outside** the generated span.

**Definition line - token in column 0, one space, then the text:**

```text
¹ the reader sees an already committed version
```

| Position | Generated class | Default look |
|---|---|---|
| inline | `p s22` | purple |
| definition (column 0) | `g s22` | green |

- Only the token is colored, never the explanation text.
- `^^¹^^` or `!!¹!!` with the required spaces is stripped and treated
  exactly like a bare `¹`, so the output is identical either way. Do not add
  emphasis markers around a gloss token yourself.
- An existing `<span class="...">¹</span>` in the input is left alone, so
  re-running the color stage is safe.
- Set `FOOT_ENABLED = False`, or empty both classes, to switch the feature off;
  the tokens then stay plain text.

### 2.4 Contexts that are never processed

| Context | Behavior |
|---|---|
| fenced code (```` ``` ```` or `~~~~`) | passed through verbatim, markers stay literal |
| inline code (`` `x` ``) | protected before any substitution |
| heading lines (`#` at column 0-3) | skipped by the color stage |

Consequence: markers inside a heading are **not** converted. Do not write `^^`
or `!!` in a heading - put the emphasis in the body.

---

## 3. Structure the tool depends on

- **Blank lines are the unit.** The RTL stage wraps one blank-line-separated
  group at a time, so a table or a list is never cut in half. Keep a blank line
  before and after every block you want treated as a unit.
- **Headings are ATX only** (`#` to `######`). A setext heading (`===` or `---`
  under a line) is not recognized, and a bare `---` reads as a separator.
- **The first line may be a head line.** Whatever matches `HEAD_PATTERN`
  (default: the stylesheet `<link>`) is kept outside every `<div dir="rtl">`,
  followed by exactly one blank line. An empty `HEAD_PATTERN` means no head
  handling.
- **Smart RTL grouping.** With `SMART_RTL = True` a group is wrapped only if it
  contains a character from `RTL_PATTERN`, or if its first line is a heading
  whose level is selected by `HEADING_LEVELS`. With `SMART_RTL = False` every
  non-empty group is wrapped. `HEADING_LEVELS` accepts `"2-6"`, `"1,3-4"`, and
  inverts with a leading `^` or `-`; parts outside 1-6 are ignored.
- **HTML blocks pass through.** With `HANDLE_HTML = True`, a line starting with
  an HTML tag opens a raw block that is copied unchanged until the tags balance,
  so hand-written HTML in the source survives.

---

## 4. What the tool generates - never write it yourself

`<div dir="rtl">`, `<div dir="ltr">`, `<details>`, `<summary>`,
`<span class="...">` and the `<link rel="stylesheet">` line are all output. The
reverse stage removes exactly these shapes, so anything you write by hand in that
vocabulary risks being stripped or double-wrapped. Write markers only.

`reverse` maps classes back with `RULES` (default `h=!!, *=^^`): only the
**first** class of a span counts, the first matching prefix wins, and `*` is the
fallback. A custom class starting with `h` comes back as `!!`; anything else
comes back as `^^`. If you add your own color classes to the stylesheet, extend
`RULES` so the round trip stays closed.

---

## 5. Deliberate choices and known gaps

Each of these is a decision, not a bug. The code carries a comment at the exact
line so anyone can change it in place.

1. **The default fold summary is Persian** (`DEFAULT_SUMMARY` in
   `md_color_gui.py` and `md_reverse_gui.py`). A fold block with no title
   renders that label for every user. Change it in both files and keep them
   equal, or `reverse` stops recognizing a bare `^!`.
2. **Fold content is forced left-to-right.** The generated `<div dir="ltr">`
   inside `<details>` assumes the folded content is code, which is the common
   case for exercise answers. If you fold RTL prose instead, delete that one
   line in `md_color_gui.py` - the block then inherits the surrounding
   direction. Nothing else depends on it.
3. **An empty `CSS_HREF` still emits `<link rel="stylesheet" href="">`** instead
   of meaning "no stylesheet". Set it to a real path, or delete the line after
   running.
4. **The unclosed-tag scan only tracks ```` ``` ```` fences**, not `~~~~`. A line
   that looks like an HTML tag inside a tilde fence can be reported as unclosed.
   The color and reverse stages handle both fence styles correctly.
5. **A stray `!^` with no opening marker** switches the rest of the file into raw
   mode until the next `!^`.

---

## 6. Failure behavior

Nothing is healed silently. Every anomaly produces a greppable marker in the
output and a line in the log:

| Situation | Result |
|---|---|
| odd `^^` or `!!` on a line | line left unchanged + warning with the line number |
| unclosed HTML tag | an **empty** closing tag written right after the open one + warning |
| unclosed `^!` block | warning, file still written |
| invalid `RTL_PATTERN` or `HEAD_PATTERN` | warning, falls back to the default, run continues |
| file already processed | `Already fixed. Nothing to do.` and no write |

The empty-tag marker is intentional: searching the output for
`<div[^>]*>\s*\n</div>` finds every place the tool had to compensate, which is
where to look first when a note renders wrong.

---

## 7. Adapting the spec to another language

The scripts apply grammar, not language. To reuse them for another writing
system:

| Goal | Change |
|---|---|
| a different script counts as right-to-left | `RTL_PATTERN` in `md_rtl_advance_gui.py` (also a GUI field). Keep LTR scripts out - including them wraps Latin or CJK text in an RTL div and breaks the layout |
| notes are fully left-to-right | leave `SMART_RTL = True` and point `RTL_PATTERN` at a range your text never contains, or run the color stage only and skip RTL |
| different fold markers | `FOLD_OPEN` and `FOLD_CLOSE` (GUI fields), plus `DETAILS_OPEN_RE` and `DETAILS_CLOSE` in `md_color_gui.py` |
| different gloss alphabet | `FOOT_OPEN` in both `md_color_gui.py` and `md_reverse_gui.py` |
| different colors | `md.css`, plus `RULES` in `md_reverse_gui.py` so the round trip still closes |
| different head line | `HEAD_PATTERN` |
| your own summary text | `DEFAULT_SUMMARY` in both files, kept equal |
| section vocabulary, caps, table rules | your style file - see [`rules.md`](../rules.md) for the shape of one |

---

## See also

- [`README.md`](../README.md) - install, quick start, measured token savings
- [`md_batch_ai.md`](../md_batch_ai.md) - compact CLI and API reference for AI agents
- [`rules.md`](../rules.md) - one complete example style built on this spec
