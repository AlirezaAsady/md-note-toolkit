import os
import subprocess
import sys
import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import md_batch as batch  # noqa: E402
import md_batch_gui as gui  # noqa: E402
import md_menu_tools as tools  # noqa: E402

RAW = 'سلام ^^قرمز^^ و !!رنگ!! ¹* متن\n\n¹* توضیح\n\nEnglish\n\n'
CODE = '```python\nx = "^^keep^^ ¹ code"\n<details>\n</details>\nnext\n```\n'


class NtOs:
    """Stand-in for the os module inside md_batch.

    retire_original picks the Recycle Bin branch on `os.name == "nt"` and the
    .bak branch everywhere else, so without this the recycled assertions would
    only ever be exercised on Windows. Everything except .name is the real os.
    """

    name = "nt"

    def __getattr__(self, item):
        return getattr(os, item)


class FileFixture(unittest.TestCase):
    def setUp(self):
        # Same volume as the repo: os.replace() cannot cross drives.
        self.scope = tempfile.TemporaryDirectory(dir=ROOT)
        self.folder = Path(self.scope.name)
        self.recycled = []
        self.patcher = patch.object(batch, "to_recycle_bin", self.recycle)
        self.patcher.start()
        self.os_patcher = patch.object(batch, "os", NtOs())
        self.os_patcher.start()

    def tearDown(self):
        self.os_patcher.stop()
        self.patcher.stop()
        self.scope.cleanup()

    def recycle(self, src):
        self.recycled.append((src, src.read_bytes()))
        src.unlink()

    def make(self, name="a.md", text=RAW):
        path = self.folder / name
        path.write_text(text, encoding="utf-8", newline="")
        return path

    def run_one(self, src, mode, new_file=False):
        result = batch.run_batch([src], mode, new_file)[0]
        self.assertIsNone(result.error)
        return result


class BatchTests(FileFixture):
    def test_retire_original_on_this_platform(self):
        src = self.make("gone.md", "data")
        original = src.read_bytes()
        with patch.object(batch, "os", os):  # the real branch, not NtOs
            bak = batch.retire_original(src)
        self.assertFalse(src.exists())
        if os.name == "nt":
            self.assertIsNone(bak)
            self.assertEqual(self.recycled, [(src, original)])
        else:
            self.assertEqual(bak.name, "gone.md.bak")
            self.assertEqual(bak.read_bytes(), original)
            self.assertFalse(self.recycled)

    def test_color_new_keeps_original(self):
        src = self.make(text=RAW + CODE)
        original = src.read_bytes()
        result = self.run_one(src, "color", True)
        self.assertEqual(result.destination.name, "a.out.md")
        text = result.destination.read_text(encoding="utf-8")
        self.assertIn('<span class="r">قرمز</span>', text)
        self.assertIn('<span class="p s22">¹*</span>', text)
        self.assertIn(CODE, text)
        self.assertEqual(src.read_bytes(), original)
        self.assertFalse(self.recycled)

    def test_rtl_new_keeps_markers_and_code(self):
        src = self.make(text=RAW + CODE)
        result = self.run_one(src, "rtl", True)
        self.assertEqual(result.destination.name, "a.rtl.md")
        text = result.destination.read_text(encoding="utf-8")
        self.assertIn('<div dir="rtl">', text)
        self.assertIn("^^قرمز^^", text)
        self.assertIn(CODE, text)
        self.assertNotIn('<span class="r">', text)

    def test_forward_uses_input_not_raw_sibling_and_recycles_once(self):
        src = self.make(text=RAW + CODE)
        sibling = self.make("a.raw.md", "do not read or modify\n")
        original = src.read_bytes()
        result = self.run_one(src, "forward")
        self.assertEqual(result.destination, src)
        self.assertEqual(self.recycled, [(src, original)])
        text = src.read_text(encoding="utf-8")
        self.assertIn('<span class="r">قرمز</span>', text)
        self.assertIn('<div dir="rtl">', text)
        self.assertIn(CODE, text)
        self.assertEqual(sibling.read_text(), "do not read or modify\n")

    def test_reverse_new_and_roundtrip(self):
        src = self.make(text=RAW + CODE)
        self.run_one(src, "forward")
        final = src.read_bytes()
        result = self.run_one(src, "reverse", True)
        self.assertEqual(result.destination.name, "a.raw.md")
        text = result.destination.read_text(encoding="utf-8")
        self.assertIn("^^قرمز^^", text)
        self.assertIn("!!رنگ!!", text)
        self.assertIn(" ¹* ", text)
        self.assertNotIn('<link', text)
        self.assertIn(CODE, text)
        self.assertEqual(src.read_bytes(), final)
        self.run_one(result.destination, "forward")
        self.assertEqual(result.destination.read_bytes(), final)

    def test_reverse_in_place(self):
        src = self.make(text='<span class="r">red</span>\n')
        self.run_one(src, "reverse")
        self.assertEqual(src.read_text(), "^^red^^\n")
        self.assertEqual(len(self.recycled), 1)

    def test_all_modes_preserve_lf_and_crlf(self):
        for eol in ("\n", "\r\n"):
            for mode in batch.MODES:
                with self.subTest(eol=repr(eol), mode=mode):
                    text = '<span class="r">قرمز</span>\n' if mode == "reverse" else RAW
                    src = self.make(f"{mode}.md", text.replace("\n", eol))
                    self.run_one(src, mode)
                    data = src.read_bytes()
                    if eol == "\n":
                        self.assertNotIn(b"\r", data)
                    else:
                        self.assertIn(b"\r\n", data)
                        self.assertNotIn(b"\n", data.replace(b"\r\n", b""))

    def test_continue_after_missing_and_bad_utf8(self):
        bad = self.folder / "bad.md"
        bad.write_bytes(b"\xff")
        good = self.make()
        results = batch.run_batch([self.folder / "missing.md", bad, good], "color", True)
        self.assertEqual([r.status for r in results], ["error", "error", "saved"])
        self.assertEqual(bad.read_bytes(), b"\xff")

    def test_warning_keeps_malformed_marker_visible(self):
        src = self.make(text="سلام ^^broken\n")
        result = self.run_one(src, "forward")
        self.assertTrue(result.warnings)
        self.assertIn("^^broken", src.read_text(encoding="utf-8"))

    def test_rtl_warning_is_returned(self):
        src = self.make(text='<div dir="ltr">\nسلام\n')
        result = self.run_one(src, "rtl", True)
        self.assertTrue(any("unclosed HTML" in w for w in result.warnings))

    def test_new_output_exists_is_refused(self):
        src = self.make()
        dst = self.make("a.out.md", "keep\n")
        result = batch.run_batch([src], "color", True)[0]
        self.assertEqual(result.status, "error")
        self.assertEqual(dst.read_text(), "keep\n")
        self.assertFalse(self.recycled)

    def test_new_output_cannot_be_another_input(self):
        src = self.make()
        dst = self.make("a.out.md", "keep\n")
        results = batch.run_batch([src, dst], "color", True)
        self.assertIn("Output is an input file", results[0].error)
        self.assertEqual(dst.read_text(), "keep\n")

    def test_duplicate_paths_run_once(self):
        src = self.make()
        results = batch.run_batch([src, f'"{src}"', src.parent / "." / src.name], "forward")
        self.assertEqual(len(results), 1)
        self.assertEqual(len(self.recycled), 1)

    def test_unchanged_file_is_not_recycled(self):
        src = self.make(text="English\n")
        result = self.run_one(src, "reverse")
        self.assertEqual(result.status, "unchanged")
        self.assertFalse(self.recycled)

    def test_recycle_failure_keeps_original_and_removes_temp(self):
        src = self.make()
        original = src.read_bytes()
        with patch.object(batch, "to_recycle_bin", side_effect=OSError("blocked")):
            result = batch.run_batch([src], "forward")[0]
        self.assertEqual(result.status, "error")
        self.assertEqual(src.read_bytes(), original)
        self.assertFalse(list(self.folder.glob("*.tmp")))

    def test_rename_failure_keeps_converted_file_for_recovery(self):
        src = self.make()
        with patch.object(batch.os, "replace", side_effect=OSError("locked")):
            result = batch.run_batch([src], "color")[0]
        self.assertEqual(result.status, "error")
        self.assertIn("converted file kept at", result.error)
        temps = list(self.folder.glob("*.tmp"))
        self.assertEqual(len(temps), 1)
        self.assertIn('<span class="r">', temps[0].read_text(encoding="utf-8"))
        self.assertEqual(len(self.recycled), 1)

    def test_normalizer_preserves_both_fence_styles(self):
        for fence in ("```", "~~~~"):
            text = f'{fence}\n<details>\n</details>\nnext\n{fence}\n'
            self.assertEqual(batch.normalize_for_reverse(text.split("\n")), text.split("\n"))

    def test_reverse_tilde_fence_keeps_html_example(self):
        text = '~~~html\n<div dir="rtl">\n\n<span class="r">red</span>\n\n</div>\n~~~\n'
        src = self.make(text=text)
        result = self.run_one(src, "reverse")
        self.assertEqual(result.status, "unchanged")
        self.assertEqual(src.read_text(encoding="utf-8"), text)

    def test_reverse_preserves_long_and_unclosed_fences(self):
        for text in ('````html\n```\n<span class="r">red</span>\n````\n', '~~~html\n<span class="r">red</span>\n'):
            src = self.make(text=text)
            self.run_one(src, "reverse")
            self.assertEqual(src.read_text(encoding="utf-8"), text)

    def test_bad_path_does_not_abort_other_files(self):
        good = self.make()
        results = batch.run_batch(["bad\x00.md", good], "color", True)
        self.assertEqual([r.status for r in results], ["error", "saved"])

    def test_warning_survives_rtl_stage_failure(self):
        src = self.make(text="سلام ^^broken\n")
        original = src.read_bytes()
        with patch.object(batch.md_rtl_advance_gui, "process_file", side_effect=OSError("blocked")):
            result = batch.run_batch([src], "forward")[0]
        self.assertEqual(result.status, "error")
        self.assertTrue(result.warnings)
        self.assertEqual(src.read_bytes(), original)
        self.assertFalse(list(self.folder.glob("*.tmp")))

    def test_validation(self):
        for paths, mode, new_file in (([], "color", False), (["a"], "forward", True), (["a"], "all", False)):
            with self.assertRaises(ValueError):
                batch.run_batch(paths, mode, new_file)
        with self.assertRaises(ValueError):
            batch.run_batch("a.md", "color")

    def test_cli_multiple_quoted_paths_and_failure_code(self):
        first = self.make("first file.md")
        second = self.make("دوم.md")
        result = subprocess.run(
            [sys.executable, str(ROOT / "md_batch.py"), "color", str(first), str(second), "--new"],
            capture_output=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("saved=2", result.stdout)
        result = subprocess.run(
            [sys.executable, str(ROOT / "md_batch.py"), "reverse", str(self.folder / "missing.md")],
            capture_output=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("failed=1", result.stdout)

    def test_cli_invalid_combination_changes_nothing(self):
        src = self.make()
        original = src.read_bytes()
        result = subprocess.run(
            [sys.executable, str(ROOT / "md_batch.py"), "forward", str(src), "--new"],
            capture_output=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(src.read_bytes(), original)

    def test_import_does_not_open_window(self):
        result = subprocess.run(
            [sys.executable, "-c", "import md_batch, md_batch_gui, tkinter; assert tkinter._default_root is None"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


class GuiTests(FileFixture):
    def setUp(self):
        super().setUp()
        self.root = tk.Tk()
        self.app = gui.App(self.root)
        self.root.update()

    def tearDown(self):
        self.root.destroy()
        super().tearDown()

    def wait_for_job(self):
        deadline = time.monotonic() + 10
        while self.app.busy and time.monotonic() < deadline:
            self.root.update()
        self.assertFalse(self.app.busy, "GUI worker did not finish")

    def test_gui_defaults_and_mode_switch(self):
        self.assertTrue(self.root.winfo_viewable())
        self.assertEqual(self.app.mode_var.get(), "forward")
        self.assertFalse(self.app.new_var.get())
        self.assertTrue(self.app.new_check.instate(["disabled"]))
        self.app.mode_var.set("color")
        self.app.new_check.invoke()
        self.assertTrue(self.app.new_var.get())
        self.app.mode_var.set("forward")
        self.assertFalse(self.app.new_var.get())
        self.assertTrue(self.app.new_check.instate(["disabled"]))

    def test_gui_clipboard_and_browse_append_paths(self):
        first = self.make("first file.md")
        second = self.make("second.md")
        self.root.clipboard_clear()
        self.root.clipboard_append(f'"{first}"\n\n"{second}"\n')
        self.app.paste()
        self.assertEqual(self.app.paths(), [str(first), str(second)])
        with patch.object(gui.filedialog, "askopenfilenames", return_value=(str(first),)):
            self.app.browse()
        self.assertEqual(len(self.app.paths()), 2)
        self.app.clear_paths()
        self.app.run_button.invoke()
        self.assertIn("No input paths", self.app.log_box.get("1.0", "end"))

    def test_gui_run_batch_and_restore_controls(self):
        first = self.make()
        second = self.make("b.md", "سلام ^^broken\n")
        self.app.add_paths([first, self.folder / "missing.md", second])
        self.app.run_button.invoke()
        self.assertTrue(self.app.run_button.instate(["disabled"]))
        self.app.close()
        self.assertTrue(self.root.winfo_exists())
        self.wait_for_job()
        self.assertEqual([r.status for r in self.app.last_report], ["saved", "error", "saved"])
        self.assertEqual(len(self.recycled), 2)
        self.assertEqual(self.app.status_var.get(), "Finished: 3 files; failed=1; warned=1")
        self.assertFalse(self.app.run_button.instate(["disabled"]))
        self.assertTrue(self.app.new_check.instate(["disabled"]))

    def test_gui_new_file(self):
        src = self.make()
        original = src.read_bytes()
        self.app.add_paths([src])
        self.app.mode_var.set("color")
        self.app.new_check.invoke()
        self.app.run_button.invoke()
        self.wait_for_job()
        self.assertEqual(src.read_bytes(), original)
        self.assertTrue((self.folder / "a.out.md").is_file())
        self.assertFalse(self.recycled)
        self.assertFalse(self.app.new_check.instate(["disabled"]))


class MenuToolsTests(FileFixture):
    """md_menu_tools.set_css edits a real source file, so it gets real tests."""

    def setUp(self):
        super().setUp()
        self.css = self.folder / "md.css"
        self.css.write_text("body{}", encoding="utf-8")
        self.target = self.folder / "md_color_gui.py"
        self.target.write_bytes((ROOT / "md_color_gui.py").read_bytes())
        self.original = self.target.read_bytes()
        self.patcher2 = patch.object(tools, "TARGET", self.target)
        self.patcher2.start()

    def tearDown(self):
        self.patcher2.stop()
        super().tearDown()

    def ask(self, answer):
        with patch("builtins.input", return_value=answer):
            return tools.set_css()

    def test_bad_values_are_refused_and_write_nothing(self):
        relative = "md.css"
        missing = str(self.folder / "missing.css")
        wrong_kind = str(self.folder / "notes.txt")
        for answer in ("", "   ", relative, missing, wrong_kind,
                       'C:\\a"b.css', str(self.css) + "\\", "a\nb"):
            with self.subTest(answer=answer):
                self.assertEqual(self.ask(answer), 1)
                self.assertEqual(self.target.read_bytes(), self.original)
                self.assertFalse(list(self.folder.glob("*.bak")))
                self.assertFalse(list(self.folder.glob("*.tmp")))

    def test_only_the_css_href_line_changes(self):
        self.assertEqual(self.ask(str(self.css)), 0)
        # splitlines-style: the working copy may be LF or CRLF, and which one
        # is checked by test_line_endings_and_backup instead.
        before = self.original.decode("utf-8").replace("\r\n", "\n").split("\n")
        after = self.target.read_bytes().decode("utf-8").replace("\r\n", "\n").split("\n")
        self.assertEqual(len(before), len(after))
        changed = [(i, b, a) for i, (b, a) in enumerate(zip(before, after)) if b != a]
        self.assertEqual(len(changed), 1)
        index, old, new = changed[0]
        self.assertTrue(old.startswith("CSS_HREF = "), old)
        self.assertEqual(new, f'CSS_HREF = r"{self.css}"')
        self.assertEqual(after[index + 1], before[index + 1])

    def test_line_endings_and_backup(self):
        crlf = self.original.decode("utf-8").replace("\r\n", "\n").replace("\n", "\r\n")
        self.target.write_bytes(crlf.encode("utf-8"))
        self.assertEqual(self.ask(str(self.css)), 0)
        written = self.target.read_bytes()
        self.assertEqual(written.count(b"\r\n"), crlf.encode("utf-8").count(b"\r\n"))
        self.assertNotIn(b"\r\r", written)
        backup = self.target.with_suffix(".py.bak")
        self.assertEqual(backup.read_bytes(), crlf.encode("utf-8"))
        self.assertFalse(list(self.folder.glob("*.tmp")))

    def test_two_assignments_are_refused(self):
        text = self.original.decode("utf-8")
        doubled = text.replace("CSS_HREF = ", 'CSS_HREF = "a"\nCSS_HREF = ', 1)
        self.target.write_bytes(doubled.encode("utf-8"))
        self.assertEqual(self.ask(str(self.css)), 1)
        self.assertEqual(self.target.read_bytes(), doubled.encode("utf-8"))
        self.assertFalse(list(self.folder.glob("*.tmp")))

    def test_same_value_again_is_a_no_op(self):
        self.assertEqual(self.ask(str(self.css)), 0)
        once = self.target.read_bytes()
        self.assertEqual(self.ask(str(self.css)), 0)
        self.assertEqual(self.target.read_bytes(), once)

    def test_url_is_accepted_without_touching_the_disk(self):
        self.assertEqual(self.ask("https://example.com/md.css"), 0)
        self.assertIn(b'CSS_HREF = r"https://example.com/md.css"', self.target.read_bytes())

    def test_pasted_path_with_quotes_is_accepted(self):
        # Windows "Copy as path" wraps the path in double quotes.
        self.assertEqual(self.ask(f'"{self.css}"'), 0)
        self.assertIn(f'CSS_HREF = r"{self.css}"'.encode("utf-8"),
                      self.target.read_bytes())

    def test_embedded_quote_is_still_refused(self):
        for answer in (f'{self.css}"', f'a"b"{self.css}', 'C:\\a"b.css', '"'):
            with self.subTest(answer=answer):
                self.assertEqual(self.ask(answer), 1)
                self.assertEqual(self.target.read_bytes(), self.original)


if __name__ == "__main__":
    unittest.main()
