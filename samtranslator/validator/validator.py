import json
import os
import re
from pathlib import Path
from typing import Any

import jsonschema

from samtranslator.internal.deprecation_control import deprecated

from . import sam_schema


class SamTemplateValidator:
    """
    SAM function validation, on the deprecation path.
    """

    UNICODE_TYPE_REGEX = re.compile("u('[^']+')")

    @deprecated()
    def __init__(self, schema=None) -> None:  # type: ignore[no-untyped-def]
        """
        Constructor
        Parameters
        ----------
        schema_path : str, optional
            Path to a schema to use for validation, by default None, the default schema.json will be used
        """
        if not schema:
            schema = self._read_json(sam_schema.SCHEMA_NEW_FILE)

        # Helps resolve the $Ref to external files
        # For cross platform resolving, we have to load the sub schemas into
        # a store and pass it to the Resolver. We cannot use the "file://" style
        # of referencing inside a "$ref" of a schema as this will lead to mixups
        # on Windows because of different path separator: \\ instead of /
        schema_store = {}
        definitions_dir = sam_schema.SCHEMA_DIR / "definitions"

        for sub_schema in os.listdir(definitions_dir):
            if sub_schema.endswith(".json"):
                with (definitions_dir / sub_schema).open(encoding="utf-8") as f:
                    schema_content = f.read()
                schema_store[sub_schema] = json.loads(schema_content)

        resolver = jsonschema.RefResolver.from_schema(schema, store=schema_store)  # type: ignore[no-untyped-call]

        SAMValidator = jsonschema.validators.extend(
            jsonschema.Draft7Validator,
            type_checker=jsonschema.Draft7Validator.TYPE_CHECKER.redefine_many(
                {"object": is_object, "intrinsic": is_intrinsic}
            ),
        )
        self.validator = SAMValidator(schema, resolver=resolver)

    @staticmethod
    @deprecated()
    def validate(template_dict, schema=None):  # type: ignore[no-untyped-def]
        """
        Validates a SAM Template
        [DEPRECATED]: Instanciate this class and use the get_errors instead:
            validator = SamTemplateValidator()
            validator.get_errors(template_dict)
        Kept for backward compatibility
        Parameters
        ----------
        template_dict : dict
            Template
        schema : dict, optional
            Schema content, defaults to the integrated schema
        Returns
        -------
        str
            Validation errors separated by commas ","
        """
        validator = SamTemplateValidator(schema)

        return ", ".join(validator.get_errors(template_dict))

    @deprecated()
    def get_errors(self, template_dict):  # type: ignore[no-untyped-def]
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

        # Set of "[Path.To.Element] Error message"
        # To track error uniqueness, Dict instead of List, for speed
        errors_set = {}  # type: ignore[var-annotated]

        for e in validation_errors:
            self._process_error(e, errors_set)  # type: ignore[no-untyped-call]

        # To be consistent across python versions 2 and 3, we have to sort the final result
        # It seems that the validator is not receiving the properties in the same order between python 2 and 3
        # It thus returns errors in a different order
        return sorted(errors_set.keys())

    def _process_error(self, error, errors_set):  # type: ignore[no-untyped-def]
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
            # Format the message with pseudo JSON Path:
            # [Path.To.Element] Error message
            error_path = ".".join([str(p) for p in error.absolute_path]) if error.absolute_path else "."

            error_content = f"[{error_path}] {self._cleanup_error_message(error)}"  # type: ignore[no-untyped-call]

            if error_content not in errors_set:
                # We set the value to None as we don't use it
                errors_set[error_content] = None
            return

        for context_error in error.context:
            # Each "context" item is also a validation error
            self._process_error(context_error, errors_set)  # type: ignore[no-untyped-call]

    def _cleanup_error_message(self, error):  # type: ignore[no-untyped-def]
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
        if final_message.startswith(("None is not of type ", "None is not one of ")):
            return "Must not be empty"
        if " does not match " in final_message and "patternError" in error.schema:
            return re.sub("does not match .+", error.schema.get("patternError"), final_message)

        return final_message

    def _read_json(self, filepath: Path) -> Any:
        """
        Returns the content of a JSON file
        Parameters
        ----------
        filepath : Path
            File path
        Returns
        -------
        dict
            Dictionary representing the JSON content
        """
        with filepath.open(encoding="utf-8") as fp:
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
