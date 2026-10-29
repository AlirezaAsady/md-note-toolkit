#!/usr/bin/env python3
"""Batch CLI/API: reverse, color, rtl, or forward (color then RTL)."""

import argparse
import ctypes
import logging
import os
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import md_color_gui
import md_reverse_gui
import md_rtl_advance_gui

DEFAULT_MODE = "forward"
NEW_FILE = False
MODES = ("reverse", "color", "rtl", "forward")
logger = logging.getLogger(__name__)


@dataclass
class FileResult:
    source: Path
    destination: Path | None = None
    status: str = "error"
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


def normalize_for_reverse(lines):
    # Older notes may omit dir on details or the blank line after its close.
    out, fence = [], None
    for i, line in enumerate(lines):
        match = md_reverse_gui.FENCE_RE.match(line)
        if fence is None and match:
            fence = match.group(1)
            out.append(line)
            continue
        if fence is not None:
            if (
                match
                and match.group(1)[0] == fence[0]
                and len(match.group(1)) >= len(fence)
                and line.strip() == match.group(1)
            ):
                fence = None
            out.append(line)
            continue
        if line.strip() == "<details>":
            line = '<details dir="rtl">'
        out.append(line)
        if line.strip() == "</details>":
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if nxt:
                out.append("")
    return out


def output_path(src, mode):
    return {
        "reverse": md_reverse_gui.default_out,
        "color": md_color_gui.default_out,
        "rtl": md_rtl_advance_gui.default_out,
    }[mode](src)


def reverse_text(raw, warnings):
    lines = raw.replace("\r\n", "\n").split("\n")
    protected, held, block, fence = [], {}, [], None
    for line in lines:
        match = md_reverse_gui.FENCE_RE.match(line)
        if fence is None:
            if match is None:
                protected.append(line)
                continue
            fence = match.group(1)
            block = [line]
            continue
        block.append(line)
        if (
            match and match.group(1)[0] == fence[0]
            and len(match.group(1)) >= len(fence)
            and line.strip() == match.group(1)
        ):
            token = uuid.uuid4().hex
            held[token] = "\n".join(block)
            protected.extend(["```", token, "```"])
            fence = None
    if fence is not None:
        token = uuid.uuid4().hex
        held[token] = "\n".join(block)
        protected.extend(["```", token, "```"])
    levels = (
        md_reverse_gui.parse_levels(md_reverse_gui.HEADING_LEVELS)
        if md_reverse_gui.HEADINGS_ONLY and not md_reverse_gui.REMOVE_RTL
        else set()
    )
    result, stage_warnings = md_reverse_gui.process(
        normalize_for_reverse(protected),
        md_reverse_gui.parse_rules(md_reverse_gui.RULES),
        md_reverse_gui.REVERSE_COLOR, md_reverse_gui.REMOVE_RTL,
        levels, md_reverse_gui.REMOVE_LINK,
    )
    warnings.extend(stage_warnings)
    text = "\n".join(result)
    for token, content in held.items():
        text = text.replace(f"```\n{token}\n```", content)
    return text


def convert_file(src, raw, mode, warnings):
    if mode == "reverse":
        return reverse_text(raw, warnings)
    if mode == "rtl":
        text, stage_warnings = md_rtl_advance_gui.process_file(src)
        warnings.extend(stage_warnings)
        return raw if text is None else text

    lines, stage_warnings = md_color_gui.process(raw.splitlines(keepends=True))
    warnings.extend(stage_warnings)
    colored = "".join(lines)
    if mode == "color":
        return colored

    # RTL accepts a file, so keep its input separate until both steps succeed.
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=src.parent,
            prefix=f".{src.name}.", suffix=".colored.tmp", delete=False,
        ) as handle:
            tmp = Path(handle.name)
            handle.write(colored)
        text, rtl_warnings = md_rtl_advance_gui.process_file(tmp)
        warnings.extend(rtl_warnings)
        return colored if text is None else text
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)


def to_recycle_bin(src):
    if os.name != "nt":
        raise OSError("Replacing originals requires the Windows Recycle Bin")
    ole32 = ctypes.OleDLL("ole32")
    shell32 = ctypes.OleDLL("shell32")
    pointer = ctypes.c_void_p
    ole32.CoInitializeEx.argtypes = [pointer, ctypes.c_ulong]
    ole32.CoCreateInstance.argtypes = [pointer, pointer, ctypes.c_ulong, pointer, ctypes.POINTER(pointer)]
    shell32.SHCreateItemFromParsingName.argtypes = [ctypes.c_wchar_p, pointer, pointer, ctypes.POINTER(pointer)]
    ole32.CoUninitialize.argtypes = []
    ole32.CoUninitialize.restype = None

    def guid(value):
        return (ctypes.c_ubyte * 16).from_buffer_copy(uuid.UUID(value).bytes_le)

    def call(interface, index, argtypes=(), *args):
        vtable = ctypes.cast(interface, ctypes.POINTER(ctypes.POINTER(pointer))).contents
        method = ctypes.WINFUNCTYPE(ctypes.c_long, pointer, *argtypes)(vtable[index])
        hr = method(interface, *args)
        if hr < 0:
            raise OSError(f"Recycle Bin operation failed (HRESULT 0x{hr & 0xFFFFFFFF:08X})")

    operation, item = pointer(), pointer()
    ole32.CoInitializeEx(None, 2)
    try:
        ole32.CoCreateInstance(
            guid("3ad05575-8857-4850-9277-11b85bdb8e09"), None, 1,
            guid("947aab5f-0a5c-4c13-b4d6-4bf7836fc9f8"), ctypes.byref(operation),
        )
        shell32.SHCreateItemFromParsingName(
            str(src), None, guid("43826d1e-e718-42ee-bc55-a1e261c37bfe"), ctypes.byref(item),
        )
        # RECYCLEONDELETE forbids the legacy API's permanent-delete fallback.
        flags = 0x00080000 | 0x00100000 | 0x0040 | 0x0010 | 0x0400 | 0x0004 | 0x2000
        call(operation, 5, (ctypes.c_ulong,), flags)
        call(operation, 18, (pointer, pointer), item, None)
        call(operation, 21)
        aborted = ctypes.c_int()
        call(operation, 22, (ctypes.POINTER(ctypes.c_int),), ctypes.byref(aborted))
        if aborted.value:
            raise OSError("Recycle Bin operation was aborted")
    finally:
        if item:
            call(item, 2)
        if operation:
            call(operation, 2)
        ole32.CoUninitialize()


def unique_bak(src):
    # Never overwrite an earlier backup: notes.md.bak, notes.md.bak.2, ...
    bak = Path(f"{src}.bak")
    n = 2
    while bak.exists():
        bak = Path(f"{src}.bak.{n}")
        n += 1
    return bak


def retire_original(src):
    """Move the original out of the way before the result takes its name.

    Windows sends it to the Recycle Bin. Other platforms have no shell recycle
    API, so the file is renamed to <name>.bak instead - still recoverable, and
    *.bak is gitignored. Returns the backup path, or None when the Recycle Bin
    was used.
    """
    if os.name == "nt":
        to_recycle_bin(src)
        return None
    bak = unique_bak(src)
    src.rename(bak)
    return bak


def save_result(src, dst, text, new_file):
    if new_file:
        with open(dst, "x", encoding="utf-8", newline="") as handle:
            try:
                handle.write(text)
            except Exception:
                handle.close()
                dst.unlink()
                raise
        return None

    retired = False
    bak = None
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=src.parent,
            prefix=f".{src.name}.", suffix=".tmp", delete=False,
        ) as handle:
            tmp = Path(handle.name)
            handle.write(text)
        bak = retire_original(src)
        retired = True
        os.replace(tmp, src)
    except Exception as exc:
        if retired:
            where = str(bak) if bak else "the Recycle Bin"
            raise OSError(
                f"Original is in {where}; converted file kept at {tmp}: {exc}"
            ) from exc
        raise
    finally:
        if not retired and tmp is not None:
            tmp.unlink(missing_ok=True)
    if bak is not None:
        return f"no Recycle Bin on this platform; original kept as {bak.name}"
    return None


def run_batch(paths, mode=DEFAULT_MODE, new_file=NEW_FILE, log=None):
    if mode not in MODES:
        raise ValueError(f"Mode must be one of: {', '.join(MODES)}")
    if new_file and mode == "forward":
        raise ValueError("Color+RTL only supports replacing the original; omit --new")
    if isinstance(paths, (str, Path)):
        raise ValueError("Pass a list of paths, not a single string or Path")
    sources, path_errors = [], {}
    for path in paths:
        value = str(path).strip().strip('"')
        if not value:
            continue
        src = Path(value)
        try:
            src = src.resolve()
        except Exception as exc:
            path_errors[len(sources)] = str(exc)
            sources.append(src)
            continue
        if src not in sources:
            sources.append(src)
    if not sources:
        raise ValueError("No input paths")
    report = []
    emit = logger.info if log is None else log
    for index, src in enumerate(sources, 1):
        emit(f"[{index}/{len(sources)}] {mode}: {src}")
        result = FileResult(source=src)
        try:
            if index - 1 in path_errors:
                raise ValueError(path_errors[index - 1])
            dst = output_path(src, mode).resolve() if new_file else src
            if new_file and dst in sources:
                raise ValueError(f"Output is an input file: {dst}")
            raw = src.read_bytes().decode("utf-8")
            eol = "\r\n" if "\r\n" in raw else "\n"
            text = convert_file(src, raw, mode, result.warnings)
            text = text.replace("\r\n", "\n").replace("\n", eol)
            if not new_file and text == raw:
                result.status = "unchanged"
            else:
                note = save_result(src, dst, text, new_file)
                if note:
                    result.warnings.append(note)
                result.status = "saved"
            result.destination = dst
        except Exception as exc:
            result.error = str(exc)
        report.append(result)
        for warning in result.warnings:
            emit(f"Warning: {src}: {warning}")
        if result.error is not None:
            emit(f"Error: {src}: {result.error}")
        else:
            emit(f"{result.status.capitalize()}: {result.destination}")
    saved = sum(item.status == "saved" for item in report)
    unchanged = sum(item.status == "unchanged" for item in report)
    failed = sum(item.status == "error" for item in report)
    warned = sum(bool(item.warnings) for item in report)
    emit(f"Summary: saved={saved}, unchanged={unchanged}, failed={failed}, warned={warned}")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=MODES)
    parser.add_argument("paths", nargs="+", help="UTF-8 file paths, quoted if needed")
    parser.add_argument(
        "--new", action="store_true", default=NEW_FILE,
        help="Write a new file (single-step modes only); existing outputs are not overwritten",
    )
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    try:
        report = run_batch(args.paths, args.mode, args.new)
    except ValueError as exc:
        parser.error(str(exc))
    return 1 if any(item.status == "error" for item in report) else 0


if __name__ == "__main__":
    sys.exit(main())
