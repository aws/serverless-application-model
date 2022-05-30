import copy
import re

from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.model import ResourceMacro, PropertyType
from samtranslator.model.eventsources import FUNCTION_EVETSOURCE_METRIC_PREFIX
from samtranslator.model.types import is_type, list_of, dict_of, one_of, is_str
from samtranslator.model.intrinsics import is_intrinsic, ref, fnGetAtt, fnSub, make_shorthand, make_conditional
from samtranslator.model.tags.resource_tagging import get_tag_list

from samtranslator.model.s3 import S3Bucket
from samtranslator.model.sns import SNSSubscription
from samtranslator.model.lambda_ import LambdaPermission
from samtranslator.model.events import EventsRule
from samtranslator.model.eventsources.pull import SQS
from samtranslator.model.sqs import SQSQueue, SQSQueuePolicy, SQSQueuePolicies
from samtranslator.model.eventbridge_utils import EventBridgeRuleUtils
from samtranslator.model.iot import IotTopicRule
from samtranslator.model.cognito import CognitoUserPool
from samtranslator.translator import logical_id_generator
from samtranslator.translator.arn_generator import ArnGenerator
from samtranslator.model.exceptions import InvalidEventException, InvalidResourceException, InvalidDocumentException
from samtranslator.swagger.swagger import SwaggerEditor
from samtranslator.open_api.open_api import OpenApiEditor
from samtranslator.utils.py27hash_fix import Py27Dict, Py27UniStr

CONDITION = "Condition"

REQUEST_PARAMETER_PROPERTIES = ["Required", "Caching"]


class PushEventSource(ResourceMacro):
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

    principal = None

    def _construct_permission(
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
        except NotImplementedError:
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
        "Schedule": PropertyType(True, is_str()),
        "Input": PropertyType(False, is_str()),
        "Enabled": PropertyType(False, is_type(bool)),
        "Name": PropertyType(False, is_str()),
        "Description": PropertyType(False, is_str()),
        "DeadLetterConfig": PropertyType(False, is_type(dict)),
        "RetryPolicy": PropertyType(False, is_type(dict)),
    }

    @cw_timer(prefix=FUNCTION_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, **kwargs):
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
        if self.Enabled is not None:
            events_rule.State = "ENABLED" if self.Enabled else "DISABLED"
        events_rule.Name = self.Name
        events_rule.Description = self.Description

        source_arn = events_rule.get_runtime_attr("arn")
        dlq_queue_arn = None
        if self.DeadLetterConfig is not None:
            EventBridgeRuleUtils.validate_dlq_config(self.logical_id, self.DeadLetterConfig)
            dlq_queue_arn, dlq_resources = EventBridgeRuleUtils.get_dlq_queue_arn_and_resources(
                self, source_arn, passthrough_resource_attributes
            )
            resources.extend(dlq_resources)

        events_rule.Targets = [self._construct_target(function, dlq_queue_arn)]

        resources.append(self._construct_permission(function, source_arn=source_arn))

        return resources

    def _construct_target(self, function, dead_letter_queue_arn=None):
        """Constructs the Target property for the EventBridge Rule.

        :returns: the Target property
        :rtype: dict
        """
        target = {"Arn": function.get_runtime_attr("arn"), "Id": self.logical_id + "LambdaTarget"}
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
        "EventBusName": PropertyType(False, is_str()),
        "Pattern": PropertyType(False, is_type(dict)),
        "DeadLetterConfig": PropertyType(False, is_type(dict)),
        "RetryPolicy": PropertyType(False, is_type(dict)),
        "Input": PropertyType(False, is_str()),
        "InputPath": PropertyType(False, is_str()),
        "Target": PropertyType(False, is_type(dict)),
    }

    @cw_timer(prefix=FUNCTION_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, **kwargs):
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
        source_arn = events_rule.get_runtime_attr("arn")

        dlq_queue_arn = None
        if self.DeadLetterConfig is not None:
            EventBridgeRuleUtils.validate_dlq_config(self.logical_id, self.DeadLetterConfig)
            dlq_queue_arn, dlq_resources = EventBridgeRuleUtils.get_dlq_queue_arn_and_resources(
                self, source_arn, passthrough_resource_attributes
            )
            resources.extend(dlq_resources)

        events_rule.Targets = [self._construct_target(function, dlq_queue_arn)]

        resources.append(events_rule)
        resources.append(self._construct_permission(function, source_arn=source_arn))

        return resources

    def _construct_target(self, function, dead_letter_queue_arn=None):
        """Constructs the Target property for the CloudWatch Events/EventBridge Rule.

        :returns: the Target property
        :rtype: dict
        """
        target_id = self.Target["Id"] if self.Target and "Id" in self.Target else self.logical_id + "LambdaTarget"
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
        "Bucket": PropertyType(True, is_str()),
        "Events": PropertyType(True, one_of(is_str(), list_of(is_str())), False),
        "Filter": PropertyType(False, dict_of(is_str(), is_str())),
    }

    def resources_to_link(self, resources):
        if isinstance(self.Bucket, dict) and "Ref" in self.Bucket:
            bucket_id = self.Bucket["Ref"]
            if not isinstance(bucket_id, str):
                raise InvalidEventException(self.relative_id, "'Ref' value in S3 events is not a valid string.")
            if bucket_id in resources:
                return {"bucket": resources[bucket_id], "bucket_id": bucket_id}
        raise InvalidEventException(self.relative_id, "S3 events must reference an S3 bucket in the same template.")

    @cw_timer(prefix=FUNCTION_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, **kwargs):
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
        permission = self._construct_permission(function, source_account=source_account)
        if CONDITION in permission.resource_attributes:
            self._depend_on_lambda_permissions_using_tag(bucket, permission)
        else:
            self._depend_on_lambda_permissions(bucket, permission)
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
        self._inject_notification_configuration(function, bucket)
        resources.append(S3Bucket.from_dict(bucket_id, bucket))

        return resources

    def _depend_on_lambda_permissions(self, bucket, permission):
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
        except TypeError:
            raise InvalidResourceException(
                self.logical_id,
                "Invalid type for field 'DependsOn'. Expected a string or list of strings.",
            )

        depends_on_set.add(permission.logical_id)
        bucket["DependsOn"] = list(depends_on_set)

        return bucket

    def _depend_on_lambda_permissions_using_tag(self, bucket, permission):
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
        dep_tag = {
            "sam:ConditionalDependsOn:"
            + permission.logical_id: {
                "Fn::If": [permission.resource_attributes[CONDITION], ref(permission.logical_id), "no dependency"]
            }
        }
        properties["Tags"] = tags + get_tag_list(dep_tag)
        return bucket

    def _inject_notification_configuration(self, function, bucket):
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

        properties = bucket.get("Properties", None)
        if properties is None:
            properties = {}
            bucket["Properties"] = properties

        notification_config = properties.get("NotificationConfiguration", None)
        if notification_config is None:
            notification_config = {}
            properties["NotificationConfiguration"] = notification_config

        lambda_notifications = notification_config.get("LambdaConfigurations", None)
        if lambda_notifications is None:
            lambda_notifications = []
            notification_config["LambdaConfigurations"] = lambda_notifications

        if not isinstance(lambda_notifications, list):
            raise InvalidResourceException(self.logical_id, "Invalid type for LambdaConfigurations. Must be a list.")

        for event_mapping in event_mappings:
            if event_mapping not in lambda_notifications:
                lambda_notifications.append(event_mapping)
        return bucket


class SNS(PushEventSource):
    """SNS topic event source for SAM Functions."""

    resource_type = "SNS"
    principal = "sns.amazonaws.com"
    property_types = {
        "Topic": PropertyType(True, is_str()),
        "Region": PropertyType(False, is_str()),
        "FilterPolicy": PropertyType(False, dict_of(is_str(), list_of(one_of(is_str(), is_type(dict))))),
        "SqsSubscription": PropertyType(False, one_of(is_type(bool), is_type(dict))),
    }

    @cw_timer(prefix=FUNCTION_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, **kwargs):
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
                function,
            )
            return [self._construct_permission(function, source_arn=self.Topic), subscription]

        # SNS -> SQS(Create New) -> Lambda
        if isinstance(self.SqsSubscription, bool):
            resources = []
            queue = self._inject_sqs_queue(function)
            queue_arn = queue.get_runtime_attr("arn")
            queue_url = queue.get_runtime_attr("queue_url")

            queue_policy = self._inject_sqs_queue_policy(self.Topic, queue_arn, queue_url, function)
            subscription = self._inject_subscription(
                "sqs", queue_arn, self.Topic, self.Region, self.FilterPolicy, function
            )
            event_source = self._inject_sqs_event_source_mapping(function, role, queue_arn)

            resources = resources + event_source
            resources.append(queue)
            resources.append(queue_policy)
            resources.append(subscription)
            return resources

        # SNS -> SQS(Existing) -> Lambda
        resources = []
        queue_arn = self.SqsSubscription.get("QueueArn", None)
        queue_url = self.SqsSubscription.get("QueueUrl", None)
        if not queue_arn or not queue_url:
            raise InvalidEventException(self.relative_id, "No QueueARN or QueueURL provided.")

        queue_policy_logical_id = self.SqsSubscription.get("QueuePolicyLogicalId", None)
        batch_size = self.SqsSubscription.get("BatchSize", None)
        enabled = self.SqsSubscription.get("Enabled", None)

        queue_policy = self._inject_sqs_queue_policy(
            self.Topic, queue_arn, queue_url, function, queue_policy_logical_id
        )
        subscription = self._inject_subscription("sqs", queue_arn, self.Topic, self.Region, self.FilterPolicy, function)
        event_source = self._inject_sqs_event_source_mapping(function, role, queue_arn, batch_size, enabled)

        resources = resources + event_source
        resources.append(queue_policy)
        resources.append(subscription)
        return resources

    def _inject_subscription(self, protocol, endpoint, topic, region, filterPolicy, function):
        subscription = SNSSubscription(self.logical_id, attributes=function.get_passthrough_resource_attributes())
        subscription.Protocol = protocol
        subscription.Endpoint = endpoint
        subscription.TopicArn = topic

        if region is not None:
            subscription.Region = region

        if filterPolicy is not None:
            subscription.FilterPolicy = filterPolicy

        return subscription

    def _inject_sqs_queue(self, function):
        return SQSQueue(self.logical_id + "Queue", attributes=function.get_passthrough_resource_attributes())

    def _inject_sqs_event_source_mapping(self, function, role, queue_arn, batch_size=None, enabled=None):
        event_source = SQS(
            self.logical_id + "EventSourceMapping", attributes=function.get_passthrough_resource_attributes()
        )
        event_source.Queue = queue_arn
        event_source.BatchSize = batch_size or 10
        event_source.Enabled = enabled or True
        return event_source.to_cloudformation(function=function, role=role)

    def _inject_sqs_queue_policy(self, topic_arn, queue_arn, queue_url, function, logical_id=None):
        policy = SQSQueuePolicy(
            logical_id or self.logical_id + "QueuePolicy", attributes=function.get_passthrough_resource_attributes()
        )

        policy.PolicyDocument = SQSQueuePolicies.sns_topic_send_message_role_policy(topic_arn, queue_arn)
        policy.Queues = [queue_url]
        return policy


class Api(PushEventSource):
    """Api method event source for SAM Functions."""

    resource_type = "Api"
    principal = "apigateway.amazonaws.com"
    property_types = {
        "Path": PropertyType(True, is_str()),
        "Method": PropertyType(True, is_str()),
        # Api Event sources must "always" be paired with a Serverless::Api
        "RestApiId": PropertyType(True, is_str()),
        "Stage": PropertyType(False, is_str()),
        "Auth": PropertyType(False, is_type(dict)),
        "RequestModel": PropertyType(False, is_type(dict)),
        "RequestParameters": PropertyType(False, is_type(list)),
    }

    def resources_to_link(self, resources):
        """
        If this API Event Source refers to an explicit API resource, resolve the reference and grab
        necessary data from the explicit API
        """

        # If RestApiId is a resource in the same template, then we try find the StageName by following the reference
        # Otherwise we default to a wildcard. This stage name is solely used to construct the permission to
        # allow this stage to invoke the Lambda function. If we are unable to resolve the stage name, we will
        # simply permit all stages to invoke this Lambda function
        # This hack is necessary because customers could use !ImportValue, !Ref or other intrinsic functions which
        # can be sometimes impossible to resolve (ie. when it has cross-stack references)
        permitted_stage = "*"
        stage_suffix = "AllStages"
        explicit_api = None
        rest_api_id = self.get_rest_api_id_string(self.RestApiId)
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
                    if not permitted_stage:
                        raise InvalidResourceException(rest_api_id, "StageName cannot be empty.")
                    stage_suffix = permitted_stage
                else:
                    stage_suffix = "Stage"

            else:
                # RestApiId is a string, not an intrinsic, but we did not find a valid API resource for this ID
                raise InvalidEventException(
                    self.relative_id,
                    "RestApiId property of Api event must reference a valid " "resource in the same template.",
                )

        return {"explicit_api": explicit_api, "explicit_api_stage": {"suffix": stage_suffix}}

    @cw_timer(prefix=FUNCTION_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, **kwargs):
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

        resources.extend(self._get_permissions(kwargs))

        explicit_api = kwargs["explicit_api"]
        if explicit_api.get("__MANAGE_SWAGGER"):
            self._add_swagger_integration(explicit_api, function, intrinsics_resolver)

        return resources

    def _get_permissions(self, resources_to_link):
        permissions = []

        # By default, implicit APIs get a stage called Prod. If the API event refers to an
        # explicit API using RestApiId property, we should grab the stage name of the explicit API
        # all stages for an API are given permission
        permitted_stage = "*"
        suffix = "Prod"
        if "explicit_api_stage" in resources_to_link:
            suffix = resources_to_link["explicit_api_stage"]["suffix"]
        self.Stage = suffix

        permissions.append(self._get_permission(resources_to_link, permitted_stage, suffix))
        return permissions

    def _get_permission(self, resources_to_link, stage, suffix):
        # It turns out that APIGW doesn't like trailing slashes in paths (#665)
        # and removes as a part of their behaviour, but this isn't documented.
        # The regex removes the tailing slash to ensure the permission works as intended
        path = re.sub(r"^(.+)/$", r"\1", self.Path)

        if not stage or not suffix:
            raise RuntimeError("Could not add permission to lambda function.")

        path = SwaggerEditor.get_path_without_trailing_slash(path)
        method = "*" if self.Method.lower() == "any" else self.Method.upper()

        api_id = self.RestApiId

        # RestApiId can be a simple string or intrinsic function like !Ref. Using Fn::Sub will handle both cases
        resource = "${__ApiId__}/" + "${__Stage__}/" + method + path
        partition = ArnGenerator.get_partition_name()
        source_arn = fnSub(
            ArnGenerator.generate_arn(partition=partition, service="execute-api", resource=resource),
            {"__ApiId__": api_id, "__Stage__": stage},
        )

        return self._construct_permission(resources_to_link["function"], source_arn=source_arn, suffix=suffix)

    def _add_swagger_integration(self, api, function, intrinsics_resolver):
        """Adds the path and method for this Api event source to the Swagger body for the provided RestApi.

        :param model.apigateway.ApiGatewayRestApi rest_api: the RestApi to which the path and method should be added.
        """
        swagger_body = api.get("DefinitionBody")
        if swagger_body is None:
            return

        partition = ArnGenerator.get_partition_name()
        uri = _build_apigw_integration_uri(function, partition)

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

        editor.add_lambda_integration(self.Path, self.Method, uri, self.Auth, api.get("Auth"), condition=condition)

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

                    _check_valid_authorizer_types(
                        self.relative_id, self.Method, self.Path, method_authorizer, api_authorizers, False
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

        if self.RequestModel:
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

                editor.add_request_model_to_method(
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

                    editor.add_request_validator_to_method(
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
                        key in REQUEST_PARAMETER_PROPERTIES for key in parameter_value.keys()
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
                    settings.update({"Name": parameter})

                    parameters.append(settings)

                else:
                    raise InvalidEventException(
                        self.relative_id,
                        "Invalid value for 'RequestParameters' property. Property must be either a string or an object",
                    )

            editor.add_request_parameters_to_method(
                path=self.Path, method_name=self.Method, request_parameters=parameters
            )

        api["DefinitionBody"] = editor.swagger

    @staticmethod
    def get_rest_api_id_string(rest_api_id):
        """
        rest_api_id can be either a string or a dictionary where the actual api id is the value at key "Ref".
        If rest_api_id is a dictionary with key "Ref", returns value at key "Ref". Otherwise, return rest_api_id.

        :param rest_api_id: a string or dictionary that contains the api id
        :return: string value of rest_api_id
        """
        return rest_api_id["Ref"] if isinstance(rest_api_id, dict) and "Ref" in rest_api_id else rest_api_id


class AlexaSkill(PushEventSource):
    resource_type = "AlexaSkill"
    principal = "alexa-appkit.amazon.com"

    property_types = {"SkillId": PropertyType(False, is_str())}

    @cw_timer(prefix=FUNCTION_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, **kwargs):
        function = kwargs.get("function")

        if not function:
            raise TypeError("Missing required keyword argument: function")

        resources = []
        resources.append(self._construct_permission(function, event_source_token=self.SkillId))

        return resources


class IoTRule(PushEventSource):
    resource_type = "IoTRule"
    principal = "iot.amazonaws.com"

    property_types = {"Sql": PropertyType(True, is_str()), "AwsIotSqlVersion": PropertyType(False, is_str())}

    @cw_timer(prefix=FUNCTION_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, **kwargs):
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

        resources.append(self._construct_permission(function, source_arn=source_arn, source_account=source_account))
        resources.append(self._construct_iot_rule(function))

        return resources

    def _construct_iot_rule(self, function):
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
        "UserPool": PropertyType(True, is_str()),
        "Trigger": PropertyType(True, one_of(is_str(), list_of(is_str())), False),
    }

    def resources_to_link(self, resources):
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
    def to_cloudformation(self, **kwargs):
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
        lambda_permission = self._construct_permission(
            function, source_arn=source_arn, prefix=function.logical_id + "Cognito"
        )
        for attribute, value in function.get_passthrough_resource_attributes().items():
            lambda_permission.set_resource_attribute(attribute, value)
        resources.append(lambda_permission)

        self._inject_lambda_config(function, userpool)
        resources.append(CognitoUserPool.from_dict(userpool_id, userpool))
        return resources

    def _inject_lambda_config(self, function, userpool):
        event_triggers = self.Trigger
        if isinstance(self.Trigger, str):
            event_triggers = [self.Trigger]

        # TODO can these be conditional?

        properties = userpool.get("Properties", None)
        if properties is None:
            properties = {}
            userpool["Properties"] = properties

        lambda_config = properties.get("LambdaConfig", None)
        if lambda_config is None:
            lambda_config = {}
            properties["LambdaConfig"] = lambda_config

        for event_trigger in event_triggers:
            if event_trigger not in lambda_config:
                lambda_config[event_trigger] = function.get_runtime_attr("arn")
            else:
                raise InvalidEventException(
                    self.relative_id, 'Cognito trigger "{trigger}" defined multiple times.'.format(trigger=self.Trigger)
                )
        return userpool


class HttpApi(PushEventSource):
    """Api method event source for SAM Functions."""

    resource_type = "HttpApi"
    principal = "apigateway.amazonaws.com"
    property_types = {
        "Path": PropertyType(False, is_str()),
        "Method": PropertyType(False, is_str()),
        "ApiId": PropertyType(False, is_str()),
        "Stage": PropertyType(False, is_str()),
        "Auth": PropertyType(False, is_type(dict)),
        "TimeoutInMillis": PropertyType(False, is_type(int)),
        "RouteSettings": PropertyType(False, is_type(dict)),
        "PayloadFormatVersion": PropertyType(False, is_str()),
    }

    def resources_to_link(self, resources):
        """
        If this API Event Source refers to an explicit API resource, resolve the reference and grab
        necessary data from the explicit API
        """

        api_id = self.ApiId
        if isinstance(api_id, dict) and "Ref" in api_id:
            api_id = api_id["Ref"]

        explicit_api = resources[api_id].get("Properties", {})

        return {"explicit_api": explicit_api}

    @cw_timer(prefix=FUNCTION_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, **kwargs):
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

        if self.Method is not None:
            # Convert to lower case so that user can specify either GET or get
            self.Method = self.Method.lower()

        resources.extend(self._get_permissions(kwargs))

        explicit_api = kwargs["explicit_api"]
        self._add_openapi_integration(explicit_api, function, explicit_api.get("__MANAGE_SWAGGER"))

        return resources

    def _get_permissions(self, resources_to_link):
        permissions = []

        # Give permission to all stages by default
        permitted_stage = "*"

        permission = self._get_permission(resources_to_link, permitted_stage)
        if permission:
            permissions.append(permission)
        return permissions

    def _get_permission(self, resources_to_link, stage):
        # It turns out that APIGW doesn't like trailing slashes in paths (#665)
        # and removes as a part of their behaviour, but this isn't documented.
        # The regex removes the tailing slash to ensure the permission works as intended
        path = re.sub(r"^(.+)/$", r"\1", self.Path)

        editor = None
        if resources_to_link["explicit_api"].get("DefinitionBody"):
            try:
                editor = OpenApiEditor(resources_to_link["explicit_api"].get("DefinitionBody"))
            except InvalidDocumentException as e:
                api_logical_id = self.ApiId.get("Ref") if isinstance(self.ApiId, dict) else self.ApiId
                raise InvalidResourceException(api_logical_id, e)

        # If this is using the new $default path, keep path blank and add a * permission
        if path == OpenApiEditor._DEFAULT_PATH:
            path = ""
        elif editor and editor.is_integration_function_logical_id_match(
            OpenApiEditor._DEFAULT_PATH, OpenApiEditor._X_ANY_METHOD, resources_to_link.get("function").logical_id
        ):
            # Case where default exists for this function, and so the permissions for that will apply here as well
            # This can save us several CFN resources (not duplicating permissions)
            return
        else:
            path = OpenApiEditor.get_path_without_trailing_slash(path)

        # Handle case where Method is already the ANY ApiGateway extension
        if self.Method.lower() == "any" or self.Method.lower() == OpenApiEditor._X_ANY_METHOD:
            method = "*"
        else:
            method = self.Method.upper()

        api_id = self.ApiId

        # ApiId can be a simple string or intrinsic function like !Ref. Using Fn::Sub will handle both cases
        resource = "${__ApiId__}/" + "${__Stage__}/" + method + path
        source_arn = fnSub(
            ArnGenerator.generate_arn(partition="${AWS::Partition}", service="execute-api", resource=resource),
            {"__ApiId__": api_id, "__Stage__": stage},
        )

        return self._construct_permission(resources_to_link["function"], source_arn=source_arn)

    def _add_openapi_integration(self, api, function, manage_swagger=False):
        """Adds the path and method for this Api event source to the OpenApi body for the provided RestApi.

        :param model.apigateway.ApiGatewayRestApi rest_api: the RestApi to which the path and method should be added.
        """
        open_api_body = api.get("DefinitionBody")
        if open_api_body is None:
            return

        uri = _build_apigw_integration_uri(function, "${AWS::Partition}")

        editor = OpenApiEditor(open_api_body)

        if manage_swagger and editor.has_integration(self.Path, self.Method):
            # Cannot add the Lambda Integration, if it is already present
            raise InvalidEventException(
                self.relative_id,
                "API method '{method}' defined multiple times for path '{path}'.".format(
                    method=self.Method, path=self.Path
                ),
            )

        condition = None
        if CONDITION in function.resource_attributes:
            condition = function.resource_attributes[CONDITION]

        editor.add_lambda_integration(self.Path, self.Method, uri, self.Auth, api.get("Auth"), condition=condition)
        if self.Auth:
            self._add_auth_to_openapi_integration(api, editor)
        if self.TimeoutInMillis:
            editor.add_timeout_to_method(api=api, path=self.Path, method_name=self.Method, timeout=self.TimeoutInMillis)
        path_parameters = re.findall("{(.*?)}", self.Path)
        if path_parameters:
            editor.add_path_parameters_to_method(
                api=api, path=self.Path, method_name=self.Method, path_parameters=path_parameters
            )

        if self.PayloadFormatVersion:
            editor.add_payload_format_version_to_method(
                api=api, path=self.Path, method_name=self.Method, payload_format_version=self.PayloadFormatVersion
            )
        api["DefinitionBody"] = editor.openapi

    def _add_auth_to_openapi_integration(self, api, editor):
        """Adds authorization to the lambda integration
        :param api: api object
        :param editor: OpenApiEditor object that contains the OpenApi definition
        """
        method_authorizer = self.Auth.get("Authorizer")
        api_auth = api.get("Auth", {})
        if not method_authorizer:
            if api_auth.get("DefaultAuthorizer"):
                self.Auth["Authorizer"] = method_authorizer = api_auth.get("DefaultAuthorizer")
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

        _check_valid_authorizer_types(
            self.relative_id, self.Method, self.Path, method_authorizer, api_authorizers, iam_authorizer_enabled
        )

        if method_authorizer == "NONE":
            if not api_auth.get("DefaultAuthorizer"):
                raise InvalidEventException(
                    self.relative_id,
                    "Unable to set Authorizer on API method [{method}] for path [{path}] because 'NONE' "
                    "is only a valid value when a DefaultAuthorizer on the API is specified.".format(
                        method=self.Method, path=self.Path
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
                        authorizer=method_authorizer, method=self.Method, path=self.Path
                    ),
                )

            if not api_authorizers.get(method_authorizer):
                raise InvalidEventException(
                    self.relative_id,
                    "Unable to set Authorizer [{authorizer}] on API method [{method}] for path [{path}] "
                    "because it wasn't defined in the API's Authorizers.".format(
                        authorizer=method_authorizer, method=self.Method, path=self.Path
                    ),
                )

        if self.Auth.get("AuthorizationScopes") and not isinstance(self.Auth.get("AuthorizationScopes"), list):
            raise InvalidEventException(
                self.relative_id,
                "Unable to set Authorizer on API method [{method}] for path [{path}] because "
                "'AuthorizationScopes' must be a list of strings.".format(method=self.Method, path=self.Path),
            )

        editor.add_auth_to_method(api=api, path=self.Path, method_name=self.Method, auth=self.Auth)


def _build_apigw_integration_uri(function, partition):
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


def _check_valid_authorizer_types(
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
