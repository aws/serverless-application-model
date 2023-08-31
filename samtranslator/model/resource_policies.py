from collections import namedtuple
from enum import Enum
from typing import Any, Dict, List

from samtranslator.model.exceptions import InvalidTemplateException
from samtranslator.model.intrinsics import (
    is_intrinsic,
    is_intrinsic_if,
    is_intrinsic_no_value,
    validate_intrinsic_if_items,
)

PolicyEntry = namedtuple("PolicyEntry", "data type")


class ResourcePolicies:
    """
    Class encapsulating the policies property of SAM resources. This class strictly encapsulates the data
    and does not take opinions on how to handle them.

    There are three types of policies:
        - Policy Statements
        - AWS or Custom Managed Policy names/arns
        - Policy Templates

    This class is capable of parsing and detecting the type of the policy. Optionally, if policy template information
    is provided to this class, it will detect Policy Templates too.
    """

    POLICIES_PROPERTY_NAME = "Policies"

    def __init__(self, resource_properties: Dict[str, Any], policy_template_processor: Any = None) -> None:
        """
        Initialize with policies data from resource's properties

        :param dict resource_properties: Dictionary containing properties of this resource
        :param policy_template_processor: Optional Instance of PolicyTemplateProcessor that can conclusively detect
            if a given policy is a template or not. If not provided, then this class will not detect policy templates.
        """

        # This variable is required to get policies
        self._policy_template_processor = policy_template_processor

        # Build the list of policies upon construction.
        self.policies = self._get_policies(resource_properties)

    def get(self):  # type: ignore[no-untyped-def]
        """
        Iterator method that "yields" the next policy entry on subsequent calls to this method.

        :yields namedtuple("data", "type"): Yields a named tuple containing the policy data and its type
        """

        yield from self.policies

    def __len__(self):  # type: ignore[no-untyped-def]
        return len(self.policies)

    def _get_policies(self, resource_properties: Dict[str, Any]) -> List[Any]:
        """
        Returns a list of policies from the resource properties. This method knows how to interpret and handle
        polymorphic nature of the policies property.

        Policies can be one of the following:

            * Managed policy name: string
            * List of managed policy names: list of strings
            * IAM Policy document: dict containing Statement key
            * List of IAM Policy documents: list of IAM Policy Document
            * Policy Template: dict with only one key where key is in list of supported policy template names
            * List of Policy Templates: list of Policy Template


        :param dict resource_properties: Dictionary of resource properties containing the policies property.
            It is assumed that this is already a dictionary and contains policies key.
        :return list of PolicyEntry: List of policies, where each item is an instance of named tuple `PolicyEntry`
        """

        policies = None

        if self._contains_policies(resource_properties):  # type: ignore[no-untyped-call]
            policies = resource_properties[self.POLICIES_PROPERTY_NAME]

        if not policies:
            # Policies is None or empty
            return []

        if not isinstance(policies, list):
            # Just a single entry. Make it into a list of convenience
            policies = [policies]

        result = []
        for policy in policies:
            policy_type = self._get_type(policy)  # type: ignore[no-untyped-call]
            entry = PolicyEntry(data=policy, type=policy_type)
            result.append(entry)

        return result

    def _contains_policies(self, resource_properties):  # type: ignore[no-untyped-def]
        """
        Is there policies data in this resource?

        :param dict resource_properties: Properties of the resource
        :return: True if we can process this resource. False, otherwise
        """
        return (
            resource_properties is not None
            and isinstance(resource_properties, dict)
            and self.POLICIES_PROPERTY_NAME in resource_properties
        )

    def _get_type(self, policy):  # type: ignore[no-untyped-def]
        """
        Returns the type of the given policy

        :param string or dict policy: Policy data
        :return PolicyTypes: Type of the given policy. None, if type could not be inferred
        """

        # Must handle intrinsic functions. Policy could be a primitive type or an intrinsic function

        # Managed policies are of type string
        if isinstance(policy, str):
            return PolicyTypes.MANAGED_POLICY

        # Handle the special case for 'if' intrinsic function
        if is_intrinsic_if(policy):
            return self._get_type_from_intrinsic_if(policy)  # type: ignore[no-untyped-call]

        # Intrinsic functions are treated as managed policies by default
        if is_intrinsic(policy):
            return PolicyTypes.MANAGED_POLICY

        # Policy statement is a dictionary with the key "Statement" in it
        if isinstance(policy, dict) and "Statement" in policy:
            return PolicyTypes.POLICY_STATEMENT

        # This could be a policy template then.
        if self._is_policy_template(policy):  # type: ignore[no-untyped-call]
            return PolicyTypes.POLICY_TEMPLATE

        # Nothing matches. Don't take opinions on how to handle it. Instead just set the appropriate type.
        return PolicyTypes.UNKNOWN

    def _is_policy_template(self, policy):  # type: ignore[no-untyped-def]
        """
        Is the given policy data a policy template? Policy templates is a dictionary with one key which is the name
        of the template.

        :param dict policy: Policy data
        :return: True, if this is a policy template. False if it is not
        """

        return (
            self._policy_template_processor is not None
            and isinstance(policy, dict)
            and len(policy) == 1
            and self._policy_template_processor.has(next(iter(policy.keys()))) is True
        )

    def _get_type_from_intrinsic_if(self, policy):  # type: ignore[no-untyped-def]
        """
        Returns the type of the given policy assuming that it is an intrinsic if function

        :param policy: Input value to get type from
        :return: PolicyTypes: Type of the given policy. PolicyTypes.UNKNOWN, if type could not be inferred
        """
        intrinsic_if_value = policy["Fn::If"]

        try:
            validate_intrinsic_if_items(intrinsic_if_value)
        except ValueError as e:
            raise InvalidTemplateException(str(e)) from e

        if_data = intrinsic_if_value[1]
        else_data = intrinsic_if_value[2]

        if_data_type = self._get_type(if_data)  # type: ignore[no-untyped-call]
        else_data_type = self._get_type(else_data)  # type: ignore[no-untyped-call]

        if if_data_type == else_data_type:
            return if_data_type

        if is_intrinsic_no_value(if_data):
            return else_data_type

        if is_intrinsic_no_value(else_data):
            return if_data_type

        raise InvalidTemplateException(
            "Different policy types within the same Fn::If statement is unsupported. "
            "Separate different policy types into different Fn::If statements"
        )


class PolicyTypes(Enum):
    """
    Enum of different policy types supported by SAM & this plugin
    """

    MANAGED_POLICY = "managed_policy"
    POLICY_STATEMENT = "policy_statement"
    POLICY_TEMPLATE = "policy_template"
    UNKNOWN = "unknown"
