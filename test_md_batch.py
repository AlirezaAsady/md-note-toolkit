import os
import subprocess
import sys
import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

import md_batch as batch
import md_batch_gui as gui

HERE = Path(__file__).parent
RAW = 'سلام ^^قرمز^^ و !!رنگ!! ¹* متن\n\n¹* توضیح\n\nEnglish\n\n'
CODE = '```python\nx = "^^keep^^ ¹ code"\n<details>\n</details>\nnext\n```\n'


class FileFixture(unittest.TestCase):
    def setUp(self):
        self.scope = tempfile.TemporaryDirectory(dir=HERE)
        self.folder = Path(self.scope.name)
        self.recycled = []
        self.patcher = patch.object(batch, "to_recycle_bin", self.recycle)
        self.patcher.start()

    def tearDown(self):
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
            [sys.executable, str(HERE / "md_batch.py"), "color", str(first), str(second), "--new"],
            capture_output=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("saved=2", result.stdout)
        result = subprocess.run(
            [sys.executable, str(HERE / "md_batch.py"), "reverse", str(self.folder / "missing.md")],
            capture_output=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("failed=1", result.stdout)

    def test_cli_invalid_combination_changes_nothing(self):
        src = self.make()
        original = src.read_bytes()
        result = subprocess.run(
            [sys.executable, str(HERE / "md_batch.py"), "forward", str(src), "--new"],
            capture_output=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(src.read_bytes(), original)

    def test_import_does_not_open_window(self):
        result = subprocess.run(
            [sys.executable, "-c", "import md_batch, md_batch_gui, tkinter; assert tkinter._default_root is None"],
            cwd=HERE, capture_output=True, text=True,
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


if __name__ == "__main__":
    unittest.main()
