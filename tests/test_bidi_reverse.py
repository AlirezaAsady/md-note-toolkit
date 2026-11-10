#!/usr/bin/env python3
"""Tests for the reverse bidi marker (<bdi>X</bdi> -> "@@ X @@") in md_reverse_gui.py.

Run from the my-md folder:  python -m unittest test_md_batch test_bidi_reverse
"""

import unittest

import md_color_gui
import md_reverse_gui

RULES = md_reverse_gui.parse_rules(md_reverse_gui.RULES)


def reverse(text):
    # run only the Color step (the one that carries the bidi reverse)
    lines, warnings = md_reverse_gui.process(
        text.split("\n"), RULES, True, False, set(), False
    )
    return "\n".join(lines), warnings


class TestBidiReverseConverts(unittest.TestCase):
    def test_simple_cell(self):
        out, w = reverse("| <bdi>GETDATE()</bdi> | col |")
        self.assertEqual(out, "| @@ GETDATE() @@ | col |")
        self.assertEqual(w, [])

    def test_handwritten_cell_keeps_inner_spaces(self):
        # X is kept byte-for-byte; exactly one space is added on each inner side
        out, w = reverse("<bdi> `now()` </bdi>")
        self.assertEqual(out, "@@  `now()`  @@")
        self.assertEqual(w, [])

    def test_two_pairs_on_one_line(self):
        out, w = reverse("<bdi>a</bdi> and <bdi>b</bdi>")
        self.assertEqual(out, "@@ a @@ and @@ b @@")
        self.assertEqual(w, [])

    def test_span_inside_bdi(self):
        out, w = reverse('<bdi><span class="hy">x</span></bdi>')
        self.assertEqual(out, "@@ !!x!! @@")
        self.assertEqual(w, [])

    def test_pipe_inside_inline_code_is_allowed(self):
        out, w = reverse("<bdi>`a|b`</bdi>")
        self.assertEqual(out, "@@ `a|b` @@")
        self.assertEqual(w, [])


class TestBidiReverseWarnings(unittest.TestCase):
    def assert_untouched(self, text):
        out, w = reverse(text)
        self.assertEqual(out, text)
        self.assertEqual(len(w), 1, w)
        self.assertTrue(w[0].startswith("Line 1:"), w[0])
        return w[0]

    def test_attribute_is_not_mapped(self):
        w = self.assert_untouched('<bdi dir="ltr">x</bdi>')
        self.assertIn("not mapped", w)

    def test_open_without_close(self):
        w = self.assert_untouched("<bdi>x")
        self.assertIn("no closing", w)

    def test_stray_close(self):
        w = self.assert_untouched("</bdi>")
        self.assertIn("stray", w)

    def test_empty_content(self):
        w = self.assert_untouched("<bdi></bdi>")
        self.assertIn("empty", w)

    def test_nested_bdi_warns_once(self):
        w = self.assert_untouched("<bdi>a<bdi>b</bdi>c</bdi>")
        self.assertIn("nesting", w)

    def test_content_contains_at_at(self):
        w = self.assert_untouched("<bdi>a@@b</bdi>")
        self.assertIn("@@", w)

    def test_pipe_outside_inline_code(self):
        w = self.assert_untouched("<bdi>a|b</bdi>")
        self.assertIn('"|"', w)


class TestBidiReverseGuards(unittest.TestCase):
    def assert_untouched_quiet(self, text):
        out, w = reverse(text)
        self.assertEqual(out, text)
        self.assertEqual(w, [])

    def test_inside_inline_code(self):
        self.assert_untouched_quiet("use `<bdi>x</bdi>` here")

    def test_inside_fenced_block(self):
        self.assert_untouched_quiet("```\n<bdi>x</bdi>\n```")

    def test_inside_heading(self):
        self.assert_untouched_quiet("# <bdi>x</bdi>")


class TestBidiRoundTrip(unittest.TestCase):
    @unittest.skipUnless(
        getattr(md_color_gui, "BIDI_ENABLED", None) is not None,
        "forward not merged yet",
    )
    def test_forward_reverse_forward_is_byte_identical(self):
        raw = [
            "| ستون | مقدار |\n",
            "@@ GETDATE() @@\n",
            "@@  `now()`  @@\n",
            "@@ !!مهم!! @@\n",
        ]
        fwd1, w1 = md_color_gui.process(list(raw))
        self.assertEqual(w1, [])
        mid, w2 = md_reverse_gui.process(
            [ln.rstrip("\n") for ln in fwd1], RULES, True, False, set(), True
        )
        self.assertEqual(w2, [])
        fwd2, w3 = md_color_gui.process([ln + "\n" for ln in mid])
        self.assertEqual(w3, [])
        self.assertEqual(fwd2, fwd1)


if __name__ == "__main__":
    unittest.main()
