import hashlib
import json

from unittest import TestCase
from mock import patch
from samtranslator.translator.logical_id_generator import LogicalIdGenerator


class TestLogicalIdGenerator(TestCase):
    """
    Test the implementation of LogicalIDGenerator
    """

    def setUp(self):
        self.prefix = "prefix"

    @patch.object(LogicalIdGenerator, "_stringify")
    def test_gen_no_data(self, stringify_mock):

        generator = LogicalIdGenerator(self.prefix)

        self.assertEqual(self.prefix, generator.gen())

        # Calling gen() again should return the same result
        self.assertEqual(generator.gen(), generator.gen())

        stringify_mock.assert_not_called()

    @patch.object(LogicalIdGenerator, "get_hash")
    @patch.object(LogicalIdGenerator, "_stringify")
    def test_gen_dict_data(self, stringify_mock, get_hash_mock):
        data = {"foo": "bar"}
        stringified_data = "stringified data"
        hash_value = "some hash value"
        get_hash_mock.return_value = hash_value
        stringify_mock.return_value = stringified_data

        generator = LogicalIdGenerator(self.prefix, data_obj=data)

        expected = "{}{}".format(self.prefix, hash_value)
        self.assertEqual(expected, generator.gen())
        get_hash_mock.assert_called_once_with()
        stringify_mock.assert_called_once_with(data)

        self.assertEqual(generator.gen(), generator.gen())

    @patch.object(LogicalIdGenerator, "_stringify")
    def test_gen_hash_data_override(self, stringify_mock):
        data = {"foo": "bar"}
        stringified_data = "stringified data"
        hash_value = "6b86b273ff"
        stringify_mock.return_value = stringified_data

        generator = LogicalIdGenerator(self.prefix, data_obj=data, data_hash=hash_value)

        expected = "{}{}".format(self.prefix, hash_value)
        self.assertEqual(expected, generator.gen())
        stringify_mock.assert_called_once_with(data)

        self.assertEqual(generator.gen(), generator.gen())

    @patch.object(LogicalIdGenerator, "_stringify")
    def test_gen_hash_data_empty(self, stringify_mock):
        data = {"foo": "bar"}
        stringified_data = "stringified data"
        hash_value = ""
        stringify_mock.return_value = stringified_data

        generator = LogicalIdGenerator(self.prefix, data_obj=data, data_hash=hash_value)

        stringify_mock.assert_called_once_with(data)
        self.assertEqual(generator.gen(), generator.gen())

    def test_gen_stability_with_copy(self):
        data = {"foo": "bar", "a": "b"}
        generator = LogicalIdGenerator(self.prefix, data_obj=data)

        old = generator.gen()
        new = LogicalIdGenerator(self.prefix, data_obj=data.copy()).gen()  # Create a copy of data obj
        self.assertEqual(old, new)

    def test_gen_stability_with_different_dict_ordering(self):
        data = {"foo": "bar", "nested": {"a": "b", "c": "d"}}
        data_other = {"nested": {"c": "d", "a": "b"}, "foo": "bar"}  # Same content but different ordering of keys
        generator = LogicalIdGenerator(self.prefix, data_obj=data)

        old = generator.gen()
        new = LogicalIdGenerator(self.prefix, data_obj=data_other).gen()
        self.assertEqual(old, new)

    def test_gen_changes_on_different_dict_data(self):
        data = {"foo": "bar", "nested": {"a": "b", "c": "d"}}
        data_other = {"foo2": "bar", "nested": {"a": "b", "c": "d"}}  # Just changing one key

        old = LogicalIdGenerator(self.prefix, data_obj=data)
        new = LogicalIdGenerator(self.prefix, data_obj=data_other).gen()
        self.assertNotEqual(old, new)

    def test_gen_changes_on_different_string_data(self):
        data = "some data"
        data_other = "some other data"

        old = LogicalIdGenerator(self.prefix, data_obj=data)
        new = LogicalIdGenerator(self.prefix, data_obj=data_other).gen()
        self.assertNotEqual(old, new)

    @patch.object(LogicalIdGenerator, "get_hash")
    @patch.object(LogicalIdGenerator, "_stringify")
    def test_error_stringifying(self, stringify_mock, get_hash_mock):
        data = {"foo": "bar"}
        hash_value = "some hash value"
        get_hash_mock.return_value = hash_value
        stringify_mock.side_effect = TypeError("error")

        with self.assertRaises(TypeError):
            LogicalIdGenerator(self.prefix, data_obj=data)

        get_hash_mock.assert_not_called()

    @patch.object(LogicalIdGenerator, "_stringify")
    def testget_hash(self, stringify_mock):
        data = "some data"
        stringified_data = "some stringified data"
        stringify_mock.return_value = stringified_data

        generator = LogicalIdGenerator(self.prefix, data_obj=data)

        # We are essentially duplicating the implementation here. This is done on purpose to prevent
        # accidental change of the algorithm. Any changes to the hash generation must be backwards compatible.
        # This test will help catch such issues before hand.
        utf_data = str(stringified_data).encode("utf8")
        expected = hashlib.sha1(bytes(utf_data)).hexdigest()[:10]
        self.assertEqual(expected, generator.get_hash())

        stringify_mock.assert_called_once_with(data)

    @patch.object(LogicalIdGenerator, "_stringify")
    def testget_hash_no_data(self, stringify_mock):
        data = "some data"
        stringified_data = None
        stringify_mock.return_value = stringified_data

        generator = LogicalIdGenerator(self.prefix, data_obj=data)

        self.assertEqual("", generator.get_hash())

        stringify_mock.assert_called_once_with(data)

    def test_stringify_basic_objects(self):
        data = {"a": "b", "c": [4, 3, 1]}
        expected = '{"a":"b","c":[4,3,1]}'
        generator = LogicalIdGenerator(self.prefix, data_obj=data)

        self.assertEqual(expected, generator._stringify(data))

    def test_stringify_basic_objects_sorting(self):
        data = {"c": [4, 3, 1], "a": "b"}
        expected = '{"a":"b","c":[4,3,1]}'
        generator = LogicalIdGenerator(self.prefix, data_obj=data)

        self.assertEqual(expected, generator._stringify(data))

    def test_stringify_array_sorting(self):
        data = ["a", 1, {"z": "x", "b": "d"}]
        expected = '["a",1,{"b":"d","z":"x"}]'
        generator = LogicalIdGenerator(self.prefix, data_obj=data)

        self.assertEqual(expected, generator._stringify(data))

    def test_stringify_strings(self):
        data = "some data"
        generator = LogicalIdGenerator(self.prefix, data_obj=data)

        # Strings should be returned unmodified ie. json dump is short circuited
        self.assertEqual(data, generator._stringify(data))

    @patch.object(json, "dumps")
    def test_stringify_expectations(self, json_dumps_mock):
        data = ["foo"]
        expected = "bar"
        json_dumps_mock.return_value = expected

        generator = LogicalIdGenerator(self.prefix, data_obj=data)
        self.assertEqual(expected, generator._stringify(data))

        json_dumps_mock.assert_called_with(data, separators=(",", ":"), sort_keys=True)

    @patch.object(json, "dumps")
    def test_stringify_expectations_for_string(self, json_dumps_mock):
        data = "foo"

        generator = LogicalIdGenerator(self.prefix, data_obj=data)
        self.assertEqual(data, generator._stringify(data))

        json_dumps_mock.assert_not_called()
