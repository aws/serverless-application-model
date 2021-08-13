""" SAM macro definitions """
from six import string_types
import copy
import uuid

import samtranslator.model.eventsources
import samtranslator.model.eventsources.pull
import samtranslator.model.eventsources.push
import samtranslator.model.eventsources.cloudwatchlogs
from .api.api_generator import ApiGenerator
from .api.http_api_generator import HttpApiGenerator
from .packagetype import ZIP, IMAGE
from .s3_utils.uri_parser import construct_s3_location_object, construct_image_code_object
from .tags.resource_tagging import get_tag_list
from samtranslator.model import PropertyType, SamResourceMacro, ResourceTypeResolver
from samtranslator.model.apigateway import (
    ApiGatewayDeployment,
    ApiGatewayStage,
    ApiGatewayDomainName,
    ApiGatewayUsagePlan,
    ApiGatewayUsagePlanKey,
    ApiGatewayApiKey,
)
from samtranslator.model.apigatewayv2 import ApiGatewayV2Stage, ApiGatewayV2DomainName
from samtranslator.model.cloudformation import NestedStack
from samtranslator.model.s3 import S3Bucket
from samtranslator.model.cloudwatch import SyntheticsCanary, CloudWatchAlarm
from samtranslator.model.dynamodb import DynamoDBTable
from samtranslator.model.exceptions import InvalidEventException, InvalidResourceException
from samtranslator.model.resource_policies import ResourcePolicies, PolicyTypes
from samtranslator.model.iam import IAMRole, IAMRolePolicies
from samtranslator.model.lambda_ import (
    LambdaFunction,
    LambdaVersion,
    LambdaAlias,
    LambdaLayerVersion,
    LambdaEventInvokeConfig,
)
from samtranslator.model.types import dict_of, is_str, is_type, list_of, one_of, any_type
from samtranslator.translator import logical_id_generator
from samtranslator.translator.arn_generator import ArnGenerator
from samtranslator.model.intrinsics import (
    is_intrinsic_if,
    is_intrinsic_no_value,
    ref,
    make_not_conditional,
    make_conditional,
    make_and_condition,
)
from samtranslator.model.sqs import SQSQueue
from samtranslator.model.sns import SNSTopic
from samtranslator.model.stepfunctions import StateMachineGenerator
from samtranslator.model.role_utils import construct_role_for_resource
from samtranslator.model.xray_utils import get_xray_managed_policy_name

# len(prefix) + MAX_CANARY_LOGICAL_ID_LENGTH + MAX_CANARY_UNIQUE_ID_LENGTH + 1 (extra '-' char added) must be less
# than or equal to 21
# https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-synthetics-canary.html#cfn-synthetics-canary-name
MAX_CANARY_LOGICAL_ID_LENGTH = 11
MAX_CANARY_UNIQUE_ID_LENGTH = 5
CANARY_NAME_PREFIX = "sam-"

# The default values for ComparisonOperator, Threshold and Period based on the MetricName provided by the user
# These default values were acquired from the Create Canary page in the Synthetics Canary dashboard
# https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Synthetics_Canaries_metrics.html
DEFAULT_METRIC_VALUES = {
    "SuccessPercent": {"ComparisonOperator": "LessThanThreshold", "Threshold": 90, "Period": 300},
    "Failed": {"ComparisonOperator": "GreaterThanOrEqualToThreshold", "Threshold": 1, "Period": 300},
    "Duration": {"ComparisonOperator": "GreaterThanThreshold", "Threshold": 30000, "Period": 900},
}
# the main metrics produced by Synthetics Canary
# sorted for backwards compatibility (python 2.7 automatically sorts keys)
VALID_CANARY_METRICS = list(sorted(DEFAULT_METRIC_VALUES))


class SamFunction(SamResourceMacro):
    """SAM function macro."""

    resource_type = "AWS::Serverless::Function"
    property_types = {
        "FunctionName": PropertyType(False, one_of(is_str(), is_type(dict))),
        "Handler": PropertyType(False, is_str()),
        "Runtime": PropertyType(False, is_str()),
        "CodeUri": PropertyType(False, one_of(is_str(), is_type(dict))),
        "ImageUri": PropertyType(False, is_str()),
        "PackageType": PropertyType(False, is_str()),
        "InlineCode": PropertyType(False, one_of(is_str(), is_type(dict))),
        "DeadLetterQueue": PropertyType(False, is_type(dict)),
        "Description": PropertyType(False, is_str()),
        "MemorySize": PropertyType(False, is_type(int)),
        "Timeout": PropertyType(False, is_type(int)),
        "VpcConfig": PropertyType(False, is_type(dict)),
        "Role": PropertyType(False, is_str()),
        "AssumeRolePolicyDocument": PropertyType(False, is_type(dict)),
        "Policies": PropertyType(False, one_of(is_str(), is_type(dict), list_of(one_of(is_str(), is_type(dict))))),
        "PermissionsBoundary": PropertyType(False, is_str()),
        "Environment": PropertyType(False, dict_of(is_str(), is_type(dict))),
        "Events": PropertyType(False, dict_of(is_str(), is_type(dict))),
        "Tags": PropertyType(False, is_type(dict)),
        "Tracing": PropertyType(False, one_of(is_type(dict), is_str())),
        "KmsKeyArn": PropertyType(False, one_of(is_type(dict), is_str())),
        "DeploymentPreference": PropertyType(False, is_type(dict)),
        "ReservedConcurrentExecutions": PropertyType(False, any_type()),
        "Layers": PropertyType(False, list_of(one_of(is_str(), is_type(dict)))),
        "EventInvokeConfig": PropertyType(False, is_type(dict)),
        # Intrinsic functions in value of Alias property are not supported, yet
        "AutoPublishAlias": PropertyType(False, one_of(is_str())),
        "AutoPublishCodeSha256": PropertyType(False, one_of(is_str())),
        "VersionDescription": PropertyType(False, is_str()),
        "ProvisionedConcurrencyConfig": PropertyType(False, is_type(dict)),
        "FileSystemConfigs": PropertyType(False, list_of(is_type(dict))),
        "ImageConfig": PropertyType(False, is_type(dict)),
        "CodeSigningConfigArn": PropertyType(False, is_str()),
    }
    event_resolver = ResourceTypeResolver(
        samtranslator.model.eventsources,
        samtranslator.model.eventsources.pull,
        samtranslator.model.eventsources.push,
        samtranslator.model.eventsources.cloudwatchlogs,
    )

    # DeadLetterQueue
    dead_letter_queue_policy_actions = {"SQS": "sqs:SendMessage", "SNS": "sns:Publish"}
    #

    # Conditions
    conditions = {}

    # Customers can refer to the following properties of SAM function
    referable_properties = {
        "Alias": LambdaAlias.resource_type,
        "Version": LambdaVersion.resource_type,
        # EventConfig auto created SQS and SNS
        "DestinationTopic": SNSTopic.resource_type,
        "DestinationQueue": SQSQueue.resource_type,
    }

    def resources_to_link(self, resources):
        try:
            return {"event_resources": self._event_resources_to_link(resources)}
        except InvalidEventException as e:
            raise InvalidResourceException(self.logical_id, e.message)

    def to_cloudformation(self, **kwargs):
        """Returns the Lambda function, role, and event resources to which this SAM Function corresponds.

        :param dict kwargs: already-converted resources that may need to be modified when converting this \
        macro to pure CloudFormation
        :returns: a list of vanilla CloudFormation Resources, to which this Function expands
        :rtype: list
        """
        resources = []
        intrinsics_resolver = kwargs["intrinsics_resolver"]
        mappings_resolver = kwargs.get("mappings_resolver", None)
        conditions = kwargs.get("conditions", {})

        if self.DeadLetterQueue:
            self._validate_dlq()

        lambda_function = self._construct_lambda_function()
        resources.append(lambda_function)

        if self.ProvisionedConcurrencyConfig:
            if not self.AutoPublishAlias:
                raise InvalidResourceException(
                    self.logical_id,
                    "To set ProvisionedConcurrencyConfig " "AutoPublishALias must be defined on the function",
                )

        lambda_alias = None
        alias_name = ""
        if self.AutoPublishAlias:
            alias_name = self._get_resolved_alias_name("AutoPublishAlias", self.AutoPublishAlias, intrinsics_resolver)
            code_sha256 = None
            if self.AutoPublishCodeSha256:
                code_sha256 = intrinsics_resolver.resolve_parameter_refs(self.AutoPublishCodeSha256)
            lambda_version = self._construct_version(
                lambda_function, intrinsics_resolver=intrinsics_resolver, code_sha256=code_sha256
            )
            lambda_alias = self._construct_alias(alias_name, lambda_function, lambda_version)
            resources.append(lambda_version)
            resources.append(lambda_alias)

        if self.DeploymentPreference:
            self._validate_deployment_preference_and_add_update_policy(
                kwargs.get("deployment_preference_collection", None),
                lambda_alias,
                intrinsics_resolver,
                mappings_resolver,
            )
        event_invoke_policies = []
        if self.EventInvokeConfig:
            function_name = lambda_function.logical_id
            event_invoke_resources, event_invoke_policies = self._construct_event_invoke_config(
                function_name, alias_name, lambda_alias, intrinsics_resolver, conditions
            )
            resources.extend(event_invoke_resources)

        managed_policy_map = kwargs.get("managed_policy_map", {})
        if not managed_policy_map:
            raise Exception("Managed policy map is empty, but should not be.")

        execution_role = None
        if lambda_function.Role is None:
            execution_role = self._construct_role(managed_policy_map, event_invoke_policies)
            lambda_function.Role = execution_role.get_runtime_attr("arn")
            resources.append(execution_role)

        try:
            resources += self._generate_event_resources(
                lambda_function,
                execution_role,
                kwargs["event_resources"],
                intrinsics_resolver,
                lambda_alias=lambda_alias,
            )
        except InvalidEventException as e:
            raise InvalidResourceException(self.logical_id, e.message)

        return resources

    def _construct_event_invoke_config(self, function_name, alias_name, lambda_alias, intrinsics_resolver, conditions):
        """
        Create a `AWS::Lambda::EventInvokeConfig` based on the input dict `EventInvokeConfig`
        """
        resources = []
        policy_document = []

        # Try to resolve.
        resolved_event_invoke_config = intrinsics_resolver.resolve_parameter_refs(self.EventInvokeConfig)

        logical_id = "{id}EventInvokeConfig".format(id=function_name)
        if lambda_alias:
            lambda_event_invoke_config = LambdaEventInvokeConfig(
                logical_id=logical_id, depends_on=[lambda_alias.logical_id], attributes=self.resource_attributes
            )
        else:
            lambda_event_invoke_config = LambdaEventInvokeConfig(
                logical_id=logical_id, attributes=self.resource_attributes
            )

        dest_config = {}
        input_dest_config = resolved_event_invoke_config.get("DestinationConfig")
        if input_dest_config and input_dest_config.get("OnSuccess") is not None:
            resource, on_success, policy = self._validate_and_inject_resource(
                input_dest_config.get("OnSuccess"), "OnSuccess", logical_id, conditions
            )
            dest_config["OnSuccess"] = on_success
            self.EventInvokeConfig["DestinationConfig"]["OnSuccess"]["Destination"] = on_success.get("Destination")
            if resource is not None:
                resources.extend([resource])
            if policy is not None:
                policy_document.append(policy)

        if input_dest_config and input_dest_config.get("OnFailure") is not None:
            resource, on_failure, policy = self._validate_and_inject_resource(
                input_dest_config.get("OnFailure"), "OnFailure", logical_id, conditions
            )
            dest_config["OnFailure"] = on_failure
            self.EventInvokeConfig["DestinationConfig"]["OnFailure"]["Destination"] = on_failure.get("Destination")
            if resource is not None:
                resources.extend([resource])
            if policy is not None:
                policy_document.append(policy)

        lambda_event_invoke_config.FunctionName = ref(function_name)
        if alias_name:
            lambda_event_invoke_config.Qualifier = alias_name
        else:
            lambda_event_invoke_config.Qualifier = "$LATEST"
        lambda_event_invoke_config.DestinationConfig = dest_config
        lambda_event_invoke_config.MaximumEventAgeInSeconds = resolved_event_invoke_config.get(
            "MaximumEventAgeInSeconds"
        )
        lambda_event_invoke_config.MaximumRetryAttempts = resolved_event_invoke_config.get("MaximumRetryAttempts")
        resources.extend([lambda_event_invoke_config])

        return resources, policy_document

    def _validate_and_inject_resource(self, dest_config, event, logical_id, conditions):
        """
        For Event Invoke Config, if the user has not specified a destination ARN for SQS/SNS, SAM
        auto creates a SQS and SNS resource with defaults. Intrinsics are supported in the Destination
        ARN property, so to handle conditional ifs we have to inject if conditions in the auto created
        SQS/SNS resources as well as in the policy documents.
        """
        accepted_types_list = ["SQS", "SNS", "EventBridge", "Lambda"]
        auto_inject_list = ["SQS", "SNS"]
        resource = None
        policy = {}
        destination = {}
        destination["Destination"] = dest_config.get("Destination")

        resource_logical_id = logical_id + event
        if dest_config.get("Type") is None or dest_config.get("Type") not in accepted_types_list:
            raise InvalidResourceException(
                self.logical_id, "'Type: {}' must be one of {}".format(dest_config.get("Type"), accepted_types_list)
            )

        property_condition, dest_arn = self._get_or_make_condition(
            dest_config.get("Destination"), logical_id, conditions
        )
        if dest_config.get("Destination") is None or property_condition is not None:
            combined_condition = self._make_and_conditions(
                self.get_passthrough_resource_attributes().get("Condition"), property_condition, conditions
            )
            if dest_config.get("Type") in auto_inject_list:
                if dest_config.get("Type") == "SQS":
                    resource = SQSQueue(
                        resource_logical_id + "Queue", attributes=self.get_passthrough_resource_attributes()
                    )
                if dest_config.get("Type") == "SNS":
                    resource = SNSTopic(
                        resource_logical_id + "Topic", attributes=self.get_passthrough_resource_attributes()
                    )
                if combined_condition:
                    resource.set_resource_attribute("Condition", combined_condition)
                if property_condition:
                    destination["Destination"] = make_conditional(
                        property_condition, resource.get_runtime_attr("arn"), dest_arn
                    )
                else:
                    destination["Destination"] = resource.get_runtime_attr("arn")
                policy = self._add_event_invoke_managed_policy(
                    dest_config, resource_logical_id, property_condition, destination["Destination"]
                )
            else:
                raise InvalidResourceException(
                    self.logical_id, "Destination is required if Type is not {}".format(auto_inject_list)
                )
        if dest_config.get("Destination") is not None and property_condition is None:
            policy = self._add_event_invoke_managed_policy(
                dest_config, resource_logical_id, None, dest_config.get("Destination")
            )

        return resource, destination, policy

    def _make_and_conditions(self, resource_condition, property_condition, conditions):
        if resource_condition is None:
            return property_condition

        if property_condition is None:
            return resource_condition

        and_condition = make_and_condition([{"Condition": resource_condition}, {"Condition": property_condition}])
        condition_name = self._make_gen_condition_name(resource_condition + "AND" + property_condition, self.logical_id)
        conditions[condition_name] = and_condition

        return condition_name

    def _get_or_make_condition(self, destination, logical_id, conditions):
        """
        This method checks if there is an If condition on Destination property. Since we auto create
        SQS and SNS if the destination ARN is not provided, we need to make sure that If condition
        is handled here.
        True case: Only create the Queue/Topic if the condition is true
        Destination: !If [SomeCondition, {Ref: AWS::NoValue}, queue-arn]

        False case : Only create the Queue/Topic if the condition is false.
        Destination: !If [SomeCondition, queue-arn, {Ref: AWS::NoValue}]

        For the false case, we need to add a new condition that negates the existing condition, and
        add that to the top-level Conditions.
        """
        if destination is None:
            return None, None
        if is_intrinsic_if(destination):
            dest_list = destination.get("Fn::If")
            if is_intrinsic_no_value(dest_list[1]) and is_intrinsic_no_value(dest_list[2]):
                return None, None
            if is_intrinsic_no_value(dest_list[1]):
                return dest_list[0], dest_list[2]
            if is_intrinsic_no_value(dest_list[2]):
                condition = dest_list[0]
                not_condition = self._make_gen_condition_name("NOT" + condition, logical_id)
                conditions[not_condition] = make_not_conditional(condition)
                return not_condition, dest_list[1]
        return None, None

    def _make_gen_condition_name(self, name, hash_input):
        # Make sure the property name is not over 255 characters (CFN limit)
        hash_digest = logical_id_generator.LogicalIdGenerator("", hash_input).gen()
        condition_name = name + hash_digest
        if len(condition_name) > 255:
            return input(condition_name)[:255]
        return condition_name

    def _get_resolved_alias_name(self, property_name, original_alias_value, intrinsics_resolver):
        """
        Alias names can be supplied as an intrinsic function. This method tries to extract alias name from a reference
        to a parameter. If it cannot completely resolve (ie. if a complex intrinsic function was used), then this
        method raises an exception. If alias name is just a plain string, it will return as is

        :param dict or string original_alias_value: Value of Alias property as provided by the customer
        :param samtranslator.intrinsics.resolver.IntrinsicsResolver intrinsics_resolver: Instance of the resolver that
            knows how to resolve parameter references
        :return string: Alias name
        :raises InvalidResourceException: If the value is a complex intrinsic function that cannot be resolved
        """

        # Try to resolve.
        resolved_alias_name = intrinsics_resolver.resolve_parameter_refs(original_alias_value)

        if not isinstance(resolved_alias_name, string_types):
            # This is still a dictionary which means we are not able to completely resolve intrinsics
            raise InvalidResourceException(
                self.logical_id, "'{}' must be a string or a Ref to a template parameter".format(property_name)
            )

        return resolved_alias_name

    def _construct_lambda_function(self):
        """Constructs and returns the Lambda function.

        :returns: a list containing the Lambda function and execution role resources
        :rtype: list
        """
        lambda_function = LambdaFunction(
            self.logical_id, depends_on=self.depends_on, attributes=self.resource_attributes
        )

        if self.FunctionName:
            lambda_function.FunctionName = self.FunctionName

        lambda_function.Handler = self.Handler
        lambda_function.Runtime = self.Runtime
        lambda_function.Description = self.Description
        lambda_function.MemorySize = self.MemorySize
        lambda_function.Timeout = self.Timeout
        lambda_function.VpcConfig = self.VpcConfig
        lambda_function.Role = self.Role
        lambda_function.Environment = self.Environment
        lambda_function.Code = self._construct_code_dict()
        lambda_function.KmsKeyArn = self.KmsKeyArn
        lambda_function.ReservedConcurrentExecutions = self.ReservedConcurrentExecutions
        lambda_function.Tags = self._construct_tag_list(self.Tags)
        lambda_function.Layers = self.Layers
        lambda_function.FileSystemConfigs = self.FileSystemConfigs
        lambda_function.ImageConfig = self.ImageConfig
        lambda_function.PackageType = self.PackageType

        if self.Tracing:
            lambda_function.TracingConfig = {"Mode": self.Tracing}

        if self.DeadLetterQueue:
            lambda_function.DeadLetterConfig = {"TargetArn": self.DeadLetterQueue["TargetArn"]}

        lambda_function.CodeSigningConfigArn = self.CodeSigningConfigArn

        self._validate_package_type(lambda_function)
        return lambda_function

    def _add_event_invoke_managed_policy(self, dest_config, logical_id, condition, dest_arn):
        policy = {}
        if dest_config and dest_config.get("Type"):
            if dest_config.get("Type") == "SQS":
                policy = IAMRolePolicies.sqs_send_message_role_policy(dest_arn, logical_id)
            if dest_config.get("Type") == "SNS":
                policy = IAMRolePolicies.sns_publish_role_policy(dest_arn, logical_id)
            # Event Bridge and Lambda Arns are passthrough.
            if dest_config.get("Type") == "EventBridge":
                policy = IAMRolePolicies.event_bus_put_events_role_policy(dest_arn, logical_id)
            if dest_config.get("Type") == "Lambda":
                policy = IAMRolePolicies.lambda_invoke_function_role_policy(dest_arn, logical_id)
        return policy

    def _construct_role(self, managed_policy_map, event_invoke_policies):
        """Constructs a Lambda execution role based on this SAM function's Policies property.

        :returns: the generated IAM Role
        :rtype: model.iam.IAMRole
        """
        role_attributes = self.get_passthrough_resource_attributes()

        if self.AssumeRolePolicyDocument is not None:
            assume_role_policy_document = self.AssumeRolePolicyDocument
        else:
            assume_role_policy_document = IAMRolePolicies.lambda_assume_role_policy()

        managed_policy_arns = [ArnGenerator.generate_aws_managed_policy_arn("service-role/AWSLambdaBasicExecutionRole")]
        if self.Tracing:
            managed_policy_name = get_xray_managed_policy_name()
            managed_policy_arns.append(ArnGenerator.generate_aws_managed_policy_arn(managed_policy_name))
        if self.VpcConfig:
            managed_policy_arns.append(
                ArnGenerator.generate_aws_managed_policy_arn("service-role/AWSLambdaVPCAccessExecutionRole")
            )

        function_policies = ResourcePolicies(
            {"Policies": self.Policies},
            # No support for policy templates in the "core"
            policy_template_processor=None,
        )
        policy_documents = []

        if self.DeadLetterQueue:
            policy_documents.append(
                IAMRolePolicies.dead_letter_queue_policy(
                    self.dead_letter_queue_policy_actions[self.DeadLetterQueue["Type"]],
                    self.DeadLetterQueue["TargetArn"],
                )
            )

        if self.EventInvokeConfig:
            if event_invoke_policies is not None:
                policy_documents.extend(event_invoke_policies)

        execution_role = construct_role_for_resource(
            resource_logical_id=self.logical_id,
            attributes=role_attributes,
            managed_policy_map=managed_policy_map,
            assume_role_policy_document=assume_role_policy_document,
            resource_policies=function_policies,
            managed_policy_arns=managed_policy_arns,
            policy_documents=policy_documents,
            permissions_boundary=self.PermissionsBoundary,
            tags=self._construct_tag_list(self.Tags),
        )
        return execution_role

    def _validate_package_type(self, lambda_function):
        """
        Validates Function based on the existence of Package type
        """
        packagetype = lambda_function.PackageType or ZIP

        if packagetype not in [ZIP, IMAGE]:
            raise InvalidResourceException(
                lambda_function.logical_id,
                "PackageType needs to be `{zip}` or `{image}`".format(zip=ZIP, image=IMAGE),
            )

        def _validate_package_type_zip():
            if not all([lambda_function.Runtime, lambda_function.Handler]):
                raise InvalidResourceException(
                    lambda_function.logical_id,
                    "Runtime and Handler needs to be present when PackageType is of type `{zip}`".format(zip=ZIP),
                )

            if any([lambda_function.Code.get("ImageUri", False), lambda_function.ImageConfig]):
                raise InvalidResourceException(
                    lambda_function.logical_id,
                    "ImageUri or ImageConfig cannot be present when PackageType is of type `{zip}`".format(zip=ZIP),
                )

        def _validate_package_type_image():
            if any([lambda_function.Handler, lambda_function.Runtime, lambda_function.Layers]):
                raise InvalidResourceException(
                    lambda_function.logical_id,
                    "Runtime, Handler, Layers cannot be present when PackageType is of type `{image}`".format(
                        image=IMAGE
                    ),
                )
            if not lambda_function.Code.get("ImageUri"):
                raise InvalidResourceException(
                    lambda_function.logical_id,
                    "ImageUri needs to be present when PackageType is of type `{image}`".format(image=IMAGE),
                )

        _validate_per_package_type = {ZIP: _validate_package_type_zip, IMAGE: _validate_package_type_image}

        # Call appropriate validation function based on the package type.
        return _validate_per_package_type[packagetype]()

    def _validate_dlq(self):
        """Validates whether the DeadLetterQueue LogicalId is validation
        :raise: InvalidResourceException
        """
        # Validate required logical ids
        valid_dlq_types = str(list(self.dead_letter_queue_policy_actions.keys()))
        if not self.DeadLetterQueue.get("Type") or not self.DeadLetterQueue.get("TargetArn"):
            raise InvalidResourceException(
                self.logical_id,
                "'DeadLetterQueue' requires Type and TargetArn properties to be specified.".format(valid_dlq_types),
            )

        # Validate required Types
        if not self.DeadLetterQueue["Type"] in self.dead_letter_queue_policy_actions:
            raise InvalidResourceException(
                self.logical_id, "'DeadLetterQueue' requires Type of {}".format(valid_dlq_types)
            )

    def _event_resources_to_link(self, resources):
        event_resources = {}
        if self.Events:
            for logical_id, event_dict in self.Events.items():
                try:
                    event_source = self.event_resolver.resolve_resource_type(event_dict).from_dict(
                        self.logical_id + logical_id, event_dict, logical_id
                    )
                except (TypeError, AttributeError) as e:
                    raise InvalidEventException(logical_id, "{}".format(e))
                event_resources[logical_id] = event_source.resources_to_link(resources)
        return event_resources

    @staticmethod
    def order_events(event):
        """
        Helper method for sorting Function Events. Returns a key to use in sorting this event

        This is mainly used for HttpApi Events, where we need to evaluate the "$default" path (if any)
            before we evaluate any of the other paths ("/", etc), so we can make sure we don't create any
            redundant permissions. This sort places "$" before "/" or any alphanumeric characters.
        :param event: tuple of (logical_id, event_dictionary) that contains event information
        """
        logical_id, event_dict = event
        if not isinstance(event_dict, dict):
            return logical_id
        return event_dict.get("Properties", {}).get("Path", logical_id)

    def _generate_event_resources(
        self, lambda_function, execution_role, event_resources, intrinsics_resolver, lambda_alias=None
    ):
        """Generates and returns the resources associated with this function's events.

        :param model.lambda_.LambdaFunction lambda_function: generated Lambda function
        :param iam.IAMRole execution_role: generated Lambda execution role
        :param implicit_api: Global Implicit API resource where the implicit APIs get attached to, if necessary
        :param implicit_api_stage: Global implicit API stage resource where implicit APIs get attached to, if necessary
        :param event_resources: All the event sources associated with this Lambda function
        :param model.lambda_.LambdaAlias lambda_alias: Optional Lambda Alias resource if we want to connect the
            event sources to this alias

        :returns: a list containing the function's event resources
        :rtype: list
        """
        resources = []
        if self.Events:
            for logical_id, event_dict in sorted(self.Events.items(), key=SamFunction.order_events):
                try:
                    eventsource = self.event_resolver.resolve_resource_type(event_dict).from_dict(
                        lambda_function.logical_id + logical_id, event_dict, logical_id
                    )
                except TypeError as e:
                    raise InvalidEventException(logical_id, "{}".format(e))

                kwargs = {
                    # When Alias is provided, connect all event sources to the alias and *not* the function
                    "function": lambda_alias or lambda_function,
                    "role": execution_role,
                    "intrinsics_resolver": intrinsics_resolver,
                }

                for name, resource in event_resources[logical_id].items():
                    kwargs[name] = resource
                resources += eventsource.to_cloudformation(**kwargs)

        return resources

    def _construct_code_dict(self):
        """Constructs Lambda Code Dictionary based on the accepted SAM artifact properties such
        as `InlineCode`, `CodeUri` and `ImageUri` and also raises errors if more than one of them is
        defined. `PackageType` determines which artifacts are considered.

        :raises InvalidResourceException when conditions on the SAM artifact properties are not met.
        """
        # list of accepted artifacts
        packagetype = self.PackageType or ZIP
        artifacts = {}

        if packagetype == ZIP:
            artifacts = {"InlineCode": self.InlineCode, "CodeUri": self.CodeUri}
        elif packagetype == IMAGE:
            artifacts = {"ImageUri": self.ImageUri}

        if packagetype not in [ZIP, IMAGE]:
            raise InvalidResourceException(self.logical_id, "invalid 'PackageType' : {}".format(packagetype))

        # Inline function for transformation of inline code.
        # It accepts arbitrary argumemnts, because the arguments do not matter for the result.
        def _construct_inline_code(*args, **kwargs):
            return {"ZipFile": self.InlineCode}

        # dispatch mechanism per artifact on how it needs to be transformed.
        artifact_dispatch = {
            "InlineCode": _construct_inline_code,
            "CodeUri": construct_s3_location_object,
            "ImageUri": construct_image_code_object,
        }

        filtered_artifacts = dict(filter(lambda x: x[1] != None, artifacts.items()))
        # There are more than one allowed artifact types present, raise an Error.
        # There are no valid artifact types present, also raise an Error.
        if len(filtered_artifacts) > 1 or len(filtered_artifacts) == 0:
            if packagetype == ZIP and len(filtered_artifacts) == 0:
                raise InvalidResourceException(self.logical_id, "Only one of 'InlineCode' or 'CodeUri' can be set.")
            elif packagetype == IMAGE:
                raise InvalidResourceException(self.logical_id, "'ImageUri' must be set.")

        filtered_keys = [key for key in filtered_artifacts.keys()]
        # NOTE(sriram-mv): This precedence order is important. It is protect against python2 vs python3
        # dictionary ordering when getting the key values with .keys() on a dictionary.
        # Do not change this precedence order.
        if "InlineCode" in filtered_keys:
            filtered_key = "InlineCode"
        elif "CodeUri" in filtered_keys:
            filtered_key = "CodeUri"
        elif "ImageUri" in filtered_keys:
            filtered_key = "ImageUri"
        else:
            raise InvalidResourceException(self.logical_id, "Either 'InlineCode' or 'CodeUri' must be set.")
        dispatch_function = artifact_dispatch[filtered_key]
        return dispatch_function(artifacts[filtered_key], self.logical_id, filtered_key)

    def _construct_version(self, function, intrinsics_resolver, code_sha256=None):
        """Constructs a Lambda Version resource that will be auto-published when CodeUri of the function changes.
        Old versions will not be deleted without a direct reference from the CloudFormation template.

        :param model.lambda_.LambdaFunction function: Lambda function object that is being connected to a version
        :param model.intrinsics.resolver.IntrinsicsResolver intrinsics_resolver: Class that can help resolve
            references to parameters present in CodeUri. It is a common usecase to set S3Key of Code to be a
            template parameter. Need to resolve the values otherwise we will never detect a change in Code dict
        :param str code_sha256: User predefined hash of the Lambda function code
        :return: Lambda function Version resource
        """
        code_dict = function.Code
        if not code_dict:
            raise ValueError("Lambda function code must be a valid non-empty dictionary")

        if not intrinsics_resolver:
            raise ValueError("intrinsics_resolver is required for versions creation")

        # Resolve references to template parameters before creating hash. This will *not* resolve all intrinsics
        # because we cannot resolve runtime values like Arn of a resource. For purposes of detecting changes, this
        # is good enough. Here is why:
        #
        # When using intrinsic functions there are two cases when has must change:
        #   - Value of the template parameter changes
        #   - (or) LogicalId of a referenced resource changes ie. !GetAtt NewResource.Arn
        #
        # Later case will already change the hash because some value in the Code dictionary changes. We handle the
        # first case by resolving references to template parameters. It is okay even if these references are
        # present inside another intrinsic such as !Join. The resolver will replace the reference with the parameter's
        # value and keep all other parts of !Join identical. This will still trigger a change in the hash.
        code_dict = intrinsics_resolver.resolve_parameter_refs(code_dict)

        # Construct the LogicalID of Lambda version by appending 10 characters of SHA of CodeUri. This is necessary
        # to trigger creation of a new version every time code location changes. Since logicalId changes, CloudFormation
        # will drop the old version and create a new one for us. We set a DeletionPolicy on the version resource to
        # prevent CloudFormation from actually deleting the underlying version resource
        #
        # SHA Collisions: For purposes of triggering a new update, we are concerned about just the difference previous
        #                 and next hashes. The chances that two subsequent hashes collide is fairly low.
        prefix = "{id}Version".format(id=self.logical_id)
        logical_dict = {}
        try:
            logical_dict = code_dict.copy()
        except (AttributeError, UnboundLocalError):
            pass
        else:
            if function.Environment:
                logical_dict.update(function.Environment)
            if function.MemorySize:
                logical_dict.update({"MemorySize": function.MemorySize})
        logical_id = logical_id_generator.LogicalIdGenerator(prefix, logical_dict, code_sha256).gen()

        attributes = self.get_passthrough_resource_attributes()
        if attributes is None:
            attributes = {}
        if "DeletionPolicy" not in attributes:
            attributes["DeletionPolicy"] = "Retain"

        lambda_version = LambdaVersion(logical_id=logical_id, attributes=attributes)
        lambda_version.FunctionName = function.get_runtime_attr("name")
        lambda_version.Description = self.VersionDescription

        return lambda_version

    def _construct_alias(self, name, function, version):
        """Constructs a Lambda Alias for the given function and pointing to the given version

        :param string name: Name of the alias
        :param model.lambda_.LambdaFunction function: Lambda function object to associate the alias with
        :param model.lambda_.LambdaVersion version: Lambda version object to associate the alias with
        :return: Lambda alias object
        :rtype model.lambda_.LambdaAlias
        """

        if not name:
            raise InvalidResourceException(self.logical_id, "Alias name is required to create an alias")

        logical_id = "{id}Alias{suffix}".format(id=function.logical_id, suffix=name)
        alias = LambdaAlias(logical_id=logical_id, attributes=self.get_passthrough_resource_attributes())
        alias.Name = name
        alias.FunctionName = function.get_runtime_attr("name")
        alias.FunctionVersion = version.get_runtime_attr("version")
        if self.ProvisionedConcurrencyConfig:
            alias.ProvisionedConcurrencyConfig = self.ProvisionedConcurrencyConfig

        return alias

    def _validate_deployment_preference_and_add_update_policy(
        self, deployment_preference_collection, lambda_alias, intrinsics_resolver, mappings_resolver
    ):
        if "Enabled" in self.DeploymentPreference:
            # resolve intrinsics and mappings for Type
            enabled = self.DeploymentPreference["Enabled"]
            enabled = intrinsics_resolver.resolve_parameter_refs(enabled)
            enabled = mappings_resolver.resolve_parameter_refs(enabled)
            self.DeploymentPreference["Enabled"] = enabled

        if "Type" in self.DeploymentPreference:
            # resolve intrinsics and mappings for Type
            preference_type = self.DeploymentPreference["Type"]
            preference_type = intrinsics_resolver.resolve_parameter_refs(preference_type)
            preference_type = mappings_resolver.resolve_parameter_refs(preference_type)
            self.DeploymentPreference["Type"] = preference_type

        if deployment_preference_collection is None:
            raise ValueError("deployment_preference_collection required for parsing the deployment preference")

        deployment_preference_collection.add(self.logical_id, self.DeploymentPreference)

        if deployment_preference_collection.get(self.logical_id).enabled:
            if self.AutoPublishAlias is None:
                raise InvalidResourceException(
                    self.logical_id, "'DeploymentPreference' requires AutoPublishAlias property to be specified."
                )
            if lambda_alias is None:
                raise ValueError("lambda_alias expected for updating it with the appropriate update policy")

            lambda_alias.set_resource_attribute(
                "UpdatePolicy", deployment_preference_collection.update_policy(self.logical_id).to_dict()
            )


class SamCanary(SamResourceMacro):
    """SAM canary macro."""

    resource_type = "AWS::Serverless::Canary"
    property_types = {
        "FunctionName": PropertyType(False, one_of(is_str(), is_type(dict))),
        "Handler": PropertyType(True, is_str()),
        "Runtime": PropertyType(True, is_str()),
        "CodeUri": PropertyType(False, one_of(is_str(), is_type(dict))),
        "InlineCode": PropertyType(False, one_of(is_str(), is_type(dict))),
        "MemorySize": PropertyType(False, is_type(int)),
        "Tags": PropertyType(False, is_type(dict)),
        # Easier to pass through as AWS::Synthetics::Canary only accepts a boolean
        "ActiveTracing": PropertyType(False, is_type(bool)),
        "AssumeRolePolicyDocument": PropertyType(False, is_type(dict)),
        "Timeout": PropertyType(False, is_type(int)),
        "Role": PropertyType(False, is_str()),
        "Schedule": PropertyType(True, is_type(dict)),
        "StartCanaryAfterCreation": PropertyType(True, is_type(bool)),
        "ArtifactS3Location": PropertyType(False, one_of(is_type(dict), is_str())),
        "FailureRetentionPeriod": PropertyType(False, is_type(int)),
        "SuccessRetentionPeriod": PropertyType(False, is_type(int)),
        "VpcConfig": PropertyType(False, is_type(dict)),
        "Environment": PropertyType(False, dict_of(is_str(), is_type(dict))),
        "Policies": PropertyType(False, one_of(is_str(), is_type(dict), list_of(one_of(is_str(), is_type(dict))))),
        "CanaryMetricAlarms": PropertyType(False, list_of(is_type(dict))),
    }

    def to_cloudformation(self, **kwargs):
        """Returns the Synthetics Canary to which this SAM Canary corresponds.

        :param dict kwargs: already-converted resources that may need to be modified when converting this \
        macro to pure CloudFormation
        :returns: a list of vanilla CloudFormation Resources, to which this Serverless Canary expands
        :rtype: list
        """
        resources = []
        managed_policy_map = kwargs.get("managed_policy_map", {})
        synthetics_canary = self._construct_synthetics_canary()
        resources.append(synthetics_canary)

        # A S3 Bucket resource will be added to the transformed template if the user doesn't provide an artifact
        # bucket to store canary results

        artifact_bucket_name = ""
        if not self.ArtifactS3Location:
            s3bucket = self._construct_artifact_bucket()
            resources.append(s3bucket)
            synthetics_canary.ArtifactS3Location = {"Fn::Join": ["", ["s3://", {"Ref": s3bucket.logical_id}]]}
            artifact_bucket_name = {"Ref": s3bucket.logical_id}

        if not self.Role:
            role = self._construct_role(artifact_bucket_name, managed_policy_map)
            resources.append(role)
            synthetics_canary.ExecutionRoleArn = role.get_runtime_attr("arn")

        if self.CanaryMetricAlarms:
            self._validate_cloudwatch_alarms()
            for alarm_dict in self.CanaryMetricAlarms:
                resources.append(self._construct_cloudwatch_alarm(alarm_dict))

        return resources

    def _validate_cloudwatch_alarms(self):
        """Validates the CanaryMetricAlarms property in Serverless Canary

        The property should follow the following structure

        CanaryMetricAlarms:
            - AlarmName:
                MetricName (required): one of the metrics in VALID_CANARY_METRICS
                Threshold (optional): any value of type double
                ComparisonOperator (optional): any of the valid values (https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-cw-alarm.html#cfn-cloudwatch-alarms-comparisonoperator)
                Period (optional): Integer that is 10, 30, 60, or any multiple of 60

        Note: Alarm names are used as logical ids for their respective CloudWatchAlarm property so if user has multiple
        alarms there should be no duplicate names as we don't want the alarms to override each other without the user's
        knowledge

        :raise: InvalidResourceException
        """
        # keeps list of alarm names to make sure there are no duplicates
        list_of_alarm_names = []
        for alarm_dict in self.CanaryMetricAlarms:

            # Throw an error if there is more than one alarm in the array index, like for example
            # CanaryMetricAlarms:
            #     - Alarm1:
            #         MetricName: SuccessPercent
            #       Alarm2:
            #         MetricName: SuccessPercent
            #         Threshold: 90
            #     - Alarm3:
            #         MetricName: Failed
            # throws an error for Alarm2 since its Alarm1 is already defined in that dict
            if len(alarm_dict) != 1:
                raise InvalidResourceException(self.logical_id, "Must have one alarm per array index")

            # get the alarm name and the properties the user defined for the alarm
            alarm_name = next(iter(alarm_dict))
            alarm_item = alarm_dict[alarm_name]

            # MetricName property is required
            if alarm_item is None or "MetricName" not in alarm_item:
                raise InvalidResourceException(
                    self.logical_id,
                    "CloudWatch alarm '{key}' is missing required property 'MetricName'.".format(key=alarm_name),
                )

            metric_name = alarm_item["MetricName"]

            # MetricName must be one of the values in VALID_CANARY_METRICS
            if metric_name not in VALID_CANARY_METRICS:
                raise InvalidResourceException(
                    self.logical_id,
                    "MetricName needs to be one of {}".format(VALID_CANARY_METRICS),
                )

            # make sure all the alarm names are unique
            if alarm_name in list_of_alarm_names:
                raise InvalidResourceException(self.logical_id, "Duplicate CloudWatch alarm names")
            else:
                list_of_alarm_names.append(alarm_name)

    def _construct_cloudwatch_alarm(self, alarm_dict):
        """Constructs an CloudWatch::Alarm resource if the user specifies the CloudWatchAlarm property in Serverless Canary

        :param dict alarm_dict: Alarm name and properties as provided by the customer
        :returns: the generated CloudWatch Alarm
        :rtype: model.cloudwatch.CloudWatchAlarm
        """

        # gets alarm name and the properties defined by user
        alarm_name = next(iter(alarm_dict))
        alarm_item = alarm_dict[alarm_name]

        cloudwatch_alarm = CloudWatchAlarm(
            logical_id=alarm_name,
            depends_on=self.depends_on,
            attributes=self.get_passthrough_resource_attributes(),
        )

        # default settings for the CloudWatch alarms
        # the settings are identical to the Alarms that are made by Synthetics Canary using their dashboard
        cloudwatch_alarm.MetricName = alarm_item["MetricName"]
        cloudwatch_alarm.Namespace = "CloudWatchSynthetics"
        cloudwatch_alarm.EvaluationPeriods = 1
        cloudwatch_alarm.Statistic = "Sum"
        cloudwatch_alarm.TreatMissingData = "notBreaching"
        # connects the alarm to the metric produced by the Synthetics canary from this Serverless resource
        cloudwatch_alarm.Dimensions = [{"Name": "CanaryName", "Value": {"Ref": self.logical_id}}]

        # set the values if user provides them, if not set them to default value based on the MetricName
        cloudwatch_alarm.ComparisonOperator = alarm_item.get(
            "ComparisonOperator", DEFAULT_METRIC_VALUES[alarm_item["MetricName"]]["ComparisonOperator"]
        )

        cloudwatch_alarm.Threshold = float(
            alarm_item.get("Threshold", DEFAULT_METRIC_VALUES[alarm_item["MetricName"]]["Threshold"])
        )

        cloudwatch_alarm.Period = alarm_item.get("Period", DEFAULT_METRIC_VALUES[alarm_item["MetricName"]]["Period"])

        return cloudwatch_alarm

    def _construct_role(self, artifact_bucket_name, managed_policy_map):
        """Constructs an IAM:Role resource only if user doesn't specify Role property in Serverless Canary

        -   If the ArtifactS3Location property isn't specified then the the policies to execute the Canary and handle
            the resulting data will be added
        -   If the Tracing property is enabled then the XRay policy based on the user's region will be added
        -   If the VpcConfig property is specified then the policy to execute VPC will be added
        -   If the Policies property is specified then the that will be appended to the IAM::Role's Policies property

        :returns: the generated IAM Role
        :rtype: model.iam.IAMRole
        """
        role_attributes = self.get_passthrough_resource_attributes()
        if self.AssumeRolePolicyDocument:
            assume_role_policy_document = self.AssumeRolePolicyDocument
        else:
            assume_role_policy_document = IAMRolePolicies.lambda_assume_role_policy()

        # add AWS managed policies if user has enabled VpcConfig or Tracing
        managed_policy_arns = []
        if self.VpcConfig:
            managed_policy_arns.append(
                ArnGenerator.generate_aws_managed_policy_arn("service-role/AWSLambdaVPCAccessExecutionRole")
            )
        if self.ActiveTracing is True:
            managed_policy_name = get_xray_managed_policy_name()
            managed_policy_arns.append(ArnGenerator.generate_aws_managed_policy_arn(managed_policy_name))

        # if user has defined Policies property, those policies will be appended to this role
        function_policies = ResourcePolicies(
            {"Policies": self.Policies},
            # No support for policy templates in the "core"
            policy_template_processor=None,
        )

        # The policy to execute the canary is only added to the role if the user hasn't defined ArtifactS3Location
        # this emulates CloudWatch Synthetics Canary dashboard's behavior
        policy_documents = []
        if self.ArtifactS3Location is None:
            policy_documents.extend(
                (
                    IAMRolePolicies.canary_put_artifacts_in_s3_policy(
                        logical_id=self.logical_id, result_bucket=artifact_bucket_name
                    ),
                    IAMRolePolicies.canary_put_logs_policy(logical_id=self.logical_id),
                    IAMRolePolicies.canary_put_metric_data_policy(logical_id=self.logical_id),
                )
            )

        execution_role = construct_role_for_resource(
            resource_logical_id=self.logical_id,
            attributes=role_attributes,
            managed_policy_map=managed_policy_map,
            assume_role_policy_document=assume_role_policy_document,
            resource_policies=function_policies,
            managed_policy_arns=managed_policy_arns,
            policy_documents=policy_documents,
            permissions_boundary=None,
            tags=self._construct_tag_list(self.Tags),
        )
        return execution_role

    def _construct_artifact_bucket(self):
        """Constructs a S3Bucket resource to store canary artifacts.

        :returns: the generated S3Bucket
        :rtype: model.s3.S3Bucket
        """

        # Construct the LogicalId of S3Bucket by appending ArtifactBucket to the Canary LogicalId. Once deployed, the
        # bucket name will be automatically generated by Cloudformation.
        # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-name.html

        logical_id = self.logical_id + "ArtifactBucket"

        # Set the DeletionPolicy of the S3 resource to Retain to prevent CloudFormation from trying to delete the
        # bucket when its not empty. This is necessary because if a user creates and runs a serverless canary without
        # an artifact bucket, then tries to delete/replace that resource, CloudFormation will try to delete the
        # artifact bucket made by SAM which will throw an error since its not empty. Retaining the bucket will bypass
        # this error.

        passthrough_attributes = self.get_passthrough_resource_attributes()
        if passthrough_attributes is None:
            passthrough_attributes = {}
        passthrough_attributes["DeletionPolicy"] = "Retain"

        s3bucket = S3Bucket(
            logical_id=logical_id,
            depends_on=self.depends_on,
            attributes=passthrough_attributes,
        )
        s3bucket.BucketEncryption = {
            "ServerSideEncryptionConfiguration": [{"ServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
        }
        s3bucket.Tags = self._construct_tag_list(self.Tags)

        return s3bucket

    def _construct_synthetics_canary(self):

        """Constructs a AWS::Synthetics::Canary resource."""
        canary = SyntheticsCanary(
            self.logical_id, depends_on=self.depends_on, attributes=self.get_passthrough_resource_attributes()
        )
        canary.ArtifactS3Location = self.ArtifactS3Location
        canary.Code = self._construct_code_dict
        canary.ExecutionRoleArn = self.Role
        canary.FailureRetentionPeriod = self.FailureRetentionPeriod
        # constructs default name if FunctionName isn't provided because Synthetics Canary resource requires a Name,
        # also requires it be lower case
        canary.Name = self.FunctionName if self.FunctionName else self._construct_canary_name()
        canary.RuntimeVersion = self.Runtime
        canary.Schedule = self.Schedule
        canary.StartCanaryAfterCreation = self.StartCanaryAfterCreation
        canary.SuccessRetentionPeriod = self.SuccessRetentionPeriod
        canary.Tags = self._construct_tag_list(self.Tags)
        canary.VPCConfig = self.VpcConfig

        if self.ActiveTracing or self.Environment or self.MemorySize or self.Timeout:
            canary.RunConfig = self._construct_run_config()
        return canary

    def _construct_canary_name(self):
        """
        Need to construct canary name since the Name property is required in AWS::Synthetics::Canary and CloudFormation
        doesn't automatically generate one upon deployment

        Synthetics Canary name is limited to 21 characters
        https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-synthetics-canary.html#cfn-synthetics-canary-name

        len(prefix) + MAX_CANARY_LOGICAL_ID_LENGTH + MAX_CANARY_UNIQUE_ID_LENGTH + 1 (extra '-' char added) must be less
        than or equal to 21
        """

        logical_id_lowered = self.logical_id.lower()[:MAX_CANARY_LOGICAL_ID_LENGTH] + "-"
        suffix = uuid.uuid4().hex[:MAX_CANARY_UNIQUE_ID_LENGTH]

        return CANARY_NAME_PREFIX + logical_id_lowered + suffix

    @staticmethod
    def _extract_not_none_properties(d):
        """
        Filters out and returns not None properties
        """
        return {k: v for k, v in d if v is not None}

    def _construct_run_config(self):
        """
        If the user specifies any of Tracing, MemorySize, Timeout or Environment then the RunConfig resource in the
        transformed AWS::Synthetics::Canary needs to be added. Note, for Environment property the syntax in
        AWS::Serverless::Canary is

        Environment:
            Variables:
                Var1: Var2

        while in AWS::Synthetics::Canary its

        EnvironmentVariables:
            Var1: Var2

        so it needs to be transformed accordingly
        """
        runconfig = {
            "ActiveTracing": self.ActiveTracing,
            "MemoryInMB": self.MemorySize,
            "TimeoutInSeconds": self.Timeout,
        }
        if self.Environment:
            runconfig["EnvironmentVariables"] = self.Environment["Variables"]

        return self._extract_not_none_properties(runconfig.items())

    @property
    def _construct_code_dict(self):
        """Constructs Synthetics Canary Code Dictionary based on the accepted SAM artifact properties such
        as `InlineCode` and `CodeUri`

        :raises InvalidResourceException when conditions on the SAM artifact properties are not met.
        """
        # accepted artifacts
        artifacts = {"InlineCode": self.InlineCode, "CodeUri": self.CodeUri}

        filtered_artifacts = self._extract_not_none_properties(artifacts.items())
        filtered_artifact_keys = list(filtered_artifacts.keys())

        # Note: To emulate the same behavior as SAM Function, if user includes both InlineCode and CodeUri,
        # InlineCode will take priority
        if "InlineCode" in filtered_artifact_keys:
            # Inline function for transformation of inline code.
            return {"Handler": self.Handler, "Script": self.InlineCode}
        elif "CodeUri" in filtered_artifact_keys:
            # extracts Bucket and Key values, adds Handler and extracted values to Code object
            code = construct_s3_location_object(self.CodeUri, self.logical_id, "CodeUri")
            code["Handler"] = self.Handler
            return code
        else:
            raise InvalidResourceException(self.logical_id, "Either 'InlineCode' or 'CodeUri' must be set.")


class SamApi(SamResourceMacro):
    """SAM rest API macro."""

    resource_type = "AWS::Serverless::Api"
    property_types = {
        # Internal property set only by Implicit API plugin. If set to True, the API Event Source code will inject
        # Lambda Integration URI to the Swagger. To preserve backwards compatibility, this must be set only for
        # Implicit APIs. For Explicit APIs, customer is expected to set integration URI themselves.
        # In the future, we might rename and expose this property to customers so they can have SAM manage Explicit APIs
        # Swagger.
        "__MANAGE_SWAGGER": PropertyType(False, is_type(bool)),
        "Name": PropertyType(False, one_of(is_str(), is_type(dict))),
        "StageName": PropertyType(True, one_of(is_str(), is_type(dict))),
        "Tags": PropertyType(False, is_type(dict)),
        "DefinitionBody": PropertyType(False, is_type(dict)),
        "DefinitionUri": PropertyType(False, one_of(is_str(), is_type(dict))),
        "CacheClusterEnabled": PropertyType(False, is_type(bool)),
        "CacheClusterSize": PropertyType(False, is_str()),
        "Variables": PropertyType(False, is_type(dict)),
        "EndpointConfiguration": PropertyType(False, one_of(is_str(), is_type(dict))),
        "MethodSettings": PropertyType(False, is_type(list)),
        "BinaryMediaTypes": PropertyType(False, is_type(list)),
        "MinimumCompressionSize": PropertyType(False, is_type(int)),
        "Cors": PropertyType(False, one_of(is_str(), is_type(dict))),
        "Auth": PropertyType(False, is_type(dict)),
        "GatewayResponses": PropertyType(False, is_type(dict)),
        "AccessLogSetting": PropertyType(False, is_type(dict)),
        "CanarySetting": PropertyType(False, is_type(dict)),
        "TracingEnabled": PropertyType(False, is_type(bool)),
        "OpenApiVersion": PropertyType(False, is_str()),
        "Models": PropertyType(False, is_type(dict)),
        "Domain": PropertyType(False, is_type(dict)),
        "Description": PropertyType(False, is_str()),
        "Mode": PropertyType(False, is_str()),
    }

    referable_properties = {
        "Stage": ApiGatewayStage.resource_type,
        "Deployment": ApiGatewayDeployment.resource_type,
        "DomainName": ApiGatewayDomainName.resource_type,
        "UsagePlan": ApiGatewayUsagePlan.resource_type,
        "UsagePlanKey": ApiGatewayUsagePlanKey.resource_type,
        "ApiKey": ApiGatewayApiKey.resource_type,
    }

    def to_cloudformation(self, **kwargs):
        """Returns the API Gateway RestApi, Deployment, and Stage to which this SAM Api corresponds.

        :param dict kwargs: already-converted resources that may need to be modified when converting this \
        macro to pure CloudFormation
        :returns: a list of vanilla CloudFormation Resources, to which this Function expands
        :rtype: list
        """
        resources = []

        intrinsics_resolver = kwargs["intrinsics_resolver"]
        self.BinaryMediaTypes = intrinsics_resolver.resolve_parameter_refs(self.BinaryMediaTypes)
        self.Domain = intrinsics_resolver.resolve_parameter_refs(self.Domain)
        self.Auth = intrinsics_resolver.resolve_parameter_refs(self.Auth)
        redeploy_restapi_parameters = kwargs.get("redeploy_restapi_parameters")
        shared_api_usage_plan = kwargs.get("shared_api_usage_plan")
        template_conditions = kwargs.get("conditions")

        api_generator = ApiGenerator(
            self.logical_id,
            self.CacheClusterEnabled,
            self.CacheClusterSize,
            self.Variables,
            self.depends_on,
            self.DefinitionBody,
            self.DefinitionUri,
            self.Name,
            self.StageName,
            shared_api_usage_plan,
            template_conditions,
            tags=self.Tags,
            endpoint_configuration=self.EndpointConfiguration,
            method_settings=self.MethodSettings,
            binary_media=self.BinaryMediaTypes,
            minimum_compression_size=self.MinimumCompressionSize,
            cors=self.Cors,
            auth=self.Auth,
            gateway_responses=self.GatewayResponses,
            access_log_setting=self.AccessLogSetting,
            canary_setting=self.CanarySetting,
            tracing_enabled=self.TracingEnabled,
            resource_attributes=self.resource_attributes,
            passthrough_resource_attributes=self.get_passthrough_resource_attributes(),
            open_api_version=self.OpenApiVersion,
            models=self.Models,
            domain=self.Domain,
            description=self.Description,
            mode=self.Mode,
        )

        (
            rest_api,
            deployment,
            stage,
            permissions,
            domain,
            basepath_mapping,
            route53,
            usage_plan_resources,
        ) = api_generator.to_cloudformation(redeploy_restapi_parameters)

        resources.extend([rest_api, deployment, stage])
        resources.extend(permissions)
        if domain:
            resources.extend([domain])
        if basepath_mapping:
            resources.extend(basepath_mapping)
        if route53:
            resources.extend([route53])
        # contains usage plan, api key and usageplan key resources
        if usage_plan_resources:
            resources.extend(usage_plan_resources)
        return resources


class SamHttpApi(SamResourceMacro):
    """SAM rest API macro."""

    resource_type = "AWS::Serverless::HttpApi"
    property_types = {
        # Internal property set only by Implicit HTTP API plugin. If set to True, the API Event Source code will
        # inject Lambda Integration URI to the OpenAPI. To preserve backwards compatibility, this must be set only for
        # Implicit APIs. For Explicit APIs, this is managed by the DefaultDefinitionBody Plugin.
        # In the future, we might rename and expose this property to customers so they can have SAM manage Explicit APIs
        # Swagger.
        "__MANAGE_SWAGGER": PropertyType(False, is_type(bool)),
        "StageName": PropertyType(False, one_of(is_str(), is_type(dict))),
        "Tags": PropertyType(False, is_type(dict)),
        "DefinitionBody": PropertyType(False, is_type(dict)),
        "DefinitionUri": PropertyType(False, one_of(is_str(), is_type(dict))),
        "StageVariables": PropertyType(False, is_type(dict)),
        "CorsConfiguration": PropertyType(False, one_of(is_type(bool), is_type(dict))),
        "AccessLogSettings": PropertyType(False, is_type(dict)),
        "DefaultRouteSettings": PropertyType(False, is_type(dict)),
        "Auth": PropertyType(False, is_type(dict)),
        "RouteSettings": PropertyType(False, is_type(dict)),
        "Domain": PropertyType(False, is_type(dict)),
        "FailOnWarnings": PropertyType(False, is_type(bool)),
        "Description": PropertyType(False, is_str()),
        "DisableExecuteApiEndpoint": PropertyType(False, is_type(bool)),
    }

    referable_properties = {
        "Stage": ApiGatewayV2Stage.resource_type,
        "DomainName": ApiGatewayV2DomainName.resource_type,
    }

    def to_cloudformation(self, **kwargs):
        """Returns the API GatewayV2 Api, Deployment, and Stage to which this SAM Api corresponds.

        :param dict kwargs: already-converted resources that may need to be modified when converting this \
        macro to pure CloudFormation
        :returns: a list of vanilla CloudFormation Resources, to which this Function expands
        :rtype: list
        """
        resources = []
        intrinsics_resolver = kwargs["intrinsics_resolver"]
        self.CorsConfiguration = intrinsics_resolver.resolve_parameter_refs(self.CorsConfiguration)

        intrinsics_resolver = kwargs["intrinsics_resolver"]
        self.Domain = intrinsics_resolver.resolve_parameter_refs(self.Domain)

        api_generator = HttpApiGenerator(
            self.logical_id,
            self.StageVariables,
            self.depends_on,
            self.DefinitionBody,
            self.DefinitionUri,
            self.StageName,
            tags=self.Tags,
            auth=self.Auth,
            cors_configuration=self.CorsConfiguration,
            access_log_settings=self.AccessLogSettings,
            route_settings=self.RouteSettings,
            default_route_settings=self.DefaultRouteSettings,
            resource_attributes=self.resource_attributes,
            passthrough_resource_attributes=self.get_passthrough_resource_attributes(),
            domain=self.Domain,
            fail_on_warnings=self.FailOnWarnings,
            description=self.Description,
            disable_execute_api_endpoint=self.DisableExecuteApiEndpoint,
        )

        (
            http_api,
            stage,
            domain,
            basepath_mapping,
            route53,
        ) = api_generator.to_cloudformation()

        resources.append(http_api)
        if domain:
            resources.append(domain)
        if basepath_mapping:
            resources.extend(basepath_mapping)
        if route53:
            resources.append(route53)

        # Stage is now optional. Only add it if one is created.
        if stage:
            resources.append(stage)

        return resources


class SamSimpleTable(SamResourceMacro):
    """SAM simple table macro."""

    resource_type = "AWS::Serverless::SimpleTable"
    property_types = {
        "PrimaryKey": PropertyType(False, dict_of(is_str(), is_str())),
        "ProvisionedThroughput": PropertyType(False, dict_of(is_str(), one_of(is_type(int), is_type(dict)))),
        "TableName": PropertyType(False, one_of(is_str(), is_type(dict))),
        "Tags": PropertyType(False, is_type(dict)),
        "SSESpecification": PropertyType(False, is_type(dict)),
    }
    attribute_type_conversions = {"String": "S", "Number": "N", "Binary": "B"}

    def to_cloudformation(self, **kwargs):
        dynamodb_resources = self._construct_dynamodb_table()

        return [dynamodb_resources]

    def _construct_dynamodb_table(self):
        dynamodb_table = DynamoDBTable(self.logical_id, depends_on=self.depends_on, attributes=self.resource_attributes)

        if self.PrimaryKey:
            if "Name" not in self.PrimaryKey or "Type" not in self.PrimaryKey:
                raise InvalidResourceException(
                    self.logical_id, "'PrimaryKey' is missing required Property 'Name' or 'Type'."
                )
            primary_key = {
                "AttributeName": self.PrimaryKey["Name"],
                "AttributeType": self._convert_attribute_type(self.PrimaryKey["Type"]),
            }

        else:
            primary_key = {"AttributeName": "id", "AttributeType": "S"}

        dynamodb_table.AttributeDefinitions = [primary_key]
        dynamodb_table.KeySchema = [{"AttributeName": primary_key["AttributeName"], "KeyType": "HASH"}]

        if self.ProvisionedThroughput:
            dynamodb_table.ProvisionedThroughput = self.ProvisionedThroughput
        else:
            dynamodb_table.BillingMode = "PAY_PER_REQUEST"

        if self.SSESpecification:
            dynamodb_table.SSESpecification = self.SSESpecification

        if self.TableName:
            dynamodb_table.TableName = self.TableName

        if bool(self.Tags):
            dynamodb_table.Tags = get_tag_list(self.Tags)

        return dynamodb_table

    def _convert_attribute_type(self, attribute_type):
        if attribute_type in self.attribute_type_conversions:
            return self.attribute_type_conversions[attribute_type]
        raise InvalidResourceException(self.logical_id, "Invalid 'Type' \"{actual}\".".format(actual=attribute_type))


class SamApplication(SamResourceMacro):
    """SAM application macro."""

    APPLICATION_ID_KEY = "ApplicationId"
    SEMANTIC_VERSION_KEY = "SemanticVersion"

    resource_type = "AWS::Serverless::Application"

    # The plugin will always insert the TemplateUrl parameter
    property_types = {
        "Location": PropertyType(True, one_of(is_str(), is_type(dict))),
        "TemplateUrl": PropertyType(False, is_str()),
        "Parameters": PropertyType(False, is_type(dict)),
        "NotificationARNs": PropertyType(False, list_of(one_of(is_str(), is_type(dict)))),
        "Tags": PropertyType(False, is_type(dict)),
        "TimeoutInMinutes": PropertyType(False, is_type(int)),
    }

    def to_cloudformation(self, **kwargs):
        """Returns the stack with the proper parameters for this application"""
        nested_stack = self._construct_nested_stack()
        return [nested_stack]

    def _construct_nested_stack(self):
        """Constructs a AWS::CloudFormation::Stack resource"""
        nested_stack = NestedStack(
            self.logical_id, depends_on=self.depends_on, attributes=self.get_passthrough_resource_attributes()
        )
        nested_stack.Parameters = self.Parameters
        nested_stack.NotificationARNs = self.NotificationARNs
        application_tags = self._get_application_tags()
        nested_stack.Tags = self._construct_tag_list(self.Tags, application_tags)
        nested_stack.TimeoutInMinutes = self.TimeoutInMinutes
        nested_stack.TemplateURL = self.TemplateUrl if self.TemplateUrl else ""

        return nested_stack

    def _get_application_tags(self):
        """Adds tags to the stack if this resource is using the serverless app repo"""
        application_tags = {}
        if isinstance(self.Location, dict):
            if self.APPLICATION_ID_KEY in self.Location.keys() and self.Location[self.APPLICATION_ID_KEY] is not None:
                application_tags[self._SAR_APP_KEY] = self.Location[self.APPLICATION_ID_KEY]
            if (
                self.SEMANTIC_VERSION_KEY in self.Location.keys()
                and self.Location[self.SEMANTIC_VERSION_KEY] is not None
            ):
                application_tags[self._SAR_SEMVER_KEY] = self.Location[self.SEMANTIC_VERSION_KEY]
        return application_tags


class SamLayerVersion(SamResourceMacro):
    """SAM Layer macro"""

    resource_type = "AWS::Serverless::LayerVersion"
    property_types = {
        "LayerName": PropertyType(False, one_of(is_str(), is_type(dict))),
        "Description": PropertyType(False, is_str()),
        "ContentUri": PropertyType(True, one_of(is_str(), is_type(dict))),
        "CompatibleRuntimes": PropertyType(False, list_of(one_of(is_str(), is_type(dict)))),
        "LicenseInfo": PropertyType(False, is_str()),
        "RetentionPolicy": PropertyType(False, is_str()),
    }

    RETAIN = "Retain"
    DELETE = "Delete"
    retention_policy_options = [RETAIN.lower(), DELETE.lower()]

    def to_cloudformation(self, **kwargs):
        """Returns the Lambda layer to which this SAM Layer corresponds.

        :param dict kwargs: already-converted resources that may need to be modified when converting this \
        macro to pure CloudFormation
        :returns: a list of vanilla CloudFormation Resources, to which this Function expands
        :rtype: list
        """
        resources = []

        # Append any CFN resources:
        intrinsics_resolver = kwargs["intrinsics_resolver"]
        resources.append(self._construct_lambda_layer(intrinsics_resolver))

        return resources

    def _construct_lambda_layer(self, intrinsics_resolver):
        """Constructs and returns the Lambda function.

        :returns: a list containing the Lambda function and execution role resources
        :rtype: list
        """
        # Resolve intrinsics if applicable:
        self.LayerName = self._resolve_string_parameter(intrinsics_resolver, self.LayerName, "LayerName")
        self.LicenseInfo = self._resolve_string_parameter(intrinsics_resolver, self.LicenseInfo, "LicenseInfo")
        self.Description = self._resolve_string_parameter(intrinsics_resolver, self.Description, "Description")
        self.RetentionPolicy = self._resolve_string_parameter(
            intrinsics_resolver, self.RetentionPolicy, "RetentionPolicy"
        )

        # If nothing defined, this will be set to Retain
        retention_policy_value = self._get_retention_policy_value()

        attributes = self.get_passthrough_resource_attributes()
        if attributes is None:
            attributes = {}
        if "DeletionPolicy" not in attributes:
            attributes["DeletionPolicy"] = self.RETAIN
        if retention_policy_value is not None:
            attributes["DeletionPolicy"] = retention_policy_value

        old_logical_id = self.logical_id

        # This is to prevent the passthrough resource attributes to be included for hashing
        hash_dict = copy.deepcopy(self.to_dict())
        if "DeletionPolicy" in hash_dict.get(old_logical_id):
            del hash_dict[old_logical_id]["DeletionPolicy"]
        if "UpdateReplacePolicy" in hash_dict.get(old_logical_id):
            del hash_dict[old_logical_id]["UpdateReplacePolicy"]
        if "Metadata" in hash_dict.get(old_logical_id):
            del hash_dict[old_logical_id]["Metadata"]

        new_logical_id = logical_id_generator.LogicalIdGenerator(old_logical_id, hash_dict).gen()
        self.logical_id = new_logical_id

        lambda_layer = LambdaLayerVersion(self.logical_id, depends_on=self.depends_on, attributes=attributes)

        # Changing the LayerName property: when a layer is published, it is given an Arn
        # example: arn:aws:lambda:us-west-2:123456789012:layer:MyLayer:1
        # where MyLayer is the LayerName property if it exists; otherwise, it is the
        # LogicalId of this resource. Since a LayerVersion is an immutable resource, when
        # CloudFormation updates this resource, it will ALWAYS create a new version then
        # delete the old version if the logical ids match. What this does is change the
        # logical id of every layer (so a `DeletionPolicy: Retain` can work) and set the
        # LayerName property of the layer so that the Arn will still always be the same
        # with the exception of an incrementing version number.
        if not self.LayerName:
            self.LayerName = old_logical_id

        lambda_layer.LayerName = self.LayerName
        lambda_layer.Description = self.Description
        lambda_layer.Content = construct_s3_location_object(self.ContentUri, self.logical_id, "ContentUri")
        lambda_layer.CompatibleRuntimes = self.CompatibleRuntimes
        lambda_layer.LicenseInfo = self.LicenseInfo

        return lambda_layer

    def _get_retention_policy_value(self):
        """
        Sets the deletion policy on this resource. The default is 'Retain'.

        :return: value for the DeletionPolicy attribute.
        """

        if self.RetentionPolicy is None:
            return None
        elif self.RetentionPolicy.lower() == self.RETAIN.lower():
            return self.RETAIN
        elif self.RetentionPolicy.lower() == self.DELETE.lower():
            return self.DELETE
        elif self.RetentionPolicy.lower() not in self.retention_policy_options:
            raise InvalidResourceException(
                self.logical_id,
                "'{}' must be one of the following options: {}.".format("RetentionPolicy", [self.RETAIN, self.DELETE]),
            )


class SamStateMachine(SamResourceMacro):
    """SAM state machine macro."""

    resource_type = "AWS::Serverless::StateMachine"
    property_types = {
        "Definition": PropertyType(False, is_type(dict)),
        "DefinitionUri": PropertyType(False, one_of(is_str(), is_type(dict))),
        "Logging": PropertyType(False, is_type(dict)),
        "Role": PropertyType(False, is_str()),
        "DefinitionSubstitutions": PropertyType(False, is_type(dict)),
        "Events": PropertyType(False, dict_of(is_str(), is_type(dict))),
        "Name": PropertyType(False, is_str()),
        "Type": PropertyType(False, is_str()),
        "Tags": PropertyType(False, is_type(dict)),
        "Policies": PropertyType(False, one_of(is_str(), list_of(one_of(is_str(), is_type(dict), is_type(dict))))),
        "Tracing": PropertyType(False, is_type(dict)),
        "PermissionsBoundary": PropertyType(False, is_str()),
    }
    event_resolver = ResourceTypeResolver(
        samtranslator.model.stepfunctions.events,
    )

    def to_cloudformation(self, **kwargs):
        managed_policy_map = kwargs.get("managed_policy_map", {})
        intrinsics_resolver = kwargs["intrinsics_resolver"]
        event_resources = kwargs["event_resources"]

        state_machine_generator = StateMachineGenerator(
            logical_id=self.logical_id,
            depends_on=self.depends_on,
            managed_policy_map=managed_policy_map,
            intrinsics_resolver=intrinsics_resolver,
            definition=self.Definition,
            definition_uri=self.DefinitionUri,
            logging=self.Logging,
            name=self.Name,
            policies=self.Policies,
            permissions_boundary=self.PermissionsBoundary,
            definition_substitutions=self.DefinitionSubstitutions,
            role=self.Role,
            state_machine_type=self.Type,
            tracing=self.Tracing,
            events=self.Events,
            event_resources=event_resources,
            event_resolver=self.event_resolver,
            tags=self.Tags,
            resource_attributes=self.resource_attributes,
            passthrough_resource_attributes=self.get_passthrough_resource_attributes(),
        )

        resources = state_machine_generator.to_cloudformation()
        return resources

    def resources_to_link(self, resources):
        try:
            return {"event_resources": self._event_resources_to_link(resources)}
        except InvalidEventException as e:
            raise InvalidResourceException(self.logical_id, e.message)

    def _event_resources_to_link(self, resources):
        event_resources = {}
        if self.Events:
            for logical_id, event_dict in self.Events.items():
                try:
                    event_source = self.event_resolver.resolve_resource_type(event_dict).from_dict(
                        self.logical_id + logical_id, event_dict, logical_id
                    )
                except (TypeError, AttributeError) as e:
                    raise InvalidEventException(logical_id, "{}".format(e))
                event_resources[logical_id] = event_source.resources_to_link(resources)
        return event_resources
