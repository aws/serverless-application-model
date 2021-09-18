from unittest import TestCase
from samtranslator.utils.py27hash_fix import Py27UniStr


class TestPy27UniStr(TestCase):
    def test_equality(self):
        original_str = "Hello, World!"
        py27_str = Py27UniStr(original_str)
        self.assertEqual(original_str, py27_str)

    def test_add_both_py27unistr(self):
        part1 = Py27UniStr("foo")
        part2 = Py27UniStr("bar")
        added = part1 + part2
        self.assertIsInstance(added, Py27UniStr)
        self.assertEqual(added, "foobar")

    def test_add_py27unistr_and_normal_str(self):
        part1 = Py27UniStr("foo")
        part2 = "bar"
        added1 = part1 + part2
        self.assertIsInstance(added1, Py27UniStr)
        self.assertEqual(added1, "foobar")

        added2 = part2 + part1
        self.assertIsInstance(added2, str)
        self.assertNotIsInstance(added2, Py27UniStr)
        self.assertEqual(added2, "barfoo")

    def test_repr(self):
        py27str = Py27UniStr("some string")
        self.assertEqual(repr(py27str), "u'some string'")

    def test_upper(self):
        py27str = Py27UniStr("upper")
        upper = py27str.upper()
        self.assertIsInstance(upper, Py27UniStr)
        self.assertEqual(upper, "UPPER")

    def test_lower(self):
        py27str = Py27UniStr("LOWER")
        lower = py27str.lower()
        self.assertIsInstance(lower, Py27UniStr)
        self.assertEqual(lower, "lower")

    def test_replace_wihtout_count(self):
        py27str = Py27UniStr("aaa_bbb_aaa")
        replaced = py27str.replace("b", "a")
        self.assertIsInstance(replaced, Py27UniStr)
        self.assertEqual(replaced, "aaa_aaa_aaa")

    def test_replace_with_count(self):
        py27str = Py27UniStr("a_bb_a")
        replaced = py27str.replace("b", "c", 1)
        self.assertIsInstance(replaced, Py27UniStr)
        self.assertEqual(replaced, "a_cb_a")

    def test_split_without_maxsplit(self):
        before = Py27UniStr("a,b,c")
        after = before.split(",")
        self.assertIsInstance(after, list)
        self.assertEqual(after, ["a", "b", "c"])
        for c in after:
            self.assertIsInstance(c, Py27UniStr)

    def test_split_with_maxsplit(self):
        before = Py27UniStr("a,b,c")
        after = before.split(",", 1)
        self.assertIsInstance(after, list)
        self.assertEqual(after, ["a", "b,c"])
        for c in after:
            self.assertIsInstance(c, Py27UniStr)




