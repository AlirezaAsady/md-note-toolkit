import ctypes
import os
import re
import subprocess
import tkinter as tk
from ctypes import wintypes
from pathlib import Path
from tkinter import filedialog, ttk

# Block-level HTML tags that must stay untouched (no RTL wrapping)
HTML_TAGS = ("details", "pre", "table", "div", "script", "style")
OPEN_RE = re.compile(r"<(?:%s)\b" % "|".join(HTML_TAGS), re.I)
CLOSE_RE = re.compile(r"</(?:%s)\s*>" % "|".join(HTML_TAGS), re.I)

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
RTL_RE = re.compile(
    r"[\u0590-\u05FF\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]"
)

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


def has_rtl_text(lines):
    return any(RTL_RE.search(line) for line in lines)


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


def emit_group(group, output, levels, exclude=False):
    # One blank-line-separated block. Invert mode (exclude): a heading whose
    # level is in `levels` is emitted raw — no wrapper at all, even if RTL.
    # Normal mode: wrap if the group holds RTL text or such a heading.
    if exclude:
        if heading_match(group, levels):
            output.extend(group)
        elif has_rtl_text(group):
            output.extend(wrap_text(group))
        else:
            output.extend(group)
        return
    if has_rtl_text(group) or heading_match(group, levels):
        output.extend(wrap_text(group))
    else:
        output.extend(group)


def flush(text_lines, output, smart=False, levels=(), exclude=False):
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
            emit_group(group, output, levels, exclude)
            group = []
        if output and output[-1] != "":
            output.append("")  # keep exactly one blank line between blocks
    if group:
        emit_group(group, output, levels, exclude)


def parse_markers(text):
    # Comma-separated box text -> tuple of markers; empty -> ()
    return tuple(part.strip() for part in text.split(",") if part.strip())


def find_unclosed(lines, handle_html, fold_open, fold_close):
    # Pass 1 -> {line index: [tag names opened there and never closed]}
    stack = []
    unclosed = {}
    inside_code = False
    inside_fold = False

    def drop(idx, name):
        unclosed.setdefault(idx, []).append(name)

    for idx, line in enumerate(lines):
        s = line.strip()
        if inside_fold:
            if s in fold_close:
                inside_fold = False
            continue
        if s.startswith("```"):
            inside_code = not inside_code
            continue
        if inside_code or not handle_html:
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
    exclude, levels = parse_levels(heading_levels)
    # Empty value disables the feature
    fold_open = tuple(fold_open) if fold_open else ()
    fold_close = tuple(fold_close) if fold_close else ()
    warnings = []
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

    unclosed = find_unclosed(lines, handle_html, fold_open, fold_close)

    output = []
    text_lines = []
    inside_code = False
    inside_fold = False  # whole fold block stays raw, like a code block
    html_depth = 0  # number nesting level of open HTML blocks

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if inside_fold:  # raw until the close marker, nothing is wrapped
            output.append(line)
            if stripped in fold_close:
                inside_fold = False
            continue
        if stripped.startswith("```"):  # fence (open or close)
            flush(text_lines, output, smart, levels, exclude)
            text_lines = []
            inside_code = not inside_code
            output.append(line)
        elif inside_code:  # must come before the HTML check
            output.append(line)
        elif handle_html and (
            html_depth > 0 or (stripped.startswith("<") and OPEN_RE.match(stripped))
        ):
            flush(text_lines, output, smart, levels, exclude)
            text_lines = []
            html_depth += len(OPEN_RE.findall(line)) - len(CLOSE_RE.findall(line))
            html_depth = max(html_depth, 0)
            output.append(line)
            if autoclose:
                # empty tag right after the open one: searchable failure marker
                for name in reversed(unclosed.get(idx, ())):
                    output.append(f"</{name}>")
                    html_depth = max(html_depth - 1, 0)
        elif stripped in fold_close or stripped.startswith(fold_open):
            # fold open: pass raw and switch to raw mode until the close marker
            flush(text_lines, output, smart, levels, exclude)
            text_lines = []
            output.append(line)
            inside_fold = True
        else:
            text_lines.append(line)

    flush(text_lines, output, smart, levels, exclude)
    if html_depth > 0:
        warnings.append(f"Unclosed HTML block (depth = {html_depth}).")
    if unclosed:
        total = sum(len(v) for v in unclosed.values())
        tail = " Auto-closed with an empty tag." if autoclose else ""
        warnings.append(f"{total} unclosed HTML tag(s) found.{tail}")
    if inside_fold:
        warnings.append("Unclosed fold block (no close marker found).")

    output = head + output
    return eol.join(output) + eol, warnings


# ---------- یاری‌های فایل ----------


def default_out(src):
    # notes.md -> notes.rtl.md (same folder)
    return Path(src).with_name(Path(src).stem + OUT_SUFFIX)


def to_recycle_bin(path):
    # Move a file to the Windows Recycle Bin (recoverable) via the shell API
    class SHFILEOPSTRUCTW(ctypes.Structure):
        _pack_ = 1 if ctypes.sizeof(ctypes.c_void_p) == 4 else 8
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("wFunc", wintypes.UINT),
            ("pFrom", wintypes.LPCWSTR),
            ("pTo", wintypes.LPCWSTR),
            ("fFlags", ctypes.c_ushort),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", wintypes.LPCWSTR),
        ]

    if os.name != "nt":
        raise OSError("Recycle Bin is only supported on Windows")
    op = SHFILEOPSTRUCTW()
    op.wFunc = 3  # FO_DELETE
    op.pFrom = str(Path(path).resolve()) + "\0"  # list must end with a double null
    # ALLOWUNDO | NOCONFIRMATION | NOERRORUI | SILENT
    op.fFlags = 0x0040 | 0x0010 | 0x0400 | 0x0004
    if (
        ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
        or op.fAnyOperationsAborted
    ):
        raise OSError("Could not move the original file to the Recycle Bin")


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
    heading_var = tk.StringVar(value=HEADING_LEVELS)
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
                heading_levels=heading_var.get().strip(),
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

    # ردیف 0: دو چک‌باکس کنار هم
    ttk.Checkbutton(
        settings, text="راست‌چین هوشمند (فقط بخش‌های فارسی)", variable=smart_var
    ).grid(row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 4))
    ttk.Checkbutton(
        settings, text="پردازش تگ‌های HTML (خارج از div)", variable=handle_html_var
    ).grid(row=0, column=1, sticky="w", padx=(6, 0), pady=(0, 4))

    # ردیف 1: چک‌باکس autoclose + لیبل سرصفحه
    ttk.Checkbutton(
        settings, text="بستن خودکار تگ بی‌بسته (قابل جست‌وجو)", variable=autoclose_var
    ).grid(row=1, column=0, sticky="w", padx=(0, 6), pady=(0, 4))
    ttk.Label(settings, text="الگوی سرصفحه (regex — خالی = غیرفعال)").grid(
        row=1, column=1, sticky="w", padx=(6, 0), pady=(0, 4)
    )

    # ردیف 2: فیلد سرصفحه (عرض کامل)
    ttk.Entry(settings, textvariable=head_var).grid(
        row=2, column=0, columnspan=2, sticky="ew", pady=(0, 8)
    )

    # ردیف 3–4: علامت‌های تاشو
    ttk.Label(settings, text="شروع بلوک تاشو").grid(
        row=3, column=0, sticky="w", padx=(0, 6)
    )
    ttk.Label(settings, text="پایان بلوک تاشو").grid(
        row=3, column=1, sticky="w", padx=(6, 0)
    )
    ttk.Entry(settings, textvariable=fold_open_var).grid(
        row=4, column=0, sticky="ew", padx=(0, 6)
    )
    ttk.Entry(settings, textvariable=fold_close_var).grid(
        row=4, column=1, sticky="ew", padx=(6, 0)
    )

    # ردیف 5–6: سطح عنوان‌هایی که همیشه wrap می‌شوند (فقط حالت هوشمند)
    ttk.Label(
        settings,
        text="سطح عنوان‌ها: 2-6 = همیشه راست‌چین | ^2-6 یا -2-6 = هرگز (چپ‌چین) | خالی = خاموش",
    ).grid(row=5, column=0, columnspan=2, sticky="w", padx=(0, 6), pady=(8, 0))
    ttk.Entry(settings, textvariable=heading_var).grid(
        row=6, column=0, columnspan=2, sticky="ew", padx=(0, 6)
    )

    # چیدمان پنجره
    frame = ttk.Frame(root, padding=12)
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)
    frame.rowconfigure(7, weight=1)

    ttk.Label(frame, text="مسیر فایل ورودی (تایپ یا جای‌گذاری کن، یا انتخاب فایل را بزن):").grid(
        row=0, column=0, columnspan=2, sticky="w"
    )

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
