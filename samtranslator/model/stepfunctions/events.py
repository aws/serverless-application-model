import json

from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.model import PropertyType, ResourceMacro
from samtranslator.model.events import EventsRule
from samtranslator.model.iam import IAMRole, IAMRolePolicies
from samtranslator.model.types import dict_of, is_str, is_type, list_of, one_of
from samtranslator.model.intrinsics import fnSub
from samtranslator.translator import logical_id_generator
from samtranslator.model.exceptions import InvalidEventException, InvalidResourceException
from samtranslator.model.eventbridge_utils import EventBridgeRuleUtils
from samtranslator.model.eventsources.push import Api as PushApi
from samtranslator.translator.arn_generator import ArnGenerator
from samtranslator.swagger.swagger import SwaggerEditor
from samtranslator.open_api.open_api import OpenApiEditor

CONDITION = "Condition"
SFN_EVETSOURCE_METRIC_PREFIX = "SFNEventSource"


class EventSource(ResourceMacro):
    """Base class for event sources for SAM State Machine.

    :cvar str principal: The AWS service principal of the source service.
    """

    principal = None

    def _generate_logical_id(self, prefix, suffix, resource_type):
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

    def _construct_role(self, resource, permissions_boundary=None, prefix=None, suffix=""):
        """Constructs the IAM Role resource allowing the event service to invoke
        the StartExecution API of the state machine resource it is associated with.

        :param model.stepfunctions.StepFunctionsStateMachine resource: The state machine resource associated with the event
        :param string permissions_boundary: The ARN of the policy used to set the permissions boundary for the role
        :param string prefix: Prefix to use for the logical ID of the IAM role
        :param string suffix: Suffix to add for the logical ID of the IAM role

        :returns: the IAM Role resource
        :rtype: model.iam.IAMRole
        """
        role_logical_id = self._generate_logical_id(prefix=prefix, suffix=suffix, resource_type="Role")
        event_role = IAMRole(role_logical_id, attributes=resource.get_passthrough_resource_attributes())
        event_role.AssumeRolePolicyDocument = IAMRolePolicies.construct_assume_role_policy_for_service_principal(
            self.principal
        )
        state_machine_arn = resource.get_runtime_attr("arn")
        event_role.Policies = [
            IAMRolePolicies.step_functions_start_execution_role_policy(state_machine_arn, role_logical_id)
        ]

        if permissions_boundary:
            event_role.PermissionsBoundary = permissions_boundary

        return event_role


class Schedule(EventSource):
    """Scheduled executions for SAM State Machine."""

    resource_type = "Schedule"
    principal = "events.amazonaws.com"
    property_types = {
        "Schedule": PropertyType(True, is_str()),
        "Input": PropertyType(False, is_str()),
        "Enabled": PropertyType(False, is_type(bool)),
        "Name": PropertyType(False, is_str()),
        "Description": PropertyType(False, is_str()),
        "DeadLetterConfig": PropertyType(False, is_type(dict)),
        "RetryPolicy": PropertyType(False, is_type(dict)),
    }

    @cw_timer(prefix=SFN_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, resource, **kwargs):
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

        events_rule.ScheduleExpression = self.Schedule
        if self.Enabled is not None:
            events_rule.State = "ENABLED" if self.Enabled else "DISABLED"
        events_rule.Name = self.Name
        events_rule.Description = self.Description

        role = self._construct_role(resource, permissions_boundary)
        resources.append(role)

        source_arn = events_rule.get_runtime_attr("arn")
        dlq_queue_arn = None
        if self.DeadLetterConfig is not None:
            EventBridgeRuleUtils.validate_dlq_config(self.logical_id, self.DeadLetterConfig)
            dlq_queue_arn, dlq_resources = EventBridgeRuleUtils.get_dlq_queue_arn_and_resources(
                self, source_arn, passthrough_resource_attributes
            )
            resources.extend(dlq_resources)
        events_rule.Targets = [self._construct_target(resource, role, dlq_queue_arn)]

        return resources

    def _construct_target(self, resource, role, dead_letter_queue_arn=None):
        """Constructs the Target property for the EventBridge Rule.

        :returns: the Target property
        :rtype: dict
        """
        target = {
            "Arn": resource.get_runtime_attr("arn"),
            "Id": self.logical_id + "StepFunctionsTarget",
            "RoleArn": role.get_runtime_attr("arn"),
        }
        if self.Input is not None:
            target["Input"] = self.Input

        if self.DeadLetterConfig is not None:
            target["DeadLetterConfig"] = {"Arn": dead_letter_queue_arn}

        if self.RetryPolicy is not None:
            target["RetryPolicy"] = self.RetryPolicy

        return target


class CloudWatchEvent(EventSource):
    """CloudWatch Events/EventBridge event source for SAM State Machine."""

    resource_type = "CloudWatchEvent"
    principal = "events.amazonaws.com"
    property_types = {
        "EventBusName": PropertyType(False, is_str()),
        "Pattern": PropertyType(False, is_type(dict)),
        "Input": PropertyType(False, is_str()),
        "InputPath": PropertyType(False, is_str()),
        "DeadLetterConfig": PropertyType(False, is_type(dict)),
        "RetryPolicy": PropertyType(False, is_type(dict)),
    }

    @cw_timer(prefix=SFN_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, resource, **kwargs):
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
        events_rule.EventBusName = self.EventBusName
        events_rule.EventPattern = self.Pattern

        resources.append(events_rule)

        role = self._construct_role(resource, permissions_boundary)
        resources.append(role)

        source_arn = events_rule.get_runtime_attr("arn")
        dlq_queue_arn = None
        if self.DeadLetterConfig is not None:
            EventBridgeRuleUtils.validate_dlq_config(self.logical_id, self.DeadLetterConfig)
            dlq_queue_arn, dlq_resources = EventBridgeRuleUtils.get_dlq_queue_arn_and_resources(
                self, source_arn, passthrough_resource_attributes
            )
            resources.extend(dlq_resources)

        events_rule.Targets = [self._construct_target(resource, role, dlq_queue_arn)]

        return resources

    def _construct_target(self, resource, role, dead_letter_queue_arn=None):
        """Constructs the Target property for the CloudWatch Events/EventBridge Rule.

        :returns: the Target property
        :rtype: dict
        """
        target = {
            "Arn": resource.get_runtime_attr("arn"),
            "Id": self.logical_id + "StepFunctionsTarget",
            "RoleArn": role.get_runtime_attr("arn"),
        }
        if self.Input is not None:
            target["Input"] = self.Input

        if self.InputPath is not None:
            target["InputPath"] = self.InputPath

        if self.DeadLetterConfig is not None:
            target["DeadLetterConfig"] = {"Arn": dead_letter_queue_arn}

        if self.RetryPolicy is not None:
            target["RetryPolicy"] = self.RetryPolicy

        return target


class EventBridgeRule(CloudWatchEvent):
    """EventBridge Rule event source for SAM State Machine."""

    resource_type = "EventBridgeRule"


class Api(EventSource):
    """Api method event source for SAM State Machines."""

    resource_type = "Api"
    principal = "apigateway.amazonaws.com"
    property_types = {
        "Path": PropertyType(True, is_str()),
        "Method": PropertyType(True, is_str()),
        # Api Event sources must "always" be paired with a Serverless::Api
        "RestApiId": PropertyType(True, is_str()),
        "Stage": PropertyType(False, is_str()),
        "Auth": PropertyType(False, is_type(dict)),
    }

    def resources_to_link(self, resources):
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
                    stage_suffix = "Stage"

            else:
                # RestApiId is a string, not an intrinsic, but we did not find a valid API resource for this ID
                raise InvalidEventException(
                    self.relative_id,
                    "RestApiId property of Api event must reference a valid resource in the same template.",
                )

        return {"explicit_api": explicit_api, "explicit_api_stage": {"suffix": stage_suffix}}

    @cw_timer(prefix=SFN_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, resource, **kwargs):
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

        role = self._construct_role(resource, permissions_boundary)
        resources.append(role)

        explicit_api = kwargs["explicit_api"]
        if explicit_api.get("__MANAGE_SWAGGER"):
            self._add_swagger_integration(explicit_api, resource, role, intrinsics_resolver)

        return resources

    def _add_swagger_integration(self, api, resource, role, intrinsics_resolver):
        """Adds the path and method for this Api event source to the Swagger body for the provided RestApi.

        :param model.apigateway.ApiGatewayRestApi rest_api: the RestApi to which the path and method should be added.
        """
        swagger_body = api.get("DefinitionBody")
        if swagger_body is None:
            return

        resource_arn = resource.get_runtime_attr("arn")
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

        editor.add_state_machine_integration(
            self.Path,
            self.Method,
            integration_uri,
            role.get_runtime_attr("arn"),
            self._generate_request_template(resource),
            condition=condition,
        )

        # Note: Refactor and combine the section below with the Api eventsource for functions
        if self.Auth:
            method_authorizer = self.Auth.get("Authorizer")
            api_auth = api.get("Auth")
            api_auth = intrinsics_resolver.resolve_parameter_refs(api_auth)

            if method_authorizer:
                api_authorizers = api_auth and api_auth.get("Authorizers")

                if method_authorizer != "AWS_IAM":
                    if method_authorizer != "NONE" and not api_authorizers:
                        raise InvalidEventException(
                            self.relative_id,
                            "Unable to set Authorizer [{authorizer}] on API method [{method}] for path [{path}] "
                            "because the related API does not define any Authorizers.".format(
                                authorizer=method_authorizer, method=self.Method, path=self.Path
                            ),
                        )

                    if method_authorizer != "NONE" and not api_authorizers.get(method_authorizer):
                        raise InvalidEventException(
                            self.relative_id,
                            "Unable to set Authorizer [{authorizer}] on API method [{method}] for path [{path}] "
                            "because it wasn't defined in the API's Authorizers.".format(
                                authorizer=method_authorizer, method=self.Method, path=self.Path
                            ),
                        )

                    if method_authorizer == "NONE":
                        if not api_auth or not api_auth.get("DefaultAuthorizer"):
                            raise InvalidEventException(
                                self.relative_id,
                                "Unable to set Authorizer on API method [{method}] for path [{path}] because 'NONE' "
                                "is only a valid value when a DefaultAuthorizer on the API is specified.".format(
                                    method=self.Method, path=self.Path
                                ),
                            )

            if self.Auth.get("AuthorizationScopes") and not isinstance(self.Auth.get("AuthorizationScopes"), list):
                raise InvalidEventException(
                    self.relative_id,
                    "Unable to set Authorizer on API method [{method}] for path [{path}] because "
                    "'AuthorizationScopes' must be a list of strings.".format(method=self.Method, path=self.Path),
                )

            apikey_required_setting = self.Auth.get("ApiKeyRequired")
            apikey_required_setting_is_false = apikey_required_setting is not None and not apikey_required_setting
            if apikey_required_setting_is_false and (not api_auth or not api_auth.get("ApiKeyRequired")):
                raise InvalidEventException(
                    self.relative_id,
                    "Unable to set ApiKeyRequired [False] on API method [{method}] for path [{path}] "
                    "because the related API does not specify any ApiKeyRequired.".format(
                        method=self.Method, path=self.Path
                    ),
                )

            if method_authorizer or apikey_required_setting is not None:
                editor.add_auth_to_method(api=api, path=self.Path, method_name=self.Method, auth=self.Auth)

            if self.Auth.get("ResourcePolicy"):
                resource_policy = self.Auth.get("ResourcePolicy")
                editor.add_resource_policy(resource_policy=resource_policy, path=self.Path, stage=self.Stage)
                if resource_policy.get("CustomStatements"):
                    editor.add_custom_statements(resource_policy.get("CustomStatements"))

        api["DefinitionBody"] = editor.swagger

    def _generate_request_template(self, resource):
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
