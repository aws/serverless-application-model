from typing import Any

from samtranslator.intrinsics.actions import RefAction
from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.policy_template_processor.exceptions import InsufficientParameterValues, InvalidParameterValues

POLICY_PARAMETER_DISAMBIGUATE_PREFIX = "___SAM_POLICY_PARAMETER_"


class Template:
    """
    Class representing a single policy template. It includes the name, parameters and template dictionary.
    """

    def __init__(self, template_name, parameters, template_definition) -> None:  # type: ignore[no-untyped-def]
        """
        Initialize a template.
        For simplicity, this method assumes that inputs have already been validated against the JSON Schema. So no
        further validation is performed.

        :param string template_name: Name of this template
        :param dict parameters: Dictionary representing parameters. Refer to the JSON Schema for structure of this dict
        :param template_definition: Template definition. Refer to JSON Schema for structure of this dict
        :raises ValueError: If one or more of the parameters are not referenced in the template definition
        """
        self.name = template_name
        self.parameters = parameters
        self.definition = template_definition

    def to_statement(self, parameter_values):  # type: ignore[no-untyped-def]
        """
        With the given values for each parameter, this method will return a policy statement that can be used
        directly with IAM.

        :param dict parameter_values: Dict containing values for each parameter defined in the template
        :return dict: Dictionary containing policy statement
        :raises InvalidParameterValues: If parameter values is not a valid dictionary or does not contain values
            for all parameters
        :raises InsufficientParameterValues: If the parameter values don't have values for all required parameters
        """

        missing = self.missing_parameter_values(parameter_values)  # type: ignore[no-untyped-call]
        if len(missing) > 0:
            # str() of elements of list to prevent any `u` prefix from being displayed in user-facing error message
            raise InsufficientParameterValues(
                f"Following required parameters of template '{self.name}' don't have values: {[str(m) for m in missing]}"
            )

        # Select only necessary parameter_values. this is to prevent malicious or accidental
        # injection of values for parameters not intended in the template. This is important because "Ref" resolution
        # will substitute any references for which a value is provided.
        necessary_parameter_values = {
            POLICY_PARAMETER_DISAMBIGUATE_PREFIX + name: value
            for name, value in parameter_values.items()
            if name in self.parameters
        }

        # Only "Ref" is supported
        supported_intrinsics = {RefAction.intrinsic_name: RefAction()}

        resolver = IntrinsicsResolver(necessary_parameter_values, supported_intrinsics)
        definition_copy = self._disambiguate_policy_parameter(self.definition)

        return resolver.resolve_parameter_refs(definition_copy)

    @staticmethod
    def _disambiguate_policy_parameter(policy_definition: Any) -> Any:
        """
        Return a deepcopy of policy definition where all parameters are
        renamed to avoid naming collision of normal CFN parameters.
        This is to avoid IntrinsicResolver.resolve_parameter_refs()
        will make infinitely recursion on this:
        ```
        - DynamoDBCrudPolicy:
          TableName:  <- this is the policy parameter
            Fn::ImportValue:
              Fn::Join:
              - '-'
              - - Ref: TableName <- this is the CFN parameter
                - hello
                - Ref: EnvironmentType
        ```
        Once IntrinsicResolver.resolve_parameter_refs() replace the "Ref: TableName"
        with "TableName: .... Ref: TableName - hello ---"
        There are "Ref: TableName" in it again (indefinitely).
        """

        def _traverse(node: Any) -> Any:
            if isinstance(node, dict):
                copy = {key: _traverse(value) for key, value in node.items()}
                if "Ref" in copy and isinstance(copy["Ref"], str):
                    copy["Ref"] = POLICY_PARAMETER_DISAMBIGUATE_PREFIX + copy["Ref"]
                return copy
            if isinstance(node, list):
                return [_traverse(item) for item in node]
            return node

        return _traverse(policy_definition)

    def missing_parameter_values(self, parameter_values):  # type: ignore[no-untyped-def]
        """
        Checks if the given input contains values for all parameters used by this template

        :param dict parameter_values: Dictionary of values for each parameter used in the template
        :return list: List of names of parameters that are missing.
        :raises InvalidParameterValues: When parameter values is not a valid dictionary
        """

        if not self._is_valid_parameter_values(parameter_values):  # type: ignore[no-untyped-call]
            raise InvalidParameterValues("Parameter values are required to process a policy template")

        return list(set(self.parameters.keys()) - set(parameter_values.keys()))

    @staticmethod
    def _is_valid_parameter_values(parameter_values):  # type: ignore[no-untyped-def]
        """
        Checks if the given parameter values dictionary is valid
        :param dict parameter_values:
        :return: True, if it is valid. False otherwise
        """
        return parameter_values is not None and isinstance(parameter_values, dict)

    @staticmethod
    def from_dict(template_name, template_values_dict):  # type: ignore[no-untyped-def]
        """
        Parses the input and returns an instance of this class.

        :param string template_name: Name of the template
        :param dict template_values_dict: Dictionary containing the value of the template. This dict must have passed
            the JSON Schema validation.
        :return Template: Instance of this class containing the values provided in this dictionary
        """

        parameters = template_values_dict.get("Parameters", {})
        definition = template_values_dict.get("Definition", {})

        return Template(template_name, parameters, definition)
