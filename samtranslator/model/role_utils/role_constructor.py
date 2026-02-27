from typing import Any, Callable, Dict, List, Optional

from samtranslator.internal.managed_policies import get_bundled_managed_policy_map
from samtranslator.internal.types import GetManagedPolicyMap
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.iam import IAMRole
from samtranslator.model.intrinsics import is_intrinsic_if, is_intrinsic_no_value
from samtranslator.model.resource_policies import PolicyTypes
from samtranslator.translator.arn_generator import ArnGenerator


def _get_managed_policy_arn(
    name: str,
    managed_policy_map: Optional[Dict[str, str]],
    get_managed_policy_map: Optional[GetManagedPolicyMap],
) -> str:
    """
    Get the ARN of a AWS managed policy name. Used in Policies property of
    AWS::Serverless::Function and AWS::Serverless::StateMachine.

    The intention is that the bundled managed policy map is used in the majority
    of cases, avoiding the extra IAM calls (IAM is partition-global; AWS managed
    policies are the same for any region within a partition).

    Determined in this order:
      1. Caller-provided managed policy map (can be None, mostly for compatibility)
      2. Managed policy map bundled with the transform code (fast!)
      3. Caller-provided managed policy map (lazily called function)

    If it matches no ARN, the name is used as-is.
    """
    # Caller-provided managed policy map
    if managed_policy_map:
        arn = managed_policy_map.get(name)
        if arn:
            return arn

    # Bundled managed policy map
    partition = ArnGenerator.get_partition_name()
    bundled_managed_policy_map = get_bundled_managed_policy_map(partition)
    if bundled_managed_policy_map:
        arn = bundled_managed_policy_map.get(name)
        if arn:
            return arn

    # If it's already an ARN, we're done
    # https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html
    is_arn = name.startswith("arn:")
    if is_arn:
        return name

    # Caller-provided function to get managed policy map (fallback)
    if get_managed_policy_map:
        fallback_managed_policy_map = get_managed_policy_map()
        if fallback_managed_policy_map:
            arn = fallback_managed_policy_map.get(name)
            if arn:
                return arn

    return name


def _convert_intrinsic_if_values(
    intrinsic_if: Dict[str, List[Any]], is_convertible: Callable[[Any], Any], convert: Callable[[Any], Any]
) -> Dict[str, List[Any]]:
    """
    Convert the true and false value of the intrinsic if function according to
    `convert` function.

    :param intrinsic_if: A dict of the form {"Fn::If": [condition, value_if_true, value_if_false]}
    :type intrinsic_if: Dict[str, List[Any]]
    :param is_convertible: The function used to decide if the value must be converted
    :type convert: Callable[[Any], Any]
    :param convert: The function used to make the conversion
    :type convert: Callable[[Any], Any]
    :return: The input dict with values converted
    :rtype: Dict[str, List[Any]]
    """
    value_if_true = intrinsic_if["Fn::If"][1]
    value_if_false = intrinsic_if["Fn::If"][2]

    if is_convertible(value_if_true):
        intrinsic_if["Fn::If"][1] = convert(value_if_true)

    if is_convertible(value_if_false):
        intrinsic_if["Fn::If"][2] = convert(value_if_false)

    return intrinsic_if


def construct_role_for_resource(  # type: ignore[no-untyped-def] # noqa: PLR0913
    resource_logical_id,
    attributes,
    managed_policy_map,
    assume_role_policy_document,
    resource_policies,
    managed_policy_arns=None,
    policy_documents=None,
    role_path=None,
    permissions_boundary=None,
    tags=None,
    get_managed_policy_map=None,
) -> IAMRole:
    """
    Constructs an execution role for a resource.
    :param resource_logical_id: The logical_id of the SAM resource that the role will be associated with
    :param attributes: Map of resource attributes to their values
    :param managed_policy_map: Map of managed policy names to the ARNs
    :param assume_role_policy_document: The trust policy that must be associated with the role
    :param resource_policies: ResourcePolicies object encapuslating the policies property of SAM resource
    :param managed_policy_arns: List of managed policy ARNs to be associated with the role
    :param policy_documents: List of policy documents to be associated with the role
    :param role_path: The path to the role
    :param permissions_boundary: The ARN of the policy used to set the permissions boundary for the role
    :param tags: Tags to be associated with the role

    :returns: the generated IAM Role
    :rtype: model.iam.IAMRole
    """
    role_logical_id = resource_logical_id + "Role"
    execution_role = IAMRole(logical_id=role_logical_id, attributes=attributes)
    execution_role.AssumeRolePolicyDocument = assume_role_policy_document

    if not managed_policy_arns:
        managed_policy_arns = []

    if not policy_documents:
        policy_documents = []

    for index, policy_entry in enumerate(resource_policies.get()):
        if policy_entry.type is PolicyTypes.POLICY_STATEMENT:
            if is_intrinsic_if(policy_entry.data):
                intrinsic_if = _convert_intrinsic_if_values(
                    policy_entry.data,
                    lambda value: not is_intrinsic_no_value(value),
                    lambda value: (
                        {
                            "PolicyName": execution_role.logical_id + "Policy" + str(index),  # noqa: B023
                            "PolicyDocument": value,
                        }
                    ),
                )

                policy_documents.append(intrinsic_if)

            else:
                policy_documents.append(
                    {
                        "PolicyName": execution_role.logical_id + "Policy" + str(index),
                        "PolicyDocument": policy_entry.data,
                    }
                )

        elif policy_entry.type is PolicyTypes.MANAGED_POLICY:
            # There are three options:
            #   Managed Policy Name (string): Try to convert to Managed Policy ARN
            #   Managed Policy Arn (string): Insert it directly into the list
            #   Intrinsic Function (dict): Try to convert each statement to Managed Policy Arn
            #
            # When you insert into managed_policy_arns list, de-dupe to prevent same ARN from showing up twice
            #

            policy_arn = policy_entry.data
            if isinstance(policy_arn, str):
                policy_arn = _get_managed_policy_arn(
                    policy_arn,
                    managed_policy_map,
                    get_managed_policy_map,
                )
            elif is_intrinsic_if(policy_arn):
                policy_arn = _convert_intrinsic_if_values(
                    policy_arn,
                    lambda value: not is_intrinsic_no_value(value) and isinstance(value, str),
                    lambda value: _get_managed_policy_arn(value, managed_policy_map, get_managed_policy_map),
                )

            # De-Duplicate managed policy arns before inserting. Mainly useful
            # when customer specifies a managed policy which is already inserted
            # by SAM, such as AWSLambdaBasicExecutionRole
            if policy_arn not in managed_policy_arns:
                managed_policy_arns.append(policy_arn)
        else:
            # Policy Templates are not supported here in the "core"
            raise InvalidResourceException(
                resource_logical_id,
                f"Policy at index {index} in the '{resource_policies.POLICIES_PROPERTY_NAME}' property is not valid",
            )

    execution_role.ManagedPolicyArns = list(managed_policy_arns)
    execution_role.Policies = policy_documents or None
    execution_role.Path = role_path
    execution_role.PermissionsBoundary = permissions_boundary
    execution_role.Tags = tags

    return execution_role
