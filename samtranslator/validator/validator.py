from collections import OrderedDict
import json
import re

import jsonschema
from jsonschema.exceptions import ValidationError

from . import sam_schema


class SamTemplateValidator(object):
    """
    SAM template validator
    """

    # Useful to find a unicode prefixed string type to replace it with the non unicode version
    # On Python2, the validator returns types in error messages prefixed with 'u'
    # We remove them to be consistent between python versions
    # Example: "u'integer'" -> "'integer'"
    UNICODE_TYPE_REGEX = re.compile("u('[^']+')")

    def __init__(self, schema=None):
        """
        Constructor

        Parameters
        ----------
        schema_path : str, optional
            Path to a schema to use for validation, by default None, the default schema.json will be used
        """
        # Replaces the static method with the instance method
        # Otherwise the instance would call the static one
        # Static one is kept for backward compatibility
        self.validate = self._validate

        if not schema:
            schema = self._read_json(sam_schema.SCHEMA_NEW_FILE)

        # Helps resolve the $Ref to external files
        # schema content must be passed to resolve local (#/def...) references
        resolver = jsonschema.RefResolver("file://" + sam_schema.SCHEMA_DIR + "/", schema)

        SAMValidator = jsonschema.validators.extend(
            jsonschema.Draft7Validator,
            type_checker=jsonschema.Draft7Validator.TYPE_CHECKER.redefine_many(
                {"object": is_object, "intrinsic": is_intrinsic}
            ),
        )
        self.validator = SAMValidator(schema, resolver=resolver)

    @staticmethod
    def validate(template_dict, schema=None):
        """
        Validates a SAM Template

        [DEPRECATED]: Instanciate this class and use the instance method instead:
            validator = SamTemplateValidator()
            validator.validate(template_dict)

        Parameters
        ----------
        template_dict : dict
            Template
        schema : dict, optional
            Schema content, by default None

        Returns
        -------
        list[str]
            List of validation errors
        """
        validator = SamTemplateValidator(schema)

        return ", ".join(validator.validate(template_dict))

    def _validate(self, template_dict):
        """
        Validates a SAM Template

        Parameters
        ----------
        template_dict : dict
            Template to validate
        schema : str, optional
            Schema content, by default None

        Returns
        -------
        list[str]
            List of validation errors if any, empty otherwise
        """

        # Tree of Error objects
        # Each object can have a list of child errors in its Context attribute
        validation_errors = self.validator.iter_errors(template_dict)

        # Set of "[/Path/To/Element] Error message"
        # To track error uniqueness, Dict instead of List, for speed
        errors_set = {}

        for e in validation_errors:
            self._process_error(e, errors_set)

        # To be consistent across python versions 2 and 3, we have to sort the final result
        # It seems that the validator is not receiving the properties in the same order between python 2 and 3
        # It thus returns errors in a different order
        return sorted(errors_set.keys())

    def _process_error(self, error, errors_set):
        """
        Processes the validation errors recursively
        error is actually a tree of errors
        Each error can have a list of child errors in its 'context' attribute

        Parameters
        ----------
        error : Error
            Error at the head
        errors_set : Dict
            Set of formatted errors
        """
        if error is None:
            return

        if not error.context:
            # We only display the leaves
            # Format the message:
            # [/Path/To/Element] Error message
            error_path = "/".join([str(p) for p in error.absolute_path]) if error.absolute_path else "/"

            error_content = "[{}] {}".format(error_path, self._cleanup_error_message(error))

            if error_content not in errors_set:
                # We set the value to None as we don't use it
                errors_set[error_content] = None
            return

        for context_error in error.context:
            # Each context item is also a validation error
            self._process_error(context_error, errors_set)

    def _cleanup_error_message(self, error):
        """
        Cleans an error message up to remove unecessary clutter or replace
        it with a more meaningful one

        Parameters
        ----------
        error : Error
            Error message to clean

        Returns
        -------
        str
            Cleaned message
        """
        final_message = re.sub(self.UNICODE_TYPE_REGEX, r"\1", error.message)

        if final_message.endswith(" under any of the given schemas"):
            return "Is not valid"
        if final_message.startswith("None is not of type ") or final_message.startswith("None is not one of "):
            return "Must not be empty"
        if " does not match " in final_message and "patternError" in error.schema:
            return re.sub("does not match .+", error.schema.get("patternError"), final_message)

        return final_message

    def _read_json(self, filepath):
        """
        Returns the content of a JSON file

        Parameters
        ----------
        filepath : str
            File path

        Returns
        -------
        dict
            Dictionary representing the JSON content
        """
        with open(filepath) as fp:
            return json.load(fp)


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


def is_object(checker, instance):
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
    return isinstance(instance, dict) and not has_intrinsic_attr(instance)


def is_intrinsic(checker, instance):
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
    return isinstance(instance, dict) and has_intrinsic_attr(instance)


def has_intrinsic_attr(dict):
    """
    Returns a value indicating whether the dict has an intrinsic attribute
    Only one attribute which must be one of the intrinsics

    Parameters
    ----------
    dict : dict
        Dictionary

    Returns
    -------
    boolean
        True if only has one intrinsic attribute, False otherwise
    """
    return len(dict) == 1 and next(iter(dict)) in INTRINSIC_ATTR
