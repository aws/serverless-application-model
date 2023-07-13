import re

from samtranslator.internal.deprecation_control import deprecated


class SamTemplateValidator:
    """
    Using dummy values; unused code.
    """

    UNICODE_TYPE_REGEX = re.compile("u('[^']+')")

    @deprecated()
    def __init__(self, schema=None) -> None:  # type: ignore[no-untyped-def]
        pass

    @staticmethod
    @deprecated()
    def validate(template_dict, schema=None):  # type: ignore[no-untyped-def]
        return ""

    @deprecated()
    def get_errors(self, template_dict):  # type: ignore[no-untyped-def]
        return []


# Type definition redefinitions
INTRINSIC_ATTR = {
    "Fn::And",
    "Fn::Base64",
    "Fn::Cidr",
    "Fn::Equals",
    "Fn::FindInMap",
    "Fn::GetAtt",
    "Fn::GetAZs",
    "Fn::If",
    "Fn::ImportValue",
    "Fn::Join",
    "Fn::Not",
    "Fn::Or",
    "Fn::Select",
    "Fn::Split",
    "Fn::Sub",
    "Fn::Transform",
    "Ref",
}


def is_object(checker, instance):  # type: ignore[no-untyped-def]
    """
    'object' type definition
    Overloaded to exclude intrinsic functions

    Parameters
    ----------
    checker : dict
        Checker
    instance : element
        Template element

    Returns
    -------
    boolean
        True if an object, False otherwise
    """
    return isinstance(instance, dict) and not has_intrinsic_attr(instance)  # type: ignore[no-untyped-call]


def is_intrinsic(checker, instance):  # type: ignore[no-untyped-def]
    """
    'intrinsic' type definition

    Parameters
    ----------
    checker : dict
        [description]
    instance : [type]
        [description]

    Returns
    -------
    [type]
        [description]
    """
    return isinstance(instance, dict) and has_intrinsic_attr(instance)  # type: ignore[no-untyped-call]


def has_intrinsic_attr(instance):  # type: ignore[no-untyped-def]
    """
    Returns a value indicating whether the instance has an intrinsic attribute
    Only one attribute which must be one of the intrinsics

    Parameters
    ----------
    instance : dict
        Dictionary

    Returns
    -------
    boolean
        True if only has one intrinsic attribute, False otherwise
    """
    return len(instance) == 1 and next(iter(instance)) in INTRINSIC_ATTR
