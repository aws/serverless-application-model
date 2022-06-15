""" SAM macro definitions """
import copy
from typing import Union
from samtranslator.intrinsics.resolver import IntrinsicsResolver

import samtranslator.model.eventsources
import samtranslator.model.eventsources.pull
import samtranslator.model.eventsources.push
import samtranslator.model.eventsources.cloudwatchlogs
from .api.api_generator import ApiGenerator
from .api.http_api_generator import HttpApiGenerator
from .packagetype import ZIP, IMAGE
from .s3_utils.uri_parser import construct_s3_location_object, construct_image_code_object
from .tags.resource_tagging import get_tag_list
from samtranslator.metrics.method_decorator import cw_timer
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
from samtranslator.model.architecture import ARM64, X86_64
from samtranslator.model.cloudformation import NestedStack
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
    LambdaUrl,
    LambdaPermission,
)
from samtranslator.model.types import dict_of, is_str, is_type, list_of, one_of, any_type
from samtranslator.translator import logical_id_generator
from samtranslator.translator.arn_generator import ArnGenerator
from samtranslator.model.intrinsics import (
    is_intrinsic,
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
        "EphemeralStorage": PropertyType(False, is_type(dict)),
        # Intrinsic functions in value of Alias property are not supported, yet
        "AutoPublishAlias": PropertyType(False, one_of(is_str())),
        "AutoPublishCodeSha256": PropertyType(False, one_of(is_str())),
        "VersionDescription": PropertyType(False, is_str()),
        "ProvisionedConcurrencyConfig": PropertyType(False, is_type(dict)),
        "FileSystemConfigs": PropertyType(False, list_of(is_type(dict))),
        "ImageConfig": PropertyType(False, is_type(dict)),
        "CodeSigningConfigArn": PropertyType(False, is_str()),
        "Architectures": PropertyType(False, list_of(one_of(is_str(), is_type(dict)))),
        "FunctionUrlConfig": PropertyType(False, is_type(dict)),
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

    @cw_timer
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
        feature_toggle = kwargs.get("feature_toggle")

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
                if not isinstance(code_sha256, str):
                    raise InvalidResourceException(
                        self.logical_id,
                        "AutoPublishCodeSha256 must be a string",
                    )
            lambda_version = self._construct_version(
                lambda_function, intrinsics_resolver=intrinsics_resolver, code_sha256=code_sha256
            )
            lambda_alias = self._construct_alias(alias_name, lambda_function, lambda_version)
            resources.append(lambda_version)
            resources.append(lambda_alias)

        if self.FunctionUrlConfig:
            lambda_url = self._construct_function_url(lambda_function, lambda_alias)
            resources.append(lambda_url)
            url_permission = self._construct_url_permission(lambda_function, lambda_alias)
            if url_permission:
                resources.append(url_permission)

        if self.DeploymentPreference:
            self._validate_deployment_preference_and_add_update_policy(
                kwargs.get("deployment_preference_collection", None),
                lambda_alias,
                intrinsics_resolver,
                mappings_resolver,
                self.get_passthrough_resource_attributes(),
                feature_toggle,
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

        if not isinstance(resolved_alias_name, str):
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
        lambda_function.Architectures = self.Architectures
        lambda_function.EphemeralStorage = self.EphemeralStorage

        if self.Tracing:
            lambda_function.TracingConfig = {"Mode": self.Tracing}

        if self.DeadLetterQueue:
            lambda_function.DeadLetterConfig = {"TargetArn": self.DeadLetterQueue["TargetArn"]}

        lambda_function.CodeSigningConfigArn = self.CodeSigningConfigArn

        self._validate_package_type(lambda_function)
        self._validate_architectures(lambda_function)
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

    def _validate_architectures(self, lambda_function):
        """
        Validates Function based on the existence of architecture type

        parameters
        ----------
        lambda_function: LambdaFunction
            Object of function properties supported on AWS Lambda

        Raises
        ------
        InvalidResourceException
            Raised when the Architectures property is invalid
        """

        architectures = [X86_64] if lambda_function.Architectures is None else lambda_function.Architectures

        if is_intrinsic(architectures):
            return

        if (
            not isinstance(architectures, list)
            or len(architectures) != 1
            or (not is_intrinsic(architectures[0]) and (architectures[0] not in [X86_64, ARM64]))
        ):
            raise InvalidResourceException(
                lambda_function.logical_id,
                "Architectures needs to be a list with one string, either `{}` or `{}`.".format(X86_64, ARM64),
            )

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

        if not (isinstance(self.DeadLetterQueue.get("Type"), str)):
            raise InvalidResourceException(
                self.logical_id,
                "'DeadLetterQueue' property 'Type' should be of type str.",
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
        self,
        deployment_preference_collection,
        lambda_alias,
        intrinsics_resolver,
        mappings_resolver,
        passthrough_resource_attributes,
        feature_toggle=None,
    ):
        if "Enabled" in self.DeploymentPreference:
            # resolve intrinsics and mappings for Enabled
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

        if "PassthroughCondition" in self.DeploymentPreference:
            self.DeploymentPreference["PassthroughCondition"] = self._resolve_property_to_boolean(
                self.DeploymentPreference["PassthroughCondition"],
                "PassthroughCondition",
                intrinsics_resolver,
                mappings_resolver,
            )
        elif feature_toggle:
            self.DeploymentPreference["PassthroughCondition"] = feature_toggle.is_enabled(
                "deployment_preference_condition_fix"
            )
        else:
            self.DeploymentPreference["PassthroughCondition"] = False

        if deployment_preference_collection is None:
            raise ValueError("deployment_preference_collection required for parsing the deployment preference")

        deployment_preference_collection.add(
            self.logical_id,
            self.DeploymentPreference,
            passthrough_resource_attributes.get("Condition"),
        )

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

    def _resolve_property_to_boolean(
        self,
        property_value: Union[bool, str, dict],
        property_name: str,
        intrinsics_resolver: IntrinsicsResolver,
        mappings_resolver: IntrinsicsResolver,
    ) -> bool:
        """
        Resolves intrinsics, if any, and/or converts string in a given property to boolean.
        Raises InvalidResourceException if can't resolve intrinsic or can't resolve string to boolean

        :param property_value: property value to resolve
        :param property_name: name/key of property to resolve
        :param intrinsics_resolver: resolves intrinsics
        :param mappings_resolver: resolves FindInMap
        :return bool: resolved boolean value
        """
        processed_property_value = intrinsics_resolver.resolve_parameter_refs(property_value)
        processed_property_value = mappings_resolver.resolve_parameter_refs(processed_property_value)

        # FIXME: We should support not only true/false, but also yes/no, on/off? See https://yaml.org/type/bool.html
        if processed_property_value in [True, "true", "True"]:
            return True
        elif processed_property_value in [False, "false", "False"]:
            return False
        elif is_intrinsic(processed_property_value):  # couldn't resolve intrinsic
            raise InvalidResourceException(
                self.logical_id,
                f"Unsupported intrinsic: the only intrinsic functions supported for "
                f"property {property_name} are FindInMap and parameter Refs.",
            )
        else:
            raise InvalidResourceException(self.logical_id, f"Invalid value for property {property_name}.")

    def _construct_function_url(self, lambda_function, lambda_alias):
        """
        This method is used to construct a lambda url resource

        Parameters
        ----------
        lambda_function : LambdaFunction
            Lambda Function resource
        lambda_alias : LambdaAlias
            Lambda Alias resource

        Returns
        -------
        LambdaUrl
            Lambda Url resource
        """
        self._validate_function_url_params(lambda_function)

        logical_id = f"{lambda_function.logical_id}Url"
        lambda_url_attributes = self.get_passthrough_resource_attributes()
        lambda_url = LambdaUrl(logical_id=logical_id, attributes=lambda_url_attributes)

        cors = self.FunctionUrlConfig.get("Cors")
        if cors:
            lambda_url.Cors = cors
        lambda_url.AuthType = self.FunctionUrlConfig.get("AuthType")
        lambda_url.TargetFunctionArn = (
            lambda_alias.get_runtime_attr("arn") if lambda_alias else lambda_function.get_runtime_attr("name")
        )
        return lambda_url

    def _validate_function_url_params(self, lambda_function):
        """
        Validate parameters provided to configure Lambda Urls
        """
        self._validate_url_auth_type(lambda_function)
        self._validate_cors_config_parameter(lambda_function)

    def _validate_url_auth_type(self, lambda_function):
        if is_intrinsic(self.FunctionUrlConfig):
            return

        auth_type = self.FunctionUrlConfig.get("AuthType")
        if auth_type and is_intrinsic(auth_type):
            return

        if not auth_type or auth_type not in ["AWS_IAM", "NONE"]:
            raise InvalidResourceException(
                lambda_function.logical_id,
                "AuthType is required to configure function property `FunctionUrlConfig`. Please provide either AWS_IAM or NONE.",
            )

    def _validate_cors_config_parameter(self, lambda_function):
        if is_intrinsic(self.FunctionUrlConfig):
            return

        cors_property_data_type = {
            "AllowOrigins": list,
            "AllowMethods": list,
            "AllowCredentials": bool,
            "AllowHeaders": list,
            "ExposeHeaders": list,
            "MaxAge": int,
        }

        cors = self.FunctionUrlConfig.get("Cors")

        if not cors or is_intrinsic(cors):
            return

        for prop_name, prop_value in cors.items():
            if prop_name not in cors_property_data_type:
                raise InvalidResourceException(
                    lambda_function.logical_id,
                    "{} is not a valid property for configuring Cors.".format(prop_name),
                )
            prop_type = cors_property_data_type.get(prop_name)
            if not is_intrinsic(prop_value) and not isinstance(prop_value, prop_type):
                raise InvalidResourceException(
                    lambda_function.logical_id,
                    "{} must be of type {}.".format(prop_name, str(prop_type).split("'")[1]),
                )

    def _construct_url_permission(self, lambda_function, lambda_alias):
        """
        Construct the lambda permission associated with the function url resource in a case
        for public access when AuthType is NONE

        Parameters
        ----------
        lambda_function : LambdaUrl
            Lambda Function resource

        llambda_alias : LambdaAlias
            Lambda Alias resource

        Returns
        -------
        LambdaPermission
            The lambda permission appended to a function url resource with public access
        """
        auth_type = self.FunctionUrlConfig.get("AuthType")

        if auth_type not in ["NONE"] or is_intrinsic(self.FunctionUrlConfig):
            return None

        logical_id = f"{lambda_function.logical_id}UrlPublicPermissions"
        lambda_permission_attributes = self.get_passthrough_resource_attributes()
        lambda_permission = LambdaPermission(logical_id=logical_id, attributes=lambda_permission_attributes)
        lambda_permission.Action = "lambda:InvokeFunctionUrl"
        lambda_permission.FunctionName = (
            lambda_alias.get_runtime_attr("arn") if lambda_alias else lambda_function.get_runtime_attr("name")
        )
        lambda_permission.Principal = "*"
        lambda_permission.FunctionUrlAuthType = auth_type
        return lambda_permission


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
        "DisableExecuteApiEndpoint": PropertyType(False, is_type(bool)),
        "ApiKeySourceType": PropertyType(False, is_str()),
    }

    referable_properties = {
        "Stage": ApiGatewayStage.resource_type,
        "Deployment": ApiGatewayDeployment.resource_type,
        "DomainName": ApiGatewayDomainName.resource_type,
        "UsagePlan": ApiGatewayUsagePlan.resource_type,
        "UsagePlanKey": ApiGatewayUsagePlanKey.resource_type,
        "ApiKey": ApiGatewayApiKey.resource_type,
    }

    @cw_timer
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
            disable_execute_api_endpoint=self.DisableExecuteApiEndpoint,
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
            api_key_source_type=self.ApiKeySourceType,
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

    @cw_timer
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

    @cw_timer
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

    @cw_timer
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
        "CompatibleArchitectures": PropertyType(False, list_of(one_of(is_str(), is_type(dict)))),
        "CompatibleRuntimes": PropertyType(False, list_of(one_of(is_str(), is_type(dict)))),
        "LicenseInfo": PropertyType(False, is_str()),
        "RetentionPolicy": PropertyType(False, is_str()),
    }

    RETAIN = "Retain"
    DELETE = "Delete"
    retention_policy_options = [RETAIN.lower(), DELETE.lower()]

    @cw_timer
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

        lambda_layer.CompatibleArchitectures = self.CompatibleArchitectures
        self._validate_architectures(lambda_layer)
        lambda_layer.CompatibleRuntimes = self.CompatibleRuntimes
        lambda_layer.LicenseInfo = self.LicenseInfo

        return lambda_layer

    def _get_retention_policy_value(self):
        """
        Sets the deletion policy on this resource. The default is 'Retain'.

        :return: value for the DeletionPolicy attribute.
        """

        if is_intrinsic(self.RetentionPolicy):
            # RetentionPolicy attribute of AWS::Serverless::LayerVersion does set the DeletionPolicy
            # attribute. And DeletionPolicy attribute does not support intrinsic values.
            raise InvalidResourceException(
                self.logical_id,
                "'RetentionPolicy' does not accept intrinsic functions, "
                "please use one of the following options: {}".format([self.RETAIN, self.DELETE]),
            )

        if self.RetentionPolicy is None:
            return None
        elif self.RetentionPolicy.lower() == self.RETAIN.lower():
            return self.RETAIN
        elif self.RetentionPolicy.lower() == self.DELETE.lower():
            return self.DELETE
        elif self.RetentionPolicy.lower() not in self.retention_policy_options:
            raise InvalidResourceException(
                self.logical_id,
                "'RetentionPolicy' must be one of the following options: {}.".format([self.RETAIN, self.DELETE]),
            )

    def _validate_architectures(self, lambda_layer):
        """Validate the values inside the CompatibleArchitectures field of a layer

        Parameters
        ----------
        lambda_layer: SamLayerVersion
            The AWS Lambda layer version to validate

        Raises
        ------
        InvalidResourceException
            If any of the architectures is not valid
        """
        architectures = lambda_layer.CompatibleArchitectures or [X86_64]
        # Intrinsics are not validated
        if is_intrinsic(architectures):
            return
        for arq in architectures:
            # We validate the values only if we they're not intrinsics
            if not is_intrinsic(arq) and not arq in [ARM64, X86_64]:
                raise InvalidResourceException(
                    lambda_layer.logical_id,
                    "CompatibleArchitectures needs to be a list of '{}' or '{}'".format(X86_64, ARM64),
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

    @cw_timer
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
