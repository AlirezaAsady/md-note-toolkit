# md-note-toolkit

**English** | [فارسی](README.fa.md)

[![CI](https://github.com/AlirezaAsady/md-note-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/AlirezaAsady/md-note-toolkit/actions/workflows/ci.yml)

Write notes as plain Markdown with a few small markers, and turn them into a
styled, right-to-left note with one click - or back again.

Python standard library only, no pip install.

| raw file - what you or an AI writes | styled note - what you read |
|---|---|
| <img src="examples/img/section2-before.webp" width="420" alt="A note section written as plain Markdown with small markers"> | <img src="examples/img/section2-after.webp" width="420" alt="The same section rendered with colors, gloss tokens and right-to-left text"> |

- **A clean raw file:** plain Markdown plus tiny markers, easy to read, diff and hand to an AI.
- **A styled RTL note:** colors, folds, glosses and per-block text direction, generated for you.
- **A way back:** Reverse turns the styled note into the clean raw file again.

## Quick start

Step 1, and step 3 on Linux and macOS, need a terminal. Windows: press the Windows
key, type `cmd`, press Enter. macOS: Applications > Utilities > Terminal. Linux: Ctrl+Alt+T.

**1. Check Python.** Type `python --version` and press Enter (`python3` on Linux and
macOS). It worked if you see `Python 3.10` or a higher number. If Windows opens the
Microsoft Store instead, Python is not installed - read the box below.

<details>
<summary>I do not have Python</summary>

**Windows**

```bat
winget install Python.Python.3.12
```

If that fails (`winget` is missing on old builds), download the installer from
<https://www.python.org/downloads/windows/>, run it, and **tick the box
"Add python.exe to PATH"** on the first screen before clicking Install. The
installer already includes tkinter, the GUI library the windows use.

Close the terminal, open a new one, and run `python --version` again.

**Linux (Debian, Ubuntu, Mint)**

```bash
sudo apt install python3 python3-tk
python3 --version
```

The windows need `python3-tk`; Python alone is not enough. On other distros,
install Python plus your distro's Tk package for Python.

**macOS (Homebrew)**

```bash
brew install python
python3 --version
brew install python-tk@3.14
```

Homebrew ships tkinter separately. Use the same `3.x` number that
`python3 --version` printed, for example `python-tk@3.13`.

**Check the GUI library** on any system. A small test window should open:

```bash
python3 -m tkinter
```

Python 3.10 is the minimum because the code uses `Path | None` and `list[str]`
annotations. Tested on 3.10 and 3.14.

</details>

**2. Get the files.** Press the green **Code** button on this page, then **Download
ZIP**, and extract it, or run `git clone https://github.com/AlirezaAsady/md-note-toolkit.git`.
It worked if the folder holds `md_menu.cmd` and `md_batch_gui.py`.

**3. Start it.**

- **Windows:** double-click `md_menu.cmd`, type `1`, press Enter.
- **Linux / macOS** (the menu is Windows only): type `cd `, drag the folder onto the
  terminal, press Enter, then run `python3 md_batch_gui.py`.

It worked if a window titled **Markdown batch processor** opens. You never edit code
to point at the stylesheet: the default works, and if you move `md.css`, menu option 6
rewrites the path for you.

<details>
<summary>Windows warned me about the file</summary>

A `.cmd` that came from a download can raise **Open File - Security Warning**.
Right-click `md_menu.cmd`, choose **Properties**, tick **Unblock**, press OK, and
open it again. The file is a few lines of plain text - you can read it in
Notepad first if you prefer. No window opens at all? Python is not on `PATH`.

</details>

<details>
<summary>What the menu looks like</summary>

```
 ===========================================
   md-note-toolkit
 ===========================================
   1   Batch        several files, one window
   2   Color        markers -> HTML spans and folds
   3   RTL          wrap right-to-left blocks
   4   Color + RTL  opens both of the above
   5   Reverse      HTML -> markers again
   6   Stylesheet   set the CSS path in md_color_gui.py
   7   Shortcut     put this menu on the Windows desktop
   0   Exit
 ===========================================
```

</details>

**4. Give the rules to an AI.** Attach [`docs/MY_STYLE.md`](docs/MY_STYLE.md) and
[`docs/SPEC.md`](docs/SPEC.md) and ask it to write your note. You never write HTML. It
worked if the file has markers like `^^...^^` and no `<div>` or `<span>`.

<details>
<summary>Prompt you can paste</summary>

```text
Write a note about <TOPIC> for <WHAT YOU ALREADY KNOW>.
Follow the attached docs/SPEC.md and docs/MY_STYLE.md exactly.
Output only the Markdown source of the note, in one code block.
```

</details>

**5. Style the note.** In the window press **Add files** and pick the note. Leave
**Color + RTL** selected and press **Run batch**. It worked if the last log line starts
with `Summary: saved=1`. The old file went to the Recycle Bin (Windows) or was renamed
to `.bak` (Linux, macOS). **Reverse** brings the clean markers back.

Windows has no Recycle Bin for every location: a USB stick, a network share or a very
large file can be deleted for good. Work on a copy there, or untick **Replace original**
so the result is written next to the input.

That is the whole workflow: the AI writes markers, one window styles them, Reverse undoes it.

## The problem

| Missing in Markdown | What people do instead | Cost |
|---|---|---|
| per-block text direction | hand-written `<div dir="rtl">` | raw file becomes unreadable |
| colored emphasis | `<span style="...">` | inline styles, unmaintainable |
| collapsible sections | `<details>` + `<summary>` | 5 lines instead of 2 |
| second-language glosses | inline translation | layout breaks, tokens explode |

Persian, Arabic and Hebrew writers, and anyone taking bilingual notes, hit all four. This
toolkit keeps plain Markdown plus a few markers and generates the HTML.

> **The spec is the product; the scripts are the compiler.** Note quality comes
> from the style rules, not from the code. The code only makes applying them cheap.

## How it works

| Marker | Becomes | Use for |
|---|---|---|
| `^^text^^` | red span | warnings, errors, differences |
| `!!text!!` | highlighted span | key terms, definitions |
| `^!` ... `!^` | collapsible block | exercise answers, optional depth |
| `¹ word` | colored gloss token | short translation of a hard phrase |
| ```` ``` ```` | left untouched | fenced code is never processed |

- `^^` and `!!` open and close on one line, never nest, never go in headings or code.
- Use 2-3 of them per ~20 lines at most, or they stop meaning anything.
- `^!` and `!^` each stand alone on their own line. Text after `^!` becomes the title.
- A gloss token needs a space on both sides (`copy ¹ , no waiting`); its definition line starts with it in column 0.
- An odd number of `^^` or `!!` on a line is left as written and reported. The tool never guesses.

```
raw notes (markers)  --color-->  HTML spans + details  --rtl-->  styled RTL note
        ^                                                              |
        +------------------------- reverse ----------------------------+
```

Full grammar, the generated HTML and the round-trip rules: [`docs/SPEC.md`](docs/SPEC.md).

## Example gallery

The pair at the top is section 2 of [`examples/before.md`](examples/before.md)
(raw) and [`examples/after.md`](examples/after.md) (generated). GitHub strips the
stylesheet, so all images are local renders.

<details>
<summary>Section 3, and what a fold looks like</summary>

| before | after |
|---|---|
| <img src="examples/img/section3-before.webp" width="420" alt="Section 3 as raw markers"> | <img src="examples/img/section3-after.webp" width="420" alt="Section 3 rendered with a red warning span and a collapsible block"> |

</details>

<details>
<summary>Restyle it: change a class, or change the stylesheet</summary>

<img src="examples/img/section2-after-reclassed.webp" width="620" alt="Section 2 rendered after two class names were edited">

Two words were edited in the generated file: `class="hy"` became
`class="hy s26"`, and `class="r"` became `class="m"`. Nothing else moved. The
tool emits class names, never inline `style=""`, so the rendered file stays
editable. To recolor every note at once, edit [`md.css`](md.css) instead:

```css
.r {
  color: #c00000;            /* ^^text^^, was #ff0000 */
}
.hy {
  background-color: #ffe08a; /* !!text!!, was #ffff00 */
}
```

</details>

## Make it yours

The scripts never read your style; [`docs/MY_STYLE.md`](docs/MY_STYLE.md) tells the AI.
Its defaults: simple English (B2) explanations; Persian for questions, exercises, hard
points and `¹` glosses; fixed section names; at most 2-3 colored markers per section.

| I want... | Tell the AI... |
|---|---|
| more Persian paragraphs, English only for terms | "Write explanations in Persian. Keep technical terms and code comments in English." |
| another language pair or level | "Replace Persian with Arabic and B2 with C1." |
| less color, no glosses, other section names | "At most 1 marker per section." / "Do not use gloss tokens." / "Rename the sections to ..." |
| another right-to-left script | nothing - edit `RTL_PATTERN` in `md_rtl_advance_gui.py` (one constant, also a field in the RTL window) |
| a left-to-right language | nothing - choose **Color** instead of **Color + RTL** and keep colors, folds and glosses |

To change it: copy `docs/MY_STYLE.md`, edit the lines under `## Language` (or ask any AI
to rewrite them), then send your copy plus `docs/SPEC.md` with every note request. The
marker syntax is fixed. The style rules are free.

## Token savings

**The comparison that matters is not raw markers versus rendered HTML. It is the same AI
writing the same note twice.**

| the same note, written twice | with the rules attached | without them |
|---|---|---|
| what the AI types | `^^x^^`, `!!x!!`, `^!` … `!^`, `¹`, `$a^2+b^2$` | `<span class="f1 fm">x</span>`, `<div dir="rtl">`, `<details>` + `<summary>`, plus a `<style>` block defining those classes |
| what you keep and re-read | that marker file | that HTML file |
| what breaks | nothing - the tool opens and closes every tag | unclosed tags, silently lost RTL |

The rules do the saving; the toolkit only makes them cheap to keep. Without them the AI
still writes the HTML, and that HTML is the file you re-read in every later session.
Measured on a prose-heavy note the author wrote that way, before this toolkit existed:

| | characters |
|---|---|
| what the AI typed by hand | 27233 |
| of that, HTML markup instead of content | 12004 (44.1%) |
| the same note written with markers | 16517 |
| saved, on this write and on every re-read | 10716 (39.3%) |

**Which end of that range you are on is your note's shape, not the toolkit's.** A folder
of 34 SQL study notes measured **7 to 8 percent** and is the floor: fenced code and pipe
tables are 48% of those files and are byte-identical in both forms, so almost nothing in
them can be saved. The 39.3% note is not the ceiling either - the more color, folds,
glosses and formula spans a note carries, the more it saves.

**The rules are the fixed cost.** `docs/SPEC.md` is about 10,000 characters and
`docs/MY_STYLE.md` about 14,000. The AI needs both before it writes one marker, so for a
note of 3,000 characters the rules cost several times the note every time you attach
them. Putting them in your editor's project instructions or system prompt stops the
pasting and stops them drifting out of date; it does not stop them being sent. What the
markers save is the note itself, and that saving repeats on every later session.

<details>
<summary>Why it saves tokens</summary>

Four mechanisms, biggest first:

1. **Re-reading.** Generation is paid once; re-reading is paid every session.
   Reverse means you never keep HTML as your source.
2. **Safe editing.** One hand-written HTML note once had 13 unclosed
   `<div dir="ltr">` tags, and a whole exercises section silently lost its RTL.
   With markers there is no HTML to break. If a tag is still left open, the
   tool writes an empty, greppable tag pair instead of healing it silently:
   search `<div[^>]*>\s*\n</div>`.
3. **Glosses.** A `¹` plus two words costs a few tokens; a full translation
   costs 5 to 10 times more and breaks the layout.
4. **Short markers.** `^!` / `!^` instead of `<details>` + `<summary>`;
   `^^x^^` instead of `<span class="r">x</span>`.

</details>

<details>
<summary>What each tag and each span costs</summary>

Each row is the same formatting written both ways. The text you wrote is not in these
numbers - only the markup around it.

| as a marker | chars | as hand-written HTML | chars | saved each time |
|---|---|---|---|---|
| `!!term!!` | 8 | `<span class="hy">term</span>` | 28 | 20 |
| `$a^2+b^2$` | 9 | `<span class="f1 fm">a^2+b^2</span>` | 34 | 25 |
| `¹` | 1 | `<span class="p s22">¹</span>` | 28 | 27 |
| `^! Title` + `!^` | 11 | `<details dir="rtl">` + `<summary>` + `<div dir="ltr">` + 2 closes | 78 | 67 |
| nothing | 0 | `<div dir="rtl">` … `</div>` around a block | 23 | 23 |
| nothing | 0 | a `<style>` block defining the classes | 2820 | 2780 once |

`$a^2+b^2$` is the only row that is not a toolkit marker. `docs/MY_STYLE.md` allows KaTeX
math and the scripts pass it through untouched; the HTML column is what the AI typed for
that same formula before the rules existed.

The last two rows are what the tool takes off your hands: the marker file never types
them, and the rendered file gets them back on its own.

The 39.3% note carried **312 span pairs - 8092 characters of span tags, across 43
different class names.** One of them, `<span class="f1 fm">`, appeared 102 times at 27
characters each: 2754 characters for a single formatting decision, plus the 2820-character
`<style>` block written to define it. That class exists in neither `md.css` nor any script
in this repo - the AI invented it, and typing it 102 times is what the rules stop.

Four kinds of marker plus plain math in the marker file. Forty-three span class names in
the hand-written one.

</details>

<details>
<summary>Raw markers versus rendered output</summary>

The other comparison, the viewer's side of it, measured on
[`examples/before.md`](examples/before.md):

| | characters | lines |
|---|---|---|
| raw markers - what the AI writes and re-reads | 3086 | 87 |
| rendered output - what the viewer shows | 4229 | 170 |

The raw file is 1143 characters smaller, about 27 percent (stylesheet line excluded).
`examples/measure.py` counts characters and runs no tokenizer - the "about 285 tokens" it
prints is only the usual rule of thumb of about 4 English characters per token. Persian
needs more tokens per character than English, and every wrapper the tool adds is pure
ASCII, so the real token saving is smaller than the character saving.

</details>

<details>
<summary>What moves your number</summary>

The percentage tracks how many of these constructs a note uses per thousand characters,
not its length and not its language mix. What moves it:

- **Markers per KB.** More colors, folds and glosses mean more saving.
- **RTL blocks.** Each one gets a wrapper the raw file does not have.
- **Note size.** The fixed stylesheet line weighs more in a small note.
- **Persian share.** Persian usually costs more tokens per character than
  English, so in tokens it dilutes the percentage even when the characters
  saved are the same.
- **Tokenizer.** Any real tokenizer will do; they disagree with each other, so
  name the one you used next to the numbers.

Both ends above were measured on the author's own study notes. Only the summaries are
published; the notes themselves stay private.

</details>

Reproduce the single-file numbers with `python examples/measure.py`. It also checks that
`after.md` is real tool output and that Reverse gives the source back. It takes one file
today, so loop over your own folder to get your own number.

## Is it for you?

- **Yes, if** you write notes daily and want a raw file that stays readable, diffable and
  cheap for an AI to edit.
- **No, if** you need precise print layout, heavy math, or collaborators who expect Word.
  Word and PDF are better there.
- **GitHub only?** GitHub keeps `dir` and `details` when it renders Markdown, but drops the
  stylesheet link, so the colors do not show. You still get the clean raw file, the RTL
  wrappers and the fold markup. Check it once with your own gist before you rely on it.

## Reference

<details>
<summary>Command line and Python API</summary>

```bash
python md_batch.py forward "notes.md"          # color, then RTL
python md_batch.py reverse "notes.md"          # back to clean Markdown
python md_batch.py forward "a.md" "b.md"       # several files in one run
python md_batch.py color "notes.md" --new      # write notes.out.md, keep input
```

Modes: `reverse`, `color`, `rtl`, `forward` (= color then RTL). `--new` works
for single-step modes only and never overwrites an existing output. Exit codes:
`0` success, `1` one or more files failed, `2` invalid arguments.

```python
import md_batch
results = md_batch.run_batch(["a.md", "b.md"], mode="forward")
for r in results:
    print(r.source, r.status, r.warnings)
```

Each record has `source`, `destination`, `status` (`saved` / `unchanged` /
`error`), `warnings` and `error`. A failure never stops the remaining files.
An unchanged file is not rewritten, so its timestamp stays put.

Instructions written for an AI that drives the CLI: [`md_batch_ai.md`](md_batch_ai.md).

</details>

<details>
<summary>All settings</summary>

Every setting is a constant at the top of its script. The GUI windows pre-fill from
these constants. An empty value means the feature is off.

**Color - `md_color_gui.py`**

| Constant | Default | In the window | What it changes |
|---|---|---|---|
| `CSS_HREF` | `md.css` next to the script | - | stylesheet linked on line 1. Must be absolute: a viewer resolves it relative to the note. Menu option 6 rewrites it |
| `FOOT_ENABLED` | `True` | Color footnotes | off: `¹` tokens stay plain text |
| `FOOT_INLINE_CLASS` | `"p s22"` | - | classes of a token inside a sentence (purple) |
| `FOOT_DEF_CLASS` | `"g s22"` | - | classes of a token in column 0 (green) |
| `FOOT_OPEN` | `¹²³⁴⁵⁶⁷⁸⁹⁰` | - | characters that start a token; keep equal in `md_reverse_gui.py` |
| `DEFAULT_SUMMARY` | a Persian label | - | title of a fold with no title; keep equal in `md_reverse_gui.py` |
| `REPLACE_ORIGINAL` | `True` | Replace original | on: rewrite in place, old copy to the Recycle Bin. Off: write `notes.out.md` |
| `OUT_SUFFIX` | `".out.md"` | - | name of the new file when replace is off |

Headings and fenced code are always skipped. An existing `<span>` around a
token is left alone, so running twice is safe.

**RTL - `md_rtl_advance_gui.py`**

| Constant | Default | In the window | What it changes |
|---|---|---|---|
| `SMART_RTL` | `True` | checkbox | on: wrap only blocks that contain RTL text. Off: wrap every block |
| `RTL_PATTERN` | Hebrew + all Arabic blocks | field | which characters count as RTL. Never add Latin or CJK. `RTL_RE` is compiled from it |
| `HEADING_LEVELS` | `"1-6"` | field | heading levels always wrapped: `2-6`, `1,3-4`. Leading `^` or `-` means never |
| `HANDLE_HTML` | `True` | checkbox | copy hand-written HTML blocks unchanged and report unclosed tags |
| `AUTOCLOSE_HTML` | `True` | checkbox | after an unclosed tag, write an empty, greppable close tag |
| `HTML_TAGS` | `details, pre, table, div, script, style` | - | block tags that pass through unwrapped |
| `FOLD_OPEN`, `FOLD_CLOSE` | `^!`, `!^` | fields | fold marker lines, never wrapped |
| `HEAD_PATTERN` | the stylesheet `<link>` | field | first line kept outside every wrapper |
| `REPLACE_ORIGINAL` | `True` | checkbox | as above; off writes `notes.rtl.md` |
| `OUT_SUFFIX` | `".rtl.md"` | - | name of the new file when replace is off |

Blocks are split on blank lines, so a table or a list is never cut in half.

**Reverse - `md_reverse_gui.py`**

| Constant | Default | In the window | What it changes |
|---|---|---|---|
| `REVERSE_COLOR` | `True` | Color (spans, ^! blocks) | spans and folds back to markers |
| `RULES` | `"h=!!, *=^^"` | Rules | class to marker; first match wins, `*` is the fallback |
| `REMOVE_RTL` | `True` | RTL wrappers (all) | strip every `<div dir="rtl">` |
| `HEADINGS_ONLY` | `False` | RTL around headings only | keep prose wrappers, remove heading ones |
| `HEADING_LEVELS` | `"1-6"` | levels box | which levels count for the option above |
| `REMOVE_LINK` | `True` | Remove first-line `<link>` | drop the stylesheet line |
| `FOOT_CLASSES` | `("p", "g")` | - | span classes that are gloss tokens |
| `FOOT_OPEN`, `DEFAULT_SUMMARY` | as in Color | - | must match `md_color_gui.py` |

Replace original starts unticked here; the new file is `notes.raw.md`.

**Batch - `md_batch.py`, `md_batch_gui.py`**

| Constant | Default | In the window | What it changes |
|---|---|---|---|
| `DEFAULT_MODE` | `"forward"` | Operation | which mode starts selected; `forward` is shown as Color + RTL |
| `NEW_FILE` | `False` | Write to new file | keep the input, write `.raw.md` / `.out.md` / `.rtl.md`. Refused for `forward` and when an output would overwrite an input |
| `WINDOW_SIZE` | `"1000x720"` | - | start size of the batch window |

Batch uses the constants of the three scripts, not the checkboxes of an open
window. Importing any module opens nothing.

</details>

<details>
<summary>md_menu.cmd - what each option does</summary>

- Options 1-5 run `start pythonw` on the matching `.py` file in the same folder.
- Option 6 runs `md_menu_tools.py set-css`: it accepts only an absolute path to
  an existing `.css` file or an `http(s)://` / `file://` URL, rewrites the one
  `CSS_HREF =` line in `md_color_gui.py`, and keeps the old copy as `md_color_gui.py.bak`.
- Option 7 runs `md_menu_tools.py shortcut`: one desktop `.lnk` to the menu, nothing else.
- Neither option touches a file outside this folder or the network.
- No window opens? Python is not on `PATH`. Change `pythonw` to `python` on the
  launch lines and the error is shown instead of hidden.

</details>

<details>
<summary>Known limitations</summary>

- **Round trip.** Reverse gives back every content line in the same order. The
  one thing it can change is the blank line after a fold close: the RTL pass
  keeps exactly one blank between blocks, so `!^` can end up glued to the next
  block. The markers still work. `examples/measure.py` reports this as a warning.
- **Replacing the original** sends the old file to the Windows Recycle Bin. Some
  locations have no Recycle Bin for a given file (USB sticks, network shares, very
  large files) and Windows deletes it permanently. Keep **Replace original** off in
  those places, or pass `--new`, so the result is written beside the input.
- Outside Windows there is no Recycle Bin, so each replace leaves a backup:
  `notes.md.bak`, then `notes.md.bak.2`, and so on. Backups are never
  overwritten, so clear them out yourself. `*.bak` is gitignored.
- `RTL_PATTERN` includes Persian digits `U+06F0-U+06F9` (they sit in the Arabic
  block), so one stray Persian digit in an English paragraph forces that block
  RTL. The style rules forbid Persian digits for this reason.
- Text inside a `^!` fold is left raw, so the RTL pass does not wrap it. The
  fold also forces left-to-right on the assumption that it holds code. To fold
  prose, remove the `<div dir="ltr">` line and its `</div>` in `md_color_gui.py`.
  See [`docs/SPEC.md`](docs/SPEC.md) section 5.
- The default title of a fold with no title is Persian (`DEFAULT_SUMMARY`).
  Change it in `md_color_gui.py` and `md_reverse_gui.py` together.
- The tool is marker-based, not a full Markdown parser. It does not understand
  nested lists inside folds or setext headings.
- The unclosed-tag scan skips code fences but not inline code. A literal
  `<div>` inside backticks in prose counts as an open tag. Write it without the
  angle bracket.

</details>

<details>
<summary>Tests and CI</summary>

```bash
python -m pytest                  # or: python tests/test_md_batch.py
```

37 tests, standard library `unittest` cases that pytest also collects. No
downloads and no network; the suite builds its own scratch files and mocks the
Recycle Bin call. Every push to `main` runs it on Windows (Python 3.10 and
3.14) and on Ubuntu - see [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

`examples/after.md` is generated, never edited by hand. To regenerate it:

```bash
cp examples/before.md examples/after.md
python md_batch.py forward examples/after.md
```

Then set its stylesheet `href` to `../md.css`; the tool writes an absolute path
that only works on your machine.

</details>

<details>
<summary>Project layout</summary>

```
md_batch.py            headless CLI and batch engine (main entry point)
md_batch_gui.py        Tkinter window over the same engine
md_color_gui.py        markers -> HTML spans, details, gloss colors
md_rtl_advance_gui.py  RTL wrapping, smart mode, unclosed-tag detection
md_reverse_gui.py      HTML -> markers, removes RTL wrappers and link line
md_recycle.py          the one Recycle Bin call, shared by every script
md_menu.cmd            Windows number menu that opens any window
md_menu_tools.py       menu options 6 and 7: set CSS_HREF, desktop shortcut
md_batch_ai.md         compact CLI/API reference written for AI agents
md.css                 default stylesheet
docs/SPEC.md           marker grammar, generated HTML, round-trip contract
docs/MY_STYLE.md       one complete example style preset
examples/before.md     sample note as raw markers
examples/after.md      the same note after color + RTL
examples/measure.py    reproduces the numbers and checks the round trip
examples/img/          screenshots of the rendered example
tests/test_md_batch.py unittest suite, no external fixtures
pytest.ini             points pytest at tests/
.github/workflows/     CI: Windows and Ubuntu run the suite on every push
```

</details>

## License

MIT - see [`LICENSE`](LICENSE).
