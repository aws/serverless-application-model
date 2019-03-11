import json

import jsonschema
from jsonschema.exceptions import ValidationError

from . import sam_schema


class SamTemplateValidator(object):

    @staticmethod
    def validate(template_dict, schema=None):
        """
        Is this a valid SAM template dictionary

        :param dict template_dict: Data to be validated
        :param dict schema: Optional, dictionary containing JSON Schema representing SAM template
        :return: Empty string if there are no validation errors in template
        """

        if not schema:
            schema = SamTemplateValidator._read_schema()

        validation_errors = ""

        try:
            jsonschema.validate(template_dict, schema)
        except ValidationError as ex:
            # Stringifying the exception will give us useful error message
            validation_errors = str(ex)
            # Swallowing expected exception here as our caller is expecting validation errors and
            # not the valiation exception itself
            pass

        return validation_errors

    @staticmethod
    def _read_schema():
        """
        Reads the JSON Schema at given file path

        :param string schema_file: Optional path to the schema file. If not provided, the system configured value
            will be used
        :return dict: JSON Schema of the policy template
        """
        return SamTemplateValidator._read_json(sam_schema.SCHEMA_FILE)

    @staticmethod
    def _read_json(filepath):
        """
        Helper method to read a JSON file
        :param filepath: Path to the file
        :return dict: Dictionary containing file data
        """
        with open(filepath, "r") as fp:
            return json.load(fp)
