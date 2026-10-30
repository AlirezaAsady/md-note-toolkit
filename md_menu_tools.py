"""The two advanced options behind md_menu.cmd.

set-css  rewrites only the CSS_HREF line of md_color_gui.py
shortcut puts a Windows desktop shortcut to md_menu.cmd on the desktop

Batch is a bad place to validate a path and splice it into Python source, so
md_menu.cmd only launches this file and every check happens here.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "md_color_gui.py"
# No $ anchor: under re.M it matches before the \n of a CRLF pair, so "." would
# swallow the \r and that one line would silently lose its Windows ending.
LINE_RE = re.compile(r"^CSS_HREF = [^\r\n]*", re.M)
URL_PREFIXES = ("http://", "https://", "file://")
MENU = "md_menu.cmd"


def fail(reason):
    print(f"\n[refused] {reason}")
    print("Nothing was written.")
    return 1


def check_path(value):
    """Return the text to embed in the source, or raise ValueError."""
    if value.lower().startswith(URL_PREFIXES):
        return value
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError(
            "that is a relative path. The value is copied into every note as\n"
            '           <link rel="stylesheet" href="..."> and resolved next to the note,\n'
            "           so it has to be absolute."
        )
    if path.suffix.lower() != ".css":
        raise ValueError(f"that does not look like a stylesheet ({path.name}).")
    if not path.is_file():
        raise ValueError(f"there is no file at {path}")
    return str(path)


def unquote(value):
    """Windows "Copy as path" hands over the path with quotes already on it."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def check_embeddable(text):
    """Guards for the value sitting inside a raw double-quoted literal."""
    if '"' in text:
        raise ValueError("the value contains a double quote, which would close\n"
                         "           the string literal.")
    if text.endswith("\\"):
        raise ValueError("the value ends with a backslash, which a raw string\n"
                         "           literal cannot carry.")
    if any(ord(ch) < 32 for ch in text):
        raise ValueError("the value contains a line break or control character.")


def read_source():
    # newline="" keeps the file's own line endings; Path.read_text cannot do
    # that before Python 3.13 and this has to run on 3.10.
    with open(TARGET, encoding="utf-8", newline="") as fh:
        return fh.read()


def write_source(path, text):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def set_css():
    print(f"Editing {TARGET.name}: the CSS_HREF line and nothing else.")
    print("Enter the full path to your .css file, or a http(s):// or file:// URL.")
    print("Empty line = cancel.\n")
    try:
        raw = unquote(input("  Stylesheet: ").strip())
    except (EOFError, KeyboardInterrupt):
        return fail("input was interrupted.")
    if not raw:
        return fail("nothing entered.")
    try:
        check_embeddable(raw)
        value = check_path(raw)
        check_embeddable(value)
    except ValueError as exc:
        return fail(str(exc))

    text = read_source()
    found = LINE_RE.findall(text)
    if len(found) != 1:
        return fail(
            f"expected exactly 1 CSS_HREF assignment in {TARGET.name}, found {len(found)}.\n"
            "           The file has been edited by hand - fix it yourself."
        )
    old = found[0]
    new = f'CSS_HREF = r"{value}"'
    if old == new:
        print("\n[ok] already set to that. Nothing to do.")
        return 0

    backup = TARGET.with_suffix(".py.bak")
    write_source(backup, text)
    temp = TARGET.with_suffix(".py.tmp")
    write_source(temp, LINE_RE.sub(lambda _: new, text, count=1))
    os.replace(temp, TARGET)

    print(f"\n[ok] {TARGET.name}")
    print(f"  was:  {old}")
    print(f"  now:  {new}")
    print(f"  The previous copy is in {backup.name} - delete it when you are happy.")
    print("  In a git clone you can also just run: git diff md_color_gui.py")
    return 0


def shortcut():
    if sys.platform != "win32":
        return fail("desktop shortcuts are Windows only.")
    cmd = ROOT / MENU
    if not cmd.is_file():
        return fail(f"{MENU} is not next to this script.")
    for path in (cmd, ROOT):
        if "'" in str(path):
            return fail("your folder name contains a single quote, which the\n"
                        "           PowerShell call cannot carry. Create the shortcut by hand:\n"
                        f"           right-click {cmd.name} - Send to - Desktop.")
    script = (
        "$d=[Environment]::GetFolderPath('Desktop');"
        f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut($d+'\\md-note-toolkit.lnk');"
        f"$s.TargetPath='{cmd}';"
        f"$s.WorkingDirectory='{ROOT}';"
        "$s.Save();"
        "Write-Output ('created: '+$s.FullName)"
    )
    done = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True, text=True,
    )
    if done.returncode != 0:
        print(done.stderr.strip() or "[refused] PowerShell did not run.")
        return 1
    print(f"\n[ok] {done.stdout.strip()}")
    print("  Delete that .lnk whenever you want - it is only a pointer.")
    return 0


def main(argv):
    action = argv[1] if len(argv) > 1 else ""
    if action == "set-css":
        return set_css()
    if action == "shortcut":
        return shortcut()
    print(__doc__)
    print("usage: python md_menu_tools.py [set-css | shortcut]")
    return 2


if __name__ == "__main__":
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv))
