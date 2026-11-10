import unittest

import md_color_gui as color
from test_md_batch import FileFixture


def run(text, bidi_enabled=None):
    lines, warnings = color.process(text.splitlines(keepends=True), bidi_enabled=bidi_enabled)
    return "".join(lines[2:]), warnings


class BidiForwardTests(unittest.TestCase):
    def test_pair_becomes_bdi_and_inner_spaces_go(self):
        out, warnings = run("تابع @@ `GETDATE()` @@ تاریخ میده\n")
        self.assertEqual(out, "تابع <bdi>`GETDATE()`</bdi> تاریخ میده\n")
        self.assertEqual(warnings, [])

    def test_extra_inner_spaces_are_kept(self):
        out, _ = run("@@  `now()`  @@\n")
        self.assertEqual(out, "<bdi> `now()` </bdi>\n")

    def test_two_pairs_in_one_table_row(self):
        out, warnings = run("| @@ `ISNULL(a, b)` @@ | @@ `COALESCE(a, b)` @@ | نکته |\n")
        self.assertEqual(
            out, "| <bdi>`ISNULL(a, b)`</bdi> | <bdi>`COALESCE(a, b)`</bdi> | نکته |\n"
        )
        self.assertEqual(warnings, [])

    def test_color_marker_inside_pair(self):
        out, _ = run("@@ !!`x()`!! @@\n")
        self.assertEqual(out, '<bdi><span class="hy">`x()`</span></bdi>\n')

    def test_unclosed_pair_leaves_only_that_line(self):
        out, warnings = run("@@ `a()` و ^^غلط^^\n\n@@ `b()` @@\n")
        self.assertEqual(out, "@@ `a()` و ^^غلط^^\n\n<bdi>`b()`</bdi>\n")
        self.assertEqual(warnings, ["Line 1: unclosed @@ pair, left unchanged"])

    def test_pair_across_table_cells_is_rejected(self):
        line = "| @@ `a()` | `b()` @@ |\n"
        out, warnings = run(line)
        self.assertEqual(out, line)
        self.assertIn("crosses a table cell", warnings[0])

    def test_nested_pair_is_rejected(self):
        line = "@@ a@@ b @@\n"
        out, warnings = run(line)
        self.assertEqual(out, line)
        self.assertIn("inside an @@ pair", warnings[0])

    def test_empty_pair_is_rejected(self):
        out, warnings = run("@@  @@\n")
        self.assertEqual(out, "@@  @@\n")
        self.assertIn("empty", warnings[0])

    def test_no_inner_space_is_not_a_marker(self):
        line = "متغیر @@version در MySQL\n"
        out, warnings = run(line)
        self.assertEqual(out, line)
        self.assertEqual(len(warnings), 1)
        self.assertIn("not a marker", warnings[0])

    def test_inline_code_fence_and_heading_are_untouched(self):
        text = "`@@ x @@` و `@@version`\n\n## @@ `h()` @@\n\n```sql\n@@ `x()` @@\n```\n"
        out, warnings = run(text)
        self.assertEqual(out, text)
        self.assertEqual(warnings, [])

    def test_triple_at_is_not_a_marker(self):
        line = "a @@@ b\n"
        out, warnings = run(line)
        self.assertEqual(out, line)
        self.assertEqual(warnings, [])

    def test_bdi_with_attributes_is_reported_not_touched(self):
        line = '<bdi dir="ltr">`x()`</bdi> و @@ `y()` @@\n'
        out, warnings = run(line)
        self.assertEqual(out, '<bdi dir="ltr">`x()`</bdi> و <bdi>`y()`</bdi>\n')
        self.assertIn("not mapped", warnings[0])

    def test_fold_title(self):
        out, warnings = run("^! تابع @@ `now()` @@\nبدنه\n!^\n")
        self.assertIn("<summary>تابع <bdi>`now()`</bdi></summary>", out)
        self.assertEqual(warnings, [])

    def test_switch_off_leaves_markers(self):
        line = "@@ `x()` @@ و @@ باز\n"
        out, warnings = run(line, bidi_enabled=False)
        self.assertEqual(out, line)
        self.assertEqual(warnings, [])


class BidiForwardFileTests(FileFixture):
    def test_forward_is_idempotent(self):
        src = self.make(text="| T-SQL | نکته |\n| --- | --- |\n| @@ `GETDATE()` @@ | زمان |\n\nخط @@ `x()` باز\n")
        first = self.run_one(src, "forward")
        self.assertEqual(first.status, "saved")
        self.assertEqual(len(first.warnings), 1)
        once = src.read_bytes()
        self.assertIn("<bdi>`GETDATE()`</bdi>", once.decode("utf-8"))
        second = self.run_one(src, "forward")
        self.assertEqual(second.status, "unchanged")
        self.assertEqual(
            [w.split(": ", 1)[1] for w in second.warnings],
            [w.split(": ", 1)[1] for w in first.warnings],
        )
        self.assertEqual(src.read_bytes(), once)


if __name__ == "__main__":
    unittest.main()
