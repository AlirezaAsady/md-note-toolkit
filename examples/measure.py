"""Reproduce the character numbers quoted in README.md.

Run from anywhere:  python examples/measure.py

It does three things, all in memory, using the same API the CLI uses:

1. counts characters in before.md (raw markers) and after.md (rendered HTML)
2. regenerates the artifact from before.md and compares it to the committed
   after.md, so the example cannot drift from the tool
3. runs reverse on the artifact and compares it to before.md, which is the
   round-trip promise: every content line comes back in order, though blank
   lines can drift - the script prints the exact diff either way

Stdlib only, like the rest of the toolkit.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

# Windows consoles default to a legacy code page that cannot print Persian.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import md_batch  # noqa: E402

BEFORE = HERE / "before.md"
AFTER = HERE / "after.md"
LINK_LINE = '<link rel="stylesheet"'


def strip_link(text):
    """Drop the stylesheet line: its href is machine specific by design."""
    return "\n".join(
        line for line in text.split("\n") if not line.startswith(LINK_LINE)
    ).lstrip("\n")


def report(label, ok, detail=""):
    mark = "OK  " if ok else "FAIL"
    print(f"  [{mark}] {label}{(' - ' + detail) if detail else ''}")
    return ok


def collapse_blanks(text):
    """Blank runs count as one blank, so editors cannot fail the check."""
    out = []
    for line in text.split("\n"):
        if not line.strip() and out and not out[-1].strip():
            continue
        out.append(line)
    return "\n".join(out)


def squash_blanks(text):
    """Keep only the content lines, so blank-line drift can be told apart."""
    return [line for line in text.split("\n") if line.strip()]


def main():
    raw = BEFORE.read_text(encoding="utf-8")
    rendered = strip_link(AFTER.read_text(encoding="utf-8"))

    print()
    print(f"  before.md  {len(raw):6d} chars  {raw.count(chr(10)) + 1:4d} lines"
          "   raw markers - what an AI writes, and re-reads")
    print(f"  after.md   {len(rendered):6d} chars  {rendered.count(chr(10)) + 1:4d} lines"
          "   rendered HTML - stylesheet line excluded")
    saved = len(rendered) - len(raw)
    pct = 100 * saved / len(rendered)
    print()
    print(f"  the source is {saved} chars ({pct:.0f}%) smaller than the artifact"
          f" - about {saved // 4} tokens")
    print("  paid once per generation, then again on every re-read")
    print()

    warnings = []
    generated = strip_link(md_batch.convert_file(BEFORE, raw, "forward", warnings))
    ok = report("after.md is real tool output",
                collapse_blanks(generated) == collapse_blanks(rendered),
                "" if collapse_blanks(generated) == collapse_blanks(rendered)
                else "regenerate it: see below")
    for text in warnings:
        print(f"         warning: {text}")

    warnings = []
    back = md_batch.reverse_text(generated, warnings)
    for text in warnings:
        print(f"         warning: {text}")

    exact = back.strip() == raw.strip()
    content = squash_blanks(back) == squash_blanks(raw)
    if exact:
        report("reverse(after.md) gives before.md back", True)
    else:
        if content:
            lost = raw.count("\n") - back.count("\n")
            print(f"  [WARN] reverse(after.md) keeps every content line, "
                  f"{lost} blank line(s) lost")
            print("         known gap: the RTL pass keeps exactly one blank line")
            print("         between blocks, so the spare blank a fold close")
            print("         relies on is gone and !^ ends up glued to the next")
            print("         block. Markers still work; the raw file only looks")
            print("         tighter than you wrote it.")
        else:
            ok = False
            report("reverse(after.md) gives before.md back", False,
                   "content differs")
        import difflib
        for line in difflib.unified_diff(
            raw.strip().split("\n"), back.strip().split("\n"),
            "before.md", "reverse(after.md)", lineterm="", n=1,
        ):
            print(f"         {line}")

    print()
    if not ok:
        print("  One check failed. Regenerate the artifact with:")
        print("      python md_batch.py forward examples/after.md")
        print("  then set its stylesheet href back to ../md.css")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
