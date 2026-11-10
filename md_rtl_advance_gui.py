import os
import re
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from md_recycle import to_recycle_bin

# Block-level HTML tags that must stay untouched (no RTL wrapping)
HTML_TAGS = ("details", "pre", "table", "div", "script", "style")
OPEN_RE = re.compile(r"<(?:%s)\b" % "|".join(HTML_TAGS), re.I)
CLOSE_RE = re.compile(r"</(?:%s)\s*>" % "|".join(HTML_TAGS), re.I)
# A collapsible block written as HTML by the color stage, its title line, and
# the LTR baseline the color stage puts inside it.
DETAILS_RE = re.compile(r"<details\b", re.I)
SUMMARY_RE = re.compile(r"<summary\b", re.I)
DIV_LTR_RE = re.compile(r'<div\s+dir="ltr"\s*>', re.I)

HANDLE_HTML = True

# A block tag that is never closed freezes html_depth, so the rest of the file
# stops being processed. When True, an empty close tag is inserted right after
# the offending open tag: the file keeps working and the broken spot stays
# searchable (e.g. <div dir="ltr"> on one line, </div> on the next).
AUTOCLOSE_HTML = True

# Head line kept outside the RTL div (regex, matched against the first line).
# Empty -> no head: RTL starts from the first line. Default = stylesheet link.
HEAD_PATTERN = r'^\s*<link\s+rel="stylesheet"'

# Fold markers that must pass through untouched (no RTL wrapping).
# Open marker may carry a short title on the same line; close marker stands alone.
FOLD_OPEN = ("^!",)  # e.g. "^!" or "^! My title"
FOLD_CLOSE = ("!^",)  # e.g. "!^"

# RTL skip sentinels: (open line, close line) pairs, exact match after strip.
# Everything between a closed pair passes the RTL wrapper untouched, like a
# code block; both sentinel lines stay in the output. Only comment-shaped
# strings are invisible in the render - any other string shows up as text.
# Empty list = feature off. An open sentinel with no close line warns, and the
# content after it is processed normally (only a closed pair skips).
RTL_SKIP = [("<!-- rtl-off -->", "<!-- /rtl-off -->")]

# True -> a fold body is processed like the rest of the file: RTL text groups
# get <div dir="rtl">, code fences and raw HTML stay untouched. The <div
# dir="ltr"> the color stage writes inside a fold is a direction baseline, not
# an opaque block, so the pass runs inside it too. False -> the whole fold
# passes through raw (old behaviour).
FOLD_BODY = True

# True -> only blank-line-separated groups holding right-to-left text get
# wrapped. False -> old behaviour: every text group is wrapped.
SMART_RTL = True

# Characters that count as right-to-left, i.e. the only thing smart mode uses to
# decide whether a group needs <div dir="rtl">. Ranges below, in order: Hebrew,
# Arabic (covers Persian پ چ ژ گ ک ی and Urdu, and Persian digits), Arabic
# Supplement, Arabic Extended-A, and the two Arabic Presentation Forms blocks
# (pre-shaped text pasted from PDFs or websites).
# Narrow it to r"[\u0600-\u06FF]" for Arabic-script only, or add any other RTL
# block you write in. Left-to-right scripts (Latin, CJK, Cyrillic, ...) must
# stay out: including them would wrap LTR text in an RTL div and break it.
# Watch out: Persian digits U+06F0-U+06F9 sit inside the Arabic block, so one
# stray Persian digit in an English paragraph forces that whole group RTL.
RTL_PATTERN = (
    r"[\u0590-\u05FF\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]"
)
RTL_RE = re.compile(RTL_PATTERN)

# Heading levels (1-6) that decide wrapping regardless of RTL text,
# e.g. "2-3" or "1,4" (mixing is fine: "1,3-4"). Empty -> feature off.
# Leading "-" or "^" inverts: those headings are never wrapped (stay LTR),
# even if they contain RTL text. Invalid parts and levels outside 1-6 are
# silently ignored, so "0-10" means "all headings". Only affects smart mode.
HEADING_LEVELS = "1-6"

# Output file suffix: notes.md -> notes.rtl.md (same folder). Used only when the
# "Replace original" box is OFF; when it is ON the result takes the input's name.
OUT_SUFFIX = ".rtl.md"

# Replace original: send the input file to the Recycle Bin (recoverable) and
# write the result to its name. Default True -> the checkbox starts ticked.
REPLACE_ORIGINAL = True

# ATX heading: starts with 1-6 '#' (leading spaces allowed). Setext headings
# (=== / --- under a line) are NOT matched — a bare --- is a separator.
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:\s|$)")

# ---------- بخش منطق ----------


def has_text(text_lines):
    # فقط وقتی True است که حداقل یک خط واقعاً متن داشته باشد
    return any(line.strip() for line in text_lines)


def wrap_text(text_lines):
    # متن را بین تگ باز و بسته‌ی div راست‌چین می‌گذارد
    return ['<div dir="rtl">', "", *text_lines, "", "</div>", ""]


def has_rtl_text(lines, rtl_re=RTL_RE):
    return any(rtl_re.search(line) for line in lines)


def parse_levels(text):
    # Optional leading "-" or "^" -> invert mode (these headings are never wrapped).
    # "2-3" / "1,4" / "1,3-4" -> set of levels; junk ignored, clamped to 1-6.
    text = text.strip()
    exclude = text[:1] in ("-", "^")
    if exclude:
        text = text[1:]
    levels = set()
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", part)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            if lo > hi:
                lo, hi = hi, lo  # "4-2" works like "2-4"
            levels.update(range(lo, hi + 1))
        elif part.isdigit():
            levels.add(int(part))
    return exclude, {n for n in levels if 1 <= n <= 6}


def heading_match(group, levels):
    # True if the group's first line is an ATX heading with a wanted level
    if not levels:
        return False
    m = HEADING_RE.match(group[0].strip())
    return bool(m) and len(m.group(1)) in levels


def emit_group(group, output, levels, exclude=False, rtl_re=RTL_RE):
    # One blank-line-separated block. Invert mode (exclude): a heading whose
    # level is in `levels` is emitted raw — no wrapper at all, even if RTL.
    # Normal mode: wrap if the group holds RTL text or such a heading.
    if exclude:
        if heading_match(group, levels):
            output.extend(group)
        elif has_rtl_text(group, rtl_re):
            output.extend(wrap_text(group))
        else:
            output.extend(group)
        return
    if has_rtl_text(group, rtl_re) or heading_match(group, levels):
        output.extend(wrap_text(group))
    else:
        output.extend(group)


def flush(text_lines, output, smart=False, levels=(), exclude=False, rtl_re=RTL_RE):
    if not smart:
        # Wrap collected text if it has content, otherwise copy as is
        if has_text(text_lines):
            output.extend(wrap_text(text_lines))
        else:
            output.extend(text_lines)
        return
    # Split on blank lines so a table or list is never cut in half
    group = []
    for line in text_lines:
        if line.strip():
            group.append(line)
            continue
        if group:
            emit_group(group, output, levels, exclude, rtl_re)
            group = []
        if output and output[-1] != "":
            output.append("")  # keep exactly one blank line between blocks
    if group:
        emit_group(group, output, levels, exclude, rtl_re)


def parse_markers(text):
    # Comma-separated box text -> tuple of markers; empty -> ()
    return tuple(part.strip() for part in text.split(",") if part.strip())


def parse_skip_pairs(text):
    # Box text "open => close, open2 => close2" -> tuple of (open, close)
    # pairs. Empty -> () = feature off; junk parts are ignored like elsewhere.
    pairs = []
    for part in text.split(","):
        if "=>" not in part:
            continue
        open_s, close_s = (x.strip() for x in part.split("=>", 1))
        if open_s and close_s:
            pairs.append((open_s, close_s))
    return tuple(pairs)


def find_unclosed(lines, handle_html, fold_open, fold_close, skip_pairs=()):
    # Pass 1 -> {line index: [tag names opened there and never closed]}
    stack = []
    unclosed = {}
    inside_code = False
    inside_fold = False
    skip_close = None  # close sentinel of the skip block being passed over

    def drop(idx, name):
        unclosed.setdefault(idx, []).append(name)

    for idx, line in enumerate(lines):
        s = line.strip()
        if skip_close is not None:
            if s == skip_close:
                skip_close = None
            continue
        if inside_fold:
            if s in fold_close:
                inside_fold = False
            continue
        if s.startswith("```"):
            inside_code = not inside_code
            continue
        if inside_code or not handle_html:
            continue
        for open_s, close_s in skip_pairs:
            if s == open_s and any(
                lines[j].strip() == close_s for j in range(idx + 1, len(lines))
            ):
                skip_close = close_s  # a closed pair is opaque, like a fence
                break
        if skip_close is not None:
            continue
        if s in fold_close or s.startswith(fold_open):
            inside_fold = True
            continue
        if not (stack or (s.startswith("<") and OPEN_RE.match(s))):
            continue
        for tag in OPEN_RE.findall(line):
            stack.append((tag[1:].lower(), idx))
        for tag in CLOSE_RE.findall(line):
            name = tag[2:-1].strip().lower()
            for j in range(len(stack) - 1, -1, -1):
                if stack[j][0] == name:
                    for inner_name, inner_idx in stack[j + 1 :]:
                        drop(inner_idx, inner_name)  # closed by an outer tag
                    del stack[j:]
                    break
    for name, idx in stack:
        drop(idx, name)  # never closed at all
    return unclosed


def find_fold_close(lines, start, fold_open, fold_close):
    # Index of the line closing the marker fold opened at `start`, or None.
    # Nested folds are counted and code fences are skipped, so a close marker
    # sitting inside a fence cannot end the block.
    depth, fence = 0, False
    for i in range(start, len(lines)):
        s = lines[i].strip()
        if s.startswith("```"):
            fence = not fence
        elif not fence:
            if fold_open and s.startswith(fold_open):
                depth += 1
            elif s in fold_close:
                depth -= 1
                if depth == 0:
                    return i
    return None


def find_tag_close(lines, start, name):
    # Index of the line closing the HTML tag opened at `start`, or None.
    open_re = re.compile(rf"<{name}\b", re.I)
    close_re = re.compile(rf"</{name}\s*>", re.I)
    depth, fence = 0, False
    for i in range(start, len(lines)):
        s = lines[i].strip()
        if s.startswith("```"):
            fence = not fence
        elif not fence:
            depth += len(open_re.findall(lines[i])) - len(close_re.findall(lines[i]))
            if depth <= 0:
                return i
    return None


def flush_keep_blanks(text_lines, output, smart, levels, exclude, rtl_re):
    # Inside a fold the blank lines are structural: the reverse tool matches
    # them. An all-blank run is copied instead of being normalised away.
    if text_lines and not has_text(text_lines):
        output.extend(text_lines)
    else:
        flush(text_lines, output, smart, levels, exclude, rtl_re)


def wrap_lines(lines, smart, levels, exclude, rtl_re, handle_html, autoclose,
               fold_open, fold_close, fold_body, in_fold=False, skip_pairs=()):
    # The wrapping state machine, reused for the whole file and for every fold
    # body. Returns (output lines, stats); stats carries the unclosed-tag count,
    # the HTML depth left open and the unclosed-fold flag so the caller reports
    # them once for the whole file.
    unclosed = find_unclosed(lines, handle_html, fold_open, fold_close, skip_pairs)
    stats = {"unclosed": sum(len(v) for v in unclosed.values()), "depth": 0,
             "fold": False, "skip": 0}
    out, text = [], []
    inside_code, html_depth = False, 0
    inside_fold = False  # fold_body off: the whole block stays raw, as before
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if inside_fold:
            out.append(line)
            if s in fold_close:
                inside_fold = False
            i += 1
            continue
        if s.startswith("```"):  # fence (open or close)
            flush_keep_blanks(text, out, smart, levels, exclude, rtl_re)
            text = []
            inside_code = not inside_code
            out.append(line)
            i += 1
            continue
        if inside_code:  # must come before the HTML check
            out.append(line)
            i += 1
            continue
        skipped = False
        for open_s, close_s in skip_pairs:
            if s != open_s:
                continue
            end = next(
                (j for j in range(i + 1, len(lines)) if lines[j].strip() == close_s),
                None,
            )
            if end is None:
                # No close line: warn once, then process normally - only a
                # closed pair skips. The open line itself is just a comment.
                stats["skip"] += 1
            else:
                flush_keep_blanks(text, out, smart, levels, exclude, rtl_re)
                text = []
                out.append(line)
                out.extend(lines[i + 1:end])  # verbatim, like a code block
                out.append(lines[end])
                i = end + 1
                skipped = True
            break
        if skipped:
            continue
        end = None
        if not html_depth:
            if fold_body and fold_open and s.startswith(fold_open):
                end = find_fold_close(lines, i, fold_open, fold_close)
                if end is None:  # no close marker: the rest stays raw
                    flush_keep_blanks(text, out, smart, levels, exclude, rtl_re)
                    out.append(line)
                    out.extend(lines[i + 1:])
                    stats["fold"] = True
                    return out, stats
            elif fold_body and handle_html and DETAILS_RE.match(s):
                end = find_tag_close(lines, i, "details")
                # None -> falls through to the HTML branch, raw and auto-closed
            elif in_fold and handle_html and DIV_LTR_RE.match(s):
                end = find_tag_close(lines, i, "div")
        if end is not None:
            flush_keep_blanks(text, out, smart, levels, exclude, rtl_re)
            text = []
            body = lines[i + 1:end]
            lead = 0
            while lead < len(body) and not body[lead].strip():
                lead += 1
            tail = len(body)
            while tail > lead and not body[tail - 1].strip():
                tail -= 1
            inner, inner_stats = wrap_lines(
                body[lead:tail], smart, levels, exclude, rtl_re, handle_html,
                autoclose, fold_open, fold_close, fold_body, True, skip_pairs,
            )
            out.append(line)
            out.extend(body[:lead])
            if tail < len(body) and inner and inner[-1] == "":
                inner = inner[:-1]  # the structural blank already separates
            out.extend(inner)
            out.extend(body[tail:])
            out.append(lines[end])
            stats["unclosed"] += inner_stats["unclosed"]
            stats["depth"] += inner_stats["depth"]
            stats["fold"] = stats["fold"] or inner_stats["fold"]
            stats["skip"] += inner_stats["skip"]
            i = end + 1
            continue
        if handle_html and (
            html_depth > 0 or (s.startswith("<") and OPEN_RE.match(s))
        ):
            flush_keep_blanks(text, out, smart, levels, exclude, rtl_re)
            text = []
            html_depth += len(OPEN_RE.findall(line)) - len(CLOSE_RE.findall(line))
            html_depth = max(html_depth, 0)
            out.append(line)
            if autoclose:
                # empty tag right after the open one: searchable failure marker
                for name in reversed(unclosed.get(i, ())):
                    out.append(f"</{name}>")
                    html_depth = max(html_depth - 1, 0)
            i += 1
            continue
        if in_fold and SUMMARY_RE.match(s):
            # the title line is never text: wrapping it would break the exact
            # header the reverse tool matches
            flush_keep_blanks(text, out, smart, levels, exclude, rtl_re)
            text = []
            out.append(line)
            i += 1
            continue
        if s in fold_close or (fold_open and s.startswith(fold_open)):
            flush_keep_blanks(text, out, smart, levels, exclude, rtl_re)
            text = []
            out.append(line)
            inside_fold = True
            i += 1
            continue
        text.append(line)
        i += 1

    flush_keep_blanks(text, out, smart, levels, exclude, rtl_re)
    stats["depth"] = html_depth
    stats["fold"] = stats["fold"] or inside_fold
    return out, stats


def process_file(
    path,
    log=None,
    handle_html=None,
    fold_open=None,
    fold_close=None,
    head_pattern=None,
    smart=None,
    autoclose=None,
    heading_levels=None,
    rtl_pattern=None,
    fold_body=None,
    skip_pairs=None,
):
    # Reads `path`, applies the RTL wrapping and RETURNS (text, warnings).
    # text is the whole result in the SOURCE file's line ending (LF or CRLF),
    # or None when there is nothing to do (already fixed). warnings is a list
    # of bare messages (no "Warning:" prefix) so the batch tool can flag files.
    # log is an optional one-arg callback for progress; None -> silent no-op,
    # so process_file(path) works on its own. Config None -> top-of-file default.
    if log is None:
        log = lambda *_: None  # noqa: E731
    handle_html = HANDLE_HTML if handle_html is None else handle_html
    head_pattern = HEAD_PATTERN if head_pattern is None else head_pattern
    fold_open = FOLD_OPEN if fold_open is None else fold_open
    fold_close = FOLD_CLOSE if fold_close is None else fold_close
    smart = SMART_RTL if smart is None else smart
    autoclose = AUTOCLOSE_HTML if autoclose is None else autoclose
    heading_levels = HEADING_LEVELS if heading_levels is None else heading_levels
    rtl_pattern = RTL_PATTERN if rtl_pattern is None else rtl_pattern
    fold_body = FOLD_BODY if fold_body is None else fold_body
    skip_pairs = RTL_SKIP if skip_pairs is None else skip_pairs
    exclude, levels = parse_levels(heading_levels)
    # Empty value disables the feature
    fold_open = tuple(fold_open) if fold_open else ()
    fold_close = tuple(fold_close) if fold_close else ()
    warnings = []
    # Which characters count as right-to-left. Only consulted in smart mode, so
    # no warning noise when smart is off. A bad or empty pattern never stops the
    # run: it falls back to the default range and says so.
    rtl_re = RTL_RE
    if smart:
        if rtl_pattern:
            try:
                rtl_re = re.compile(rtl_pattern)
            except re.error as e:
                warnings.append(f"Invalid RTL pattern: {e} - using the default range")
        else:
            warnings.append("Empty RTL pattern - using the default range")
    # فایل را می‌خواند (newline="" تا EOL واقعی منبع دیده و حفظ شود)
    log(f"Markdown file path: {path}")
    with open(path, encoding="utf-8", newline="") as f:
        raw = f.read()
    eol = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.splitlines()

    # Split off the head line (regex, kept outside the RTL div)
    head = []
    head_re = None
    if head_pattern:
        try:
            head_re = re.compile(head_pattern, re.I)
        except re.error as e:
            warnings.append(f"Invalid head pattern: {e}")
    if head_re and lines and head_re.match(lines[0]):
        head = [lines[0], ""]  # head + exactly one blank line
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]

    # اگر از قبل راست‌چین است، متوقف می‌شود.
    # Whole-file check (not just line 1): in invert mode the first heading
    # stays bare, and in smart mode an English intro may come before any div.
    # Skipped when heading levels are set: re-running to restyle headings of
    # an already-processed file is intentional and safe — existing wrappers
    # pass through as HTML blocks, so nothing is wrapped twice.
    if not levels and any(line.strip() == '<div dir="rtl">' for line in lines):
        log("Already fixed. Nothing to do.")
        return None, warnings

    output, stats = wrap_lines(
        lines, smart, levels, exclude, rtl_re, handle_html, autoclose,
        fold_open, fold_close, fold_body, skip_pairs=skip_pairs,
    )
    if stats["depth"] > 0:
        warnings.append(f"Unclosed HTML block (depth = {stats['depth']}).")
    if stats["unclosed"]:
        tail = " Auto-closed with an empty tag." if autoclose else ""
        warnings.append(f"{stats['unclosed']} unclosed HTML tag(s) found.{tail}")
    if stats["fold"]:
        warnings.append("Unclosed fold block (no close marker found).")
    if stats["skip"]:
        warnings.append(
            f"{stats['skip']} unclosed RTL skip sentinel(s); "
            "content after them processed normally."
        )

    output = head + output
    return eol.join(output) + eol, warnings


# ---------- یاری‌های فایل ----------


def default_out(src):
    # notes.md -> notes.rtl.md (same folder)
    return Path(src).with_name(Path(src).stem + OUT_SUFFIX)


def retire_original(src):
    # فایل اصلی را قبل از نشستن نتیجه روی نامش کنار می برد.
    # در ویندوز به سطل آشغال میرود. در بقیه سیستم ها API سطل آشغال وجود ندارد،
    # پس نامش به <name>.bak عوض میشود که هنوز قابل بازیابی است.
    # خروجی: مسیر فایل پشتیبان، یا None وقتی سطل آشغال استفاده شد.
    if os.name == "nt":
        to_recycle_bin(src)
        return None
    src = Path(src)
    bak = Path(f"{src}.bak")
    n = 2
    while bak.exists():
        bak = Path(f"{src}.bak.{n}")
        n += 1
    src.rename(bak)
    return bak


# ---------- بخش پنجره ----------


def main():
    root = tk.Tk()
    root.title("راست‌چین مارک‌داون")
    root.geometry("700x760")
    root.minsize(620, 680)

    path_var = tk.StringVar()  # مسیر فایل ورودی (از مرورگر یا تایپ دستی)
    out_var = tk.StringVar()  # مسیر فایل خروجی (وقتی جایگزینی خاموش است)

    # تنظیمات پردازش (مقدار پیش‌فرض از بالای فایل گرفته می‌شود)
    smart_var = tk.BooleanVar(value=SMART_RTL)
    handle_html_var = tk.BooleanVar(value=HANDLE_HTML)
    autoclose_var = tk.BooleanVar(value=AUTOCLOSE_HTML)
    head_var = tk.StringVar(value=HEAD_PATTERN)
    fold_open_var = tk.StringVar(value=", ".join(FOLD_OPEN))
    fold_close_var = tk.StringVar(value=", ".join(FOLD_CLOSE))
    fold_body_var = tk.BooleanVar(value=FOLD_BODY)
    heading_var = tk.StringVar(value=HEADING_LEVELS)
    rtl_var = tk.StringVar(value=RTL_PATTERN)
    skip_var = tk.StringVar(
        value=", ".join(f"{o} => {c}" for o, c in RTL_SKIP)
    )
    replace_var = tk.BooleanVar(value=REPLACE_ORIGINAL)

    def get_path():
        # مسیر ورودی را تمیز می‌کند: فاصله و گیومه‌ی دورش را برمی‌دارد
        return path_var.get().strip().strip('"')

    def get_out_path():
        # مسیر خروجی را تمیز می‌کند
        return out_var.get().strip().strip('"')

    def update_buttons(*args):
        # دکمه‌ها فقط وقتی فعال‌اند که مسیر ورودی به یک فایل واقعی اشاره کند
        state = "normal" if os.path.isfile(get_path()) else "disabled"
        convert_btn.config(state=state)
        folder_btn.config(state=state)

    def write_log(message):
        # یک خط به کادر لاگ اضافه می‌کند و به آخرش اسکرول می‌کند
        log_box.config(state="normal")
        log_box.insert("end", message + "\n")
        log_box.see("end")
        log_box.config(state="disabled")
        root.update_idletasks()

    def set_input(path):
        # مسیر ورودی را می‌گذارد و مسیر خروجی پیش‌فرض را از روی آن می‌سازد
        path = os.path.normpath(path)
        path_var.set(path)
        out_var.set(str(default_out(path)))

    def choose_file():
        # پنجره‌ی انتخاب فایل را باز می‌کند
        path = filedialog.askopenfilename(
            title="انتخاب فایل مارک‌داون",
            filetypes=[("Markdown", "*.md"), ("همه‌ی فایل‌ها", "*.*")],
        )
        if path:
            set_input(path)
            write_log(f"فایل انتخاب شد: {path_var.get()}")

    def paste_path():
        # Read the first line of the clipboard into the path box
        try:
            text = root.clipboard_get().strip()
        except tk.TclError:
            write_log("کلیپ‌بورد خالی است یا متن نیست.")
            return
        first = text.splitlines()[0] if text else ""
        if os.path.isfile(first.strip().strip('"')):
            set_input(first)
            write_log(f"مسیر چسبانده شد: {get_path()}")
        else:
            path_var.set(first)
            write_log("مسیر چسبانده‌شده فایل معتبر نیست.")

    def save_result(src_s, text):
        # نتیجه را روی دیسک می‌برد: جایگزینی (سطل آشغال + نام اصلی) یا خروجی جدا
        src = Path(src_s)
        tmp = None
        try:
            if replace_var.get():
                # ترتیب امن: نوشتن temp -> سطل آشغال رفتن اصلی -> تغییر نام temp
                tmp = src.with_name(src.name + ".tmp")
                with open(tmp, "w", encoding="utf-8", newline="") as f:
                    f.write(text)
                bak = retire_original(src)
                os.replace(tmp, src)
                tmp = None
                if bak is None:
                    write_log(f"جایگزین شد: {src} (فایل قبلی در سطل آشغال است)")
                else:
                    write_log(f"جایگزین شد: {src}")
                    write_log(f"فایل قبلی نگه داشته شد: {bak}")
            else:
                dst_s = get_out_path()
                if not dst_s:
                    raise ValueError("مسیر خروجی خالی است")
                dst = Path(dst_s)
                if dst.resolve() == src.resolve():
                    raise ValueError(
                        "خروجی همان ورودی است؛ گزینه‌ی جایگزینی را فعال کن"
                    )
                with open(dst, "w", encoding="utf-8", newline="") as f:
                    f.write(text)
                write_log(f"ذخیره شد: {dst}")
            write_log("انجام شد.")
        except (OSError, ValueError) as e:
            write_log(f"خطا: {e}")
            if tmp and tmp.exists():
                tmp.unlink()  # پاک کردن فایل موقت

    def convert():
        # منطق اصلی را اجرا می‌کند و نتیجه را ذخیره می‌کند
        src = get_path()
        if not os.path.isfile(src):
            write_log("فایل ورودی معتبر نیست.")
            return
        try:
            text, warnings = process_file(
                src,
                write_log,
                smart=smart_var.get(),
                handle_html=handle_html_var.get(),
                autoclose=autoclose_var.get(),
                head_pattern=head_var.get().strip(),
                fold_open=parse_markers(fold_open_var.get()),
                fold_close=parse_markers(fold_close_var.get()),
                fold_body=fold_body_var.get(),
                heading_levels=heading_var.get().strip(),
                rtl_pattern=rtl_var.get().strip(),
                skip_pairs=parse_skip_pairs(skip_var.get()),
            )
        except Exception as e:
            write_log(f"خطا: {e}")
            return
        for w in warnings:
            write_log("Warning: " + w)
        if text is None:  # nothing to do (already fixed) — already logged
            return
        save_result(src, text)

    def open_folder():
        # پوشه را باز می‌کند و خود فایل را در آن انتخاب‌شده نشان می‌دهد
        target = get_path() if os.path.isfile(get_path()) else get_out_path()
        subprocess.Popen(["explorer", f"/select,{os.path.normpath(target)}"])

    # ---------- کادر تنظیمات ----------
    settings = ttk.LabelFrame(root, text="تنظیمات پردازش", padding=10)
    settings.pack(fill="x", padx=12, pady=(12, 0))
    settings.columnconfigure(0, weight=1)
    settings.columnconfigure(1, weight=1)

    # ردیف 0 و 1: سه گزینه روشن/خاموش، بدون لیبل سرگردان در ستون کنارشان
    ttk.Checkbutton(
        settings, text="راست‌چین هوشمند (فقط بخش‌های RTL)", variable=smart_var
    ).grid(row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 4))
    ttk.Checkbutton(
        settings, text="پردازش تگ‌های HTML (خارج از div)", variable=handle_html_var
    ).grid(row=0, column=1, sticky="w", padx=(6, 0), pady=(0, 4))
    ttk.Checkbutton(
        settings, text="بستن خودکار تگ بی‌بسته (قابل جست‌وجو)", variable=autoclose_var
    ).grid(row=1, column=0, sticky="w", padx=(0, 6), pady=(0, 8))
    ttk.Checkbutton(
        settings, text="پردازش بدنه‌ی بلوک تاشو (کد خام می‌ماند)", variable=fold_body_var
    ).grid(row=1, column=1, sticky="w", padx=(6, 0), pady=(0, 8))

    # ردیف 2: دکمه‌ی باز و بسته کردن الگوها. این فیلدها سطح‌بالایی‌اند و کاربر عادی
    # هیچ‌وقت آن‌ها را تغییر نمی‌دهد، پس پیش‌فرض بسته‌اند تا فرم کوتاه بماند.
    PATTERNS_SHOW = "+ الگوها (regex) - تنظیمات سطح‌بالایی"
    PATTERNS_HIDE = "- الگوها (regex) - بستن"
    patterns_open = tk.BooleanVar(value=False)

    def toggle_patterns():
        if patterns_open.get():  # باز است -> بسته شود
            patterns.grid_forget()
            patterns_open.set(False)
            toggle_btn.config(text=PATTERNS_SHOW)
        else:  # بسته است -> باز شود
            patterns.grid(row=3, column=0, columnspan=2, sticky="ew")
            patterns_open.set(True)
            toggle_btn.config(text=PATTERNS_HIDE)

    toggle_btn = ttk.Button(settings, text=PATTERNS_SHOW, command=toggle_patterns)
    toggle_btn.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 4))

    # قاعده چیدمان: لیبل هر فیلد دقیقاً بالای همان فیلد، تا چشم دنبال لیبلِ ستون
    # روبرو نگردد. کادر وقتی بسته است اصلاً در grid نیست، پس جایی اشغال نمی‌کند.
    patterns = ttk.Frame(settings, padding=(4, 6, 4, 2))
    patterns.columnconfigure(0, weight=1)
    patterns.columnconfigure(1, weight=1)

    ttk.Label(
        patterns,
        text="کاراکترهای راست به چپ - فقط در حالت هوشمند؛ خالی یا خطا = همان پیش فرض",
    ).grid(row=0, column=0, columnspan=2, sticky="w")
    ttk.Entry(patterns, textvariable=rtl_var).grid(
        row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8)
    )

    ttk.Label(patterns, text="الگوی سرصفحه (خالی = غیرفعال)").grid(
        row=2, column=0, columnspan=2, sticky="w"
    )
    ttk.Entry(patterns, textvariable=head_var).grid(
        row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8)
    )

    ttk.Label(patterns, text="شروع بلوک تاشو").grid(
        row=4, column=0, sticky="w", padx=(0, 6)
    )
    ttk.Label(patterns, text="پایان بلوک تاشو").grid(
        row=4, column=1, sticky="w", padx=(6, 0)
    )
    ttk.Entry(patterns, textvariable=fold_open_var).grid(
        row=5, column=0, sticky="ew", padx=(0, 6)
    )
    ttk.Entry(patterns, textvariable=fold_close_var).grid(
        row=5, column=1, sticky="ew", padx=(6, 0)
    )

    ttk.Label(
        patterns,
        text="نگهبان‌های رد شدن از رپر: باز => بسته | جفت‌ها با کاما | خالی = خاموش",
    ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 0))
    ttk.Entry(patterns, textvariable=skip_var).grid(
        row=7, column=0, columnspan=2, sticky="ew", pady=(0, 4)
    )

    # ردیف 4 و 5: سطح عنوان‌هایی که همیشه wrap می‌شوند (فقط حالت هوشمند).
    # این فیلد بیرون از کادر تاشو می‌ماند: کاربر واقعاً با آن کار دارد.
    ttk.Label(
        settings,
        text="سطح عنوان‌ها: 2-6 = همیشه راست‌چین | ^2-6 یا -2-6 = هرگز (چپ‌چین) | خالی = خاموش",
    ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))
    ttk.Entry(settings, textvariable=heading_var).grid(
        row=5, column=0, columnspan=2, sticky="ew"
    )

    # چیدمان پنجره
    frame = ttk.Frame(root, padding=12)
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)
    frame.rowconfigure(7, weight=1)

    ttk.Label(
        frame, text="مسیر فایل ورودی (تایپ یا جای‌گذاری کن، یا انتخاب فایل را بزن):"
    ).grid(row=0, column=0, columnspan=2, sticky="w")

    # کادر مسیر ورودی قابل ویرایش است
    path_entry = ttk.Entry(frame, textvariable=path_var)
    path_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 6))

    ttk.Button(frame, text="انتخاب فایل", command=choose_file).grid(
        row=2, column=0, sticky="ew", padx=(0, 3), pady=(0, 6)
    )
    ttk.Button(frame, text="چسباندن مسیر (Paste Path)", command=paste_path).grid(
        row=2, column=1, sticky="ew", padx=(3, 0), pady=(0, 6)
    )

    # مسیر خروجی (فقط وقتی جایگزینی خاموش است استفاده می‌شود)
    ttk.Label(frame, text="مسیر فایل خروجی (وقتی «جایگزینی» خاموش است):").grid(
        row=3, column=0, columnspan=2, sticky="w"
    )
    out_entry = ttk.Entry(frame, textvariable=out_var)
    out_entry.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(2, 6))

    # چک‌باکس جایگزینی (پیش‌فرض فعال): فایل قبلی به سطل آشغال می‌رود
    ttk.Checkbutton(
        frame,
        text="جایگزین کردن فایل قبلی (اصلی به سطل آشغال می‌رود)",
        variable=replace_var,
    ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 6))

    folder_btn = ttk.Button(
        frame, text="باز کردن پوشه", command=open_folder, state="disabled"
    )
    folder_btn.grid(row=6, column=0, sticky="ew", padx=(0, 3))

    convert_btn = ttk.Button(frame, text="تبدیل", command=convert, state="disabled")
    convert_btn.grid(row=6, column=1, sticky="ew", padx=(3, 0))

    # هر بار متن کادر مسیر عوض شد، وضعیت دکمه‌ها دوباره بررسی می‌شود
    path_var.trace_add("write", update_buttons)

    # کادر لاگ با اسکرول
    log_frame = ttk.Frame(frame)
    log_frame.grid(row=7, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
    log_frame.columnconfigure(0, weight=1)
    log_frame.rowconfigure(0, weight=1)

    log_box = tk.Text(log_frame, height=8, state="disabled", wrap="word")
    log_box.grid(row=0, column=0, sticky="nsew")

    scrollbar = ttk.Scrollbar(log_frame, command=log_box.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    log_box.config(yscrollcommand=scrollbar.set)

    root.mainloop()


if __name__ == "__main__":
    main()
