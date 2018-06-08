from unittest import TestCase

import pytest
from parameterized import parameterized

from samtranslator.model.types import is_type, list_of, dict_of, one_of


class DummyType(object):
    pass


class TestTypes(TestCase):
    def test_is_type_validator(self):
        example_properties = [
            (1, int),
            ("Hello, World!", str),
            ({'1': 1}, dict),
            (DummyType(), DummyType)
        ]

        for value, value_type in example_properties:
            # Check that is_type(value_type) passes for value
            validate = is_type(value_type)
            self.assertTrue(validate(value), "is_type validator failed for type {}, value {}".format(value_type, value))

            # For every non-matching type, check that is_type(other_type) raises TypeError
            for _, other_type in example_properties:
                if value_type != other_type:
                    validate = is_type(other_type)
                    self.assertFalse(validate(value,
                                              should_raise=False),
                                     "is_type validator unexpectedly succeeded for type {}, value {}".format(
                                         value_type, value))
                    with pytest.raises(TypeError):
                        validate(value)

    @parameterized.expand([
        # List of expected type
        ([1, 2, 3], int, True),
        # List of mixed types
        ([1, 2, "Hello, world!", 3], int, False),
        # Not a list
        (1, int, False),
    ])
    def test_list_of_validator(self, value, item_type, should_pass):
        validate = list_of(is_type(item_type))
        if should_pass:
            self.assertTrue(validate(value),
                            "list_of validator failed for item type {}, value {}".format(item_type, value))
        else:
            self.assertFalse(validate(value,
                                      should_raise=False),
                             "list_of validator unexpectedly succeeded for item type {}, value {}".format(
                                 item_type, value))
            with pytest.raises(TypeError):
                validate(value)

    @parameterized.expand([
        # Dict of expected types
        ({str(i): i for i in range(5)}, str, int, True),
        # Dict of mixed keys
        ({'1': 1, 2: 2}, str, int, False),
        # Dict of mixed values
        ({'1': '1', '2': 2}, str, int, False),
        # Dict of mixed keys and values
        ({'1': '1', 2: 2}, str, int, False),
        # Not a dict
        (('1', 2), str, int, False)
    ])
    def test_dict_of_validator(self, value, key_type, value_type, should_pass):
        validate = dict_of(is_type(key_type), is_type(value_type))
        if should_pass:
            self.assertTrue(validate(value),
                            "dict_of validator failed for key type {}, item type {}, value {}".format(key_type,
                                                                                                      value_type,
                                                                                                      value))
        else:
            self.assertFalse(validate(value,
                                      should_raise=False),
                             "dict_of validator unexpectedly succeeded for key type {}, item type {}, value {}".format(
                                 key_type, value_type, value))
            with pytest.raises(TypeError):
                validate(value)

    @parameterized.expand([
        # Value of first expected type
        (1, [is_type(int), list_of(is_type(int))], True),
        # Value of second expected type
        ([1, 2, 3], [is_type(int), list_of(is_type(int))], True),
        # Value of neither expected type
        ("Hello, World!", [is_type(int), list_of(is_type(int))], False)
    ])
    def test_one_of_validator(self, value, validators, should_pass):
        validate = one_of(*validators)
        if should_pass:
            self.assertTrue(validate(value),
                            "one_of validator failed for validators {}, value {}".format(validators, value))
        else:
            self.assertFalse(validate(value,
                                      should_raise=False),
                             "one_of validator unexpectedly succeeded for validators {}, value {}".format(
                                 validators, value))
            with pytest.raises(TypeError):
                validate(value)
