from unittest import TestCase

from samtranslator.internal.utils.utils import remove_none_values
from samtranslator.utils.utils import (
    InvalidValueType,
    as_array,
    dict_deep_get,
    dict_deep_set,
    insert_unique,
    namespace_prefix,
    safe_dict,
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

    def test_namespace_prefix(self):
        self.assertEqual(namespace_prefix("a", "b"), "a::b")

        self.assertEqual(namespace_prefix("a", ""), "a")
        self.assertEqual(namespace_prefix("a", None), "a")
        self.assertEqual(namespace_prefix("", "b"), "b")
        self.assertEqual(namespace_prefix(None, "b"), "b")

        self.assertEqual(namespace_prefix("", ""), "")
        self.assertEqual(namespace_prefix("", None), "")
        self.assertEqual(namespace_prefix(None, ""), "")
        self.assertEqual(namespace_prefix(None, None), "")

    def test_safe_dict_no_change(self):
        d = {"resource_id_1": {"Type": "custom_type"}, "resource_id_2": {"Type": "other_type"}}
        self.assertEqual(safe_dict(d), d)

    def test_safe_dict_with_missing_loop_entry(self):
        d = {"Fn::ForEach::unique_loop_id": ["LoopKey", {"Type": "custom_type"}]}
        self.assertEqual(safe_dict(d), d)

    def test_safe_dict_with_extra_loop_entry(self):
        d = {"Fn::ForEach::unique_loop_id": ["LoopKey", ["LoopKey1", "LoopKey2"], {"custom_type_${LoopKey}": {"Type": "custom_type", "Properties": {"property": "value"}}}, "extra_loop_entry"]}
        self.assertEqual(safe_dict(d), d)

    def test_safe_dict_with_loop_single_resource(self):
        loop_id = "unique_loop_id"
        d = {f"Fn::ForEach::{loop_id}": ["LoopKey", ["LoopKey1", "LoopKey2"], {"custom_type_${LoopKey}": {"Type": "custom_type", "Properties": {"property": "value"}}}]}
        self.assertEqual(safe_dict(d), {f"{loop_id}::{k}": v for k,v in d[f"Fn::ForEach::{loop_id}"][2].items()})

    def test_safe_dict_with_loop_multiple_resources(self):
        loop_id = "unique_loop_id"
        d = {
            f"Fn::ForEach::{loop_id}": ["LoopKey", ["LoopKey1", "LoopKey2"], {
                "custom_type_${LoopKey}": {"Type": "custom_type", "Properties": {"property": "value"}},
                "other_type_${LoopKey}": {"Type": "other_type", "Properties": {"property": "value"}}
            }]
        }

        self.assertEqual(safe_dict(d), {f"{loop_id}::{k}": v for k,v in d[f"Fn::ForEach::{loop_id}"][2].items()})

    def test_safe_dict_with_loop_and_regular_resources(self):
        loop_id = "unique_loop_id"
        d = {
            "resource_id_1": {"Type": "custom_type"},
            f"Fn::ForEach::{loop_id}": ["LoopKey", ["LoopKey1", "LoopKey2"], {
                "custom_type_${LoopKey}": {"Type": "custom_type", "Properties": {"property": "value"}},
                "other_type_${LoopKey}": {"Type": "other_type", "Properties": {"property": "value"}}
            }],
            "resource_id_2": {"Type": "other_type"}
        }

        regular_resources_expected_dict = {k: d[k] for k in ["resource_id_1", "resource_id_2"]}
        loop_expected_dir = {f"{loop_id}::{k}": v for k,v in d[f"Fn::ForEach::{loop_id}"][2].items()}
        self.assertEqual(safe_dict(d), (regular_resources_expected_dict | loop_expected_dir))

    def test_safe_dict_with_multiple_loops(self):
        first_loop_id = "first_loop_id"
        second_loop_id = "second_loop_id"
        d = {
            f"Fn::ForEach::{first_loop_id}": ["LoopKey", ["LoopKey10", "LoopKey11"], {
                "custom_type_${LoopKey}": {"Type": "custom_type", "Properties": {"property": "value"}},
                "other_type_${LoopKey}": {"Type": "other_type", "Properties": {"property": "value"}}
            }],
            f"Fn::ForEach::{second_loop_id}": ["LoopKey", ["LoopKey20", "LoopKey21"], {
                "custom_type_${LoopKey}": {"Type": "custom_type", "Properties": {"property": "value"}},
                "other_type_${LoopKey}": {"Type": "other_type", "Properties": {"property": "value"}}
            }]
        }

        safe_d = safe_dict(d)
        self.assertEqual(len(safe_d), 4)

        first_expected_dict = {f"{first_loop_id}::{k}": v for k,v in d[f"Fn::ForEach::{first_loop_id}"][2].items()}
        second_expected_dict = {f"{second_loop_id}::{k}": v for k,v in d[f"Fn::ForEach::{second_loop_id}"][2].items()}
        self.assertEqual(safe_d, (first_expected_dict | second_expected_dict))

    def test_safe_dict_with_embedded_loops(self):
        outer_loop_id = "outer_loop_id"
        inner_loop_id = "inner_loop_id"
        d = {
            f"Fn::ForEach::{outer_loop_id}": ["LoopKey", ["LoopKey10", "LoopKey11"], {
                "custom_type_${LoopKey}": {"Type": "custom_type", "Properties": {"property": "value"}},
                "other_type_${LoopKey}": {"Type": "other_type", "Properties": {"property": "value"}},
                f"Fn::ForEach::{inner_loop_id}": ["LoopKey", ["LoopKey20", "LoopKey21"], {
                    "custom_type_${LoopKey}": {"Type": "custom_type", "Properties": {"property": "value"}},
                    "other_type_${LoopKey}": {"Type": "other_type", "Properties": {"property": "value"}}
                }]
            }],
        }

        safe_d = safe_dict(d)
        self.assertEqual(len(safe_d), 4)

        outer_loop_expected_dict = {"{}::{}".format(outer_loop_id, k): v for k,v in d[f"Fn::ForEach::{outer_loop_id}"][2].items() if not k.startswith("Fn::ForEach::")}
        inner_loop_expected_dict = {"{}::{}::{}".format(outer_loop_id, inner_loop_id, k.removeprefix('Fn::ForEach::')): v for k,v in d[f"Fn::ForEach::{outer_loop_id}"][2][f"Fn::ForEach::{inner_loop_id}"][2].items()}
        self.assertEqual(safe_d, (outer_loop_expected_dict | inner_loop_expected_dict))
