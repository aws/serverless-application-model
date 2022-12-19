from unittest import TestCase

from samtranslator.utils.utils import InvalidValueType, as_array, dict_deep_update, insert_unique


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

    def test_dict_deep_update(self):
        d = {"a": {"b": {"c": "hi"}}}
        dict_deep_update(d, "a.b.d", {"hello": "world"})
        self.assertEqual(d, {"a": {"b": {"c": "hi", "d": {"hello": "world"}}}})
        dict_deep_update(d, "a.b", {"hello": "world"})
        self.assertEqual(d, {"a": {"b": {"hello": "world", "c": "hi", "d": {"hello": "world"}}}})

    def test_dict_deep_update_invalid_type(self):
        d = {"a": {"b": {"c": "hi"}}}
        with self.assertRaisesRegex(InvalidValueType, r"The value of 'a\.b\.c' should be a map"):
            dict_deep_update(d, "a.b.c", {"hello": "world"})
