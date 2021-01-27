import json

import jsonschema
from jsonschema.exceptions import ValidationError

from . import sam_schema

ERRORS_MAPPING = {"None is not of type 'object'": "Must not be empty"}


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
        resolver = jsonschema.RefResolver("file://" + sam_schema.SCHEMA_DIR + "/", None)

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

        validation_errors = list(self.validator.iter_errors(template_dict))

        return [
            "{} (/{})".format(ERRORS_MAPPING.get(e.message, e.message), "/".join(e.path)) for e in validation_errors
        ]

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
