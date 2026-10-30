#!/usr/bin/env python3
"""GUI tool: ^^x^^ -> <span class="r">x</span>, !!x!! -> <span class="hy">x</span> (Windows, stdlib only)."""

import ctypes
import os
import re
import time
import tkinter as tk
from html import escape
from pathlib import Path
from tkinter import filedialog, ttk

# Stylesheet linked at the top of every processed note:
#   <link rel="stylesheet" href="CSS_HREF">
# Notes normally live in a different folder from this toolkit, so this value
# MUST be a complete path (or a file:// URL). A relative href breaks as soon
# as the note is opened from anywhere else. Put the full path of your own
# .css file here. The default resolves md.css next to this script, so a fresh
# clone works with no editing at all.
CSS_HREF = str(Path(__file__).resolve().with_name("md.css"))
FOOT_ENABLED = True
FOOT_INLINE_CLASS = "p s22"
FOOT_DEF_CLASS = "g s22"
FOOT_OPEN = "¹²³⁴⁵⁶⁷⁸⁹⁰"

# Output file suffix used when "Replace original" is OFF: notes.md -> notes.out.md
OUT_SUFFIX = ".out.md"

# Replace original: send the input file to the Recycle Bin (recoverable) and
# write the result to its name. Default True -> the checkbox starts ticked.
REPLACE_ORIGINAL = True

# ---------------------------------------------------------------- core logic
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")  # fenced code block line
HEADING_RE = re.compile(r"^ {0,3}#")  # heading line
CODE_RE = re.compile(r"(`+)(.+?)\1")  # inline code span
RED_RE = re.compile(r"\^\^(.+?)\^\^")  # non-greedy, single line
HY_RE = re.compile(r"!!(.+?)!!")
HOLD_RE = re.compile(r"\x00(\d+)\x00")  # placeholder for hidden code
LINK_RE = re.compile(r'^\s*<link\s+rel="stylesheet"\s+href="[^"]*"\s*/?>')
# Protected placeholders must not become part of a footnote token.
FOOT_TOKEN = rf"[{re.escape(FOOT_OPEN)}][^\s\x00]*?" if FOOT_OPEN else r"(?!)"
FOOT_WRAPPED_RE = re.compile(rf"(?:^|(?<= ))(\^\^|!!)({FOOT_TOKEN})\1(?= )")
FOOT_INLINE_RE = re.compile(rf"(?<= )({FOOT_TOKEN})(?= )")
FOOT_DEF_RE = re.compile(rf"^({FOOT_TOKEN})(?= )")
FOOT_SPAN_RE = re.compile(rf'<span class="[^"]*">{FOOT_TOKEN}</span>')

# Marker syntax for collapsible blocks: "^! title" ... "!^"
DETAILS_OPEN_RE = re.compile(r"^\^!(?:\s+(.*))?$")
DETAILS_CLOSE = "!^"
# Summary used for a fold block written as a bare "^!" with no title.
# Change it to your own language here, but change the same constant in
# md_reverse_gui.py too: reverse only turns a summary back into a bare "^!"
# when the two strings are equal.
DEFAULT_SUMMARY = "نمایش جواب"


def convert(line, foot_enabled=None):
    # Returns the converted line, or None if a marker count is odd
    foot_enabled = FOOT_ENABLED if foot_enabled is None else foot_enabled
    spans = []

    def hold(text):
        spans.append(text)
        return f"\x00{len(spans) - 1}\x00"

    def unwrap(m):
        css_class = FOOT_DEF_CLASS if m.start() == 0 else FOOT_INLINE_CLASS
        return m.group(2) if css_class else m.group(0)

    def paint(m):
        css_class = FOOT_DEF_CLASS if m.start() == 0 else FOOT_INLINE_CLASS
        if not css_class:
            return m.group(0)
        return hold(f'<span class="{escape(css_class)}">{escape(m.group(1))}</span>')

    text = CODE_RE.sub(lambda m: hold(m.group(0)), line)
    if foot_enabled and FOOT_OPEN and (FOOT_INLINE_CLASS or FOOT_DEF_CLASS):
        text = FOOT_SPAN_RE.sub(lambda m: hold(m.group(0)), text)
        text = FOOT_WRAPPED_RE.sub(unwrap, text)
        text = FOOT_DEF_RE.sub(paint, text)
        text = FOOT_INLINE_RE.sub(paint, text)
    if text.count("^^") % 2 or text.count("!!") % 2:
        return None
    text = RED_RE.sub(r'<span class="r">\1</span>', text)
    text = HY_RE.sub(r'<span class="hy">\1</span>', text)
    return HOLD_RE.sub(lambda m: spans[int(m.group(1))], text)


def process(lines, foot_enabled=None):
    # lines in -> (lines out, warnings)
    out, warnings, fence = [], [], None
    depth = 0  # number of open ^! blocks
    eol = "\r\n" if lines and lines[0].endswith("\r\n") else "\n"
    for n, line in enumerate(lines, 1):
        m = FENCE_RE.match(line)
        if fence is None:
            if m:  # opening fence
                fence = m.group(1)
                out.append(line)
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
            continue
        s = line.strip()
        m_open = DETAILS_OPEN_RE.match(line.rstrip("\r\n").lstrip())
        if m_open:  # "^! title" -> <details>
            title = m_open.group(1) or DEFAULT_SUMMARY
            title = convert(title, foot_enabled) or title  # allow ^^ !! in the title
            enabled = FOOT_ENABLED if foot_enabled is None else foot_enabled
            if not enabled or not FOOT_SPAN_RE.search(title):
                title = title.rstrip()
            # Folded content is assumed to be code, so the inner div forces LTR.
            # Prefer RTL prose inside a fold? Remove that div and its end tag.
            out += [
                f'<details dir="rtl">{eol}',
                f"<summary>{title}</summary>{eol}",
                eol,
                f'<div dir="ltr">{eol}',
                eol,
            ]
            depth += 1
            continue
        if s == DETAILS_CLOSE and depth > 0:  # "!^" -> </details>
            out += [eol, f"</div>{eol}", f"</details>{eol}", eol]
            depth -= 1
            continue
        if HEADING_RE.match(line):  # headings are skipped
            out.append(line)
            continue
        result = convert(line, foot_enabled)
        if result is None:
            warnings.append(f"Line {n}: odd number of ^^ or !! markers, left unchanged")
            out.append(line)
        else:
            out.append(result)

    if depth > 0:
        warnings.append(f"{depth} unclosed ^! block(s)")

    if not out or not LINK_RE.match(out[0]):  # stylesheet link first
        out.insert(0, f'<link rel="stylesheet" href="{CSS_HREF}">{eol}')
    if len(out) < 2 or out[1].strip():  # blank line after the link
        out.insert(1, eol)
    return out, warnings


# ------------------------------------------------------------- file helpers
def default_out(src):
    # notes.md -> notes.out.md (same folder)
    return src.with_name(src.stem + OUT_SUFFIX)


def to_recycle_bin(path):
    # Move a file to the Windows Recycle Bin (recoverable) via the shell API
    if os.name != "nt":
        raise OSError("Recycle Bin is only supported on Windows")
    # Imported here, not at the top of the file: wintypes declares VARIANT_BOOL
    # with _type_ "v", which only the Windows ctypes backend supports, so a
    # module-level import makes this file unimportable on Linux and macOS.
    from ctypes import wintypes

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
        root.title("Markdown span converter")
        root.geometry("1100x720")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # Top: the two editable panels
        top = ttk.Frame(root)
        top.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 4))
        top.columnconfigure((0, 1), weight=1, uniform="p")
        top.rowconfigure(0, weight=1)
        self.left = self._panel(
            top, 0, "Original file", "Paste from clipboard", self.paste_clip
        )
        self.right = self._panel(
            top, 1, "Final file", "Copy to clipboard", self.copy_clip
        )

        # Bottom: paths (left) and options (right), side by side
        bottom = ttk.Frame(root)
        bottom.grid(row=1, column=0, sticky="ew", padx=8, pady=4)
        bottom.columnconfigure(0, weight=3)
        bottom.columnconfigure(1, weight=1)

        paths = ttk.LabelFrame(bottom, text="Paths")
        paths.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        paths.columnconfigure(1, weight=1)
        self.in_var, self.out_var = tk.StringVar(), tk.StringVar()
        self._path_row(paths, 0, "Input", self.in_var, self.browse_in, True)
        self._path_row(paths, 1, "Output", self.out_var, self.browse_out, False)

        opts = ttk.LabelFrame(bottom, text="Options")
        opts.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        self.foot_var = tk.BooleanVar(value=FOOT_ENABLED)
        ttk.Checkbutton(opts, text="Color footnotes (¹)", variable=self.foot_var).pack(
            anchor="w", padx=6, pady=4
        )
        self.replace_var = tk.BooleanVar(value=REPLACE_ORIGINAL)
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
        logf.grid(row=2, column=0, sticky="ew", padx=8, pady=(4, 8))
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
        self.log("Final text copied to clipboard")

    # --- actions
    def do_convert(self):
        text = self.left.get("1.0", "end-1c")
        result, warnings = process(text.splitlines(keepends=True), self.foot_var.get())
        self.set_text(self.right, "".join(result))
        for w in warnings:
            self.log("Warning: " + w)
        self.log("Converted")

    def save(self):
        data = self.right.get("1.0", "end-1c").replace("\n", self.eol)
        if not data.strip():
            self.log("Nothing to save (final panel is empty)")
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
