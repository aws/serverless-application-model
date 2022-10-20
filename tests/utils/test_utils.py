from unittest import TestCase

from samtranslator.utils.utils import as_array, insert_unique


class TestUtils(TestCase):
    def test_as_array(self):
        self.assertEqual(as_array("foo"), ["foo"])
        self.assertEqual(as_array(None), [None])
        self.assertEqual(as_array([None]), [None])
        self.assertEqual(as_array([[None]]), [[None]])
        self.assertEqual(as_array(["foo", None]), ["foo", None])
        self.assertEqual(as_array([]), [])

    def test_insert_unique(self):
        self.assertEqual(insert_unique(None, None), [None])
        self.assertEqual(insert_unique(None, 42), [None, 42])
        self.assertEqual(insert_unique(["z", "y", "x", "z"], ["a", "y", "a"]), ["z", "y", "x", "z", "a"])
        self.assertEqual(insert_unique("z", "a"), ["z", "a"])
        self.assertEqual(insert_unique("z", ["a", "b"]), ["z", "a", "b"])
        self.assertEqual(insert_unique(["z", "y"], "a"), ["z", "y", "a"])

        # Check non-mutating
        xs = ["a"]
        vs = ["b"]
        ret = insert_unique(xs, vs)
        self.assertFalse(ret is xs)
        self.assertFalse(ret is vs)
