import pytest
from samtranslator.model.types import IS_INT, dict_of, is_type, list_of, one_of


class DummyType:
    pass


def test_is_type_validator():
    example_properties = [(1, int), ("Hello, World!", str), ({"1": 1}, dict), (DummyType(), DummyType)]

    for value, value_type in example_properties:
        # Check that is_type(value_type) passes for value
        validate = is_type(value_type)
        assert validate(value), f"is_type validator failed for type {value_type}, value {value}"

        # For every non-matching type, check that is_type(other_type) raises TypeError
        for _, other_type in example_properties:
            if value_type != other_type:
                validate = is_type(other_type)
                assert not validate(
                    value, should_raise=False
                ), f"is_type validator unexpectedly succeeded for type {value_type}, value {value}"
                with pytest.raises(TypeError):
                    validate(value)


@pytest.mark.parametrize(
    "value,item_type,should_pass",
    [
        # List of expected type
        ([1, 2, 3], int, True),
        # List of mixed types
        ([1, 2, "Hello, world!", 3], int, False),
        # Not a list
        (1, int, False),
    ],
)
def test_list_of_validator(value, item_type, should_pass):
    validate = list_of(is_type(item_type))
    if should_pass:
        assert validate(value), f"list_of validator failed for item type {item_type}, value {value}"
    else:
        assert not validate(
            value, should_raise=False
        ), f"list_of validator unexpectedly succeeded for item type {item_type}, value {value}"
        with pytest.raises(TypeError):
            validate(value)


@pytest.mark.parametrize(
    "value,key_type,value_type,should_pass",
    [
        # Dict of expected types
        ({str(i): i for i in range(5)}, str, int, True),
        # Dict of mixed keys
        ({"1": 1, 2: 2}, str, int, False),
        # Dict of mixed values
        ({"1": "1", "2": 2}, str, int, False),
        # Dict of mixed keys and values
        ({"1": "1", 2: 2}, str, int, False),
        # Not a dict
        (("1", 2), str, int, False),
    ],
)
def test_dict_of_validator(value, key_type, value_type, should_pass):
    validate = dict_of(is_type(key_type), is_type(value_type))
    if should_pass:
        assert validate(
            value
        ), f"dict_of validator failed for key type {key_type}, item type {value_type}, value {value}"
    else:
        assert not validate(
            value, should_raise=False
        ), f"dict_of validator unexpectedly succeeded for key type {key_type}, item type {value_type}, value {value}"
        with pytest.raises(TypeError):
            validate(value)


@pytest.mark.parametrize(
    "value,validators,should_pass",
    [
        # Value of first expected type
        (1, [IS_INT, list_of(IS_INT)], True),
        # Value of second expected type
        ([1, 2, 3], [IS_INT, list_of(IS_INT)], True),
        # Value of neither expected type
        ("Hello, World!", [IS_INT, list_of(IS_INT)], False),
    ],
)
def test_one_of_validator(value, validators, should_pass):
    validate = one_of(*validators)
    if should_pass:
        assert validate(value), f"one_of validator failed for validators {validators}, value {value}"
    else:
        assert not validate(
            value, should_raise=False
        ), f"one_of validator unexpectedly succeeded for validators {validators}, value {value}"
        with pytest.raises(TypeError):
            validate(value)
