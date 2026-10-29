#!/usr/bin/env python3
"""GUI tool: the reverse of md_rtl_advance_gui.py + md_color_gui.py (Windows, stdlib only).

Step A (option "Color"): <span class="..."> -> ^^x^^ / !!x!!   and   <details> block -> ^! ... !^
Step B (option "RTL" or "headings only"): removes the <div dir="rtl"> wrappers
Step C (option): removes a <link ...> on the first line

Every step works on its own. Step B only touches the exact wrapper pattern the RTL
script writes, so <div dir="ltr">, <details>, spans and code are never damaged by it.
"""

import ctypes
import os
import re
import time
import tkinter as tk
from ctypes import wintypes
from html import unescape
from pathlib import Path
from tkinter import filedialog, ttk

# ---------------------------------------------------------------- settings
# Span rules: "prefix=marker" pairs. Only the FIRST class of a span counts
# ("r hy s32" -> "r", "hb r" -> "hb"). The first matching prefix wins and
# "*" means everything else. The GUI box starts with this value.
RULES = "h=!!, *=^^"
FOOT_CLASSES = ("p", "g")
FOOT_OPEN = "¹²³⁴⁵⁶⁷⁸⁹⁰"
DEFAULT_SUMMARY = "نمایش جواب"  # summary text that means a bare "^!"
REVERSE_COLOR = True  # start value of the "Color" checkbox
REMOVE_RTL = True  # start value of the "RTL (all)" checkbox
HEADINGS_ONLY = False  # start value of the "RTL around headings only" checkbox
HEADING_LEVELS = "1-6"  # start value of the levels box: "2-3", "1,4", "1,3-4", "0-10"
REMOVE_LINK = True  # start value of the "Remove first-line <link>" checkbox

# ---------------------------------------------------------------- core logic
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")  # fenced code block line
HEADING_RE = re.compile(r"^ {0,3}#")  # heading line
CODE_RE = re.compile(r"(`+)(.+?)\1")  # inline code span
HOLD_RE = re.compile(r"\x00(\d+)\x00")  # placeholder for hidden code
# innermost span only: its content must not contain another <span
SPAN_RE = re.compile(r'<span\s+class\s*=\s*"([^"]*)"\s*>((?:(?!<span\b).)+?)</span>')
FOOT_RE = re.compile(rf"[{re.escape(FOOT_OPEN)}][^\s\x00]*" if FOOT_OPEN else r"(?!)")
SUMMARY_RE = re.compile(r"^<summary>(.*)</summary>$")
LINK_RE = re.compile(r"^\s*<link\b[^>]*>\s*$", re.I)
DIV_RTL = '<div dir="rtl">'
DIV_LTR = '<div dir="ltr">'
DETAILS_OPEN = '<details dir="rtl">'


def parse_rules(text):
    # "h=!!, *=^^" -> ([("h", "!!")], "^^")
    prefixes, default = [], None
    for part in text.split(","):
        if "=" not in part:
            continue
        key, marker = (x.strip() for x in part.split("=", 1))
        if not key or not marker:
            continue
        if key == "*":
            default = marker
        else:
            prefixes.append((key, marker))
    return prefixes, default


def pick_marker(classes, rules):
    prefixes, default = rules
    tokens = classes.split()
    first = tokens[0] if tokens else ""
    for prefix, marker in prefixes:
        if first.startswith(prefix):
            return marker
    return default


def is_footnote_span(m, text):
    classes = m.group(1).split()
    return (
        bool(classes)
        and classes[0] in FOOT_CLASSES
        and FOOT_RE.fullmatch(unescape(m.group(2))) is not None
        and (m.start() == 0 or text[m.start() - 1] == " ")
        and text[m.end() : m.end() + 1] == " "
    )


def spans_to_markers(line, rules):
    held = []

    def hide(m):  # protect inline code, like the original does
        held.append(m.group(0))
        return f"\x00{len(held) - 1}\x00"

    def repl(m):
        if is_footnote_span(m, text):
            return unescape(m.group(2))
        marker = pick_marker(m.group(1), rules)
        if marker is None:
            return m.group(0)  # no rule matched -> leave it
        return f"{marker}{m.group(2)}{marker}"

    text = CODE_RE.sub(hide, line)
    while True:  # repeat so nested spans unwrap from the inside out
        new = SPAN_RE.sub(repl, text)
        if new == text:
            break
        text = new
    return HOLD_RE.sub(lambda m: held[int(m.group(1))], text)


def blank(lines, k):
    return 0 <= k < len(lines) and not lines[k].strip()


def is_at(lines, k, text):
    return 0 <= k < len(lines) and lines[k].strip() == text


def colors_back(lines, rules, warnings):
    # Step A: spans -> markers, details block -> ^! / !^
    out, fence, depth = [], None, 0
    i = 0
    while i < len(lines):
        line = lines[i]
        m = FENCE_RE.match(line)
        if fence is None:
            if m:  # opening fence
                fence = m.group(1)
                out.append(line)
                i += 1
                continue
        else:  # inside a code block
            if (
                m
                and m.group(1)[0] == fence[0]
                and len(m.group(1)) >= len(fence)
                and line.strip() == m.group(1)
            ):
                fence = None
            out.append(line)
            i += 1
            continue
        s = line.strip()
        if s.startswith("<details"):
            # must be exactly the 5 lines md_color_gui.py writes
            sm = SUMMARY_RE.match(lines[i + 1].strip()) if i + 1 < len(lines) else None
            if (
                s == DETAILS_OPEN
                and sm
                and blank(lines, i + 2)
                and is_at(lines, i + 3, DIV_LTR)
                and blank(lines, i + 4)
            ):
                title = sm.group(1)
                if not any(is_footnote_span(m, title) for m in SPAN_RE.finditer(title)):
                    title = title.strip()
                if not title or title == DEFAULT_SUMMARY:
                    out.append("^!")
                else:
                    out.append("^! " + spans_to_markers(title, rules))
                depth += 1
                i += 5
                continue
            warnings.append(
                f"Line {i + 1}: <details> does not match the expected pattern, left unchanged"
            )
            out.append(line)
            i += 1
            continue
        # closing lines: blank, </div>, </details>, blank
        if (
            depth > 0
            and blank(lines, i)
            and is_at(lines, i + 1, "</div>")
            and is_at(lines, i + 2, "</details>")
            and blank(lines, i + 3)
        ):
            out.append("!^")
            depth -= 1
            i += 4
            continue
        if HEADING_RE.match(line):  # headings were skipped by the original
            out.append(line)
            i += 1
            continue
        new = spans_to_markers(line, rules)
        if re.search(r"<span\b", CODE_RE.sub("", new)):
            warnings.append(
                f"Line {i + 1}: <span> with no matching rule, left unchanged"
            )
        out.append(new)
        i += 1
    if depth > 0:
        warnings.append(
            f"{depth} <details> block(s) opened but the closing lines were not found"
        )
    return out


HEADING_LEVEL_RE = re.compile(
    r"^ {0,3}(#{1,6})(?:\s|$)"
)  # ATX heading, level = '#' count


def parse_levels(text):
    # "2-3" / "1,4" / "1,3-4" -> set of levels; junk ignored, clamped to 1-6
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
    return {n for n in levels if 1 <= n <= 6}


def is_lone_heading(content, levels):
    # True if the wrapped content is exactly one heading line with a wanted level
    text = [ln for ln in content if ln.strip()]
    if len(text) != 1:
        return False
    m = HEADING_LEVEL_RE.match(text[0])
    return bool(m) and len(m.group(1)) in levels


def find_rtl_close(lines, i):
    # lines[i] is the rtl open tag, lines[i + 1] is blank.
    # Returns the index of the matching </div>, or None if the pattern is broken.
    for j in range(i + 2, len(lines)):
        s = lines[j].strip()
        if s == "</div>":
            return j if j >= i + 3 and blank(lines, j - 1) else None
        if s.startswith("```") or s.startswith("^!") or s == DIV_RTL:
            return None
    return None


def remove_rtl(lines, warnings, levels=None):
    # Step B: <div dir="rtl"> + blank ... blank + </div>  ->  the bare lines
    # levels=None -> unwrap every group; a set -> only groups that hold one lone
    # heading of those levels (anything else stays wrapped)
    out, in_code, in_fold = [], False, False
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if in_fold:  # ^! ... !^ blocks were never wrapped
            out.append(line)
            if s == "!^":
                in_fold = False
            i += 1
            continue
        if s.startswith("```"):
            in_code = not in_code
            out.append(line)
            i += 1
            continue
        if in_code:
            out.append(line)
            i += 1
            continue
        if s.startswith("^!"):
            in_fold = True
            out.append(line)
            i += 1
            continue
        if s == DIV_RTL:
            j = find_rtl_close(lines, i) if blank(lines, i + 1) else None
            if j is None:
                warnings.append(
                    f'Line {i + 1}: <div dir="rtl"> does not match the expected pattern, left unchanged'
                )
            else:
                content = lines[i + 2 : j - 1]
                if levels is None or is_lone_heading(content, levels):
                    out.extend(content)  # content only; blank after </div> stays
                    i = j + 1
                    continue
        out.append(line)
        i += 1
    return out


def remove_link(lines):
    # Step C: drop a <link ...> on the first line plus the blank lines after it
    if lines and LINK_RE.match(lines[0]):
        k = 1
        while k < len(lines) and not lines[k].strip():
            k += 1
        return lines[k:]
    return lines


def process(lines, rules, do_color, do_rtl, heading_levels, do_link):
    # lines in (no line endings) -> (lines out, warnings)
    # do_rtl wins over heading_levels (a set of levels, empty = off)
    warnings = []
    if do_color:
        lines = colors_back(lines, rules, warnings)  # A
    if do_rtl:
        lines = remove_rtl(lines, warnings)  # B, every wrapper
    elif heading_levels:
        lines = remove_rtl(lines, warnings, heading_levels)  # B, lone headings only
    if do_link:
        lines = remove_link(lines)  # C
    return lines, warnings


# ------------------------------------------------------------- file helpers
def default_out(src):
    # notes.out.md -> notes.raw.md (same folder)
    stem = src.stem[:-4] if src.stem.endswith(".out") else src.stem
    return src.with_name(stem + ".raw.md")


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
    """Move the original out of the way before the result takes its name.

    Windows sends it to the Recycle Bin. Other platforms have no shell recycle
    API, so the file is renamed to <name>.bak instead - still recoverable.
    Returns the backup path, or None when the Recycle Bin was used.
    """
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


# ----------------------------------------------------------------------- GUI
class App:
    def __init__(self, root):
        self.root = root
        self.eol = "\n"  # line ending of the loaded file
        root.title("Markdown reverse converter")
        root.geometry("1100x720")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)

        # Very top: what to reverse (each part works on its own)
        what = ttk.LabelFrame(root, text="What to reverse")
        what.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 0))
        what.columnconfigure((0, 1), weight=1, uniform="w")
        self.color_var = tk.BooleanVar(value=REVERSE_COLOR)
        self.rtl_var = tk.BooleanVar(value=REMOVE_RTL)
        self.head_var = tk.BooleanVar(value=HEADINGS_ONLY)
        self.levels_var = tk.StringVar(value=HEADING_LEVELS)
        ttk.Checkbutton(
            what, text="Color (spans, ^! blocks)", variable=self.color_var
        ).grid(row=0, column=0, sticky="w", padx=6, pady=3)
        ttk.Checkbutton(what, text="RTL wrappers (all)", variable=self.rtl_var).grid(
            row=0, column=1, sticky="w", padx=6, pady=3
        )
        hf = ttk.Frame(what)
        hf.grid(row=1, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 3))
        ttk.Checkbutton(
            hf, text="RTL around headings only, levels:", variable=self.head_var
        ).pack(side="left")
        ttk.Entry(hf, textvariable=self.levels_var, width=14).pack(
            side="left", padx=(6, 0)
        )
        ttk.Label(
            hf, text='e.g. 1-6, 2,3,4, 0-10  (ignored while "RTL wrappers (all)" is on)'
        ).pack(side="left", padx=8)

        # Middle: the two editable panels
        top = ttk.Frame(root)
        top.grid(row=1, column=0, sticky="nsew", padx=8, pady=(8, 4))
        top.columnconfigure((0, 1), weight=1, uniform="p")
        top.rowconfigure(0, weight=1)
        self.left = self._panel(
            top,
            0,
            "Final file (with spans / RTL)",
            "Paste from clipboard",
            self.paste_clip,
        )
        self.right = self._panel(
            top, 1, "Raw file (markers)", "Copy to clipboard", self.copy_clip
        )

        # Bottom: paths + rules (left) and options (right), side by side
        bottom = ttk.Frame(root)
        bottom.grid(row=2, column=0, sticky="ew", padx=8, pady=4)
        bottom.columnconfigure(0, weight=3)
        bottom.columnconfigure(1, weight=1)

        paths = ttk.LabelFrame(bottom, text="Paths and rules")
        paths.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        paths.columnconfigure(1, weight=1)
        self.in_var, self.out_var = tk.StringVar(), tk.StringVar()
        self._path_row(paths, 0, "Input", self.in_var, self.browse_in, True)
        self._path_row(paths, 1, "Output", self.out_var, self.browse_out, False)
        self.rules_var = tk.StringVar(value=RULES)
        ttk.Label(paths, text="Rules").grid(row=2, column=0, padx=4, pady=3)
        ttk.Entry(paths, textvariable=self.rules_var).grid(
            row=2, column=1, columnspan=3, sticky="ew", padx=4
        )

        opts = ttk.LabelFrame(bottom, text="Options")
        opts.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        self.replace_var = tk.BooleanVar()
        self.link_var = tk.BooleanVar(value=REMOVE_LINK)
        ttk.Checkbutton(
            opts, text="Remove first-line <link>", variable=self.link_var
        ).pack(anchor="w", padx=6, pady=(4, 0))
        ttk.Checkbutton(
            opts,
            text="Replace original\n(original -> Recycle Bin)",
            variable=self.replace_var,
        ).pack(anchor="w", padx=6, pady=4)
        btns = ttk.Frame(opts)
        btns.pack(fill="x", padx=6, pady=4)
        ttk.Button(btns, text="Convert", command=self.do_convert).pack(
            side="left", expand=True, fill="x"
        )
        ttk.Button(btns, text="Save", command=self.save).pack(
            side="left", expand=True, fill="x", padx=(4, 0)
        )

        # Log
        logf = ttk.LabelFrame(root, text="Log")
        logf.grid(row=3, column=0, sticky="ew", padx=8, pady=(4, 8))
        logf.columnconfigure(0, weight=1)
        self.log_box = tk.Text(logf, height=5, state="disabled", font=("Consolas", 9))
        self.log_box.grid(row=0, column=0, sticky="ew")
        sb = ttk.Scrollbar(logf, command=self.log_box.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.log_box.config(yscrollcommand=sb.set)

    # --- widget builders
    def _panel(self, parent, col, title, btn_text, btn_cmd):
        f = ttk.LabelFrame(parent, text=title)
        f.grid(row=0, column=col, sticky="nsew", padx=4)
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1)
        txt = tk.Text(f, wrap="word", undo=True, font=("Consolas", 11))
        txt.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(f, command=txt.yview)
        sb.grid(row=0, column=1, sticky="ns")
        txt.config(yscrollcommand=sb.set)
        ttk.Button(f, text=btn_text, command=btn_cmd).grid(
            row=1, column=0, columnspan=2, sticky="ew"
        )
        return txt

    def _path_row(self, parent, row, label, var, browse_cmd, is_input):
        ttk.Label(parent, text=label).grid(row=row, column=0, padx=4, pady=3)
        e = ttk.Entry(parent, textvariable=var)
        e.grid(row=row, column=1, sticky="ew", padx=4)
        if is_input:
            e.bind("<Return>", lambda _e: self.load())  # typed path + Enter loads it
        ttk.Button(parent, text="Browse", command=browse_cmd).grid(
            row=row, column=2, padx=2
        )
        ttk.Button(
            parent, text="Paste path", command=lambda: self.paste_path(var, is_input)
        ).grid(row=row, column=3, padx=(2, 4))

    # --- helpers
    def log(self, msg):
        self.log_box.config(state="normal")
        self.log_box.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    @staticmethod
    def clean(s):
        return s.strip().strip('"')  # drop quotes from "Copy as path"

    def clipboard(self):
        try:
            return self.root.clipboard_get()
        except tk.TclError:
            self.log("Clipboard is empty or not text")
            return None

    @staticmethod
    def set_text(widget, text):
        widget.delete("1.0", "end")
        widget.insert("1.0", text)

    # --- input / output paths
    def browse_in(self):
        p = filedialog.askopenfilename(
            filetypes=[("Markdown", "*.md"), ("All files", "*.*")]
        )
        if p:
            self.in_var.set(str(Path(p)))
            self.load()

    def browse_out(self):
        src = self.clean(self.in_var.get())
        p = filedialog.asksaveasfilename(
            defaultextension=".md",
            initialdir=str(Path(src).parent) if src else None,
            initialfile=Path(self.clean(self.out_var.get())).name or None,
        )
        if p:
            self.out_var.set(str(Path(p)))

    def paste_path(self, var, is_input):
        text = self.clipboard()
        if text is not None:
            var.set(self.clean(text))
            if is_input:
                self.load()

    def load(self):
        src = Path(self.clean(self.in_var.get()))
        try:
            raw = src.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError) as e:
            self.log(f"Error: {e}")
            return
        self.eol = "\r\n" if "\r\n" in raw else "\n"  # remember the original ending
        self.set_text(self.left, raw.replace("\r\n", "\n"))
        self.right.delete("1.0", "end")
        self.out_var.set(str(default_out(src)))  # default: same folder
        self.log(f"Loaded: {src}")

    # --- clipboard
    def paste_clip(self):
        text = self.clipboard()
        if text is not None:
            self.set_text(self.left, text.replace("\r\n", "\n"))
            self.in_var.set("")  # no source file for pasted text
            self.log("Pasted text from clipboard (no source file)")

    def copy_clip(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.right.get("1.0", "end-1c"))
        self.root.update()  # keep it after the app closes
        self.log("Raw text copied to clipboard")

    # --- actions
    def do_convert(self):
        rules = parse_rules(self.rules_var.get())
        if not rules[0] and rules[1] is None:
            self.log("Warning: no valid rules, non-footnote spans will be left unchanged")
        levels = set()
        if self.head_var.get() and not self.rtl_var.get():
            levels = parse_levels(self.levels_var.get())
            if not levels:
                self.log("Warning: no valid heading levels, headings are left wrapped")
        elif self.head_var.get():
            self.log(
                'Note: "RTL wrappers (all)" is on, so the headings-only option is not needed'
            )
        text = self.left.get("1.0", "end-1c")
        result, warnings = process(
            text.split("\n"),
            rules,
            self.color_var.get(),
            self.rtl_var.get(),
            levels,
            self.link_var.get(),
        )
        self.set_text(self.right, "\n".join(result))
        for w in warnings:
            self.log("Warning: " + w)
        self.log("Converted")

    def save(self):
        data = self.right.get("1.0", "end-1c").replace("\n", self.eol)
        if not data.strip():
            self.log("Nothing to save (raw panel is empty)")
            return
        src_s = self.clean(self.in_var.get())
        tmp = None
        try:
            if self.replace_var.get():
                src = Path(src_s)
                if not src_s or not src.is_file():
                    raise ValueError("Replace needs an existing input file")
                # Safe order: write temp -> original to Recycle Bin -> rename temp
                tmp = src.with_name(src.name + ".tmp")
                with open(tmp, "w", encoding="utf-8", newline="") as f:
                    f.write(data)
                bak = retire_original(src)
                os.replace(tmp, src)
                tmp = None
                self.log(f"Replaced: {src} (original kept in {bak or 'the Recycle Bin'})")
            else:
                dst_s = self.clean(self.out_var.get())
                if not dst_s:
                    raise ValueError("Output path is empty")
                dst = Path(dst_s)
                if src_s and dst.resolve() == Path(src_s).resolve():
                    raise ValueError(
                        "Output equals input; use the Replace option instead"
                    )
                with open(dst, "w", encoding="utf-8", newline="") as f:
                    f.write(data)
                self.log(f"Saved: {dst}")
        except (OSError, ValueError) as e:
            self.log(f"Error: {e}")
            if tmp and tmp.exists():
                tmp.unlink()  # clean up the temp file


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
