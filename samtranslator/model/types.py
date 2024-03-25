"""
Validators for Resource Properties

Each function in this module returns a validator--that is, a function which takes the value of a Property and returns
True if the Property value is considered valid, and raises TypeError if it is invalid.

Validators should cover any validation logic that is *not* done by CloudFormation. For example, in a SAM Function,
the Permissions property is an ARN or list of ARNs. In this situation, we validate that the Permissions property is
either a string or a list of strings, but do not validate whether the string(s) are valid IAM policy ARNs.
"""

from typing import Any, Callable, Type, Union

import samtranslator.model.exceptions
from samtranslator.internal.deprecation_control import deprecated

# Validator always looks like def ...(value: Any, should_raise: bool = True) -> bool,
# However, Python type hint doesn't support functions with optional keyword argument
# > There is no syntax to indicate optional or keyword arguments; such function types
# > are rarely used as callback types. Callable[..., ReturnType] (literal ellipsis)
# > can be used to type hint a callable taking any number of arguments and returning ReturnType
# > https://docs.python.org/3/library/typing.html#typing.Callable
Validator = Callable[..., bool]


def is_type(valid_type: Type[Any]) -> Validator:
    """Returns a validator function that succeeds only for inputs of the provided valid_type.

    :param type valid_type: the type that should be considered valid for the validator
    :returns: a function which returns True its input is an instance of valid_type, and raises TypeError otherwise
    :rtype: callable
    """

    def validate(value: Any, should_raise: bool = True) -> bool:
        if not isinstance(value, valid_type):
            if should_raise:
                raise TypeError(f"Expected value of type {valid_type}, actual value was of type {type(value)}.")
            return False
        return True

    return validate


IS_DICT = is_type(dict)
IS_STR = is_type(str)
IS_BOOL = is_type(bool)
IS_LIST = is_type(list)
IS_INT = is_type(int)


def list_of(validate_item: Union[Type[Any], Validator]) -> Validator:
    """Returns a validator function that succeeds only if the input is a list, and each item in the list passes as input
    to the provided validator validate_item.

    :param callable validate_item: the validator function or type casting function (e.g., str()) for items in the list
    :returns: a function which returns True its input is an list of valid items, and raises TypeError otherwise
    :rtype: callable
    """

    def validate(value: Any, should_raise: bool = True) -> bool:
        validate_type = is_type(list)
        if not validate_type(value, should_raise=should_raise):
            return False

        for item in value:
            try:
                validate_item(item)
            except TypeError as e:
                if should_raise:
                    samtranslator.model.exceptions.prepend(e, "list contained an invalid item")  # type: ignore[no-untyped-call]
                    raise
                return False
        return True

    return validate


def dict_of(validate_key: Validator, validate_item: Validator) -> Validator:
    """Returns a validator function that succeeds only if the input is a dict, and each key and value in the dict passes
    as input to the provided validators validate_key and validate_item, respectively.

    :param callable validate_key: the validator function for keys in the dict
    :param callable validate_item: the validator function for values in the list
    :returns: a function which returns True its input is an dict of valid items, and raises TypeError otherwise
    :rtype: callable
    """

    def validate(value: Any, should_raise: bool = True) -> bool:
        validate_type = IS_DICT
        if not validate_type(value, should_raise=should_raise):
            return False

        for key, item in value.items():
            try:
                validate_key(key)
            except TypeError as e:
                if should_raise:
                    samtranslator.model.exceptions.prepend(e, "dict contained an invalid key")  # type: ignore[no-untyped-call]
                    raise
                return False

            try:
                validate_item(item)
            except TypeError as e:
                if should_raise:
                    samtranslator.model.exceptions.prepend(e, "dict contained an invalid value")  # type: ignore[no-untyped-call]
                    raise
                return False
        return True

    return validate


def one_of(*validators: Validator) -> Validator:
    """Returns a validator function that succeeds only if the input passes at least one of the provided validators.

    :param callable validators: the validator functions
    :returns: a function which returns True its input passes at least one of the validators, and raises TypeError
              otherwise
    :rtype: callable
    """

    def validate(value: Any, should_raise: bool = True) -> bool:
        if any(validate(value, should_raise=False) for validate in validators):
            return True

        if should_raise:
            raise TypeError("value did not match any allowable type")
        return False

    return validate


def any_type() -> Validator:
    def validate(value: Any, should_raise: bool = False) -> bool:
        return True

    return validate


@deprecated(replacement="IS_STR")
def is_str() -> Validator:
    """
    For compatibility reason, we need this `is_str()` as it
    is consumed by old versions of AWS SAM CLI (<1.71.0).

    Related PRs/commits:
    https://github.com/aws/serverless-application-model/pull/2752
    https://github.com/aws/aws-sam-cli/commit/d18f57c5f39273a04fb582f90e6c5817a4651912
    """
    return IS_STR


# Value passed directly to CloudFormation; not used by SAM
PassThrough = Any  # TODO: Make it behave like typescript's unknown
