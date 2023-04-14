import copy
import re
from abc import ABCMeta
from typing import Any, Dict, List, Optional, Union, cast

from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.model import PassThroughProperty, PropertyType, ResourceMacro
from samtranslator.model.cognito import CognitoUserPool
from samtranslator.model.eventbridge_utils import EventBridgeRuleUtils
from samtranslator.model.events import EventsRule, generate_valid_target_id
from samtranslator.model.eventsources import FUNCTION_EVETSOURCE_METRIC_PREFIX
from samtranslator.model.eventsources.pull import SQS
from samtranslator.model.exceptions import InvalidDocumentException, InvalidEventException, InvalidResourceException
from samtranslator.model.intrinsics import fnGetAtt, fnSub, is_intrinsic, make_conditional, make_shorthand, ref
from samtranslator.model.iot import IotTopicRule
from samtranslator.model.lambda_ import LambdaPermission
from samtranslator.model.s3 import S3Bucket
from samtranslator.model.sns import SNSSubscription
from samtranslator.model.sqs import SQSQueue, SQSQueuePolicies, SQSQueuePolicy
from samtranslator.model.tags.resource_tagging import get_tag_list
from samtranslator.model.types import IS_BOOL, IS_DICT, IS_INT, IS_LIST, IS_STR, PassThrough, dict_of, list_of, one_of
from samtranslator.open_api.open_api import OpenApiEditor
from samtranslator.swagger.swagger import SwaggerEditor
from samtranslator.translator import logical_id_generator
from samtranslator.translator.arn_generator import ArnGenerator
from samtranslator.utils.py27hash_fix import Py27Dict, Py27UniStr
from samtranslator.utils.utils import InvalidValueType, dict_deep_get
from samtranslator.validator.value_validator import sam_expect

CONDITION = "Condition"

REQUEST_PARAMETER_PROPERTIES = ["Required", "Caching"]
EVENT_RULE_LAMBDA_TARGET_SUFFIX = "LambdaTarget"


class PushEventSource(ResourceMacro, metaclass=ABCMeta):
    """Base class for push event sources for SAM Functions.

    Push event sources correspond to services that call Lambda's Invoke API whenever an event occurs. Each Push event
    needs an Lambda Permission resource, which will add permissions for the source service to invoke the Lambda function
    to the function's resource policy.

    SourceArn is attached to the resource policy to avoid giving lambda invoke permissions to every resource of that
    category.
    ARN is currently constructed in ARN format http://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html
    for:
    - API gateway
    - IotRule

    ARN is accessible through Fn:GetAtt for:
    - Schedule
    - Cloudwatch

    :cvar str principal: The AWS service principal of the source service.
    """

    # Note(xinhol): `PushEventSource` should have been an abstract class. Disabling the type check for the next
    # line to avoid any potential behavior change.
    # TODO: Make `PushEventSource` an abstract class and not giving `principal` initial value.
    principal: str = None  # type: ignore
    relative_id: str  # overriding the Optional[str]: for event, relative id is not None

    def _construct_permission(  # type: ignore[no-untyped-def] # noqa: too-many-arguments
        self, function, source_arn=None, source_account=None, suffix="", event_source_token=None, prefix=None
    ):
        """Constructs the Lambda Permission resource allowing the source service to invoke the function this event
        source triggers.

        :returns: the permission resource
        :rtype: model.lambda_.LambdaPermission
        """
        if prefix is None:
            prefix = self.logical_id
        if suffix.isalnum():
            permission_logical_id = prefix + "Permission" + suffix
        else:
            generator = logical_id_generator.LogicalIdGenerator(prefix + "Permission", suffix)
            permission_logical_id = generator.gen()
        lambda_permission = LambdaPermission(
            permission_logical_id, attributes=function.get_passthrough_resource_attributes()
        )
        try:
            # Name will not be available for Alias resources
            function_name_or_arn = function.get_runtime_attr("name")
        except KeyError:
            function_name_or_arn = function.get_runtime_attr("arn")

        lambda_permission.Action = "lambda:InvokeFunction"
        lambda_permission.FunctionName = function_name_or_arn
        lambda_permission.Principal = self.principal
        lambda_permission.SourceArn = source_arn
        lambda_permission.SourceAccount = source_account
        lambda_permission.EventSourceToken = event_source_token

        return lambda_permission


class Schedule(PushEventSource):
    """Scheduled executions for SAM Functions."""

    resource_type = "Schedule"
    principal = "events.amazonaws.com"
    property_types = {
        "Schedule": PropertyType(True, IS_STR),
        "RuleName": PropertyType(False, IS_STR),
        "Input": PropertyType(False, IS_STR),
        "Enabled": PropertyType(False, IS_BOOL),
        "State": PropertyType(False, IS_STR),
        "Name": PropertyType(False, IS_STR),
        "Description": PropertyType(False, IS_STR),
        "DeadLetterConfig": PropertyType(False, IS_DICT),
        "RetryPolicy": PropertyType(False, IS_DICT),
    }

    Schedule: PassThrough
    RuleName: Optional[PassThrough]
    Input: Optional[PassThrough]
    Enabled: Optional[bool]
    State: Optional[PassThrough]
    Name: Optional[PassThrough]
    Description: Optional[PassThrough]
    DeadLetterConfig: Optional[Dict[str, Any]]
    RetryPolicy: Optional[PassThrough]

    @cw_timer(prefix=FUNCTION_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, **kwargs):  # type: ignore[no-untyped-def]
        """Returns the EventBridge Rule and Lambda Permission to which this Schedule event source corresponds.

        :param dict kwargs: no existing resources need to be modified
        :returns: a list of vanilla CloudFormation Resources, to which this Schedule event expands
        :rtype: list
        """
        function = kwargs.get("function")

        if not function:
            raise TypeError("Missing required keyword argument: function")

        resources = []

        passthrough_resource_attributes = function.get_passthrough_resource_attributes()
        events_rule = EventsRule(self.logical_id, attributes=passthrough_resource_attributes)
        resources.append(events_rule)

        events_rule.ScheduleExpression = self.Schedule

        if self.State and self.Enabled is not None:
            raise InvalidEventException(self.relative_id, "State and Enabled Properties cannot both be specified.")

        if self.State:
            events_rule.State = self.State

        if self.Enabled is not None:
            events_rule.State = "ENABLED" if self.Enabled else "DISABLED"

        events_rule.Name = self.Name
        events_rule.Description = self.Description

        source_arn = events_rule.get_runtime_attr("arn")
        dlq_queue_arn = None
        if self.DeadLetterConfig is not None:
            EventBridgeRuleUtils.validate_dlq_config(self.logical_id, self.DeadLetterConfig)  # type: ignore[no-untyped-call]
            dlq_queue_arn, dlq_resources = EventBridgeRuleUtils.get_dlq_queue_arn_and_resources(  # type: ignore[no-untyped-call]
                self, source_arn, passthrough_resource_attributes
            )
            resources.extend(dlq_resources)

        events_rule.Targets = [self._construct_target(function, dlq_queue_arn)]  # type: ignore[no-untyped-call]

        resources.append(self._construct_permission(function, source_arn=source_arn))  # type: ignore[no-untyped-call]

        return resources

    def _construct_target(self, function, dead_letter_queue_arn=None):  # type: ignore[no-untyped-def]
        """Constructs the Target property for the EventBridge Rule.

        :returns: the Target property
        :rtype: dict
        """
        target_id = generate_valid_target_id(self.logical_id, EVENT_RULE_LAMBDA_TARGET_SUFFIX)
        target = {"Arn": function.get_runtime_attr("arn"), "Id": target_id}
        if self.Input is not None:
            target["Input"] = self.Input

        if self.DeadLetterConfig is not None:
            target["DeadLetterConfig"] = {"Arn": dead_letter_queue_arn}

        if self.RetryPolicy is not None:
            target["RetryPolicy"] = self.RetryPolicy

        return target


class CloudWatchEvent(PushEventSource):
    """CloudWatch Events/EventBridge event source for SAM Functions."""

    resource_type = "CloudWatchEvent"
    principal = "events.amazonaws.com"
    property_types = {
        "EventBusName": PropertyType(False, IS_STR),
        "RuleName": PropertyType(False, IS_STR),
        "Pattern": PropertyType(False, IS_DICT),
        "DeadLetterConfig": PropertyType(False, IS_DICT),
        "RetryPolicy": PropertyType(False, IS_DICT),
        "Input": PropertyType(False, IS_STR),
        "InputPath": PropertyType(False, IS_STR),
        "Target": PropertyType(False, IS_DICT),
        "Enabled": PropertyType(False, IS_BOOL),
        "State": PropertyType(False, IS_STR),
    }

    EventBusName: Optional[PassThrough]
    RuleName: Optional[PassThrough]
    Pattern: Optional[PassThrough]
    DeadLetterConfig: Optional[Dict[str, Any]]
    RetryPolicy: Optional[PassThrough]
    Input: Optional[PassThrough]
    InputPath: Optional[PassThrough]
    Target: Optional[PassThrough]
    Enabled: Optional[bool]
    State: Optional[PassThrough]

    @cw_timer(prefix=FUNCTION_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, **kwargs):  # type: ignore[no-untyped-def]
        """Returns the CloudWatch Events/EventBridge Rule and Lambda Permission to which
        this CloudWatch Events/EventBridge event source corresponds.

        :param dict kwargs: no existing resources need to be modified
        :returns: a list of vanilla CloudFormation Resources, to which this CloudWatch Events/EventBridge event expands
        :rtype: list
        """
        function = kwargs.get("function")

        if not function:
            raise TypeError("Missing required keyword argument: function")

        resources = []

        passthrough_resource_attributes = function.get_passthrough_resource_attributes()
        events_rule = EventsRule(self.logical_id, attributes=passthrough_resource_attributes)
        events_rule.EventBusName = self.EventBusName
        events_rule.EventPattern = self.Pattern
        events_rule.Name = self.RuleName
        source_arn = events_rule.get_runtime_attr("arn")

        dlq_queue_arn = None
        if self.DeadLetterConfig is not None:
            EventBridgeRuleUtils.validate_dlq_config(self.logical_id, self.DeadLetterConfig)  # type: ignore[no-untyped-call]
            dlq_queue_arn, dlq_resources = EventBridgeRuleUtils.get_dlq_queue_arn_and_resources(  # type: ignore[no-untyped-call]
                self, source_arn, passthrough_resource_attributes
            )
            resources.extend(dlq_resources)

        if self.State and self.Enabled is not None:
            raise InvalidEventException(self.relative_id, "State and Enabled Properties cannot both be specified.")

        if self.State:
            events_rule.State = self.State

        if self.Enabled is not None:
            events_rule.State = "ENABLED" if self.Enabled else "DISABLED"

        events_rule.Targets = [self._construct_target(function, dlq_queue_arn)]  # type: ignore[no-untyped-call]

        resources.append(events_rule)
        resources.append(self._construct_permission(function, source_arn=source_arn))  # type: ignore[no-untyped-call]

        return resources

    def _construct_target(self, function, dead_letter_queue_arn=None):  # type: ignore[no-untyped-def]
        """Constructs the Target property for the CloudWatch Events/EventBridge Rule.

        :returns: the Target property
        :rtype: dict
        """
        target_id = (
            self.Target["Id"]
            if self.Target and "Id" in self.Target
            else generate_valid_target_id(self.logical_id, EVENT_RULE_LAMBDA_TARGET_SUFFIX)
        )
        target = {"Arn": function.get_runtime_attr("arn"), "Id": target_id}
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
    """EventBridge Rule event source for SAM Functions."""

    resource_type = "EventBridgeRule"


class S3(PushEventSource):
    """S3 bucket event source for SAM Functions."""

    resource_type = "S3"
    principal = "s3.amazonaws.com"
    property_types = {
        "Bucket": PropertyType(True, IS_STR),
        "Events": PropertyType(True, one_of(IS_STR, list_of(IS_STR)), False),
        "Filter": PropertyType(False, dict_of(IS_STR, IS_STR)),
    }

    Bucket: Dict[str, Any]
    Events: Union[str, List[str]]
    Filter: Optional[Dict[str, str]]

    def resources_to_link(self, resources):  # type: ignore[no-untyped-def]
        if isinstance(self.Bucket, dict) and "Ref" in self.Bucket:
            bucket_id = self.Bucket["Ref"]
            if not isinstance(bucket_id, str):
                raise InvalidEventException(self.relative_id, "'Ref' value in S3 events is not a valid string.")
            if bucket_id in resources:
                return {"bucket": resources[bucket_id], "bucket_id": bucket_id}
        raise InvalidEventException(self.relative_id, "S3 events must reference an S3 bucket in the same template.")

    @cw_timer(prefix=FUNCTION_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, **kwargs):  # type: ignore[no-untyped-def]
        """Returns the Lambda Permission resource allowing S3 to invoke the function this event source triggers.

        :param dict kwargs: S3 bucket resource
        :returns: a list of vanilla CloudFormation Resources, to which this S3 event expands
        :rtype: list
        """
        function = kwargs.get("function")

        if not function:
            raise TypeError("Missing required keyword argument: function")

        if "bucket" not in kwargs or kwargs["bucket"] is None:
            raise TypeError("Missing required keyword argument: bucket")

        if "bucket_id" not in kwargs or kwargs["bucket_id"] is None:
            raise TypeError("Missing required keyword argument: bucket_id")

        bucket = kwargs["bucket"]
        bucket_id = kwargs["bucket_id"]

        resources = []

        source_account = ref("AWS::AccountId")
        permission = self._construct_permission(function, source_account=source_account)  # type: ignore[no-untyped-call]
        if CONDITION in permission.resource_attributes:
            self._depend_on_lambda_permissions_using_tag(bucket, bucket_id, permission)
        else:
            self._depend_on_lambda_permissions(bucket, permission)  # type: ignore[no-untyped-call]
        resources.append(permission)

        # NOTE: `bucket` here is a dictionary representing the S3 Bucket resource in your SAM template. If there are
        # multiple S3 Events attached to the same bucket, we will update the Bucket resource with notification
        # configuration for each event. This is the reason why we continue to use existing bucket dict and append onto
        # it.
        #
        # NOTE: There is some fragile logic here where we will append multiple resources to output
        #   SAM template but de-dupe them when merging into output CFN template. This is scary because the order of
        #   merging is literally "last one wins", which works fine because we linearly loop through the template once.
        #   The de-dupe happens inside `samtranslator.translator.Translator.translate` method when merging results of
        #   to_cloudformation() to output template.
        self._inject_notification_configuration(function, bucket, bucket_id)  # type: ignore[no-untyped-call]
        resources.append(S3Bucket.from_dict(bucket_id, bucket))

        return resources

    def _depend_on_lambda_permissions(self, bucket, permission):  # type: ignore[no-untyped-def]
        """
        Make the S3 bucket depends on Lambda Permissions resource because when S3 adds a Notification Configuration,
        it will check whether it has permissions to access Lambda. This will fail if the Lambda::Permissions is not
        already applied for this bucket to invoke the Lambda.

        :param dict bucket: Dictionary representing the bucket in SAM template. This is a raw dictionary and not a
            "resource" object
        :param model.lambda_.lambda_permission permission: Lambda Permission resource that needs to be created before
            the bucket.
        :return: Modified Bucket dictionary
        """

        depends_on = bucket.get("DependsOn", [])

        # DependsOn can be either a list of strings or a scalar string
        if isinstance(depends_on, str):
            depends_on = [depends_on]

        try:
            depends_on_set = set(depends_on)
        except TypeError as ex:
            raise InvalidResourceException(
                self.logical_id,
                "Invalid type for field 'DependsOn'. Expected a string or list of strings.",
            ) from ex

        depends_on_set.add(permission.logical_id)
        bucket["DependsOn"] = list(depends_on_set)

        return bucket

    def _depend_on_lambda_permissions_using_tag(
        self, bucket: Dict[str, Any], bucket_id: str, permission: LambdaPermission
    ) -> Dict[str, Any]:
        """
        Since conditional DependsOn is not supported this undocumented way of
        implicitely  making dependency through tags is used.

        See https://stackoverflow.com/questions/34607476/cloudformation-apply-condition-on-dependson

        It is done by using Ref wrapped in a conditional Fn::If. Using Ref implies a
        dependency, so CloudFormation will automatically wait once it reaches that function, the same
        as if you were using a DependsOn.
        """
        properties = bucket.get("Properties", None)
        if properties is None:
            properties = {}
            bucket["Properties"] = properties
        tags = properties.get("Tags", None)
        if tags is None:
            tags = []
            properties["Tags"] = tags
        sam_expect(tags, bucket_id, "Tags").to_be_a_list()
        dep_tag = {
            "sam:ConditionalDependsOn:"
            + permission.logical_id: {
                "Fn::If": [permission.resource_attributes[CONDITION], ref(permission.logical_id), "no dependency"]
            }
        }
        properties["Tags"] = tags + get_tag_list(dep_tag)
        return bucket

    def _inject_notification_configuration(self, function, bucket, bucket_id):  # type: ignore[no-untyped-def]
        base_event_mapping = {"Function": function.get_runtime_attr("arn")}

        if self.Filter is not None:
            base_event_mapping["Filter"] = self.Filter

        event_types = self.Events
        if isinstance(self.Events, str):
            event_types = [self.Events]

        event_mappings = []
        for event_type in event_types:
            lambda_event = copy.deepcopy(base_event_mapping)
            lambda_event["Event"] = event_type
            if CONDITION in function.resource_attributes:
                lambda_event = make_conditional(function.resource_attributes[CONDITION], lambda_event)
            event_mappings.append(lambda_event)

        properties = bucket.get("Properties", {})
        sam_expect(properties, bucket_id, "").to_be_a_map("Properties should be a map.")
        bucket["Properties"] = properties

        notification_config = properties.get("NotificationConfiguration", None)
        if notification_config is None:
            notification_config = {}
            properties["NotificationConfiguration"] = notification_config

        sam_expect(notification_config, bucket_id, "NotificationConfiguration").to_be_a_map()

        lambda_notifications = notification_config.get("LambdaConfigurations", None)
        if lambda_notifications is None:
            lambda_notifications = []
            notification_config["LambdaConfigurations"] = lambda_notifications

        if not isinstance(lambda_notifications, list):
            raise InvalidResourceException(bucket_id, "Invalid type for LambdaConfigurations. Must be a list.")

        for event_mapping in event_mappings:
            if event_mapping not in lambda_notifications:
                lambda_notifications.append(event_mapping)
        return bucket


class SNS(PushEventSource):
    """SNS topic event source for SAM Functions."""

    resource_type = "SNS"
    principal = "sns.amazonaws.com"
    property_types = {
        "Topic": PropertyType(True, IS_STR),
        "Region": PropertyType(False, IS_STR),
        "FilterPolicy": PropertyType(False, dict_of(IS_STR, list_of(one_of(IS_STR, IS_DICT)))),
        "FilterPolicyScope": PassThroughProperty(False),
        "SqsSubscription": PropertyType(False, one_of(IS_BOOL, IS_DICT)),
        "RedrivePolicy": PropertyType(False, IS_DICT),
    }

    Topic: str
    Region: Optional[str]
    FilterPolicy: Optional[Dict[str, Any]]
    FilterPolicyScope: Optional[str]
    SqsSubscription: Optional[Any]
    RedrivePolicy: Optional[Dict[str, Any]]

    @cw_timer(prefix=FUNCTION_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, **kwargs):  # type: ignore[no-untyped-def]
        """Returns the Lambda Permission resource allowing SNS to invoke the function this event source triggers.

        :param dict kwargs: no existing resources need to be modified
        :returns: a list of vanilla CloudFormation Resources, to which this SNS event expands
        :rtype: list
        """
        function = kwargs.get("function")
        role = kwargs.get("role")

        if not function:
            raise TypeError("Missing required keyword argument: function")

        # SNS -> Lambda
        if not self.SqsSubscription:
            subscription = self._inject_subscription(
                "lambda",
                function.get_runtime_attr("arn"),
                self.Topic,
                self.Region,
                self.FilterPolicy,
                self.FilterPolicyScope,
                self.RedrivePolicy,
                function,
            )
            return [self._construct_permission(function, source_arn=self.Topic), subscription]  # type: ignore[no-untyped-call]

        # SNS -> SQS(Create New) -> Lambda
        if isinstance(self.SqsSubscription, bool):
            resources = []  # type: ignore[var-annotated]
            queue = self._inject_sqs_queue(function)  # type: ignore[no-untyped-call]
            queue_arn = queue.get_runtime_attr("arn")
            queue_url = queue.get_runtime_attr("queue_url")

            queue_policy = self._inject_sqs_queue_policy(self.Topic, queue_arn, queue_url, function)  # type: ignore[no-untyped-call]
            subscription = self._inject_subscription(
                "sqs",
                queue_arn,
                self.Topic,
                self.Region,
                self.FilterPolicy,
                self.FilterPolicyScope,
                self.RedrivePolicy,
                function,
            )
            event_source = self._inject_sqs_event_source_mapping(function, role, queue_arn)  # type: ignore[no-untyped-call]

            resources = resources + event_source
            resources.append(queue)
            resources.append(queue_policy)
            resources.append(subscription)
            return resources

        # SNS -> SQS(Existing) -> Lambda
        resources = []
        sqs_subscription: Dict[str, Any] = sam_expect(
            self.SqsSubscription, self.relative_id, "SqsSubscription", is_sam_event=True
        ).to_be_a_map()
        queue_arn = sqs_subscription.get("QueueArn", None)
        queue_url = sqs_subscription.get("QueueUrl", None)
        if not queue_arn or not queue_url:
            raise InvalidEventException(self.relative_id, "No QueueARN or QueueURL provided.")

        queue_policy_logical_id = sqs_subscription.get("QueuePolicyLogicalId", None)
        batch_size = sqs_subscription.get("BatchSize", None)
        enabled = sqs_subscription.get("Enabled", None)

        queue_policy = self._inject_sqs_queue_policy(  # type: ignore[no-untyped-call]
            self.Topic, queue_arn, queue_url, function, queue_policy_logical_id
        )
        subscription = self._inject_subscription(
            "sqs",
            queue_arn,
            self.Topic,
            self.Region,
            self.FilterPolicy,
            self.FilterPolicyScope,
            self.RedrivePolicy,
            function,
        )
        event_source = self._inject_sqs_event_source_mapping(function, role, queue_arn, batch_size, enabled)  # type: ignore[no-untyped-call]

        resources = resources + event_source
        resources.append(queue_policy)
        resources.append(subscription)
        return resources

    def _inject_subscription(  # noqa: too-many-arguments
        self,
        protocol: str,
        endpoint: str,
        topic: str,
        region: Optional[str],
        filterPolicy: Optional[Dict[str, Any]],
        filterPolicyScope: Optional[str],
        redrivePolicy: Optional[Dict[str, Any]],
        function: Any,
    ) -> SNSSubscription:
        subscription = SNSSubscription(self.logical_id, attributes=function.get_passthrough_resource_attributes())
        subscription.Protocol = protocol
        subscription.Endpoint = endpoint
        subscription.TopicArn = topic

        if region is not None:
            subscription.Region = region

        if filterPolicy is not None:
            subscription.FilterPolicy = filterPolicy

        if filterPolicyScope is not None:
            subscription.FilterPolicyScope = filterPolicyScope

        if redrivePolicy is not None:
            subscription.RedrivePolicy = redrivePolicy

        return subscription

    def _inject_sqs_queue(self, function):  # type: ignore[no-untyped-def]
        return SQSQueue(self.logical_id + "Queue", attributes=function.get_passthrough_resource_attributes())

    def _inject_sqs_event_source_mapping(self, function, role, queue_arn, batch_size=None, enabled=None):  # type: ignore[no-untyped-def]
        event_source = SQS(
            self.logical_id + "EventSourceMapping", attributes=function.get_passthrough_resource_attributes()
        )
        event_source.Queue = queue_arn
        event_source.BatchSize = batch_size or 10
        event_source.Enabled = True
        return event_source.to_cloudformation(function=function, role=role)

    def _inject_sqs_queue_policy(self, topic_arn, queue_arn, queue_url, function, logical_id=None):  # type: ignore[no-untyped-def]
        policy = SQSQueuePolicy(
            logical_id or self.logical_id + "QueuePolicy", attributes=function.get_passthrough_resource_attributes()
        )

        policy.PolicyDocument = SQSQueuePolicies.sns_topic_send_message_role_policy(topic_arn, queue_arn)  # type: ignore[no-untyped-call]
        policy.Queues = [queue_url]
        return policy


class Api(PushEventSource):
    """Api method event source for SAM Functions."""

    resource_type = "Api"
    principal = "apigateway.amazonaws.com"
    property_types = {
        "Path": PropertyType(True, IS_STR),
        "Method": PropertyType(True, IS_STR),
        # Api Event sources must "always" be paired with a Serverless::Api
        "RestApiId": PropertyType(True, IS_STR),
        "Stage": PropertyType(False, IS_STR),
        "Auth": PropertyType(False, IS_DICT),
        "RequestModel": PropertyType(False, IS_DICT),
        "RequestParameters": PropertyType(False, IS_LIST),
    }

    Path: str
    Method: str
    RestApiId: str
    Stage: Optional[str]
    Auth: Optional[Dict[str, Any]]
    RequestModel: Optional[Dict[str, Any]]
    RequestParameters: Optional[List[Any]]

    def resources_to_link(self, resources: Dict[str, Any]) -> Dict[str, Any]:
        """
        If this API Event Source refers to an explicit API resource, resolve the reference and grab
        necessary data from the explicit API
        """
        return self.resources_to_link_for_rest_api(resources, self.relative_id, self.RestApiId)

    @staticmethod
    def resources_to_link_for_rest_api(
        resources: Dict[str, Any], relative_id: str, raw_rest_api_id: Optional[Any]
    ) -> Dict[str, Any]:
        # If RestApiId is a resource in the same template, then we try find the StageName by following the reference
        # Otherwise we default to a wildcard. This stage name is solely used to construct the permission to
        # allow this stage to invoke the Lambda function. If we are unable to resolve the stage name, we will
        # simply permit all stages to invoke this Lambda function
        # This hack is necessary because customers could use !ImportValue, !Ref or other intrinsic functions which
        # can be sometimes impossible to resolve (ie. when it has cross-stack references)
        stage_suffix = "AllStages"
        explicit_api_resource_properties = None
        rest_api_id = Api.get_rest_api_id_string(raw_rest_api_id)
        if isinstance(rest_api_id, str):
            rest_api_resource = sam_expect(
                resources.get(rest_api_id), relative_id, "RestApiId", is_sam_event=True
            ).to_be_a_map("RestApiId property of Api event must reference a valid resource in the same template.")

            explicit_api_resource_properties = sam_expect(
                rest_api_resource.get("Properties", {}), rest_api_id, "Properties", is_resource_attribute=True
            ).to_be_a_map()
            permitted_stage = explicit_api_resource_properties.get("StageName")

            # Stage could be an intrinsic, in which case leave the suffix to default value
            if isinstance(permitted_stage, str):
                if not permitted_stage:
                    raise InvalidResourceException(rest_api_id, "StageName cannot be empty.")
                stage_suffix = permitted_stage
            else:
                stage_suffix = "Stage"

        return {
            "explicit_api": explicit_api_resource_properties,
            "api_id": rest_api_id,
            "explicit_api_stage": {"suffix": stage_suffix},
        }

    @cw_timer(prefix=FUNCTION_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, **kwargs):  # type: ignore[no-untyped-def]
        """If the Api event source has a RestApi property, then simply return the Lambda Permission resource allowing
        API Gateway to call the function. If no RestApi is provided, then additionally inject the path, method, and the
        x-amazon-apigateway-integration into the Swagger body for a provided implicit API.

        :param dict kwargs: a dict containing the implicit RestApi to be modified, should no explicit RestApi \
                be provided.
        :returns: a list of vanilla CloudFormation Resources, to which this Api event expands
        :rtype: list
        """
        resources = []

        function = kwargs.get("function")
        intrinsics_resolver = kwargs.get("intrinsics_resolver")

        if not function:
            raise TypeError("Missing required keyword argument: function")

        if self.Method is not None:
            # Convert to lower case so that user can specify either GET or get
            self.Method = self.Method.lower()

        resources.extend(self._get_permissions(kwargs))  # type: ignore[no-untyped-call]

        explicit_api = kwargs["explicit_api"]
        api_id = kwargs["api_id"]
        if explicit_api.get("__MANAGE_SWAGGER") or explicit_api.get("MergeDefinitions"):
            self._add_swagger_integration(explicit_api, api_id, function, intrinsics_resolver)  # type: ignore[no-untyped-call]

        return resources

    def _get_permissions(self, resources_to_link):  # type: ignore[no-untyped-def]
        permissions = []

        # By default, implicit APIs get a stage called Prod. If the API event refers to an
        # explicit API using RestApiId property, we should grab the stage name of the explicit API
        # all stages for an API are given permission
        permitted_stage = "*"
        suffix = "Prod"
        if "explicit_api_stage" in resources_to_link:
            suffix = resources_to_link["explicit_api_stage"]["suffix"]
        self.Stage = suffix

        permissions.append(self._get_permission(resources_to_link, permitted_stage, suffix))  # type: ignore[no-untyped-call]
        return permissions

    def _get_permission(self, resources_to_link, stage, suffix):  # type: ignore[no-untyped-def]
        # It turns out that APIGW doesn't like trailing slashes in paths (#665)
        # and removes as a part of their behaviour, but this isn't documented.
        # The regex removes the tailing slash to ensure the permission works as intended
        path = re.sub(r"^(.+)/$", r"\1", self.Path)

        if not stage or not suffix:
            raise RuntimeError("Could not add permission to lambda function.")

        path = SwaggerEditor.get_path_without_trailing_slash(path)  # type: ignore[no-untyped-call]
        method = "*" if self.Method.lower() == "any" else self.Method.upper()

        api_id = self.RestApiId

        # RestApiId can be a simple string or intrinsic function like !Ref. Using Fn::Sub will handle both cases
        resource = f"${{__ApiId__}}/${{__Stage__}}/{method}{path}"
        partition = ArnGenerator.get_partition_name()
        source_arn = fnSub(
            ArnGenerator.generate_arn(partition=partition, service="execute-api", resource=resource),
            {"__ApiId__": api_id, "__Stage__": stage},
        )

        return self._construct_permission(resources_to_link["function"], source_arn=source_arn, suffix=suffix)  # type: ignore[no-untyped-call]

    def _add_swagger_integration(  # type: ignore[no-untyped-def] # noqa: too-many-statements
        self, api, api_id, function, intrinsics_resolver
    ):
        """Adds the path and method for this Api event source to the Swagger body for the provided RestApi.

        :param model.apigateway.ApiGatewayRestApi rest_api: the RestApi to which the path and method should be added.
        """
        swagger_body = api.get("DefinitionBody")
        merge_definitions = api.get("MergeDefinitions")
        if swagger_body is None:
            return
        if merge_definitions:
            # Use a skeleton swagger body for API event source to make sure the generated definition body
            # is unaffected by the inline/customer defined DefinitionBody
            swagger_body = SwaggerEditor.gen_skeleton()

        partition = ArnGenerator.get_partition_name()
        uri = _build_apigw_integration_uri(function, partition)  # type: ignore[no-untyped-call]

        editor = SwaggerEditor(swagger_body)

        if editor.has_integration(self.Path, self.Method):
            # Cannot add the Lambda Integration, if it is already present
            raise InvalidEventException(
                self.relative_id,
                'API method "{method}" defined multiple times for path "{path}".'.format(
                    method=self.Method, path=self.Path
                ),
            )

        condition = None
        if CONDITION in function.resource_attributes:
            condition = function.resource_attributes[CONDITION]

        method_auth = self.Auth or Py27Dict()
        sam_expect(method_auth, self.relative_id, "Auth", is_sam_event=True).to_be_a_map()
        api_auth = api.get("Auth") or Py27Dict()
        sam_expect(api_auth, api_id, "Auth").to_be_a_map()
        editor.add_lambda_integration(self.Path, self.Method, uri, method_auth, api_auth, condition=condition)

        # self.Stage is not None as it is set in _get_permissions()
        # before calling this method.
        # TODO: refactor to remove this cast
        stage = cast(str, self.Stage)

        if self.Auth:
            self.add_auth_to_swagger(
                self.Auth, api, api_id, self.relative_id, self.Method, self.Path, stage, editor, intrinsics_resolver
            )

        if self.RequestModel:
            sam_expect(self.RequestModel, self.relative_id, "RequestModel", is_sam_event=True).to_be_a_map()
            method_model = self.RequestModel.get("Model")

            if method_model:
                api_models = api.get("Models")
                if not api_models:
                    raise InvalidEventException(
                        self.relative_id,
                        "Unable to set RequestModel [{model}] on API method [{method}] for path [{path}] "
                        "because the related API does not define any Models.".format(
                            model=method_model, method=self.Method, path=self.Path
                        ),
                    )
                if not is_intrinsic(api_models) and not isinstance(api_models, dict):
                    raise InvalidEventException(
                        self.relative_id,
                        "Unable to set RequestModel [{model}] on API method [{method}] for path [{path}] "
                        "because the related API Models defined is of invalid type.".format(
                            model=method_model, method=self.Method, path=self.Path
                        ),
                    )
                if not isinstance(method_model, str):
                    raise InvalidEventException(
                        self.relative_id,
                        "Unable to set RequestModel [{model}] on API method [{method}] for path [{path}] "
                        "because the related API does not contain valid Models.".format(
                            model=method_model, method=self.Method, path=self.Path
                        ),
                    )

                if not api_models.get(method_model):
                    raise InvalidEventException(
                        self.relative_id,
                        "Unable to set RequestModel [{model}] on API method [{method}] for path [{path}] "
                        "because it wasn't defined in the API's Models.".format(
                            model=method_model, method=self.Method, path=self.Path
                        ),
                    )

                editor.add_request_model_to_method(  # type: ignore[no-untyped-call]
                    path=self.Path, method_name=self.Method, request_model=self.RequestModel
                )

                validate_body = self.RequestModel.get("ValidateBody")
                validate_parameters = self.RequestModel.get("ValidateParameters")

                # Checking if any of the fields are defined as it can be false we are checking if the field are not None
                if validate_body is not None or validate_parameters is not None:
                    # as we are setting two different fields we are here setting as default False
                    # In case one of them are not defined
                    validate_body = False if validate_body is None else validate_body
                    validate_parameters = False if validate_parameters is None else validate_parameters

                    # If not type None but any other type it should explicitly invalidate the Spec
                    # Those fields should be only a boolean
                    if not isinstance(validate_body, bool) or not isinstance(validate_parameters, bool):
                        raise InvalidEventException(
                            self.relative_id,
                            "Unable to set Validator to RequestModel [{model}] on API method [{method}] for path [{path}] "
                            "ValidateBody and ValidateParameters must be a boolean type, strings or intrinsics are not supported.".format(
                                model=method_model, method=self.Method, path=self.Path
                            ),
                        )

                    editor.add_request_validator_to_method(  # type: ignore[no-untyped-call]
                        path=self.Path,
                        method_name=self.Method,
                        validate_body=validate_body,
                        validate_parameters=validate_parameters,
                    )

        if self.RequestParameters:
            default_value = {"Required": False, "Caching": False}

            parameters = []
            for parameter in self.RequestParameters:
                if isinstance(parameter, dict):
                    parameter_name, parameter_value = next(iter(parameter.items()))

                    if not re.match(r"method\.request\.(querystring|path|header)\.", parameter_name):
                        raise InvalidEventException(
                            self.relative_id,
                            "Invalid value for 'RequestParameters' property. Keys must be in the format "
                            "'method.request.[querystring|path|header].{value}', "
                            "e.g 'method.request.header.Authorization'.",
                        )

                    if not isinstance(parameter_value, dict) or not all(
                        key in REQUEST_PARAMETER_PROPERTIES for key in parameter_value
                    ):
                        raise InvalidEventException(
                            self.relative_id,
                            "Invalid value for 'RequestParameters' property. Values must be an object, "
                            "e.g { Required: true, Caching: false }",
                        )

                    settings = default_value.copy()
                    settings.update(parameter_value)
                    settings.update({"Name": parameter_name})

                    parameters.append(settings)

                elif isinstance(parameter, str):
                    if not re.match(r"method\.request\.(querystring|path|header)\.", parameter):
                        raise InvalidEventException(
                            self.relative_id,
                            "Invalid value for 'RequestParameters' property. Keys must be in the format "
                            "'method.request.[querystring|path|header].{value}', "
                            "e.g 'method.request.header.Authorization'.",
                        )

                    settings = default_value.copy()
                    settings.update({"Name": parameter})  # type: ignore[dict-item]

                    parameters.append(settings)

                else:
                    raise InvalidEventException(
                        self.relative_id,
                        "Invalid value for 'RequestParameters' property. Property must be either a string or an object",
                    )

            editor.add_request_parameters_to_method(  # type: ignore[no-untyped-call]
                path=self.Path, method_name=self.Method, request_parameters=parameters
            )

        if merge_definitions:
            api["DefinitionBody"] = self._get_merged_definitions(api_id, api["DefinitionBody"], editor)
        else:
            api["DefinitionBody"] = editor.swagger

    def _get_merged_definitions(
        self,
        api_id: str,
        source_definition_body: Dict[str, Any],
        editor: SwaggerEditor,
    ) -> Dict[str, Any]:
        """
        Merge SAM generated swagger definition(dest_definition_body) into inline DefinitionBody(source_definition_body):
        - for a conflicting key, use SAM generated value
        - otherwise include key-value pairs from both definitions
        """
        merged_definition_body = source_definition_body.copy()
        source_body_paths = merged_definition_body.get("paths", {})

        try:
            path_method_body = dict_deep_get(source_body_paths, [self.Path, self.Method]) or {}
        except InvalidValueType as e:
            raise InvalidResourceException(api_id, f"Property 'DefinitionBody' is invalid: {str(e)}") from e

        sam_expect(path_method_body, api_id, f"DefinitionBody.paths.{self.Path}.{self.Method}").to_be_a_map()

        # Normalized version of HTTP Method. It also handle API Gateway specific methods like "ANY"
        method = editor._normalize_method_name(self.Method)
        dest_definition_body = editor.swagger
        generated_path_method_body = dest_definition_body["paths"][self.Path][method]
        # this guarantees that the merged definition use SAM generated value for a conflicting key
        merged_path_method_body = {**path_method_body, **generated_path_method_body}

        if self.Path not in source_body_paths:
            source_body_paths[self.Path] = {self.Method: merged_path_method_body}
        source_body_paths[self.Path][self.Method] = merged_path_method_body

        return merged_definition_body

    @staticmethod
    def get_rest_api_id_string(rest_api_id: Any) -> Any:
        """
        rest_api_id can be either a string or a dictionary where the actual api id is the value at key "Ref".
        If rest_api_id is a dictionary with key "Ref", returns value at key "Ref". Otherwise, return rest_api_id.

        :param rest_api_id: a string or dictionary that contains the api id
        :return: string value of rest_api_id
        """
        return rest_api_id["Ref"] if isinstance(rest_api_id, dict) and "Ref" in rest_api_id else rest_api_id

    @staticmethod
    def add_auth_to_swagger(  # noqa: too-many-arguments
        event_auth: Dict[str, Any],
        api: Dict[str, Any],
        api_id: str,
        event_id: str,
        method: str,
        path: str,
        stage: str,
        editor: SwaggerEditor,
        intrinsics_resolver: IntrinsicsResolver,
    ) -> None:
        method_authorizer = event_auth.get("Authorizer")
        api_auth = api.get("Auth")
        api_auth = intrinsics_resolver.resolve_parameter_refs(api_auth)

        if method_authorizer:
            api_authorizers = api_auth and api_auth.get("Authorizers")

            if method_authorizer != "AWS_IAM":
                if method_authorizer != "NONE":
                    if not api_authorizers:
                        raise InvalidEventException(
                            event_id,
                            "Unable to set Authorizer [{authorizer}] on API method [{method}] for path [{path}] "
                            "because the related API does not define any Authorizers.".format(
                                authorizer=method_authorizer, method=method, path=path
                            ),
                        )
                    sam_expect(api_authorizers, api_id, "Auth.Authorizers").to_be_a_map()

                    _check_valid_authorizer_types(  # type: ignore[no-untyped-call]
                        event_id, method, path, method_authorizer, api_authorizers, False
                    )

                    if not api_authorizers.get(method_authorizer):
                        raise InvalidEventException(
                            event_id,
                            "Unable to set Authorizer [{authorizer}] on API method [{method}] for path [{path}] "
                            "because it wasn't defined in the API's Authorizers.".format(
                                authorizer=method_authorizer, method=method, path=path
                            ),
                        )
                else:
                    _check_valid_authorizer_types(  # type: ignore[no-untyped-call]
                        event_id, method, path, method_authorizer, api_authorizers, False
                    )
                    if not api_auth or not api_auth.get("DefaultAuthorizer"):
                        raise InvalidEventException(
                            event_id,
                            "Unable to set Authorizer on API method [{method}] for path [{path}] because 'NONE' "
                            "is only a valid value when a DefaultAuthorizer on the API is specified.".format(
                                method=method, path=path
                            ),
                        )

        auth_scopes = event_auth.get("AuthorizationScopes")
        if auth_scopes:
            sam_expect(auth_scopes, event_id, "Auth.AuthorizationScopes", is_sam_event=True).to_be_a_list()

        apikey_required_setting = event_auth.get("ApiKeyRequired")
        apikey_required_setting_is_false = apikey_required_setting is not None and not apikey_required_setting
        if apikey_required_setting_is_false and (not api_auth or not api_auth.get("ApiKeyRequired")):
            raise InvalidEventException(
                event_id,
                "Unable to set ApiKeyRequired [False] on API method [{method}] for path [{path}] "
                "because the related API does not specify any ApiKeyRequired.".format(method=method, path=path),
            )

        if method_authorizer or apikey_required_setting is not None:
            editor.add_auth_to_method(api=api, path=path, method_name=method, auth=event_auth)

        resource_policy = event_auth.get("ResourcePolicy")
        if resource_policy:
            sam_expect(resource_policy, event_id, "Auth.ResourcePolicy").to_be_a_map()
            editor.add_resource_policy(resource_policy=resource_policy, path=path, stage=stage)
            if resource_policy.get("CustomStatements"):
                editor.add_custom_statements(resource_policy.get("CustomStatements"))  # type: ignore[no-untyped-call]


class AlexaSkill(PushEventSource):
    resource_type = "AlexaSkill"
    principal = "alexa-appkit.amazon.com"

    property_types = {"SkillId": PropertyType(False, IS_STR)}

    SkillId: Optional[PassThrough]

    @cw_timer(prefix=FUNCTION_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, **kwargs):  # type: ignore[no-untyped-def]
        function = kwargs.get("function")

        if not function:
            raise TypeError("Missing required keyword argument: function")

        resources = []
        resources.append(self._construct_permission(function, event_source_token=self.SkillId))  # type: ignore[no-untyped-call]

        return resources


class IoTRule(PushEventSource):
    resource_type = "IoTRule"
    principal = "iot.amazonaws.com"

    property_types = {"Sql": PropertyType(True, IS_STR), "AwsIotSqlVersion": PropertyType(False, IS_STR)}

    Sql: PassThrough
    AwsIotSqlVersion: Optional[PassThrough]

    @cw_timer(prefix=FUNCTION_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, **kwargs):  # type: ignore[no-untyped-def]
        function = kwargs.get("function")

        if not function:
            raise TypeError("Missing required keyword argument: function")

        resources = []

        resource = "rule/${RuleName}"

        partition = ArnGenerator.get_partition_name()
        source_arn = fnSub(
            ArnGenerator.generate_arn(partition=partition, service="iot", resource=resource),
            {"RuleName": ref(self.logical_id)},
        )
        source_account = fnSub("${AWS::AccountId}")

        resources.append(self._construct_permission(function, source_arn=source_arn, source_account=source_account))  # type: ignore[no-untyped-call]
        resources.append(self._construct_iot_rule(function))  # type: ignore[no-untyped-call]

        return resources

    def _construct_iot_rule(self, function):  # type: ignore[no-untyped-def]
        rule = IotTopicRule(self.logical_id, attributes=function.get_passthrough_resource_attributes())

        payload = {
            "Sql": self.Sql,
            "RuleDisabled": False,
            "Actions": [{"Lambda": {"FunctionArn": function.get_runtime_attr("arn")}}],
        }

        if self.AwsIotSqlVersion:
            payload["AwsIotSqlVersion"] = self.AwsIotSqlVersion

        rule.TopicRulePayload = payload

        return rule


class Cognito(PushEventSource):
    resource_type = "Cognito"
    principal = "cognito-idp.amazonaws.com"

    property_types = {
        "UserPool": PropertyType(True, IS_STR),
        "Trigger": PropertyType(True, one_of(IS_STR, list_of(IS_STR)), False),
    }

    UserPool: Any
    Trigger: Union[str, List[str]]

    def resources_to_link(self, resources):  # type: ignore[no-untyped-def]
        if isinstance(self.UserPool, dict) and "Ref" in self.UserPool:
            userpool_id = self.UserPool["Ref"]
            if not isinstance(userpool_id, str):
                raise InvalidEventException(
                    self.logical_id,
                    "Ref in Userpool is not a string.",
                )
            if userpool_id in resources:
                return {"userpool": resources[userpool_id], "userpool_id": userpool_id}
        raise InvalidEventException(
            self.relative_id, "Cognito events must reference a Cognito UserPool in the same template."
        )

    @cw_timer(prefix=FUNCTION_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, **kwargs):  # type: ignore[no-untyped-def]
        function = kwargs.get("function")

        if not function:
            raise TypeError("Missing required keyword argument: function")

        if "userpool" not in kwargs or kwargs["userpool"] is None:
            raise TypeError("Missing required keyword argument: userpool")

        if "userpool_id" not in kwargs or kwargs["userpool_id"] is None:
            raise TypeError("Missing required keyword argument: userpool_id")

        userpool = kwargs["userpool"]
        userpool_id = kwargs["userpool_id"]

        resources = []
        source_arn = fnGetAtt(userpool_id, "Arn")
        lambda_permission = self._construct_permission(  # type: ignore[no-untyped-call]
            function, source_arn=source_arn, prefix=function.logical_id + "Cognito"
        )
        for attribute, value in function.get_passthrough_resource_attributes().items():
            lambda_permission.set_resource_attribute(attribute, value)
        resources.append(lambda_permission)

        self._inject_lambda_config(function, userpool, userpool_id)
        resources.append(CognitoUserPool.from_dict(userpool_id, userpool, userpool_id))
        return resources

    def _inject_lambda_config(self, function: Any, userpool: Dict[str, Any], userpool_id: str) -> None:
        event_triggers = self.Trigger
        if isinstance(self.Trigger, str):
            event_triggers = [self.Trigger]

        # TODO can these be conditional?

        properties = userpool.get("Properties")
        if properties is None:
            properties = {}
            userpool["Properties"] = properties

        lambda_config = properties.get("LambdaConfig")
        if lambda_config is None:
            lambda_config = {}
            properties["LambdaConfig"] = lambda_config
        sam_expect(lambda_config, userpool_id, "LambdaConfig").to_be_a_map()

        for event_trigger in event_triggers:
            if event_trigger not in lambda_config:
                lambda_config[event_trigger] = function.get_runtime_attr("arn")
            else:
                raise InvalidEventException(
                    self.relative_id, f'Cognito trigger "{self.Trigger}" defined multiple times.'
                )


class HttpApi(PushEventSource):
    """Api method event source for SAM Functions."""

    resource_type = "HttpApi"
    principal = "apigateway.amazonaws.com"
    property_types = {
        "Path": PropertyType(False, IS_STR),
        "Method": PropertyType(False, IS_STR),
        "ApiId": PropertyType(False, IS_STR),
        "Stage": PropertyType(False, IS_STR),
        "Auth": PropertyType(False, IS_DICT),
        "TimeoutInMillis": PropertyType(False, IS_INT),
        "RouteSettings": PropertyType(False, IS_DICT),
        "PayloadFormatVersion": PropertyType(False, IS_STR),
    }

    Path: Optional[str]
    Method: Optional[str]
    ApiId: Optional[Union[str, Dict[str, str]]]
    Stage: Optional[PassThrough]
    Auth: Optional[PassThrough]
    TimeoutInMillis: Optional[PassThrough]
    RouteSettings: Optional[PassThrough]
    PayloadFormatVersion: Optional[PassThrough]

    @property
    def _method(self) -> str:
        """
        Despite Method is optional, it will be set before entering here
        in ImplicitHttpApiPlugin._process_api_events().
        """
        return cast(str, self.Method)

    @property
    def _path(self) -> str:
        """
        Despite Method is optional, it will be set before entering here
        in ImplicitHttpApiPlugin._process_api_events().
        """
        return cast(str, self.Path)

    def resources_to_link(self, resources):  # type: ignore[no-untyped-def]
        """
        If this API Event Source refers to an explicit API resource, resolve the reference and grab
        necessary data from the explicit API
        """

        api_id = self.ApiId
        if isinstance(api_id, dict) and "Ref" in api_id:
            api_id = api_id["Ref"]

        explicit_api = resources[api_id].get("Properties", {})

        return {"explicit_api": explicit_api, "api_id": api_id}

    @cw_timer(prefix=FUNCTION_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, **kwargs):  # type: ignore[no-untyped-def]
        """If the Api event source has a RestApi property, then simply return the Lambda Permission resource allowing
        API Gateway to call the function. If no RestApi is provided, then additionally inject the path, method, and the
        x-amazon-apigateway-integration into the OpenApi body for a provided implicit API.

        :param dict kwargs: a dict containing the implicit RestApi to be modified, should no explicit RestApi \
                be provided.
        :returns: a list of vanilla CloudFormation Resources, to which this Api event expands
        :rtype: list
        """
        resources = []

        function = kwargs.get("function")

        # Convert to lower case so that user can specify either GET or get
        self.Method = self._method.lower()

        resources.extend(self._get_permissions(kwargs))  # type: ignore[no-untyped-call]

        explicit_api = kwargs["explicit_api"]
        api_id = kwargs["api_id"]
        self._add_openapi_integration(explicit_api, api_id, function, explicit_api.get("__MANAGE_SWAGGER"))  # type: ignore[no-untyped-call]

        return resources

    def _get_permissions(self, resources_to_link):  # type: ignore[no-untyped-def]
        permissions = []

        # Give permission to all stages by default
        permitted_stage = "*"

        permission = self._get_permission(resources_to_link, permitted_stage)  # type: ignore[no-untyped-call]
        if permission:
            permissions.append(permission)
        return permissions

    def _get_permission(self, resources_to_link, stage):  # type: ignore[no-untyped-def]
        # It turns out that APIGW doesn't like trailing slashes in paths (#665)
        # and removes as a part of their behaviour, but this isn't documented.
        # The regex removes the tailing slash to ensure the permission works as intended
        path = re.sub(r"^(.+)/$", r"\1", self._path)

        editor = None
        if resources_to_link["explicit_api"].get("DefinitionBody"):
            try:
                editor = OpenApiEditor(resources_to_link["explicit_api"].get("DefinitionBody"))
            except InvalidDocumentException as e:
                api_logical_id = self.ApiId.get("Ref") if isinstance(self.ApiId, dict) else self.ApiId
                # TODO: api_logical_id is never None, try to make it consistent with what mypy thinks
                raise InvalidResourceException(
                    cast(str, api_logical_id), " ".join(ex.message for ex in e.causes)
                ) from e

        # If this is using the new $default path, keep path blank and add a * permission
        if path == OpenApiEditor._DEFAULT_PATH:
            path = ""
        elif editor and editor.is_integration_function_logical_id_match(  # type: ignore[no-untyped-call]
            OpenApiEditor._DEFAULT_PATH, OpenApiEditor._X_ANY_METHOD, resources_to_link.get("function").logical_id
        ):
            # Case where default exists for this function, and so the permissions for that will apply here as well
            # This can save us several CFN resources (not duplicating permissions)
            return None
        path = OpenApiEditor.get_path_without_trailing_slash(path)  # type: ignore[no-untyped-call]

        # Handle case where Method is already the ANY ApiGateway extension
        method = (
            "*"
            if self._method.lower() == "any" or self._method.lower() == OpenApiEditor._X_ANY_METHOD
            else self._method.upper()
        )

        api_id = self.ApiId

        # when the Method is "ANY" and the path is '/$default' it adds an extra "*" which causes a bug
        # the generated ARN for permissions ends with /*/*/$default which causes the path to be invalid
        # see this issue: https://github.com/aws/serverless-application-model/issues/1860
        resource = "${__ApiId__}/${__Stage__}"
        if self._method.lower() == "any" and path == f"/{OpenApiEditor._DEFAULT_PATH}":
            resource += path
        else:
            resource += f"/{method}{path}"

        # ApiId can be a simple string or intrinsic function like !Ref. Using Fn::Sub will handle both cases
        source_arn = fnSub(
            ArnGenerator.generate_arn(partition="${AWS::Partition}", service="execute-api", resource=resource),
            {"__ApiId__": api_id, "__Stage__": stage},
        )

        return self._construct_permission(resources_to_link["function"], source_arn=source_arn)  # type: ignore[no-untyped-call]

    def _add_openapi_integration(self, api, api_id, function, manage_swagger=False):  # type: ignore[no-untyped-def]
        """
        Adds the path and method for this Api event source to the OpenApi body for the provided RestApi.
        """
        open_api_body = api.get("DefinitionBody")
        if open_api_body is None:
            return

        uri = _build_apigw_integration_uri(function, "${AWS::Partition}")  # type: ignore[no-untyped-call]

        editor = OpenApiEditor(open_api_body)

        if manage_swagger and editor.has_integration(self._path, self._method):
            # Cannot add the Lambda Integration, if it is already present
            raise InvalidEventException(
                self.relative_id,
                "API method '{method}' defined multiple times for path '{path}'.".format(
                    method=self._method, path=self._path
                ),
            )

        condition = None
        if CONDITION in function.resource_attributes:
            condition = function.resource_attributes[CONDITION]

        editor.add_lambda_integration(self._path, self._method, uri, self.Auth, api.get("Auth"), condition=condition)  # type: ignore[no-untyped-call]
        if self.Auth:
            self._add_auth_to_openapi_integration(api, api_id, editor, self.Auth)
        if self.TimeoutInMillis:
            editor.add_timeout_to_method(api=api, path=self._path, method_name=self._method, timeout=self.TimeoutInMillis)  # type: ignore[no-untyped-call]
        path_parameters = re.findall("{(.*?)}", self._path)
        if path_parameters:
            editor.add_path_parameters_to_method(  # type: ignore[no-untyped-call]
                api=api, path=self._path, method_name=self._method, path_parameters=path_parameters
            )

        if self.PayloadFormatVersion:
            editor.add_payload_format_version_to_method(  # type: ignore[no-untyped-call]
                api=api, path=self._path, method_name=self._method, payload_format_version=self.PayloadFormatVersion
            )
        api["DefinitionBody"] = editor.openapi

    def _add_auth_to_openapi_integration(
        self, api: Dict[str, Any], api_id: str, editor: OpenApiEditor, auth: Dict[str, Any]
    ) -> None:
        """Adds authorization to the lambda integration
        :param api: api object
        :param api_id: api logical id
        :param editor: OpenApiEditor object that contains the OpenApi definition
        """
        method_authorizer = auth.get("Authorizer")
        api_auth = api.get("Auth", {})
        sam_expect(api_auth, api_id, "Auth").to_be_a_map()
        if not method_authorizer:
            if api_auth.get("DefaultAuthorizer"):
                auth["Authorizer"] = method_authorizer = api_auth.get("DefaultAuthorizer")
            else:
                # currently, we require either a default auth or auth in the method
                raise InvalidEventException(
                    self.relative_id,
                    "'Auth' section requires either "
                    "an explicit 'Authorizer' set or a 'DefaultAuthorizer' "
                    "configured on the HttpApi.",
                )

        # Default auth should already be applied, so apply any other auth here or scope override to default
        api_authorizers = api_auth and api_auth.get("Authorizers")

        # The IAM authorizer is built-in and not defined as a regular Authorizer.
        iam_authorizer_enabled = api_auth and api_auth.get("EnableIamAuthorizer", False) is True

        _check_valid_authorizer_types(  # type: ignore[no-untyped-call]
            self.relative_id, self._method, self._path, method_authorizer, api_authorizers, iam_authorizer_enabled
        )

        if method_authorizer == "NONE":
            if not api_auth.get("DefaultAuthorizer"):
                raise InvalidEventException(
                    self.relative_id,
                    "Unable to set Authorizer on API method [{method}] for path [{path}] because 'NONE' "
                    "is only a valid value when a DefaultAuthorizer on the API is specified.".format(
                        method=self._method, path=self._path
                    ),
                )
        # If the method authorizer is "AWS_IAM" but it's not enabled it's possible that's a custom authorizer, not the "official" one.
        # In that case a check needs to be performed to make sure that such an authorizer is defined.
        # The "official" AWS IAM authorizer is not defined as a normal authorizer so it won't exist in api_authorizer.
        elif (method_authorizer == "AWS_IAM" and not iam_authorizer_enabled) or method_authorizer != "AWS_IAM":
            if not api_authorizers:
                raise InvalidEventException(
                    self.relative_id,
                    "Unable to set Authorizer [{authorizer}] on API method [{method}] for path [{path}] "
                    "because the related API does not define any Authorizers.".format(
                        authorizer=method_authorizer, method=self._method, path=self._path
                    ),
                )

            if not api_authorizers.get(method_authorizer):
                raise InvalidEventException(
                    self.relative_id,
                    "Unable to set Authorizer [{authorizer}] on API method [{method}] for path [{path}] "
                    "because it wasn't defined in the API's Authorizers.".format(
                        authorizer=method_authorizer, method=self._method, path=self._path
                    ),
                )

        if auth.get("AuthorizationScopes") and not isinstance(auth.get("AuthorizationScopes"), list):
            raise InvalidEventException(
                self.relative_id,
                "Unable to set Authorizer on API method [{method}] for path [{path}] because "
                "'AuthorizationScopes' must be a list of strings.".format(method=self._method, path=self._path),
            )

        editor.add_auth_to_method(api=api, path=self._path, method_name=self._method, auth=self.Auth)  # type: ignore[no-untyped-call]


def _build_apigw_integration_uri(function, partition):  # type: ignore[no-untyped-def]
    function_arn = function.get_runtime_attr("arn")
    arn = (
        "arn:"
        + partition
        + ":apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/"
        + make_shorthand(function_arn)
        + "/invocations"
    )
    # function_arn is always of the form {"Fn::GetAtt": ["<function_logical_id>", "Arn"]}.
    # We only want to check if the function logical id is a Py27UniStr instance.
    if function_arn.get("Fn::GetAtt") and isinstance(function_arn["Fn::GetAtt"][0], Py27UniStr):
        arn = Py27UniStr(arn)
    return Py27Dict(fnSub(arn))


def _check_valid_authorizer_types(  # type: ignore[no-untyped-def]
    relative_id, method, path, method_authorizer, api_authorizers, iam_authorizer_enabled
):
    if method_authorizer == "NONE":
        # If the method authorizer is "NONE" then this check
        # isn't needed since DefaultAuthorizer needs to be used.
        return

    if method_authorizer == "AWS_IAM" and iam_authorizer_enabled:
        # The "official" AWS IAM authorizer is not defined as a normal authorizer so it won't exist in api_authorizers.
        # So we can safety skip this check.
        return

    if not isinstance(method_authorizer, str) or not isinstance(api_authorizers, dict):
        raise InvalidEventException(
            relative_id,
            "Unable to set Authorizer [{authorizer}] on API method [{method}] for path [{path}]. "
            "The method authorizer must be a string with a corresponding dict entry in the api authorizer.".format(
                authorizer=method_authorizer, method=method, path=path
            ),
        )
