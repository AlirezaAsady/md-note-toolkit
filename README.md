# md-note-toolkit

**English** | [فارسی](README.fa.md)

Markdown note preprocessor that keeps the **raw file clean** while producing a
styled, right-to-left, bilingual-friendly rendered note.

It adds the four things Markdown has no native syntax for - per-block text
direction, colored emphasis, collapsible sections, second-language glosses -
and it can convert the result **back** to clean Markdown.

Zero install. Python standard library only.

---

## The problem

Markdown has no native support for:

| Missing | What people do instead | Cost |
|---|---|---|
| per-block text direction | hand-written `<div dir="rtl">` | raw file becomes unreadable |
| colored emphasis | `<span style="...">` | inline styles, unmaintainable |
| collapsible sections | `<details>` + `<summary>` | 5 lines instead of 2 |
| second-language glosses | inline translation | layout breaks, tokens explode |

Persian, Arabic and Hebrew writers, and anyone taking **bilingual notes**, hit
all four constantly. The usual workaround - writing raw HTML inside Markdown -
makes the source file hard to read, hard to diff, and fragile for an AI to edit.

This toolkit keeps the source as plain Markdown plus a few tiny markers, and
generates the HTML at processing time.

> **The spec is the product; the scripts are the compiler.** Note quality comes
> from the style rules in [`docs/MY_STYLE.md`](docs/MY_STYLE.md), not from the code. The code
> only makes applying those rules cheap. Because the rules are a plain text
> file, you can hand them to any AI and rewrite them for your own language.

---

## Why Markdown and not PDF or WORD

- **Plain text means diff, grep and version control.** PDF and WORD are binary:
  you cannot see what changed, cannot merge, cannot search precisely. With a
  fixed section vocabulary (`Pitfalls`, `Cheat Sheet`, `Equivalents`, ...) one
  `grep` finds a section across *all* notes of *any* subject.
- **AI-native.** Models read and write Markdown natively. WORD and PDF need
  conversion in both directions - extra tokens plus lost structure, and tables
  and text direction usually break in the process.
- **No vendor lock-in.** Renders in VS Code, GitHub, Obsidian and any browser.
  Tens of KB instead of MB.
- **Zero dependency.** This toolkit imports nothing outside the standard
  library (`tkinter`, `re`, `ctypes`, `pathlib`, `argparse`). No `pip install`,
  no virtual environment - copy the folder and run it.

Markdown is a **worse** choice for precise print layout, heavy mathematical
publishing, and non-technical collaborators who expect WORD.

---

## Why it saves tokens

The point is not prettier notes. It is that an AI can produce high-quality
notes for a fraction of the cost, because it writes - and later re-reads -
clean Markdown instead of HTML.

**Measured** on [`examples/before.md`](examples/before.md), a complete sample
note with a TOC, prose carrying both emphasis markers, a table, seven gloss
tokens and three fold blocks:

| | characters | lines |
|---|---|---|
| raw markers - what the AI writes and re-reads | 3086 | 87 |
| rendered output - what the viewer shows | 4229 | 170 |

The source is **1143 characters (27 percent) smaller** than the artifact,
about 285 tokens. That is paid once per generation and then again on every
re-read of the note.

Reproduce it with [`examples/measure.py`](examples/measure.py), which also
checks that the committed artifact really is tool output and that `reverse`
gives the source back.

Four mechanisms, ordered by real impact:

1. **Cheap re-reading - the biggest win.** Generation savings happen once;
   re-reading savings happen every session. If you keep rendered HTML as your
   source of truth, every follow-up conversation pays for that HTML again.
   `reverse` gets you back to clean Markdown, so you never have to.
2. **Safe editing.** Clean Markdown diffs mean one section can be sent and
   edited in isolation. With hand-written HTML, an AI can drop a single
   `</div>` and - because nesting is tracked by a counter - **the rest of the
   file silently stops being RTL-wrapped.** This really happened: 13 unclosed
   `<div dir="ltr">` tags, and an entire exercises section came out
   un-processed. The optional auto-close pass emits an *empty, greppable* tag
   pair rather than healing silently, so the damage is visible:
   search `<div[^>]*>\s*\n</div>`.
3. **Glosses instead of translations.** A `¹` marker plus a two-word gloss
   costs a handful of tokens. A full inline translation costs five to ten
   times that and wrecks the layout - and the short gloss doubles as
   vocabulary practice.
4. **Short markers instead of HTML.** `^!` / `!^` instead of
   `<details>` + `<summary>`; `^^x^^` instead of `<span class="r">x</span>`.

---

## Requirements

- **Python 3.10 or newer.** The code uses `Path | None` union annotations and
  `list[str]` generics, which need 3.10. Tested on 3.14. Nothing else required.
- Any operating system. When replacing an original file, Windows sends the old
  copy to the Recycle Bin; Linux and macOS rename it to `<name>.bak` (unique,
  never overwritten) and report that as a warning. Nothing is ever deleted.

---

## Quick start

Headless CLI - the main entry point:

```bash
python md_batch.py forward "notes.md"          # apply color markers, then RTL
python md_batch.py reverse "notes.md"          # back to clean Markdown
python md_batch.py forward "a.md" "b.md"       # several files in one run
python md_batch.py color "notes.md" --new      # write notes.out.md, keep input
```

Modes: `reverse`, `color`, `rtl`, `forward` (= color then RTL). Default is
`forward`. Exit codes: `0` success, `1` one or more files failed, `2` invalid
arguments.

Graphical front ends - double-click or run directly:

```bash
python md_batch_gui.py           # multi-file window over the same engine
python md_color_gui.py           # single file: markers -> HTML
python md_rtl_advance_gui.py     # single file: RTL wrapping
python md_reverse_gui.py         # single file: HTML -> markers
```

Programmatic use:

```python
import md_batch
results = md_batch.run_batch(["a.md", "b.md"], mode="forward")
for r in results:
    print(r.source, r.status, r.warnings)
```

`run_batch` returns one record per file with `source`, `destination`, `status`
(`saved` / `unchanged` / `error`), `warnings` and `error`. Failures never stop
the remaining files.

Tests:

```bash
python test_md_batch.py
```

---

## Syntax reference

Write these in the raw Markdown file. Never write HTML by hand - the tool
generates it, and `reverse` removes it again.

| Marker | Becomes | Use for |
|---|---|---|
| `^^text^^` | red span | warnings, errors, differences |
| `!!text!!` | highlighted span | key terms, definitions |
| `^!` ... `!^` | collapsible block | exercise answers, optional depth |
| `¹ word` | colored gloss token | short translation of a hard phrase |
| ```` ``` ```` | left untouched | fenced code is never processed |

Rules for the markers:

- `^^` and `!!` stay on one line, are never nested, and never appear in
  headings or code. Cap at 2-3 per ~20 lines or they stop meaning anything.
- `^!` and `!^` each go **alone on their own line**. An optional short title
  after `^!` becomes the collapsible summary. Everything inside the block is
  left raw, exactly like a code fence.
- A gloss token needs **a space before and after it** (`copy ¹ , no waiting`).
  Those spaces are the token boundaries. The definition line starts with the
  token in column 0 followed by a space, and sits in its own paragraph
  directly below the table or block it explains - never inline mid-sentence.
- Odd numbers of `^^` or `!!` on a line are left unchanged and reported as a
  warning, never silently guessed.

The full grammar, the exact HTML each marker becomes, and the round-trip
contract live in [`docs/SPEC.md`](docs/SPEC.md).

---

## Example

`examples/` holds one complete note in both forms, so you can see exactly what
the pipeline does before you run it on your own files.

| File | What it is |
|---|---|
| [`before.md`](examples/before.md) | raw markers - what you or an AI writes |
| [`after.md`](examples/after.md) | rendered output - the artifact a viewer shows |
| [`measure.py`](examples/measure.py) | reproduces the character counts above and checks the round trip |

`after.md` is generated, never edited by hand. Regenerate it with:

```
cp examples/before.md examples/after.md
python md_batch.py forward examples/after.md
```

Then set its stylesheet `href` to `../md.css`. The tool writes the absolute
path of the `md.css` sitting next to `md_color_gui.py`, which is right on your
machine and useless to anyone else reading the repo.

### How it looks

GitHub strips the linked stylesheet, so the styled note can only be seen in VS
Code or a browser. These screenshots are that local render:

<!-- TODO: screenshots of examples/after.md rendered in VS Code / a browser -->

---

## Configuration

Every knob is a constant at the top of its module - no config file to find, no
hidden state. The GUI windows pre-fill from the same constants.

| Constant | Module | Meaning |
|---|---|---|
| `CSS_HREF` | `md_color_gui.py` | stylesheet linked into the output |
| `FOOT_ENABLED`, `FOOT_OPEN` | `md_color_gui.py` | gloss token handling |
| `OUT_SUFFIX`, `REPLACE_ORIGINAL` | `md_color_gui.py`, `md_rtl_advance_gui.py` | output naming |
| `SMART_RTL` | `md_rtl_advance_gui.py` | wrap only blocks containing RTL script |
| `RTL_RE` | `md_rtl_advance_gui.py` | which characters count as right-to-left |
| `HEADING_LEVELS` | `md_rtl_advance_gui.py`, `md_reverse_gui.py` | `"2-6"`, `"1,3-4"`; prefix `^` inverts |
| `AUTOCLOSE_HTML`, `HANDLE_HTML` | `md_rtl_advance_gui.py` | unclosed tag handling |
| `FOLD_OPEN`, `FOLD_CLOSE`, `HEAD_PATTERN` | `md_rtl_advance_gui.py` | marker syntax, head line |
| `RULES`, `REMOVE_RTL`, `REMOVE_LINK` | `md_reverse_gui.py` | reverse conversion scope |

An empty value always means the feature is off.

**About `CSS_HREF`:** the value is written into the note as
`<link rel="stylesheet" href="...">`. Notes normally live in a different folder
from this toolkit, so it **must be a complete path** (or a `file://` URL) - a
relative href breaks as soon as the note is opened from anywhere else. The
default resolves `md.css` next to the script, so a fresh clone works with no
editing. Point it at your own stylesheet to restyle everything at once.

---

## The pipeline

```
raw notes (markers)  --color-->  HTML spans + details  --rtl-->  styled RTL note
        ^                                                              |
        +------------------------- reverse ----------------------------+
```

`forward` runs color then RTL. `reverse` runs the opposite and returns clean
marker source. The round trip is content-identical, which is what makes it safe
to keep the raw file as the single source of truth.

Replacement is non-destructive: the original goes to the Recycle Bin, and
unchanged files are not touched at all, so their timestamps stay put.

---

## Who this is NOT for

If you only publish to GitHub, you probably do not need this - GitHub already
renders `<div dir="rtl">`, `<details>` and `[!NOTE]` callouts.

The toolkit pays off when you **write notes daily** and want the raw file
readable, diffable and cheap for an AI to edit, while still getting your own
visual style in VS Code or a browser.

---

## Personalizing the style spec

[`docs/MY_STYLE.md`](docs/MY_STYLE.md) is one worked example of a complete note style:
language policy, section vocabulary, emphasis caps, table rules, gloss
placement, exercises. It is **not** a requirement of the tool.

The grammar it builds on - what each marker means, what HTML comes out, what
must never be written by hand - is specified separately in
[`docs/SPEC.md`](docs/SPEC.md). That file is language-agnostic and is what you
hand to an AI when you want notes that conform to your own style.

The intended workflow is to copy it and rewrite it with any AI: change the
language pair, change the section names, change what gets emphasized. The
scripts do not care what your rules say - they only apply the marker syntax.

---

## Project layout

```
md_batch.py            headless CLI and batch engine (main entry point)
md_batch_gui.py        Tkinter window over the same engine
md_color_gui.py        markers -> HTML spans, details, gloss colors
md_rtl_advance_gui.py  RTL wrapping, smart mode, unclosed-tag detection
md_reverse_gui.py      HTML -> markers, removes RTL wrappers and link line
md.css                 default stylesheet
docs/SPEC.md           marker grammar, generated HTML, round-trip contract
docs/MY_STYLE.md       one complete example style preset
examples/before.md     sample note as raw markers
examples/after.md      the same note after color + RTL
examples/measure.py    reproduces the token numbers and checks the round trip
md_batch_ai.md         compact CLI/API reference written for AI agents
test_md_batch.py       unittest suite, no external fixtures
```

---

## Known limitations

- Outside Windows there is no Recycle Bin, so each replace leaves one backup
  behind: `notes.md.bak`, then `notes.md.bak.2`, and so on. Backups are never
  overwritten, which means repeated runs accumulate files - clear them out when
  you no longer need them. `*.bak` is gitignored.
- `SMART_RTL` decides what to wrap using `RTL_RE`, which by default covers
  Hebrew, Arabic (so Persian and Urdu included), the Arabic supplement and
  extended blocks, and both Arabic presentation-forms blocks. Edit that one
  pattern for any other RTL script. Left-to-right scripts must stay **out** of
  it - adding CJK or Latin would wrap LTR text in an RTL div and break the
  layout. Note that the Arabic block also contains Persian digits
  `U+06F0-U+06F9`, so a stray Persian digit inside an English paragraph forces
  that whole block RTL; the style rules forbid Persian digits for exactly this
  reason.
- Content inside a `^!` fold block is left raw, so RTL text there will not be
  right-aligned by the RTL pass. The generated block also forces LTR on the
  assumption that folded content is code; if you fold prose instead, remove that
  one div in `md_color_gui.py` (and its end tag) - see
  [`docs/SPEC.md`](docs/SPEC.md) section 5.
- The default summary of a titleless fold is Persian (`DEFAULT_SUMMARY`). Change
  it in `md_color_gui.py` and `md_reverse_gui.py` together.
- The tool is deliberately marker-based, not a general Markdown parser. It does
  not understand nested lists inside fold blocks or setext headings.
- `reverse` can lose the blank line that followed a fold close, so `!^` ends up
  glued to the next block in the raw file. The markers still work: the RTL pass
  normalizes block spacing to exactly one blank line, which leaves `reverse` no
  spare blank to hand back. `examples/measure.py` reports this as a warning
  rather than hiding it.
- The unclosed-tag scan skips code fences but not inline code. A literal `<div>`
  written inside backticks in prose counts as a real open tag, so the run warns
  and emits an empty, greppable tag pair. Write it without the angle bracket.

---

## Roadmap

Next steps, in order:

- [x] `examples/` - a before/after sample plus the measurement script behind the
      token numbers above
- [ ] rendered screenshots of `examples/after.md` under the Example section
- [x] `RTL_RE` - right-to-left detection is now a documented top-of-file
      config, widened from Arabic-only to Hebrew plus every Arabic block
- [x] non-Windows fallback for replacing originals - the old copy becomes a
      unique `<name>.bak` and the run reports it as a warning
- [x] `docs/SPEC.md` - the marker grammar, split out from any personal style
- [x] present `rules.md` as one example preset under `docs/` - now
      `docs/MY_STYLE.md`
- [ ] `pytest` layout and CI on Windows plus Ubuntu

---

## License

MIT - see [`LICENSE`](LICENSE).
