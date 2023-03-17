from unittest import TestCase

from samtranslator.internal.utils.utils import remove_none_values
from samtranslator.utils.utils import (
    InvalidValueType,
    as_array,
    dict_deep_get,
    dict_deep_set,
    insert_unique,
)


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

    def test_dict_deep_get(self):
        d = {"a": {"b": {"c": {"hi": "hello"}}}}
        res = dict_deep_get(d, ["a", "b", "c"])
        self.assertEqual(res, {"hi": "hello"})

        res = dict_deep_get(d, "a.b.c")
        self.assertEqual(res, {"hi": "hello"})

        res = dict_deep_get(d, ["a", "b", "d"])
        self.assertEqual(res, None)

        d = {"a": {"b": [{"c": []}]}}
        with self.assertRaisesRegex(InvalidValueType, "The value of 'a.b' should be a map"):
            dict_deep_get(d, ["a", "b", "c"])

    def test_dict_deep_set(self):
        d = {"a": {"b": {"c": "hi"}}}
        dict_deep_set(d, "a.b.d.hello", "world")
        self.assertEqual(d, {"a": {"b": {"c": "hi", "d": {"hello": "world"}}}})
        dict_deep_set(d, "a.b.hello", "world")
        dict_deep_set(d, "a.hello", "world1")
        self.assertEqual(d, {"a": {"hello": "world1", "b": {"hello": "world", "c": "hi", "d": {"hello": "world"}}}})

    def test_dict_deep_set_invalid_type(self):
        d = {"a": {"b": {"c": "hi"}}}
        with self.assertRaisesRegex(InvalidValueType, r"The value of 'a\.b\.c' should be a map"):
            dict_deep_set(d, "a.b.c.hello", "world")

        with self.assertRaisesRegex(InvalidValueType, r"It should be a map"):
            dict_deep_set("a str", "a.b.c.hello", "world")

    def test_dict_deep_set_invalid_path(self):
        d = {"a": {"b": {"c": "hi"}}}
        with self.assertRaisesRegex(ValueError, r"path cannot be empty"):
            dict_deep_set(d, "", "world")

    def test_remove_none_values(self):
        d = {"a": "hello", "b": None}
        self.assertEqual(remove_none_values(d), {"a": "hello"})

        d = {"a": None, "b": None, "c": None}
        self.assertEqual(remove_none_values(d), {})
