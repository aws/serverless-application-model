import json
from typing import Any, Dict, Optional, cast

from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.model import Property, PropertyType, ResourceMacro, Resource
from samtranslator.model.events import EventsRule
from samtranslator.model.iam import IAMRole, IAMRolePolicies
from samtranslator.model.types import IS_DICT, IS_STR, is_type
from samtranslator.model.intrinsics import fnSub
from samtranslator.translator import logical_id_generator
from samtranslator.model.exceptions import InvalidEventException
from samtranslator.model.eventbridge_utils import EventBridgeRuleUtils
from samtranslator.model.eventsources.push import Api as PushApi
from samtranslator.swagger.swagger import SwaggerEditor

CONDITION = "Condition"
SFN_EVETSOURCE_METRIC_PREFIX = "SFNEventSource"


class EventSource(ResourceMacro):
    """Base class for event sources for SAM State Machine.

    :cvar str principal: The AWS service principal of the source service.
    """

    # Note(xinhol): `EventSource` should have been an abstract class. Disabling the type check for the next
    # line to avoid any potential behavior change.
    # TODO: Make `EventSource` an abstract class and not giving `principal` initial value.
    principal: str = None  # type: ignore
    relative_id: str  # overriding the Optional[str]: for event, relative id is not None

    Target: Optional[Dict[str, str]]

    def _generate_logical_id(self, prefix, suffix, resource_type):  # type: ignore[no-untyped-def]
        """Helper utility to generate a logicial ID for a new resource

        :param string prefix: Prefix to use for the logical ID of the resource
        :param string suffix: Suffix to add for the logical ID of the resource
        :param string resource_type: Type of the resource

        :returns: the logical ID for the new resource
        :rtype: string
        """
        if prefix is None:
            prefix = self.logical_id
        if suffix.isalnum():
            logical_id = prefix + resource_type + suffix
        else:
            generator = logical_id_generator.LogicalIdGenerator(prefix + resource_type, suffix)
            logical_id = generator.gen()
        return logical_id

    def _construct_role(self, resource, permissions_boundary=None, prefix=None, suffix=""):  # type: ignore[no-untyped-def]
        """Constructs the IAM Role resource allowing the event service to invoke
        the StartExecution API of the state machine resource it is associated with.

        :param model.stepfunctions.StepFunctionsStateMachine resource: The state machine resource associated with the event
        :param string permissions_boundary: The ARN of the policy used to set the permissions boundary for the role
        :param string prefix: Prefix to use for the logical ID of the IAM role
        :param string suffix: Suffix to add for the logical ID of the IAM role

        :returns: the IAM Role resource
        :rtype: model.iam.IAMRole
        """
        role_logical_id = self._generate_logical_id(prefix=prefix, suffix=suffix, resource_type="Role")  # type: ignore[no-untyped-call]
        event_role = IAMRole(role_logical_id, attributes=resource.get_passthrough_resource_attributes())
        event_role.AssumeRolePolicyDocument = IAMRolePolicies.construct_assume_role_policy_for_service_principal(  # type: ignore[no-untyped-call]
            self.principal
        )
        state_machine_arn = resource.get_runtime_attr("arn")
        event_role.Policies = [
            IAMRolePolicies.step_functions_start_execution_role_policy(state_machine_arn, role_logical_id)  # type: ignore[no-untyped-call]
        ]

        if permissions_boundary:
            event_role.PermissionsBoundary = permissions_boundary

        return event_role


class Schedule(EventSource):
    """Scheduled executions for SAM State Machine."""

    resource_type = "Schedule"
    principal = "events.amazonaws.com"
    property_types = {
        "Schedule": PropertyType(True, IS_STR),
        "Input": PropertyType(False, IS_STR),
        "Enabled": PropertyType(False, is_type(bool)),
        "State": PropertyType(False, IS_STR),
        "Name": PropertyType(False, IS_STR),
        "Description": PropertyType(False, IS_STR),
        "DeadLetterConfig": PropertyType(False, IS_DICT),
        "RetryPolicy": PropertyType(False, IS_DICT),
        "Target": Property(False, IS_DICT),
    }

    @cw_timer(prefix=SFN_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, resource, **kwargs):  # type: ignore[no-untyped-def]
        """Returns the EventBridge Rule and IAM Role to which this Schedule event source corresponds.

        :param dict kwargs: no existing resources need to be modified
        :returns: a list of vanilla CloudFormation Resources, to which this Schedule event expands
        :rtype: list
        """
        resources = []

        permissions_boundary = kwargs.get("permissions_boundary")

        passthrough_resource_attributes = resource.get_passthrough_resource_attributes()
        events_rule = EventsRule(self.logical_id, attributes=passthrough_resource_attributes)
        resources.append(events_rule)

        events_rule.ScheduleExpression = self.Schedule  # type: ignore[attr-defined]

        if self.State and self.Enabled is not None:  # type: ignore[attr-defined, attr-defined]
            raise InvalidEventException(self.relative_id, "State and Enabled Properties cannot both be specified.")

        if self.State:  # type: ignore[attr-defined]
            events_rule.State = self.State  # type: ignore[attr-defined]

        if self.Enabled is not None:  # type: ignore[attr-defined]
            events_rule.State = "ENABLED" if self.Enabled else "DISABLED"  # type: ignore[attr-defined]

        events_rule.Name = self.Name  # type: ignore[attr-defined]
        events_rule.Description = self.Description  # type: ignore[attr-defined]

        role = self._construct_role(resource, permissions_boundary)  # type: ignore[no-untyped-call]
        resources.append(role)

        source_arn = events_rule.get_runtime_attr("arn")
        dlq_queue_arn = None
        if self.DeadLetterConfig is not None:  # type: ignore[attr-defined]
            EventBridgeRuleUtils.validate_dlq_config(self.logical_id, self.DeadLetterConfig)  # type: ignore[attr-defined, no-untyped-call]
            dlq_queue_arn, dlq_resources = EventBridgeRuleUtils.get_dlq_queue_arn_and_resources(  # type: ignore[no-untyped-call]
                self, source_arn, passthrough_resource_attributes
            )
            resources.extend(dlq_resources)
        events_rule.Targets = [self._construct_target(resource, role, dlq_queue_arn)]  # type: ignore[no-untyped-call]

        return resources

    def _construct_target(self, resource, role, dead_letter_queue_arn=None):  # type: ignore[no-untyped-def]
        """Constructs the Target property for the EventBridge Rule.

        :returns: the Target property
        :rtype: dict
        """
        target_id = (
            self.Target["Id"] if self.Target and "Id" in self.Target else self.logical_id + "StepFunctionsTarget"
        )
        target = {
            "Arn": resource.get_runtime_attr("arn"),
            "Id": target_id,
            "RoleArn": role.get_runtime_attr("arn"),
        }
        if self.Input is not None:  # type: ignore[attr-defined]
            target["Input"] = self.Input  # type: ignore[attr-defined]

        if self.DeadLetterConfig is not None:  # type: ignore[attr-defined]
            target["DeadLetterConfig"] = {"Arn": dead_letter_queue_arn}

        if self.RetryPolicy is not None:  # type: ignore[attr-defined]
            target["RetryPolicy"] = self.RetryPolicy  # type: ignore[attr-defined]

        return target


class CloudWatchEvent(EventSource):
    """CloudWatch Events/EventBridge event source for SAM State Machine."""

    resource_type = "CloudWatchEvent"
    principal = "events.amazonaws.com"
    property_types = {
        "EventBusName": PropertyType(False, IS_STR),
        "RuleName": PropertyType(False, IS_STR),
        "Pattern": PropertyType(False, IS_DICT),
        "Input": PropertyType(False, IS_STR),
        "InputPath": PropertyType(False, IS_STR),
        "DeadLetterConfig": PropertyType(False, IS_DICT),
        "RetryPolicy": PropertyType(False, IS_DICT),
        "State": PropertyType(False, IS_STR),
        "Target": Property(False, IS_DICT),
    }

    @cw_timer(prefix=SFN_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, resource, **kwargs):  # type: ignore[no-untyped-def]
        """Returns the CloudWatch Events/EventBridge Rule and IAM Role to which this
        CloudWatch Events/EventBridge event source corresponds.

        :param dict kwargs: no existing resources need to be modified
        :returns: a list of vanilla CloudFormation Resources, to which this CloudWatch Events/EventBridge event expands
        :rtype: list
        """
        resources = []

        permissions_boundary = kwargs.get("permissions_boundary")

        passthrough_resource_attributes = resource.get_passthrough_resource_attributes()
        events_rule = EventsRule(self.logical_id, attributes=passthrough_resource_attributes)
        events_rule.EventBusName = self.EventBusName  # type: ignore[attr-defined]
        events_rule.EventPattern = self.Pattern  # type: ignore[attr-defined]
        events_rule.Name = self.RuleName  # type: ignore[attr-defined]

        if self.State:  # type: ignore[attr-defined]
            events_rule.State = self.State  # type: ignore[attr-defined]

        resources.append(events_rule)

        role = self._construct_role(resource, permissions_boundary)  # type: ignore[no-untyped-call]
        resources.append(role)

        source_arn = events_rule.get_runtime_attr("arn")
        dlq_queue_arn = None
        if self.DeadLetterConfig is not None:  # type: ignore[attr-defined]
            EventBridgeRuleUtils.validate_dlq_config(self.logical_id, self.DeadLetterConfig)  # type: ignore[attr-defined, no-untyped-call]
            dlq_queue_arn, dlq_resources = EventBridgeRuleUtils.get_dlq_queue_arn_and_resources(  # type: ignore[no-untyped-call]
                self, source_arn, passthrough_resource_attributes
            )
            resources.extend(dlq_resources)

        events_rule.Targets = [self._construct_target(resource, role, dlq_queue_arn)]  # type: ignore[no-untyped-call]

        return resources

    def _construct_target(self, resource, role, dead_letter_queue_arn=None):  # type: ignore[no-untyped-def]
        """Constructs the Target property for the CloudWatch Events/EventBridge Rule.

        :returns: the Target property
        :rtype: dict
        """
        target_id = (
            self.Target["Id"] if self.Target and "Id" in self.Target else self.logical_id + "StepFunctionsTarget"
        )
        target = {
            "Arn": resource.get_runtime_attr("arn"),
            "Id": target_id,
            "RoleArn": role.get_runtime_attr("arn"),
        }
        if self.Input is not None:  # type: ignore[attr-defined]
            target["Input"] = self.Input  # type: ignore[attr-defined]

        if self.InputPath is not None:  # type: ignore[attr-defined]
            target["InputPath"] = self.InputPath  # type: ignore[attr-defined]

        if self.DeadLetterConfig is not None:  # type: ignore[attr-defined]
            target["DeadLetterConfig"] = {"Arn": dead_letter_queue_arn}

        if self.RetryPolicy is not None:  # type: ignore[attr-defined]
            target["RetryPolicy"] = self.RetryPolicy  # type: ignore[attr-defined]

        return target


class EventBridgeRule(CloudWatchEvent):
    """EventBridge Rule event source for SAM State Machine."""

    resource_type = "EventBridgeRule"


class Api(EventSource):
    """Api method event source for SAM State Machines."""

    resource_type = "Api"
    principal = "apigateway.amazonaws.com"
    property_types = {
        "Path": PropertyType(True, IS_STR),
        "Method": PropertyType(True, IS_STR),
        # Api Event sources must "always" be paired with a Serverless::Api
        "RestApiId": PropertyType(True, IS_STR),
        "Stage": PropertyType(False, IS_STR),
        "Auth": PropertyType(False, IS_DICT),
        "UnescapeMappingTemplate": Property(False, is_type(bool)),
    }

    Path: str
    Method: str
    RestApiId: str
    Stage: Optional[str]
    Auth: Optional[Dict[str, Any]]
    UnescapeMappingTemplate: Optional[bool]

    def resources_to_link(self, resources):  # type: ignore[no-untyped-def]
        """
        If this API Event Source refers to an explicit API resource, resolve the reference and grab
        necessary data from the explicit API
        """

        # If RestApiId is a resource in the same template, then we try find the StageName by following the reference
        # Otherwise we default to a wildcard. This stage name is solely used to construct the permission to
        # allow this stage to invoke the State Machine. If we are unable to resolve the stage name, we will
        # simply permit all stages to invoke this State Machine
        # This hack is necessary because customers could use !ImportValue, !Ref or other intrinsic functions which
        # can be sometimes impossible to resolve (ie. when it has cross-stack references)
        permitted_stage = "*"
        stage_suffix = "AllStages"
        explicit_api = None
        rest_api_id = PushApi.get_rest_api_id_string(self.RestApiId)
        if isinstance(rest_api_id, str):

            if (
                rest_api_id in resources
                and "Properties" in resources[rest_api_id]
                and "StageName" in resources[rest_api_id]["Properties"]
            ):

                explicit_api = resources[rest_api_id]["Properties"]
                permitted_stage = explicit_api["StageName"]

                # Stage could be a intrinsic, in which case leave the suffix to default value
                if isinstance(permitted_stage, str):
                    stage_suffix = permitted_stage
                else:
                    stage_suffix = "Stage"  # type: ignore[unreachable]

            else:
                # RestApiId is a string, not an intrinsic, but we did not find a valid API resource for this ID
                raise InvalidEventException(
                    self.relative_id,
                    "RestApiId property of Api event must reference a valid resource in the same template.",
                )

        return {"explicit_api": explicit_api, "api_id": rest_api_id, "explicit_api_stage": {"suffix": stage_suffix}}

    @cw_timer(prefix=SFN_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, resource, **kwargs):  # type: ignore[no-untyped-def]
        """If the Api event source has a RestApi property, then simply return the IAM role resource
        allowing API Gateway to start the state machine execution. If no RestApi is provided, then
        additionally inject the path, method, and the x-amazon-apigateway-integration into the
        Swagger body for a provided implicit API.

        :param model.stepfunctions.resources.StepFunctionsStateMachine resource; the state machine \
             resource to which the Api event source must be associated
        :param dict kwargs: a dict containing the implicit RestApi to be modified, should no \
            explicit RestApi be provided.

        :returns: a list of vanilla CloudFormation Resources, to which this Api event expands
        :rtype: list
        """
        resources = []

        intrinsics_resolver = kwargs.get("intrinsics_resolver")
        permissions_boundary = kwargs.get("permissions_boundary")

        if self.Method is not None:
            # Convert to lower case so that user can specify either GET or get
            self.Method = self.Method.lower()

        role = self._construct_role(resource, permissions_boundary)  # type: ignore[no-untyped-call]
        resources.append(role)

        explicit_api = kwargs["explicit_api"]
        api_id = kwargs["api_id"]
        if explicit_api.get("__MANAGE_SWAGGER"):
            self._add_swagger_integration(explicit_api, api_id, resource, role, intrinsics_resolver)  # type: ignore[no-untyped-call]

        return resources

    def _add_swagger_integration(self, api, api_id, resource, role, intrinsics_resolver):  # type: ignore[no-untyped-def]
        """Adds the path and method for this Api event source to the Swagger body for the provided RestApi.

        :param model.apigateway.ApiGatewayRestApi rest_api: the RestApi to which the path and method should be added.
        """
        swagger_body = api.get("DefinitionBody")
        if swagger_body is None:
            return

        integration_uri = fnSub("arn:${AWS::Partition}:apigateway:${AWS::Region}:states:action/StartExecution")

        editor = SwaggerEditor(swagger_body)

        if editor.has_integration(self.Path, self.Method):
            # Cannot add the integration, if it is already present
            raise InvalidEventException(
                self.relative_id,
                'API method "{method}" defined multiple times for path "{path}".'.format(
                    method=self.Method, path=self.Path
                ),
            )

        condition = None
        if CONDITION in resource.resource_attributes:
            condition = resource.resource_attributes[CONDITION]

        request_template = (
            self._generate_request_template_unescaped(resource)
            if self.UnescapeMappingTemplate
            else self._generate_request_template(resource)
        )

        editor.add_state_machine_integration(  # type: ignore[no-untyped-call]
            self.Path,
            self.Method,
            integration_uri,
            role.get_runtime_attr("arn"),
            request_template,
            condition=condition,
        )

        # self.Stage is not None as it is set in _get_permissions()
        # before calling this method.
        # TODO: refactor to remove this cast
        stage = cast(str, self.Stage)

        if self.Auth:
            PushApi.add_auth_to_swagger(
                self.Auth, api, api_id, self.relative_id, self.Method, self.Path, stage, editor, intrinsics_resolver
            )

        api["DefinitionBody"] = editor.swagger

    def _generate_request_template(self, resource: Resource) -> Dict[str, Any]:
        """Generates the Body mapping request template for the Api. This allows for the input
        request to the Api to be passed as the execution input to the associated state machine resource.

        :param model.stepfunctions.resources.StepFunctionsStateMachine resource; the state machine
                resource to which the Api event source must be associated

        :returns: a body mapping request which passes the Api input to the state machine execution
        :rtype: dict
        """
        request_templates = {
            "application/json": fnSub(
                json.dumps(
                    {
                        "input": "$util.escapeJavaScript($input.json('$'))",
                        "stateMachineArn": "${" + resource.logical_id + "}",
                    }
                )
            )
        }
        return request_templates

    def _generate_request_template_unescaped(self, resource: Resource) -> Dict[str, Any]:
        """Generates the Body mapping request template for the Api. This allows for the input
        request to the Api to be passed as the execution input to the associated state machine resource.

        Unescapes single quotes such that it's valid JSON.

        :param model.stepfunctions.resources.StepFunctionsStateMachine resource; the state machine
                resource to which the Api event source must be associated

        :returns: a body mapping request which passes the Api input to the state machine execution
        :rtype: dict
        """
        request_templates = {
            "application/json": fnSub(
                # Need to unescape single quotes escaped by escapeJavaScript.
                # Also the mapping template isn't valid JSON, so can't use json.dumps().
                # See https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-mapping-template-reference.html#util-template-reference
                """{"input": "$util.escapeJavaScript($input.json('$')).replaceAll("\\\\'","'")", "stateMachineArn": "${"""
                + resource.logical_id
                + """}"}"""
            )
        }
        return request_templates
