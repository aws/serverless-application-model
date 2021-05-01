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
    # Example: "u'integer'" -> "'integer'"
    # The validator returns types in error messages prefixed with 'u' on Python2
    UNICODE_TYPE_REGEX = re.compile("u('[^']+')")

    def __init__(self, schema_path=None):
        """
        Constructor

        Parameters
        ----------
        schema_path : str, optional
            Path to a schema to use for validation, by default None, the default schema.json will be used
        """
        if not schema_path:
            schema_content = self._read_default_schema()
        else:
            schema_content = self._read_json(schema_path)

        # Helps resolve the $Ref to external files
        # schema_content must be passed to resolve local (#/def...) references
        resolver = jsonschema.RefResolver("file://" + sam_schema.SCHEMA_DIR + "/", schema_content)

        self.validator = jsonschema.Draft7Validator(schema_content, resolver=resolver)

    def validate(self, template_dict):
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

        # Dicts of "[/Path/To/Element] Error message" -> None
        # Dicts instead of Lists, for speed
        formatted_errors = OrderedDict()
        sibling_errors = OrderedDict()

        for e in validation_errors:
            self._process_error(e, formatted_errors, sibling_errors)

        return list(formatted_errors.keys())

    def _process_error(self, error, formatted_errors, sibling_errors):
        """
        Processes the validation errors recursively
        Each error can have a list of child errors in its 'context' attribute (Tree or errors)

        Parameters
        ----------
        error : Error
            Error at the head
        formatted_errors : OrderedDict
            Final list of formatted errors
        sibling_errors : OrderedDict
            List of the current level errors, used to eliminate duplicates on a level
        """
        if error is None:
            return

        if not error.context:
            # We only display the leaves
            # Format the message:
            # [/Path/To/Element] Error message
            error_content = "[{}] {}".format(
                "/".join([str(p) for p in error.absolute_path]), self._cleanup_error_message(error.message)
            )

            if error_content not in sibling_errors:
                # Not already present in the current level errors
                # We set the value to None as we don't use it
                formatted_errors[error_content] = None
            return

        child_errors = OrderedDict()

        for context_error in error.context:
            # Each context item is also a validation error
            self._process_error(context_error, formatted_errors, child_errors)

    def _cleanup_error_message(self, message):
        """
        Cleans an error message up to remove unecessary clutter or replace
        it with a more meaningful one

        Parameters
        ----------
        message : str
            Message to clean

        Returns
        -------
        str
            Cleaned message
        """
        final_message = re.sub(self.UNICODE_TYPE_REGEX, r"\1", message)

        if final_message.endswith(" under any of the given schemas"):
            return "Is not valid"
        if final_message.startswith("None is not of type "):
            return "Must not be empty"

        return final_message

    def _read_default_schema(self):
        """
        Returns the content of the default schema

        Returns
        -------
        dict
            Content of the default schema
        """
        return self._read_json(sam_schema.SCHEMA_FILE)

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
