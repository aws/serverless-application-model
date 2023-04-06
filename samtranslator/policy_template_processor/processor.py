import json
from pathlib import Path
from typing import Any, Dict, Optional

import jsonschema
from jsonschema.exceptions import ValidationError

from samtranslator import policy_templates_data
from samtranslator.policy_template_processor.exceptions import TemplateNotFoundException
from samtranslator.policy_template_processor.template import Template


class PolicyTemplatesProcessor:
    """
    Policy templates are equivalents of managed policies that can be customized with specific resource name or ARNs.
    This class encapsulates reading, parsing and converting these templates into regular policy statements that
    IAM will accept.

    Structure of the policy templates object is as follows (Consult the JSON Schema for more detailed & accurate
    schema)

    ```yaml
    Version: semver version of this document

    Templates:
        # Name of the policy template - Ex: TemplateAmazonDynamoDBFullAccess
        <policy-template-name>:

          # List of parameters supported by this template. Only the params in this list will be replaced
          Parameters:
            TableNameParam:
              Description: Name of the DynamoDB table to give access to

          # Actual template that will be substituted
          Definition:
          - Effect: Allow
            Action:
            - dynamodb:PutItem
            Resource:
              Fn::Sub:
              - arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${TableName}
              - TableName:
                  Ref: TableNameParam
    ```

    """

    # ./schema.json
    SCHEMA_LOCATION = policy_templates_data.SCHEMA_FILE

    # ./policy_templates.json
    DEFAULT_POLICY_TEMPLATES_FILE = policy_templates_data.POLICY_TEMPLATES_FILE

    def __init__(self, policy_templates_dict: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the class

        :param policy_templates_dict: Dictionary containing the policy templates definition
        :param dict schema: Dictionary containing the JSON Schema of policy templates
        :raises ValueError: If policy templates does not match up with the schema
        """
        PolicyTemplatesProcessor._is_valid_templates_dict(policy_templates_dict, schema)

        self.policy_templates = {}
        for template_name, template_value_dict in policy_templates_dict["Templates"].items():
            self.policy_templates[template_name] = Template.from_dict(template_name, template_value_dict)  # type: ignore[no-untyped-call]

    def has(self, template_name):  # type: ignore[no-untyped-def]
        """
        Is this template available?

        :param template_name: Name of the template
        :return: True, if template name is available. False otherwise
        """
        return template_name in self.policy_templates

    def get(self, template_name):  # type: ignore[no-untyped-def]
        """
        Get the template for the given name

        :param template_name: Name of the template
        :return policy_template_processor.template.Template: Template object containing the template name & definition.
            None, if the template is not present
        """
        return self.policy_templates.get(template_name, None)

    def convert(self, template_name: str, parameter_values: str) -> Any:
        """
        Converts the given template to IAM-ready policy statement by substituting template parameters with the given
        values.

        :param template_name: Name of the template
        :param parameter_values: Values for all parameters of the template
        :return dict: Dictionary containing policy statement
        :raises ValueError: If the given inputs don't represent valid template
        :raises InsufficientParameterValues: If the parameter values don't have values for all required parameters
        """

        if not self.has(template_name):  # type: ignore[no-untyped-call]
            raise TemplateNotFoundException(template_name)

        template = self.get(template_name)  # type: ignore[no-untyped-call]
        return template.to_statement(parameter_values)

    @staticmethod
    def _is_valid_templates_dict(
        policy_templates_dict: Dict[Any, Any], schema: Optional[Dict[Any, Any]] = None
    ) -> bool:
        """
        Is this a valid policy template dictionary

        :param dict policy_templates_dict: Data to be validated
        :param dict schema: Optional, dictionary containing JSON Schema representing policy template
        :return: True, if it is valid.
        :raises ValueError: If the template dictionary doesn't match up with the schema
        """

        if not schema:
            schema = PolicyTemplatesProcessor._read_schema()

        try:
            jsonschema.validate(policy_templates_dict, schema)
        except ValidationError as ex:
            # Stringifying the exception will give us useful error message
            raise ValueError(str(ex)) from ex

        return True

    @staticmethod
    def get_default_policy_templates_json() -> Any:
        """
        Reads and returns the default policy templates JSON data from file.

        :return dict: Dictionary containing data read from default policy templates JSON file
        """

        return PolicyTemplatesProcessor._read_json(PolicyTemplatesProcessor.DEFAULT_POLICY_TEMPLATES_FILE)

    @staticmethod
    def _read_schema() -> Any:
        """
        Reads the JSON Schema at given file path

        :param string schema_file: Optional path to the schema file. If not provided, the system configured value
            will be used
        :return dict: JSON Schema of the policy template
        """

        return PolicyTemplatesProcessor._read_json(PolicyTemplatesProcessor.SCHEMA_LOCATION)

    @staticmethod
    def _read_json(filepath: Path) -> Any:
        """
        Helper method to read a JSON file
        :param filepath: Path to the file
        :return dict: Dictionary containing file data
        """
        with filepath.open(encoding="utf-8") as fp:
            return json.load(fp)
