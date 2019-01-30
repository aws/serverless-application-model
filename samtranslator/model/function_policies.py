from enum import Enum
from collections import namedtuple

from six import string_types

from samtranslator.model.intrinsics import is_instrinsic

PolicyEntry = namedtuple("PolicyEntry", "data type")


class FunctionPolicies(object):
    """
    Class encapsulating the policies property of AWS::Serverless::Function. This class strictly encapsulates the data
    and does not take opinions on how to handle them.

    There are three types of policies:
        - Policy Statements
        - AWS or Custom Managed Policy names/arns
        - Policy Templates

    This class is capable of parsing and detecting the type of the policy. Optionally, if policy template information
    is provided to this class, it will detect Policy Templates too.
    """

    POLICIES_PROPERTY_NAME = "Policies"

    def __init__(self, resource_properties, policy_template_processor=None):
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

    def get(self):
        """
        Iterator method that "yields" the next policy entry on subsequent calls to this method.

        :yields namedtuple("data", "type"): Yields a named tuple containing the policy data and its type
        """

        for policy_tuple in self.policies:
            yield policy_tuple

    def __len__(self):
        return len(self.policies)

    def _get_policies(self, resource_properties):
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

        if self._contains_policies(resource_properties):
            policies = resource_properties[self.POLICIES_PROPERTY_NAME]

        if not policies:
            # Policies is None or empty
            return []

        if not isinstance(policies, list):
            # Just a single entry. Make it into a list of convenience
            policies = [policies]

        result = []
        for policy in policies:
            policy_type = self._get_type(policy)
            entry = PolicyEntry(data=policy, type=policy_type)
            result.append(entry)

        return result

    def _contains_policies(self, resource_properties):
        """
        Is there policies data in this resource?

        :param dict resource_properties: Properties of the resource
        :return: True if we can process this resource. False, otherwise
        """
        return resource_properties is not None \
            and isinstance(resource_properties, dict) \
            and self.POLICIES_PROPERTY_NAME in resource_properties

    def _get_type(self, policy):
        """
        Returns the type of the given policy

        :param string or dict policy: Policy data
        :return PolicyTypes: Type of the given policy. None, if type could not be inferred
        """

        # Must handle intrinsic functions. Policy could be a primitive type or an intrinsic function

        # Managed policies are either string or an intrinsic function that resolves to a string
        if isinstance(policy, string_types) or is_instrinsic(policy):
            return PolicyTypes.MANAGED_POLICY

        # Policy statement is a dictionary with the key "Statement" in it
        if isinstance(policy, dict) and "Statement" in policy:
            return PolicyTypes.POLICY_STATEMENT

        # This could be a policy template then.
        if self._is_policy_template(policy):
            return PolicyTypes.POLICY_TEMPLATE

        # Nothing matches. Don't take opinions on how to handle it. Instead just set the appropriate type.
        return PolicyTypes.UNKNOWN

    def _is_policy_template(self, policy):
        """
        Is the given policy data a policy template? Policy templates is a dictionary with one key which is the name
        of the template.

        :param dict policy: Policy data
        :return: True, if this is a policy template. False if it is not
        """

        return self._policy_template_processor is not None and \
            isinstance(policy, dict) and \
            len(policy) == 1 and \
            self._policy_template_processor.has(list(policy.keys())[0]) is True


class PolicyTypes(Enum):
    """
    Enum of different policy types supported by SAM & this plugin
    """
    MANAGED_POLICY = "managed_policy"
    POLICY_STATEMENT = "policy_statement"
    POLICY_TEMPLATE = "policy_template"
    UNKNOWN = "unknown"
