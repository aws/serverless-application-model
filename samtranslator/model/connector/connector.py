from collections import namedtuple
from typing import Any, Dict, List, Optional

from samtranslator.model import ResourceResolver
from samtranslator.model.intrinsics import get_logical_id_from_intrinsic, ref, fnGetAtt
from samtranslator.utils.utils import as_array, insert_unique


# TODO: Switch to dataclass
ConnectorResourceReference = namedtuple(
    "ConnectorResourceReference",
    [
        "logical_id",
        "resource_type",
        "arn",
        "role_name",
        "queue_url",
        "resource_id",
        "name",
        "qualifier",
    ],
)


class ConnectorResourceError(Exception):
    """
    Indicates a template error making a resource unusable for connectors.
    """


def _is_nonblank_str(s: Any) -> bool:
    return s and isinstance(s, str)


def add_depends_on(logical_id: str, depends_on: str, resource_resolver: ResourceResolver):  # type: ignore[no-untyped-def]
    """
    Add DependsOn attribute to resource.
    """
    resource = resource_resolver.get_resource_by_logical_id(logical_id)
    if not resource:
        return

    old_deps = resource.get("DependsOn", [])
    deps = insert_unique(old_deps, depends_on)

    resource["DependsOn"] = deps


def replace_depends_on_logical_id(logical_id: str, replacement: List[str], resource_resolver: ResourceResolver) -> None:
    """
    For every resource's `DependsOn`, replace `logical_id` by `replacement`.
    """
    for resource in resource_resolver.get_all_resources().values():
        depends_on = as_array(resource.get("DependsOn", []))
        if logical_id in depends_on:
            depends_on.remove(logical_id)
            resource["DependsOn"] = insert_unique(depends_on, replacement)


def get_event_source_mappings(event_source_id: str, function_id: str, resource_resolver: ResourceResolver):  # type: ignore[no-untyped-def]
    """
    Get logical IDs of `AWS::Lambda::EventSourceMapping`s between resource logical IDs.
    """
    resources = resource_resolver.get_all_resources()
    for logical_id, resource in resources.items():
        if resource.get("Type") == "AWS::Lambda::EventSourceMapping":
            properties = resource.get("Properties", {})
            # Not taking intrinsics as input to function as FunctionName could be a number of
            # formats, which would require parsing it anyway
            resource_function_id = get_logical_id_from_intrinsic(properties.get("FunctionName"))
            resource_event_source_id = get_logical_id_from_intrinsic(properties.get("EventSourceArn"))
            if (
                resource_function_id
                and resource_event_source_id
                and function_id == resource_function_id
                and event_source_id == resource_event_source_id
            ):
                yield logical_id


def _is_valid_resource_reference(obj: Dict[str, Any]) -> bool:
    id_provided = "Id" in obj
    non_id_provided = len([k for k in obj.keys() if k != "Id"]) > 0
    # Must provide either Id, or a combination of other properties, but not both
    return id_provided != non_id_provided


def get_resource_reference(
    obj: Dict[str, Any], resource_resolver: ResourceResolver, connecting_obj: Dict[str, Any]
) -> ConnectorResourceReference:
    if not _is_valid_resource_reference(obj):
        raise ConnectorResourceError("Must provide either 'Id' or a combination of the other properties, not both.")

    logical_id = obj.get("Id")

    # Must either provide Id or a combination of the other properties (not both).
    # If Id is not provided, all values must come from overrides.
    if not logical_id:
        resource_type = obj.get("Type")
        if not _is_nonblank_str(resource_type):
            raise ConnectorResourceError("'Type' is missing or not a string.")
        resource_type = str(resource_type)

        return ConnectorResourceReference(
            logical_id=None,
            resource_type=resource_type,
            arn=obj.get("Arn"),
            role_name=obj.get("RoleName"),
            queue_url=obj.get("QueueUrl"),
            resource_id=obj.get("ResourceId"),
            name=obj.get("Name"),
            qualifier=obj.get("Qualifier"),
        )

    if not _is_nonblank_str(logical_id):
        raise ConnectorResourceError("'Id' is missing or not a string.")

    resource = resource_resolver.get_resource_by_logical_id(logical_id)
    if not resource:
        raise ConnectorResourceError(f"Unable to find resource with logical ID '{logical_id}'.")

    resource_type = resource.get("Type")
    if not _is_nonblank_str(resource_type):
        raise ConnectorResourceError("'Type' is missing or not a string.")
    resource_type = str(resource_type)

    properties = resource.get("Properties", {})

    arn = _get_resource_arn(logical_id, resource_type)

    role_name = _get_resource_role_name(connecting_obj.get("Id"), connecting_obj.get("Arn"), resource_type, properties)

    queue_url = _get_resource_queue_url(logical_id, resource_type)

    resource_id = _get_resource_id(logical_id, resource_type)

    name = _get_resource_name(logical_id, resource_type)

    qualifier = _get_resource_qualifier(resource_type)

    return ConnectorResourceReference(
        logical_id=logical_id,
        resource_type=resource_type,
        arn=arn,
        role_name=role_name,
        queue_url=queue_url,
        resource_id=resource_id,
        name=name,
        qualifier=qualifier,
    )


def _get_resource_role_property(
    connecting_obj_id: Optional[str], connecting_obj_arn: Optional[Any], resource_type: str, properties: Dict[str, Any]
) -> Any:
    if resource_type == "AWS::Lambda::Function":
        return properties.get("Role")
    if resource_type == "AWS::StepFunctions::StateMachine":
        return properties.get("RoleArn")
    if resource_type == "AWS::Events::Rule":
        for target in properties.get("Targets", []):
            target_arn = target.get("Arn")
            target_logical_id = get_logical_id_from_intrinsic(target_arn)
            if (target_logical_id and target_logical_id == connecting_obj_id) or (
                connecting_obj_arn and target_arn == connecting_obj_arn
            ):
                return target.get("RoleArn")
    return None


def _get_resource_role_name(
    connecting_obj_id: Optional[str], connecting_obj_arn: Optional[Any], resource_type: str, properties: Dict[str, Any]
) -> Any:
    role = _get_resource_role_property(connecting_obj_id, connecting_obj_arn, resource_type, properties)
    if not role:
        return None

    logical_id = get_logical_id_from_intrinsic(role)
    if not logical_id:
        return None

    return ref(logical_id)


def _get_resource_queue_url(logical_id: str, resource_type: str) -> Any:
    if resource_type == "AWS::SQS::Queue":
        return ref(logical_id)


def _get_resource_id(logical_id: str, resource_type: str) -> Any:
    if resource_type in ["AWS::ApiGateway::RestApi", "AWS::ApiGatewayV2::Api"]:
        return ref(logical_id)


def _get_resource_name(logical_id: str, resource_type: str) -> Any:
    if resource_type == "AWS::StepFunctions::StateMachine":
        return fnGetAtt(logical_id, "Name")


def _get_resource_qualifier(resource_type: str) -> Any:
    # Qualifier is used as the execute-api ARN suffix; by default allow whole API
    if resource_type in ["AWS::ApiGateway::RestApi", "AWS::ApiGatewayV2::Api"]:
        return "*"


def _get_resource_arn(logical_id: str, resource_type: str) -> Any:
    if resource_type in ["AWS::SNS::Topic", "AWS::StepFunctions::StateMachine"]:
        # according to documentation, Ref returns ARNs for these two resource types
        # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-stepfunctions-statemachine.html#aws-resource-stepfunctions-statemachine-return-values
        # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-sns-topic.html#aws-resource-sns-topic-return-values
        return ref(logical_id)
    # For all other supported resources, we can typically use Fn::GetAtt LogicalId.Arn to obtain ARNs
    return fnGetAtt(logical_id, "Arn")
