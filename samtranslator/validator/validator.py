import json
import re

import jsonschema
from jsonschema.exceptions import ValidationError

from . import sam_schema

ERRORS_MAPPING = {
    "None is not of type 'object'": "Must not be empty",
    "None is not of type 'string'": "Must not be empty",
    "None is not of type 'boolean'": "Must not be empty",
    "None is not of type 'integer'": "Must not be empty",
    "None is not of type 'array'": "Must not be empty",
    "None is not of type 'number'": "Must not be empty",
}


class SamTemplateValidator(object):
    """
    SAM template validator
    """

    def __init__(self, schema_path=None):
        """
        Constructor

        Parameters
        ----------
        schema_path : str, optional
            Path to a schema to use for validation, by default None, the default schema.json will be used
        """
        super().__init__()

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

        validation_errors = self.validator.iter_errors(template_dict)

        # List of
        # [/Path/To/Element] Error message. Context: additional context (if any)
        formatted_errors = []

        for e in validation_errors:
            self._process_error(e, formatted_errors)

        return formatted_errors

    def _process_error(self, error, formatted_errors, parent_path=""):
        if error is None:
            return

        # [/Path/To/Element] Error message
        error_content = "[{}/{}] {}".format(
            parent_path, "/".join([str(p) for p in error.path]), self._cleanup_error_message(error.message)
        )

        if error_content and error_content not in formatted_errors:
            # Remove duplicates
            formatted_errors.append(error_content)

        for context_error in error.context:
            # Each context item is also a validation error
            self._process_error(context_error, formatted_errors, "/__" + parent_path)

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
        final_message = message

        if final_message.endswith(" under any of the given schemas"):
            final_message = "Is not valid"

        final_message = ERRORS_MAPPING.get(final_message, final_message)

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
        with open(filepath, "r") as fp:
            return json.load(fp)
