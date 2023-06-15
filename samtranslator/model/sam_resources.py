""" SAM macro definitions """
import copy
from contextlib import suppress
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast

from typing_extensions import Literal

import samtranslator.model.eventsources
import samtranslator.model.eventsources.cloudwatchlogs
import samtranslator.model.eventsources.pull
import samtranslator.model.eventsources.push
import samtranslator.model.eventsources.scheduler
from samtranslator.feature_toggle.feature_toggle import FeatureToggle
from samtranslator.internal.intrinsics import resolve_string_parameter_in_resource
from samtranslator.internal.model.appsync import (
    APPSYNC_PIPELINE_RESOLVER_JS_CODE,
    AdditionalAuthenticationProviderType,
    ApiCache,
    ApiKey,
    AppSyncRuntimeType,
    CachingConfigType,
    DataSource,
    DomainName,
    DomainNameApiAssociation,
    DynamoDBConfigType,
    FunctionConfiguration,
    GraphQLApi,
    GraphQLSchema,
    LambdaAuthorizerConfigType,
    LogConfigType,
    OpenIDConnectConfigType,
    Resolver,
    SyncConfigType,
    UserPoolConfigType,
)
from samtranslator.internal.schema_source import aws_serverless_graphqlapi
from samtranslator.internal.schema_source.common import PermissionsType
from samtranslator.internal.types import GetManagedPolicyMap
from samtranslator.internal.utils.utils import passthrough_value, remove_none_values
from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.model import (
    PassThroughProperty,
    Property,
    PropertyType,
    Resource,
    ResourceResolver,
    ResourceTypeResolver,
    SamResourceMacro,
)
from samtranslator.model.apigateway import (
    ApiGatewayApiKey,
    ApiGatewayDeployment,
    ApiGatewayDomainName,
    ApiGatewayStage,
    ApiGatewayUsagePlan,
    ApiGatewayUsagePlanKey,
)
from samtranslator.model.apigatewayv2 import ApiGatewayV2DomainName, ApiGatewayV2Stage
from samtranslator.model.architecture import ARM64, X86_64
from samtranslator.model.cloudformation import NestedStack
from samtranslator.model.connector.connector import (
    UNSUPPORTED_CONNECTOR_PROFILE_TYPE,
    ConnectorResourceError,
    ConnectorResourceReference,
    add_depends_on,
    get_event_source_mappings,
    get_resource_reference,
    replace_depends_on_logical_id,
)
from samtranslator.model.connector_profiles.profile import (
    ConnectorProfile,
    get_profile,
    profile_replace,
    verify_profile_variables_replaced,
)
from samtranslator.model.dynamodb import DynamoDBTable
from samtranslator.model.exceptions import InvalidEventException, InvalidResourceException
from samtranslator.model.iam import IAMManagedPolicy, IAMRole, IAMRolePolicies
from samtranslator.model.intrinsics import (
    fnGetAtt,
    is_intrinsic,
    is_intrinsic_if,
    is_intrinsic_no_value,
    make_and_condition,
    make_conditional,
    make_not_conditional,
    ref,
)
from samtranslator.model.lambda_ import (
    LambdaAlias,
    LambdaEventInvokeConfig,
    LambdaFunction,
    LambdaLayerVersion,
    LambdaPermission,
    LambdaUrl,
    LambdaVersion,
)
from samtranslator.model.preferences.deployment_preference_collection import DeploymentPreferenceCollection
from samtranslator.model.resource_policies import ResourcePolicies
from samtranslator.model.role_utils import construct_role_for_resource
from samtranslator.model.sns import SNSTopic, SNSTopicPolicy
from samtranslator.model.sqs import SQSQueue, SQSQueuePolicy
from samtranslator.model.stepfunctions import StateMachineGenerator
from samtranslator.model.types import (
    IS_BOOL,
    IS_DICT,
    IS_INT,
    IS_LIST,
    IS_STR,
    PassThrough,
    any_type,
    dict_of,
    list_of,
    one_of,
)
from samtranslator.model.xray_utils import get_xray_managed_policy_name
from samtranslator.translator import logical_id_generator
from samtranslator.translator.arn_generator import ArnGenerator
from samtranslator.utils.types import Intrinsicable
from samtranslator.validator.value_validator import sam_expect

from .api.api_generator import ApiGenerator
from .api.http_api_generator import HttpApiGenerator
from .packagetype import IMAGE, ZIP
from .s3_utils.uri_parser import construct_image_code_object, construct_s3_location_object
from .tags.resource_tagging import get_tag_list

_CONDITION_CHAR_LIMIT = 255


class SamFunction(SamResourceMacro):
    """SAM function macro."""

    resource_type = "AWS::Serverless::Function"
    property_types = {
        "FunctionName": PropertyType(False, one_of(IS_STR, IS_DICT)),
        "Handler": PassThroughProperty(False),
        "Runtime": PassThroughProperty(False),
        "CodeUri": PassThroughProperty(False),
        "ImageUri": PassThroughProperty(False),
        "PackageType": PassThroughProperty(False),
        "InlineCode": PassThroughProperty(False),
        "DeadLetterQueue": PropertyType(False, IS_DICT),
        "Description": PassThroughProperty(False),
        "MemorySize": PassThroughProperty(False),
        "Timeout": PassThroughProperty(False),
        "VpcConfig": PassThroughProperty(False),
        "Role": PropertyType(False, IS_STR),
        "AssumeRolePolicyDocument": PropertyType(False, IS_DICT),
        "Policies": PropertyType(False, one_of(IS_STR, IS_DICT, list_of(one_of(IS_STR, IS_DICT)))),
        "RolePath": PassThroughProperty(False),
        "PermissionsBoundary": PropertyType(False, IS_STR),
        "Environment": PropertyType(False, dict_of(IS_STR, IS_DICT)),
        "Events": PropertyType(False, dict_of(IS_STR, IS_DICT)),
        "Tags": PropertyType(False, IS_DICT),
        "PropagateTags": PropertyType(False, IS_BOOL),
        "Tracing": PropertyType(False, one_of(IS_DICT, IS_STR)),
        "KmsKeyArn": PassThroughProperty(False),
        "DeploymentPreference": PropertyType(False, IS_DICT),
        "ReservedConcurrentExecutions": PassThroughProperty(False),
        "Layers": PropertyType(False, list_of(one_of(IS_STR, IS_DICT))),
        "EventInvokeConfig": PropertyType(False, IS_DICT),
        "EphemeralStorage": PassThroughProperty(False),
        # Intrinsic functions in value of Alias property are not supported, yet
        "AutoPublishAlias": PropertyType(False, one_of(IS_STR)),
        "AutoPublishCodeSha256": PropertyType(False, one_of(IS_STR)),
        "AutoPublishAliasAllProperties": Property(False, IS_BOOL),
        "VersionDescription": PassThroughProperty(False),
        "ProvisionedConcurrencyConfig": PassThroughProperty(False),
        "FileSystemConfigs": PassThroughProperty(False),
        "ImageConfig": PassThroughProperty(False),
        "CodeSigningConfigArn": PassThroughProperty(False),
        "Architectures": PassThroughProperty(False),
        "SnapStart": PropertyType(False, IS_DICT),
        "FunctionUrlConfig": PropertyType(False, IS_DICT),
        "RuntimeManagementConfig": PassThroughProperty(False),
    }

    FunctionName: Optional[Intrinsicable[str]]
    Handler: Optional[str]
    Runtime: Optional[str]
    CodeUri: Optional[Any]
    ImageUri: Optional[str]
    PackageType: Optional[str]
    InlineCode: Optional[Any]
    DeadLetterQueue: Optional[Dict[str, Any]]
    Description: Optional[Intrinsicable[str]]
    MemorySize: Optional[Intrinsicable[int]]
    Timeout: Optional[Intrinsicable[int]]
    VpcConfig: Optional[Dict[str, Any]]
    Role: Optional[Intrinsicable[str]]
    AssumeRolePolicyDocument: Optional[Dict[str, Any]]
    Policies: Optional[List[Any]]
    RolePath: Optional[PassThrough]
    PermissionsBoundary: Optional[Intrinsicable[str]]
    Environment: Optional[Dict[str, Any]]
    Events: Optional[Dict[str, Any]]
    Tags: Optional[Dict[str, Any]]
    PropagateTags: Optional[bool]
    Tracing: Optional[Dict[str, Any]]
    KmsKeyArn: Optional[Intrinsicable[str]]
    DeploymentPreference: Optional[Dict[str, Any]]
    ReservedConcurrentExecutions: Optional[Any]
    Layers: Optional[List[Any]]
    EventInvokeConfig: Optional[Dict[str, Any]]
    EphemeralStorage: Optional[Dict[str, Any]]
    AutoPublishAlias: Optional[Intrinsicable[str]]
    AutoPublishCodeSha256: Optional[Intrinsicable[str]]
    AutoPublishAliasAllProperties: Optional[bool]
    VersionDescription: Optional[Intrinsicable[str]]
    ProvisionedConcurrencyConfig: Optional[Dict[str, Any]]
    FileSystemConfigs: Optional[Dict[str, Any]]
    ImageConfig: Optional[Dict[str, Any]]
    CodeSigningConfigArn: Optional[Intrinsicable[str]]
    Architectures: Optional[List[Any]]
    SnapStart: Optional[Dict[str, Any]]
    FunctionUrlConfig: Optional[Dict[str, Any]]

    event_resolver = ResourceTypeResolver(
        samtranslator.model.eventsources,
        samtranslator.model.eventsources.pull,
        samtranslator.model.eventsources.push,
        samtranslator.model.eventsources.cloudwatchlogs,
        samtranslator.model.eventsources.scheduler,
    )

    # DeadLetterQueue
    dead_letter_queue_policy_actions = {"SQS": "sqs:SendMessage", "SNS": "sns:Publish"}
    #

    # Conditions
    conditions: Dict[str, Any] = {}  # TODO: Replace `Any` with something more specific

    # Customers can refer to the following properties of SAM function
    referable_properties = {
        "Alias": LambdaAlias.resource_type,
        "Version": LambdaVersion.resource_type,
        # EventConfig auto created SQS and SNS
        "DestinationTopic": SNSTopic.resource_type,
        "DestinationQueue": SQSQueue.resource_type,
    }

    def resources_to_link(self, resources: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return {"event_resources": self._event_resources_to_link(resources)}
        except InvalidEventException as e:
            raise InvalidResourceException(self.logical_id, e.message) from e

    @cw_timer
    def to_cloudformation(self, **kwargs):  # type: ignore[no-untyped-def]
        """Returns the Lambda function, role, and event resources to which this SAM Function corresponds.

        :param dict kwargs: already-converted resources that may need to be modified when converting this \
        macro to pure CloudFormation
        :returns: a list of vanilla CloudFormation Resources, to which this Function expands
        :rtype: list
        """
        resources: List[Any] = []
        intrinsics_resolver: IntrinsicsResolver = kwargs["intrinsics_resolver"]
        mappings_resolver: Optional[IntrinsicsResolver] = kwargs.get("mappings_resolver")
        conditions = kwargs.get("conditions", {})
        feature_toggle = kwargs.get("feature_toggle")

        if self.DeadLetterQueue:
            self._validate_dlq(self.DeadLetterQueue)

        lambda_function = self._construct_lambda_function()
        resources.append(lambda_function)

        if self.ProvisionedConcurrencyConfig and not self.AutoPublishAlias:
            raise InvalidResourceException(
                self.logical_id,
                "To set ProvisionedConcurrencyConfig AutoPublishALias must be defined on the function",
            )

        lambda_alias: Optional[LambdaAlias] = None
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
            lambda_url = self._construct_function_url(lambda_function, lambda_alias, self.FunctionUrlConfig)
            resources.append(lambda_url)
            url_permission = self._construct_url_permission(lambda_function, lambda_alias, self.FunctionUrlConfig)
            if url_permission:
                resources.append(url_permission)

        self._validate_deployment_preference_and_add_update_policy(
            kwargs.get("deployment_preference_collection", None),
            lambda_alias,
            intrinsics_resolver,
            cast(IntrinsicsResolver, mappings_resolver),  # TODO: better handle mappings_resolver's Optional
            self.get_passthrough_resource_attributes(),
            feature_toggle,
        )

        event_invoke_policies: List[Dict[str, Any]] = []
        if self.EventInvokeConfig:
            function_name = lambda_function.logical_id
            event_invoke_resources, event_invoke_policies = self._construct_event_invoke_config(
                function_name, alias_name, lambda_alias, intrinsics_resolver, conditions, self.EventInvokeConfig
            )
            resources.extend(event_invoke_resources)

        managed_policy_map = kwargs.get("managed_policy_map", {})
        get_managed_policy_map = kwargs.get("get_managed_policy_map")

        execution_role = None
        if lambda_function.Role is None:
            execution_role = self._construct_role(
                managed_policy_map,
                event_invoke_policies,
                get_managed_policy_map,
            )
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
            raise InvalidResourceException(self.logical_id, e.message) from e

        self.propagate_tags(resources, self.Tags, self.PropagateTags)

        return resources

    def _construct_event_invoke_config(  # noqa: too-many-arguments
        self,
        function_name: str,
        alias_name: str,
        lambda_alias: Optional[LambdaAlias],
        intrinsics_resolver: IntrinsicsResolver,
        conditions: Any,
        event_invoke_config: Dict[str, Any],
    ) -> Tuple[List[Any], List[Dict[str, Any]]]:
        """
        Create a `AWS::Lambda::EventInvokeConfig` based on the input dict `EventInvokeConfig`
        """
        resources = []
        policy_document = []

        # Try to resolve.
        resolved_event_invoke_config = intrinsics_resolver.resolve_parameter_refs(self.EventInvokeConfig)

        logical_id = f"{function_name}EventInvokeConfig"
        lambda_event_invoke_config = (
            LambdaEventInvokeConfig(
                logical_id=logical_id, depends_on=[lambda_alias.logical_id], attributes=self.resource_attributes
            )
            if lambda_alias
            else LambdaEventInvokeConfig(logical_id=logical_id, attributes=self.resource_attributes)
        )

        dest_config = {}
        input_dest_config = resolved_event_invoke_config.get("DestinationConfig")
        if input_dest_config:
            sam_expect(input_dest_config, self.logical_id, "EventInvokeConfig.DestinationConfig").to_be_a_map()

            for config_name in ["OnSuccess", "OnFailure"]:
                config_value = input_dest_config.get(config_name)
                if config_value is not None:
                    sam_expect(
                        config_value, self.logical_id, f"EventInvokeConfig.DestinationConfig.{config_name}"
                    ).to_be_a_map()
                    resource, destination, policy = self._validate_and_inject_resource(
                        config_value, config_name, logical_id, conditions
                    )
                    dest_config[config_name] = {"Destination": destination}
                    event_invoke_config["DestinationConfig"][config_name]["Destination"] = destination
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

    def _validate_and_inject_resource(
        self, dest_config: Dict[str, Any], event: str, logical_id: str, conditions: Dict[str, Any]
    ) -> Tuple[Optional[Resource], Optional[Any], Dict[str, Any]]:
        """
        For Event Invoke Config, if the user has not specified a destination ARN for SQS/SNS, SAM
        auto creates a SQS and SNS resource with defaults. Intrinsics are supported in the Destination
        ARN property, so to handle conditional ifs we have to inject if conditions in the auto created
        SQS/SNS resources as well as in the policy documents.
        """
        accepted_types_list = ["SQS", "SNS", "EventBridge", "Lambda"]
        auto_inject_list = ["SQS", "SNS"]
        resource: Optional[Union[SNSTopic, SQSQueue]] = None
        policy = {}
        destination = dest_config.get("Destination")

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
                if resource:
                    if combined_condition:
                        resource.set_resource_attribute("Condition", combined_condition)
                    destination = (
                        make_conditional(property_condition, resource.get_runtime_attr("arn"), dest_arn)
                        if property_condition
                        else resource.get_runtime_attr("arn")
                    )
                policy = self._add_event_invoke_managed_policy(dest_config, resource_logical_id, destination)
            else:
                raise InvalidResourceException(
                    self.logical_id, f"Destination is required if Type is not {auto_inject_list}"
                )
        if dest_config.get("Destination") is not None and property_condition is None:
            policy = self._add_event_invoke_managed_policy(
                dest_config, resource_logical_id, dest_config.get("Destination")
            )

        return resource, destination, policy

    def _make_and_conditions(self, resource_condition: Any, property_condition: Any, conditions: Dict[str, Any]) -> Any:
        if resource_condition is None:
            return property_condition

        if property_condition is None:
            return resource_condition

        and_condition = make_and_condition([{"Condition": resource_condition}, {"Condition": property_condition}])
        condition_name = self._make_gen_condition_name(resource_condition + "AND" + property_condition, self.logical_id)
        conditions[condition_name] = and_condition

        return condition_name

    def _get_or_make_condition(self, destination: Any, logical_id: str, conditions: Dict[str, Any]) -> Tuple[Any, Any]:
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

    def _make_gen_condition_name(self, name: str, hash_input: str) -> str:
        # Make sure the property name is not over CFN limit (currently 255)
        hash_digest = logical_id_generator.LogicalIdGenerator("", hash_input).gen()
        condition_name: str = name + hash_digest
        if len(condition_name) > _CONDITION_CHAR_LIMIT:
            return input(condition_name)[:_CONDITION_CHAR_LIMIT]
        return condition_name

    def _get_resolved_alias_name(
        self,
        property_name: str,
        original_alias_value: Intrinsicable[str],
        intrinsics_resolver: IntrinsicsResolver,
    ) -> str:
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
                self.logical_id, f"'{property_name}' must be a string or a Ref to a template parameter"
            )

        return resolved_alias_name

    def _construct_lambda_function(self) -> LambdaFunction:
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
        lambda_function.SnapStart = self.SnapStart
        lambda_function.EphemeralStorage = self.EphemeralStorage

        if self.Tracing:
            lambda_function.TracingConfig = {"Mode": self.Tracing}

        if self.DeadLetterQueue:
            lambda_function.DeadLetterConfig = {"TargetArn": self.DeadLetterQueue["TargetArn"]}

        lambda_function.CodeSigningConfigArn = self.CodeSigningConfigArn

        lambda_function.RuntimeManagementConfig = self.RuntimeManagementConfig  # type: ignore[attr-defined]
        self._validate_package_type(lambda_function)
        return lambda_function

    def _add_event_invoke_managed_policy(
        self, dest_config: Dict[str, Any], logical_id: str, dest_arn: Any
    ) -> Dict[str, Any]:
        if dest_config and dest_config.get("Type"):
            _type = dest_config.get("Type")
            if _type == "SQS":
                return IAMRolePolicies.sqs_send_message_role_policy(dest_arn, logical_id)
            if _type == "SNS":
                return IAMRolePolicies.sns_publish_role_policy(dest_arn, logical_id)
            # Event Bridge and Lambda Arns are passthrough.
            if _type == "EventBridge":
                return IAMRolePolicies.event_bus_put_events_role_policy(dest_arn, logical_id)
            if _type == "Lambda":
                return IAMRolePolicies.lambda_invoke_function_role_policy(dest_arn, logical_id)
        return {}

    def _construct_role(
        self,
        managed_policy_map: Dict[str, Any],
        event_invoke_policies: List[Dict[str, Any]],
        get_managed_policy_map: Optional[GetManagedPolicyMap] = None,
    ) -> IAMRole:
        """Constructs a Lambda execution role based on this SAM function's Policies property.

        :returns: the generated IAM Role
        :rtype: model.iam.IAMRole
        """
        role_attributes = self.get_passthrough_resource_attributes()

        assume_role_policy_document = (
            self.AssumeRolePolicyDocument
            if self.AssumeRolePolicyDocument is not None
            else IAMRolePolicies.lambda_assume_role_policy()
        )

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

        if self.EventInvokeConfig and event_invoke_policies is not None:
            policy_documents.extend(event_invoke_policies)

        return construct_role_for_resource(
            resource_logical_id=self.logical_id,
            attributes=role_attributes,
            managed_policy_map=managed_policy_map,
            assume_role_policy_document=assume_role_policy_document,
            resource_policies=function_policies,
            managed_policy_arns=managed_policy_arns,
            policy_documents=policy_documents,
            role_path=self.RolePath,
            permissions_boundary=self.PermissionsBoundary,
            tags=self._construct_tag_list(self.Tags),
            get_managed_policy_map=get_managed_policy_map,
        )

    def _validate_package_type(self, lambda_function: LambdaFunction) -> None:
        """
        Validates Function based on the existence of Package type
        """
        packagetype = lambda_function.PackageType or ZIP

        if packagetype not in [ZIP, IMAGE]:
            raise InvalidResourceException(
                lambda_function.logical_id,
                f"PackageType needs to be `{ZIP}` or `{IMAGE}`",
            )

        def _validate_package_type_zip() -> None:
            if not all([lambda_function.Runtime, lambda_function.Handler]):
                raise InvalidResourceException(
                    lambda_function.logical_id,
                    f"Runtime and Handler needs to be present when PackageType is of type `{ZIP}`",
                )

            if any([lambda_function.Code.get("ImageUri", False), lambda_function.ImageConfig]):
                raise InvalidResourceException(
                    lambda_function.logical_id,
                    f"ImageUri or ImageConfig cannot be present when PackageType is of type `{ZIP}`",
                )

        def _validate_package_type_image() -> None:
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
                    f"ImageUri needs to be present when PackageType is of type `{IMAGE}`",
                )

        _validate_per_package_type = {ZIP: _validate_package_type_zip, IMAGE: _validate_package_type_image}

        # Call appropriate validation function based on the package type.
        return _validate_per_package_type[packagetype]()

    def _validate_dlq(self, dead_letter_queue: Dict[str, Any]) -> None:
        """Validates whether the DeadLetterQueue LogicalId is validation
        :raise: InvalidResourceException
        """
        # Validate required logical ids
        valid_dlq_types = str(list(self.dead_letter_queue_policy_actions.keys()))

        dlq_type = dead_letter_queue.get("Type")
        if not dlq_type or not dead_letter_queue.get("TargetArn"):
            raise InvalidResourceException(
                self.logical_id,
                "'DeadLetterQueue' requires Type and TargetArn properties to be specified.",
            )
        sam_expect(dlq_type, self.logical_id, "DeadLetterQueue.Type").to_be_a_string()

        # Validate required Types
        if dlq_type not in self.dead_letter_queue_policy_actions:
            raise InvalidResourceException(self.logical_id, f"'DeadLetterQueue' requires Type of {valid_dlq_types}")

    def _event_resources_to_link(self, resources: Dict[str, Any]) -> Dict[str, Any]:
        event_resources = {}
        if self.Events:
            for logical_id, event_dict in self.Events.items():
                try:
                    event_source = self.event_resolver.resolve_resource_type(event_dict).from_dict(
                        self.logical_id + logical_id, event_dict, logical_id
                    )
                except (TypeError, AttributeError) as e:
                    raise InvalidEventException(logical_id, f"{e}") from e
                event_resources[logical_id] = event_source.resources_to_link(resources)
        return event_resources

    @staticmethod
    def order_events(event: Tuple[str, Any]) -> Any:
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
        self,
        lambda_function: LambdaFunction,
        execution_role: Optional[IAMRole],
        event_resources: Any,
        intrinsics_resolver: IntrinsicsResolver,
        lambda_alias: Optional[LambdaAlias] = None,
    ) -> List[Any]:
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
                    raise InvalidEventException(logical_id, f"{e}") from e

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

    def _construct_code_dict(self) -> Dict[str, Any]:
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
            raise InvalidResourceException(self.logical_id, f"invalid 'PackageType' : {packagetype}")

        # Inline function for transformation of inline code.
        # It accepts arbitrary argumemnts, because the arguments do not matter for the result.
        def _construct_inline_code(*args: Any, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
            return {"ZipFile": self.InlineCode}

        # dispatch mechanism per artifact on how it needs to be transformed.
        artifact_dispatch: Dict[str, Callable[..., Dict[str, Any]]] = {
            "InlineCode": _construct_inline_code,
            "CodeUri": construct_s3_location_object,
            "ImageUri": construct_image_code_object,
        }

        filtered_artifacts = dict(filter(lambda x: x[1] is not None, artifacts.items()))
        # There are more than one allowed artifact types present, raise an Error.
        # There are no valid artifact types present, also raise an Error.
        if len(filtered_artifacts) > 1 or len(filtered_artifacts) == 0:
            if packagetype == ZIP and len(filtered_artifacts) == 0:
                raise InvalidResourceException(self.logical_id, "Only one of 'InlineCode' or 'CodeUri' can be set.")
            if packagetype == IMAGE:
                raise InvalidResourceException(self.logical_id, "'ImageUri' must be set.")

        filtered_keys = list(filtered_artifacts.keys())
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
        dispatch_function: Callable[..., Dict[str, Any]] = artifact_dispatch[filtered_key]
        return dispatch_function(artifacts[filtered_key], self.logical_id, filtered_key)

    def _construct_version(
        self, function: LambdaFunction, intrinsics_resolver: IntrinsicsResolver, code_sha256: Optional[str] = None
    ) -> LambdaVersion:
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
        prefix = f"{self.logical_id}Version"
        logical_dict = {}
        # We can't directly change AutoPublishAlias as that would be a breaking change, so we have to add this opt-in
        # property that when set to true would change the lambda version whenever a property in the lambda function changes
        if self.AutoPublishAliasAllProperties:
            properties = function._generate_resource_dict().get("Properties", {})
            logical_dict = properties
        else:
            with suppress(AttributeError, UnboundLocalError):
                logical_dict = code_dict.copy()
            if function.Environment:
                logical_dict.update(function.Environment)
            if function.MemorySize:
                logical_dict.update({"MemorySize": function.MemorySize})
            # If SnapStart is enabled we want to publish a new version, to have the corresponding snapshot
            if function.SnapStart and function.SnapStart.get("ApplyOn", "None") != "None":
                logical_dict.update({"SnapStart": function.SnapStart})
        logical_id = logical_id_generator.LogicalIdGenerator(prefix, logical_dict, code_sha256).gen()

        attributes = self.get_passthrough_resource_attributes()
        if "DeletionPolicy" not in attributes:
            attributes["DeletionPolicy"] = "Retain"

        lambda_version = LambdaVersion(logical_id=logical_id, attributes=attributes)
        lambda_version.FunctionName = function.get_runtime_attr("name")
        lambda_version.Description = self.VersionDescription
        # Copy the same runtime policy for the version and the function
        lambda_version.RuntimeManagementConfig = function.RuntimeManagementConfig

        return lambda_version

    def _construct_alias(self, name: str, function: LambdaFunction, version: LambdaVersion) -> LambdaAlias:
        """Constructs a Lambda Alias for the given function and pointing to the given version

        :param string name: Name of the alias
        :param model.lambda_.LambdaFunction function: Lambda function object to associate the alias with
        :param model.lambda_.LambdaVersion version: Lambda version object to associate the alias with
        :return: Lambda alias object
        :rtype model.lambda_.LambdaAlias
        """

        if not name:
            raise InvalidResourceException(self.logical_id, "Alias name is required to create an alias")

        logical_id = f"{function.logical_id}Alias{name}"
        alias = LambdaAlias(logical_id=logical_id, attributes=self.get_passthrough_resource_attributes())
        alias.Name = name
        alias.FunctionName = function.get_runtime_attr("name")
        alias.FunctionVersion = version.get_runtime_attr("version")
        if self.ProvisionedConcurrencyConfig:
            alias.ProvisionedConcurrencyConfig = self.ProvisionedConcurrencyConfig

        return alias

    def _validate_deployment_preference_and_add_update_policy(  # noqa: too-many-arguments
        self,
        deployment_preference_collection: DeploymentPreferenceCollection,
        lambda_alias: Optional[LambdaAlias],
        intrinsics_resolver: IntrinsicsResolver,
        mappings_resolver: IntrinsicsResolver,
        passthrough_resource_attributes: Dict[str, Any],
        feature_toggle: Optional[FeatureToggle] = None,
    ) -> None:
        if not self.DeploymentPreference:
            return

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
            if not self.AutoPublishAlias:
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
        property_value: Union[bool, str, Dict[str, Any]],
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
        if processed_property_value in [False, "false", "False"]:
            return False
        if is_intrinsic(processed_property_value):  # couldn't resolve intrinsic
            raise InvalidResourceException(
                self.logical_id,
                f"Unsupported intrinsic: the only intrinsic functions supported for "
                f"property {property_name} are FindInMap and parameter Refs.",
            )
        raise InvalidResourceException(self.logical_id, f"Invalid value for property {property_name}.")

    def _construct_function_url(
        self, lambda_function: LambdaFunction, lambda_alias: Optional[LambdaAlias], function_url_config: Dict[str, Any]
    ) -> LambdaUrl:
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
        self._validate_function_url_params(lambda_function, function_url_config)

        logical_id = f"{lambda_function.logical_id}Url"
        lambda_url_attributes = self.get_passthrough_resource_attributes()
        lambda_url = LambdaUrl(logical_id=logical_id, attributes=lambda_url_attributes)

        cors = function_url_config.get("Cors")
        if cors:
            lambda_url.Cors = cors
        lambda_url.AuthType = function_url_config.get("AuthType")
        lambda_url.TargetFunctionArn = (
            lambda_alias.get_runtime_attr("arn") if lambda_alias else lambda_function.get_runtime_attr("name")
        )
        lambda_url.InvokeMode = function_url_config.get("InvokeMode")
        return lambda_url

    def _validate_function_url_params(
        self, lambda_function: LambdaFunction, function_url_config: Dict[str, Any]
    ) -> None:
        """
        Validate parameters provided to configure Lambda Urls
        """
        self._validate_url_auth_type(lambda_function, function_url_config)
        self._validate_cors_config_parameter(lambda_function, function_url_config)

    def _validate_url_auth_type(self, lambda_function: LambdaFunction, function_url_config: Dict[str, Any]) -> None:
        if is_intrinsic(function_url_config):
            return

        auth_type = function_url_config.get("AuthType")
        if auth_type and is_intrinsic(auth_type):
            return

        if not auth_type or auth_type not in ["AWS_IAM", "NONE"]:
            raise InvalidResourceException(
                lambda_function.logical_id,
                "AuthType is required to configure function property `FunctionUrlConfig`. Please provide either AWS_IAM or NONE.",
            )

    def _validate_cors_config_parameter(
        self, lambda_function: LambdaFunction, function_url_config: Dict[str, Any]
    ) -> None:
        if is_intrinsic(function_url_config):
            return

        cors_property_data_type = {
            "AllowOrigins": list,
            "AllowMethods": list,
            "AllowCredentials": bool,
            "AllowHeaders": list,
            "ExposeHeaders": list,
            "MaxAge": int,
        }

        cors = function_url_config.get("Cors")

        if not cors or is_intrinsic(cors):
            return

        sam_expect(cors, lambda_function.logical_id, "FunctionUrlConfig.Cors").to_be_a_map()

        for prop_name, prop_value in cors.items():
            if prop_name not in cors_property_data_type:
                raise InvalidResourceException(
                    lambda_function.logical_id,
                    f"{prop_name} is not a valid property for configuring Cors.",
                )
            prop_type = cors_property_data_type.get(prop_name, list)
            if not is_intrinsic(prop_value) and not isinstance(prop_value, prop_type):
                raise InvalidResourceException(
                    lambda_function.logical_id,
                    "{} must be of type {}.".format(prop_name, str(prop_type).split("'")[1]),
                )

    def _construct_url_permission(
        self, lambda_function: LambdaFunction, lambda_alias: Optional[LambdaAlias], function_url_config: Dict[str, Any]
    ) -> Optional[LambdaPermission]:
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
        auth_type = function_url_config.get("AuthType")

        if auth_type not in ["NONE"] or is_intrinsic(function_url_config):
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
        "__MANAGE_SWAGGER": PropertyType(False, IS_BOOL),
        "Name": PropertyType(False, one_of(IS_STR, IS_DICT)),
        "StageName": PropertyType(True, one_of(IS_STR, IS_DICT)),
        "Tags": PropertyType(False, IS_DICT),
        "PropagateTags": PropertyType(False, IS_BOOL),
        "DefinitionBody": PropertyType(False, IS_DICT),
        "DefinitionUri": PropertyType(False, one_of(IS_STR, IS_DICT)),
        "MergeDefinitions": Property(False, IS_BOOL),
        "CacheClusterEnabled": PropertyType(False, IS_BOOL),
        "CacheClusterSize": PropertyType(False, IS_STR),
        "Variables": PropertyType(False, IS_DICT),
        "EndpointConfiguration": PropertyType(False, one_of(IS_STR, IS_DICT)),
        "MethodSettings": PropertyType(False, IS_LIST),
        "BinaryMediaTypes": PropertyType(False, IS_LIST),
        "MinimumCompressionSize": PropertyType(False, IS_INT),
        "Cors": PropertyType(False, one_of(IS_STR, IS_DICT)),
        "Auth": PropertyType(False, IS_DICT),
        "GatewayResponses": PropertyType(False, IS_DICT),
        "AccessLogSetting": PropertyType(False, IS_DICT),
        "CanarySetting": PropertyType(False, IS_DICT),
        "TracingEnabled": PropertyType(False, IS_BOOL),
        "OpenApiVersion": PropertyType(False, IS_STR),
        "Models": PropertyType(False, IS_DICT),
        "Domain": PropertyType(False, IS_DICT),
        "FailOnWarnings": PropertyType(False, IS_BOOL),
        "Description": PropertyType(False, IS_STR),
        "Mode": PropertyType(False, IS_STR),
        "DisableExecuteApiEndpoint": PropertyType(False, IS_BOOL),
        "ApiKeySourceType": PropertyType(False, IS_STR),
        "AlwaysDeploy": Property(False, IS_BOOL),
    }

    Name: Optional[Intrinsicable[str]]
    StageName: Optional[Intrinsicable[str]]
    Tags: Optional[Dict[str, Any]]
    PropagateTags: Optional[bool]
    DefinitionBody: Optional[Dict[str, Any]]
    DefinitionUri: Optional[Intrinsicable[str]]
    MergeDefinitions: Optional[bool]
    CacheClusterEnabled: Optional[Intrinsicable[bool]]
    CacheClusterSize: Optional[Intrinsicable[str]]
    Variables: Optional[Dict[str, Any]]
    EndpointConfiguration: Optional[Dict[str, Any]]
    MethodSettings: Optional[List[Any]]
    BinaryMediaTypes: Optional[List[Any]]
    MinimumCompressionSize: Optional[Intrinsicable[int]]
    Cors: Optional[Intrinsicable[str]]
    Auth: Optional[Dict[str, Any]]
    GatewayResponses: Optional[Dict[str, Any]]
    AccessLogSetting: Optional[Dict[str, Any]]
    CanarySetting: Optional[Dict[str, Any]]
    TracingEnabled: Optional[Intrinsicable[bool]]
    OpenApiVersion: Optional[Intrinsicable[str]]
    Models: Optional[Dict[str, Any]]
    Domain: Optional[Dict[str, Any]]
    FailOnWarnings: Optional[Intrinsicable[bool]]
    Description: Optional[Intrinsicable[str]]
    Mode: Optional[Intrinsicable[str]]
    DisableExecuteApiEndpoint: Optional[Intrinsicable[bool]]
    ApiKeySourceType: Optional[Intrinsicable[str]]
    AlwaysDeploy: Optional[bool]

    referable_properties = {
        "Stage": ApiGatewayStage.resource_type,
        "Deployment": ApiGatewayDeployment.resource_type,
        "DomainName": ApiGatewayDomainName.resource_type,
        "UsagePlan": ApiGatewayUsagePlan.resource_type,
        "UsagePlanKey": ApiGatewayUsagePlanKey.resource_type,
        "ApiKey": ApiGatewayApiKey.resource_type,
    }

    @cw_timer
    def to_cloudformation(self, **kwargs) -> List[Resource]:  # type: ignore[no-untyped-def]
        """Returns the API Gateway RestApi, Deployment, and Stage to which this SAM Api corresponds.

        :param dict kwargs: already-converted resources that may need to be modified when converting this \
        macro to pure CloudFormation
        :returns: a list of vanilla CloudFormation Resources, to which this Function expands
        :rtype: list
        """

        intrinsics_resolver = kwargs["intrinsics_resolver"]
        self.BinaryMediaTypes = intrinsics_resolver.resolve_parameter_refs(self.BinaryMediaTypes)
        self.Domain = intrinsics_resolver.resolve_parameter_refs(self.Domain)
        self.Auth = intrinsics_resolver.resolve_parameter_refs(self.Auth)
        redeploy_restapi_parameters = kwargs.get("redeploy_restapi_parameters")
        shared_api_usage_plan = kwargs.get("shared_api_usage_plan")
        template_conditions = kwargs.get("conditions")
        route53_record_set_groups = kwargs.get("route53_record_set_groups", {})

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
            merge_definitions=self.MergeDefinitions,
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
            fail_on_warnings=self.FailOnWarnings,
            description=self.Description,
            mode=self.Mode,
            api_key_source_type=self.ApiKeySourceType,
            always_deploy=self.AlwaysDeploy,
        )

        generated_resources = api_generator.to_cloudformation(redeploy_restapi_parameters, route53_record_set_groups)

        self.propagate_tags(generated_resources, self.Tags, self.PropagateTags)

        return generated_resources


class SamHttpApi(SamResourceMacro):
    """SAM rest API macro."""

    resource_type = "AWS::Serverless::HttpApi"
    property_types = {
        # Internal property set only by Implicit HTTP API plugin. If set to True, the API Event Source code will
        # inject Lambda Integration URI to the OpenAPI. To preserve backwards compatibility, this must be set only for
        # Implicit APIs. For Explicit APIs, this is managed by the DefaultDefinitionBody Plugin.
        # In the future, we might rename and expose this property to customers so they can have SAM manage Explicit APIs
        # Swagger.
        "__MANAGE_SWAGGER": PropertyType(False, IS_BOOL),
        "Name": PassThroughProperty(False),
        "StageName": PropertyType(False, one_of(IS_STR, IS_DICT)),
        "Tags": PropertyType(False, IS_DICT),
        "PropagateTags": PropertyType(False, IS_BOOL),
        "DefinitionBody": PropertyType(False, IS_DICT),
        "DefinitionUri": PropertyType(False, one_of(IS_STR, IS_DICT)),
        "StageVariables": PropertyType(False, IS_DICT),
        "CorsConfiguration": PropertyType(False, one_of(IS_BOOL, IS_DICT)),
        "AccessLogSettings": PropertyType(False, IS_DICT),
        "DefaultRouteSettings": PropertyType(False, IS_DICT),
        "Auth": PropertyType(False, IS_DICT),
        "RouteSettings": PropertyType(False, IS_DICT),
        "Domain": PropertyType(False, IS_DICT),
        "FailOnWarnings": PropertyType(False, IS_BOOL),
        "Description": PropertyType(False, IS_STR),
        "DisableExecuteApiEndpoint": PropertyType(False, IS_BOOL),
    }

    Name: Optional[Any]
    StageName: Optional[Intrinsicable[str]]
    Tags: Optional[Dict[str, Any]]
    PropagateTags: Optional[bool]
    DefinitionBody: Optional[Dict[str, Any]]
    DefinitionUri: Optional[Intrinsicable[str]]
    StageVariables: Optional[Dict[str, Intrinsicable[str]]]
    CorsConfiguration: Optional[Union[bool, Dict[str, Any]]]
    AccessLogSettings: Optional[Dict[str, Any]]
    DefaultRouteSettings: Optional[Dict[str, Any]]
    Auth: Optional[Dict[str, Any]]
    RouteSettings: Optional[Dict[str, Any]]
    Domain: Optional[Dict[str, Any]]
    FailOnWarnings: Optional[Intrinsicable[bool]]
    Description: Optional[Intrinsicable[str]]
    DisableExecuteApiEndpoint: Optional[Intrinsicable[bool]]

    referable_properties = {
        "Stage": ApiGatewayV2Stage.resource_type,
        "DomainName": ApiGatewayV2DomainName.resource_type,
    }

    @cw_timer
    def to_cloudformation(self, **kwargs):  # type: ignore[no-untyped-def]
        """Returns the API GatewayV2 Api, Deployment, and Stage to which this SAM Api corresponds.

        :param dict kwargs: already-converted resources that may need to be modified when converting this \
        macro to pure CloudFormation
        :returns: a list of vanilla CloudFormation Resources, to which this Function expands
        :rtype: list
        """
        resources: List[Resource] = []
        intrinsics_resolver = kwargs["intrinsics_resolver"]
        self.CorsConfiguration = intrinsics_resolver.resolve_parameter_refs(self.CorsConfiguration)
        self.Domain = intrinsics_resolver.resolve_parameter_refs(self.Domain)

        api_generator = HttpApiGenerator(
            self.logical_id,
            self.StageVariables,
            self.depends_on,
            self.DefinitionBody,
            self.DefinitionUri,
            self.Name,
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
            permissions,
        ) = api_generator.to_cloudformation(kwargs.get("route53_record_set_groups", {}))

        resources.append(http_api)
        if permissions:
            resources.extend(permissions)
        if domain:
            resources.append(domain)
        if basepath_mapping:
            resources.extend(basepath_mapping)
        if route53:
            resources.append(route53)

        # Stage is now optional. Only add it if one is created.
        if stage:
            resources.append(stage)

        self.propagate_tags(resources, self.Tags, self.PropagateTags)

        return resources


class SamSimpleTable(SamResourceMacro):
    """SAM simple table macro."""

    resource_type = "AWS::Serverless::SimpleTable"
    property_types = {
        "PointInTimeRecoverySpecification": PassThroughProperty(False),
        "PrimaryKey": PropertyType(False, dict_of(IS_STR, IS_STR)),
        "ProvisionedThroughput": PropertyType(False, dict_of(IS_STR, one_of(IS_INT, IS_DICT))),
        "TableName": PropertyType(False, one_of(IS_STR, IS_DICT)),
        "Tags": PropertyType(False, IS_DICT),
        "SSESpecification": PropertyType(False, IS_DICT),
    }

    PointInTimeRecoverySpecification: Optional[PassThrough]
    PrimaryKey: Optional[Dict[str, str]]
    ProvisionedThroughput: Optional[Dict[str, Any]]
    TableName: Optional[Intrinsicable[str]]
    Tags: Optional[Dict[str, Any]]
    SSESpecification: Optional[Dict[str, Any]]

    attribute_type_conversions = {"String": "S", "Number": "N", "Binary": "B"}

    @cw_timer
    def to_cloudformation(self, **kwargs):  # type: ignore[no-untyped-def]
        dynamodb_resources = self._construct_dynamodb_table()

        return [dynamodb_resources]

    def _construct_dynamodb_table(self) -> DynamoDBTable:
        dynamodb_table = DynamoDBTable(self.logical_id, depends_on=self.depends_on, attributes=self.resource_attributes)

        if self.PrimaryKey:
            primary_key_name = sam_expect(
                self.PrimaryKey.get("Name"), self.logical_id, "PrimaryKey.Name"
            ).to_not_be_none()
            primary_key_type = sam_expect(
                self.PrimaryKey.get("Type"), self.logical_id, "PrimaryKey.Type"
            ).to_not_be_none()
            primary_key = {
                "AttributeName": primary_key_name,
                "AttributeType": self._convert_attribute_type(primary_key_type),
            }

        else:
            primary_key = {"AttributeName": "id", "AttributeType": "S"}

        dynamodb_table.AttributeDefinitions = [primary_key]
        dynamodb_table.KeySchema = [{"AttributeName": primary_key["AttributeName"], "KeyType": "HASH"}]

        if self.PointInTimeRecoverySpecification:
            dynamodb_table.PointInTimeRecoverySpecification = self.PointInTimeRecoverySpecification

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

    def _convert_attribute_type(self, attribute_type: str) -> str:
        if attribute_type in self.attribute_type_conversions:
            return self.attribute_type_conversions[attribute_type]
        raise InvalidResourceException(self.logical_id, f"Invalid 'Type' \"{attribute_type}\".")


class SamApplication(SamResourceMacro):
    """SAM application macro."""

    APPLICATION_ID_KEY = "ApplicationId"
    SEMANTIC_VERSION_KEY = "SemanticVersion"

    resource_type = "AWS::Serverless::Application"

    # The plugin will always insert the TemplateUrl parameter
    property_types = {
        "Location": PropertyType(True, one_of(IS_STR, IS_DICT)),
        "TemplateUrl": PropertyType(False, IS_STR),
        "Parameters": PropertyType(False, IS_DICT),
        "NotificationARNs": PropertyType(False, list_of(one_of(IS_STR, IS_DICT))),
        "Tags": PropertyType(False, IS_DICT),
        "TimeoutInMinutes": PropertyType(False, IS_INT),
    }

    Location: Union[str, Dict[str, Any]]
    TemplateUrl: Optional[Intrinsicable[str]]
    Parameters: Optional[Dict[str, Any]]
    NotificationARNs: Optional[List[Any]]
    Tags: Optional[Dict[str, Any]]
    TimeoutInMinutes: Optional[Intrinsicable[int]]

    @cw_timer
    def to_cloudformation(self, **kwargs):  # type: ignore[no-untyped-def]
        """Returns the stack with the proper parameters for this application"""
        nested_stack = self._construct_nested_stack()
        return [nested_stack]

    def _construct_nested_stack(self) -> NestedStack:
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

    def _get_application_tags(self) -> Dict[str, str]:
        """Adds tags to the stack if this resource is using the serverless app repo"""
        application_tags = {}
        if isinstance(self.Location, dict):
            if self.APPLICATION_ID_KEY in self.Location and self.Location[self.APPLICATION_ID_KEY] is not None:
                application_tags[self._SAR_APP_KEY] = self.Location[self.APPLICATION_ID_KEY]
            if self.SEMANTIC_VERSION_KEY in self.Location and self.Location[self.SEMANTIC_VERSION_KEY] is not None:
                application_tags[self._SAR_SEMVER_KEY] = self.Location[self.SEMANTIC_VERSION_KEY]
        return application_tags


class SamLayerVersion(SamResourceMacro):
    """SAM Layer macro"""

    resource_type = "AWS::Serverless::LayerVersion"
    property_types = {
        "LayerName": PropertyType(False, one_of(IS_STR, IS_DICT)),
        "Description": PropertyType(False, IS_STR),
        "ContentUri": PropertyType(True, one_of(IS_STR, IS_DICT)),
        "CompatibleArchitectures": PropertyType(False, list_of(one_of(IS_STR, IS_DICT))),
        "CompatibleRuntimes": PropertyType(False, list_of(one_of(IS_STR, IS_DICT))),
        "LicenseInfo": PropertyType(False, IS_STR),
        "RetentionPolicy": PropertyType(False, IS_STR),
    }

    LayerName: Optional[Intrinsicable[str]]
    Description: Optional[Intrinsicable[str]]
    ContentUri: Dict[str, Any]
    CompatibleArchitectures: Optional[List[Any]]
    CompatibleRuntimes: Optional[List[Any]]
    LicenseInfo: Optional[Intrinsicable[str]]
    RetentionPolicy: Optional[Intrinsicable[str]]

    RETAIN = "Retain"
    DELETE = "Delete"
    retention_policy_options = [RETAIN, DELETE]

    @cw_timer
    def to_cloudformation(self, **kwargs):  # type: ignore[no-untyped-def]
        """Returns the Lambda layer to which this SAM Layer corresponds.

        :param dict kwargs: already-converted resources that may need to be modified when converting this \
        macro to pure CloudFormation
        :returns: a list of vanilla CloudFormation Resources, to which this Function expands
        :rtype: list
        """
        resources = []

        # Append any CFN resources:
        intrinsics_resolver: IntrinsicsResolver = kwargs["intrinsics_resolver"]
        resources.append(self._construct_lambda_layer(intrinsics_resolver))

        return resources

    def _construct_lambda_layer(self, intrinsics_resolver: IntrinsicsResolver) -> LambdaLayerVersion:
        """Constructs and returns the Lambda function.

        :returns: a list containing the Lambda function and execution role resources
        :rtype: list
        """
        # Resolve intrinsics if applicable:
        self.LayerName = resolve_string_parameter_in_resource(
            self.logical_id, intrinsics_resolver, self.LayerName, "LayerName"
        )
        self.LicenseInfo = resolve_string_parameter_in_resource(
            self.logical_id, intrinsics_resolver, self.LicenseInfo, "LicenseInfo"
        )
        self.Description = resolve_string_parameter_in_resource(
            self.logical_id, intrinsics_resolver, self.Description, "Description"
        )
        self.RetentionPolicy = resolve_string_parameter_in_resource(
            self.logical_id, intrinsics_resolver, self.RetentionPolicy, "RetentionPolicy"
        )

        # If nothing defined, this will be set to Retain
        retention_policy_value = self._get_retention_policy_value()

        attributes = self.get_passthrough_resource_attributes()
        if "DeletionPolicy" not in attributes:
            attributes["DeletionPolicy"] = self.RETAIN
        if retention_policy_value is not None:
            attributes["DeletionPolicy"] = retention_policy_value

        old_logical_id = self.logical_id

        # This is to prevent the passthrough resource attributes to be included for hashing
        hash_dict = copy.deepcopy(self.to_dict())
        if "DeletionPolicy" in hash_dict.get(old_logical_id, {}):
            del hash_dict[old_logical_id]["DeletionPolicy"]
        if "UpdateReplacePolicy" in hash_dict.get(old_logical_id, {}):
            del hash_dict[old_logical_id]["UpdateReplacePolicy"]
        if "Metadata" in hash_dict.get(old_logical_id, {}):
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

    def _get_retention_policy_value(self) -> Optional[str]:
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

        if not isinstance(self.RetentionPolicy, str):
            raise InvalidResourceException(
                self.logical_id,
                "Invalid 'RetentionPolicy' type, "
                "please use one of the following options: {}".format([self.RETAIN, self.DELETE]),
            )

        for option in self.retention_policy_options:
            if self.RetentionPolicy.lower() == option.lower():
                return option
        raise InvalidResourceException(
            self.logical_id,
            f"'RetentionPolicy' must be one of the following options: {[self.RETAIN, self.DELETE]}.",
        )

    def _validate_architectures(self, lambda_layer: LambdaLayerVersion) -> None:
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
            if not is_intrinsic(arq) and arq not in [ARM64, X86_64]:
                raise InvalidResourceException(
                    lambda_layer.logical_id,
                    f"CompatibleArchitectures needs to be a list of '{X86_64}' or '{ARM64}'",
                )


class SamStateMachine(SamResourceMacro):
    """SAM state machine macro."""

    resource_type = "AWS::Serverless::StateMachine"
    property_types = {
        "Definition": PropertyType(False, IS_DICT),
        "DefinitionUri": PropertyType(False, one_of(IS_STR, IS_DICT)),
        "Logging": PropertyType(False, IS_DICT),
        "Role": PropertyType(False, IS_STR),
        "RolePath": PassThroughProperty(False),
        "DefinitionSubstitutions": PropertyType(False, IS_DICT),
        "Events": PropertyType(False, dict_of(IS_STR, IS_DICT)),
        "Name": PropertyType(False, IS_STR),
        "Type": PropertyType(False, IS_STR),
        "Tags": PropertyType(False, IS_DICT),
        "PropagateTags": PropertyType(False, IS_BOOL),
        "Policies": PropertyType(False, one_of(IS_STR, list_of(one_of(IS_STR, IS_DICT, IS_DICT)))),
        "Tracing": PropertyType(False, IS_DICT),
        "PermissionsBoundary": PropertyType(False, IS_STR),
    }

    Definition: Optional[Dict[str, Any]]
    DefinitionUri: Optional[Intrinsicable[str]]
    Logging: Optional[Dict[str, Any]]
    Role: Optional[Intrinsicable[str]]
    RolePath: Optional[PassThrough]
    DefinitionSubstitutions: Optional[Dict[str, Any]]
    Events: Optional[Dict[str, Any]]
    Name: Optional[Intrinsicable[str]]
    Type: Optional[Intrinsicable[str]]
    Tags: Optional[Dict[str, Any]]
    PropagateTags: Optional[bool]
    Policies: Optional[List[Any]]
    Tracing: Optional[Dict[str, Any]]
    PermissionsBoundary: Optional[Intrinsicable[str]]

    event_resolver = ResourceTypeResolver(
        samtranslator.model.stepfunctions.events,
        samtranslator.model.eventsources.scheduler,
    )

    @cw_timer
    def to_cloudformation(self, **kwargs):  # type: ignore[no-untyped-def]
        managed_policy_map = kwargs.get("managed_policy_map", {})
        get_managed_policy_map = kwargs.get("get_managed_policy_map")
        intrinsics_resolver = kwargs["intrinsics_resolver"]
        event_resources = kwargs["event_resources"]

        state_machine_generator = StateMachineGenerator(  # type: ignore[no-untyped-call]
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
            role_path=self.RolePath,
            state_machine_type=self.Type,
            tracing=self.Tracing,
            events=self.Events,
            event_resources=event_resources,
            event_resolver=self.event_resolver,
            tags=self.Tags,
            resource_attributes=self.resource_attributes,
            passthrough_resource_attributes=self.get_passthrough_resource_attributes(),
            get_managed_policy_map=get_managed_policy_map,
        )

        generated_resources = state_machine_generator.to_cloudformation()

        self.propagate_tags(generated_resources, self.Tags, self.PropagateTags)

        return generated_resources

    def resources_to_link(self, resources: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return {"event_resources": self._event_resources_to_link(resources)}
        except InvalidEventException as e:
            raise InvalidResourceException(self.logical_id, e.message) from e

    def _event_resources_to_link(self, resources: Dict[str, Any]) -> Dict[str, Any]:
        event_resources = {}
        if self.Events:
            for logical_id, event_dict in self.Events.items():
                try:
                    event_source = self.event_resolver.resolve_resource_type(event_dict).from_dict(
                        self.logical_id + logical_id, event_dict, logical_id
                    )
                except (TypeError, AttributeError) as e:
                    raise InvalidEventException(logical_id, f"{e}") from e
                event_resources[logical_id] = event_source.resources_to_link(resources)
        return event_resources


class SamConnector(SamResourceMacro):
    """Sam connector macro.
    AWS SAM uses the LogicalIds of the AWS SAM resources in your template file to
    construct the LogicalIds of the AWS CloudFormation resources it generates
    https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification-generated-resources.html
    """

    Source: Dict[str, Any]
    Destination: Union[Dict[str, Any], List[Dict[str, Any]]]
    Permissions: List[str]

    resource_type = "AWS::Serverless::Connector"
    property_types = {
        "Source": PropertyType(True, dict_of(IS_STR, any_type())),
        "Destination": PropertyType(True, one_of(dict_of(IS_STR, any_type()), list_of(dict_of(IS_STR, any_type())))),
        "Permissions": PropertyType(True, list_of(IS_STR)),
    }

    @cw_timer
    def to_cloudformation(self, **kwargs: Any) -> List[Resource]:
        resource_resolver: ResourceResolver = kwargs["resource_resolver"]
        original_template = kwargs["original_template"]

        multi_dest = True
        if isinstance(self.Destination, dict):
            multi_dest = False
            self.Destination = [self.Destination]

        list_generated_resources: List[Resource] = []

        for dest_index, dest in enumerate(self.Destination):
            try:
                destination = get_resource_reference(dest, resource_resolver, self.Source)
                source = get_resource_reference(self.Source, resource_resolver, dest)
            except ConnectorResourceError as e:
                raise InvalidResourceException(self.logical_id, str(e)) from e

            generated_resources = self.generate_resources(
                source, destination, dest_index, multi_dest, resource_resolver
            )

            self._add_connector_metadata(generated_resources, original_template, source, destination)
            list_generated_resources.extend(generated_resources)

        generated_logical_ids = [resource.logical_id for resource in list_generated_resources]
        replace_depends_on_logical_id(self.logical_id, generated_logical_ids, resource_resolver)

        if list_generated_resources:
            return list_generated_resources

        raise InvalidResourceException(self.logical_id, "'Destination' is an empty list")

    def generate_resources(  # noqa: too-many-branches
        self,
        source: ConnectorResourceReference,
        destination: ConnectorResourceReference,
        dest_index: int,
        multi_dest: bool,
        resource_resolver: ResourceResolver,
    ) -> List[Resource]:
        profile = get_profile(source.resource_type, destination.resource_type)
        if not profile:
            raise InvalidResourceException(
                self.logical_id,
                f"Unable to create connector from {source.resource_type} to {destination.resource_type}; it's not supported or the template is invalid.",
                {UNSUPPORTED_CONNECTOR_PROFILE_TYPE: {source.resource_type: destination.resource_type}},
            )

        # removing duplicate permissions
        self.Permissions = list(set(self.Permissions))
        profile_type, profile_properties = profile["Type"], profile["Properties"]
        profile_permissions = profile_properties["AccessCategories"]
        valid_permissions_combinations = profile_properties.get("ValidAccessCategories")

        valid_permissions_str = ", ".join(profile_permissions)
        if not self.Permissions:
            raise InvalidResourceException(
                self.logical_id,
                f"'Permissions' cannot be empty; valid values are: {valid_permissions_str}.",
            )

        for permission in self.Permissions:
            if permission not in profile_permissions:
                raise InvalidResourceException(
                    self.logical_id,
                    f"Unsupported 'Permissions' provided for connector from {source.resource_type} to {destination.resource_type}; valid values are: {valid_permissions_str}.",
                )

        if valid_permissions_combinations:
            sorted_permissions_combinations = [sorted(permission) for permission in valid_permissions_combinations]
            if sorted(self.Permissions) not in sorted_permissions_combinations:
                valid_permissions_combination_str = ", ".join(
                    " + ".join(permission) for permission in sorted_permissions_combinations
                )
                raise InvalidResourceException(
                    self.logical_id,
                    f"Unsupported 'Permissions' provided for connector from {source.resource_type} to {destination.resource_type}; valid combinations are: {valid_permissions_combination_str}.",
                )

        replacement = {
            "Source.Arn": source.arn,
            "Destination.Arn": destination.arn,
            "Source.ResourceId": source.resource_id,
            "Destination.ResourceId": destination.resource_id,
            "Source.Name": source.name,
            "Destination.Name": destination.name,
            "Source.Qualifier": source.qualifier,
            "Destination.Qualifier": destination.qualifier,
        }
        try:
            profile_properties = profile_replace(profile_properties, replacement)
        except ValueError as e:
            raise InvalidResourceException(self.logical_id, str(e)) from e

        verify_profile_variables_replaced(profile_properties)

        generated_resources: List[Resource] = []
        if profile_type == "AWS_IAM_ROLE_MANAGED_POLICY":
            generated_resources.append(
                self._construct_iam_policy(
                    source, destination, profile_properties, resource_resolver, dest_index, multi_dest
                )
            )
        elif profile_type == "AWS_SQS_QUEUE_POLICY":
            generated_resources.append(
                self._construct_sqs_queue_policy(source, destination, profile_properties, dest_index, multi_dest)
            )
        elif profile_type == "AWS_SNS_TOPIC_POLICY":
            generated_resources.append(
                self._construct_sns_topic_policy(source, destination, profile_properties, dest_index, multi_dest)
            )
        elif profile_type == "AWS_LAMBDA_PERMISSION":
            generated_resources.extend(
                self._construct_lambda_permission_policy(
                    source, destination, profile_properties, dest_index, multi_dest
                )
            )
        else:
            raise TypeError(f"Profile type {profile_type} is not supported")
        return generated_resources

    def _get_policy_statements(self, profile: ConnectorProfile) -> Dict[str, Any]:
        policy_statements = []
        for name, statements in profile["AccessCategories"].items():
            if name in self.Permissions:
                policy_statements.extend(statements["Statement"])

        return {
            "Version": "2012-10-17",
            "Statement": policy_statements,
        }

    def _construct_iam_policy(  # noqa: too-many-arguments
        self,
        source: ConnectorResourceReference,
        destination: ConnectorResourceReference,
        profile: ConnectorProfile,
        resource_resolver: ResourceResolver,
        dest_index: int,
        multi_dest: bool,
    ) -> IAMManagedPolicy:
        source_policy = profile["SourcePolicy"]
        resource = source if source_policy else destination

        role_name = resource.role_name
        if not role_name:
            property_name = "Source" if source_policy else "Destination"
            raise InvalidResourceException(
                self.logical_id, f"Unable to get IAM role name from '{property_name}' resource."
            )

        policy_document = self._get_policy_statements(profile)

        policy_name = f"{self.logical_id}PolicyDestination{dest_index}" if multi_dest else f"{self.logical_id}Policy"
        policy = IAMManagedPolicy(
            logical_id=policy_name, depends_on=self.depends_on, attributes=self.resource_attributes
        )

        policy.PolicyDocument = policy_document
        policy.Roles = [role_name]

        depended_by = profile.get("DependedBy")
        if depended_by == "DESTINATION_EVENT_SOURCE_MAPPING" and source.logical_id and destination.logical_id:
            # The dependency type assumes Destination is a AWS::Lambda::Function
            esm_ids = list(get_event_source_mappings(source.logical_id, destination.logical_id, resource_resolver))
            # There can only be a single ESM from a resource to function, otherwise deployment fails
            if len(esm_ids) == 1:
                add_depends_on(esm_ids[0], policy.logical_id, resource_resolver)
        if depended_by == "SOURCE" and source.logical_id:
            add_depends_on(source.logical_id, policy.logical_id, resource_resolver)

        return policy

    def _construct_lambda_permission_policy(
        self,
        source: ConnectorResourceReference,
        destination: ConnectorResourceReference,
        profile: ConnectorProfile,
        dest_index: int,
        multi_dest: bool,
    ) -> List[LambdaPermission]:
        source_policy = profile["SourcePolicy"]
        lambda_function = source if source_policy else destination

        function_arn = lambda_function.arn
        if not function_arn:
            property_name = "Source" if source_policy else "Destination"
            raise InvalidResourceException(
                self.logical_id, f"Unable to get Lambda function ARN from '{property_name}' resource."
            )

        lambda_permissions = []
        for name in profile["AccessCategories"]:
            if name in self.Permissions:
                permission_name = (
                    f"{self.logical_id}{name}LambdaPermissionDestination{dest_index}"
                    if multi_dest
                    else f"{self.logical_id}{name}LambdaPermission"
                )
                permission = LambdaPermission(
                    logical_id=permission_name,
                    depends_on=self.depends_on,
                    attributes=self.resource_attributes,
                )

                permissions = profile["AccessCategories"][name]
                permission.Action = permissions["Action"]
                permission.FunctionName = function_arn
                permission.Principal = permissions["Principal"]
                permission.SourceArn = permissions["SourceArn"]
                permission.SourceAccount = permissions.get("SourceAccount")
                lambda_permissions.append(permission)

        return lambda_permissions

    def _construct_sns_topic_policy(
        self,
        source: ConnectorResourceReference,
        destination: ConnectorResourceReference,
        profile: ConnectorProfile,
        dest_index: int,
        multi_dest: bool,
    ) -> SNSTopicPolicy:
        source_policy = profile["SourcePolicy"]
        sns_topic = source if source_policy else destination

        topic_arn = sns_topic.arn
        if not topic_arn:
            property_name = "Source" if source_policy else "Destination"
            raise InvalidResourceException(
                self.logical_id, f"Unable to get SNS topic ARN from '{property_name}' resource."
            )

        topic_policy_name = (
            f"{self.logical_id}TopicPolicyDestination{dest_index}" if multi_dest else f"{self.logical_id}TopicPolicy"
        )
        topic_policy = SNSTopicPolicy(
            logical_id=topic_policy_name, depends_on=self.depends_on, attributes=self.resource_attributes
        )

        topic_policy.Topics = [topic_arn]
        topic_policy.PolicyDocument = self._get_policy_statements(profile)

        return topic_policy

    def _construct_sqs_queue_policy(
        self,
        source: ConnectorResourceReference,
        destination: ConnectorResourceReference,
        profile: ConnectorProfile,
        dest_index: int,
        multi_dest: bool,
    ) -> SQSQueuePolicy:
        source_policy = profile["SourcePolicy"]
        sqs_queue = source if source_policy else destination

        queue_url = sqs_queue.queue_url
        if not queue_url:
            property_name = "Source" if source_policy else "Destination"
            raise InvalidResourceException(
                self.logical_id, f"Unable to get SQS queue URL from '{property_name}' resource."
            )

        queue_policy_name = (
            f"{self.logical_id}QueuePolicyDestination{dest_index}" if multi_dest else f"{self.logical_id}QueuePolicy"
        )
        queue_policy = SQSQueuePolicy(
            logical_id=queue_policy_name, depends_on=self.depends_on, attributes=self.resource_attributes
        )

        queue_policy.PolicyDocument = self._get_policy_statements(profile)
        queue_policy.Queues = [queue_url]

        return queue_policy

    def _add_connector_metadata(
        self,
        generated_resources: List[Resource],
        original_template: Dict[str, Any],
        source: ConnectorResourceReference,
        destination: ConnectorResourceReference,
    ) -> None:
        """
        Add metadata attribute to generated resources.

        Metadata:
          aws:sam:connectors:
            <connector-logical-id>:
              Source:
                Type: <source-type>
              Destination:
                Type: <destination-type>
        """
        original_resources = original_template.get("Resources", {})
        original_source_type = original_resources.get(source.logical_id, {}).get("Type")
        original_dest_type = original_resources.get(destination.logical_id, {}).get("Type")
        metadata = {
            "aws:sam:connectors": {
                self.logical_id: {
                    # If the source/destination is a serverless resource,
                    # we prefer to include the original serverless resource type
                    # over the transformed CFN resource type so it can distinguish
                    # connector usage between serverless resources and CFN resources.
                    "Source": {"Type": original_source_type or source.resource_type},
                    "Destination": {"Type": original_dest_type or destination.resource_type},
                }
            }
        }
        for resource in generated_resources:
            # Although as today the generated resources do not have any existing metadata,
            # To make it future proof, we still does a merge to avoid overwriting.
            try:
                original_metadata = resource.get_resource_attribute("Metadata")
            except KeyError:
                original_metadata = {}
            resource.set_resource_attribute("Metadata", {**original_metadata, **metadata})


class SamGraphQLApi(SamResourceMacro):
    """SAM GraphQL API Macro (WIP)."""

    resource_type = "AWS::Serverless::GraphQLApi"
    property_types = {
        "Name": Property(False, IS_STR),
        "Tags": Property(False, IS_DICT),
        "XrayEnabled": PassThroughProperty(False),
        "Auth": Property(True, IS_DICT),
        "SchemaInline": Property(False, IS_STR),
        "SchemaUri": Property(False, IS_STR),
        "Logging": Property(False, one_of(IS_DICT, IS_BOOL)),
        "DataSources": Property(False, IS_DICT),
        "Functions": Property(False, IS_DICT),
        "Resolvers": Property(False, IS_DICT),
        "ApiKeys": Property(False, IS_DICT),
        "DomainName": Property(False, IS_DICT),
        "Cache": Property(False, IS_DICT),
    }

    Auth: List[Dict[str, Any]]
    Tags: Optional[Dict[str, Any]]
    XrayEnabled: Optional[PassThrough]
    Name: Optional[str]
    SchemaInline: Optional[str]
    SchemaUri: Optional[str]
    Logging: Optional[Union[Dict[str, Any], bool]]
    DataSources: Optional[Dict[str, Dict[str, Dict[str, Any]]]]
    Functions: Optional[Dict[str, Dict[str, Any]]]
    Resolvers: Optional[Dict[str, Dict[str, Dict[str, Any]]]]
    ApiKeys: Optional[Dict[str, Dict[str, Any]]]
    DomainName: Optional[Dict[str, Any]]
    Cache: Optional[Dict[str, Any]]

    # stop validation so we can use class variables for tracking state
    validate_setattr = False

    def __init__(
        self,
        logical_id: Optional[Any],
        relative_id: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(logical_id, relative_id=relative_id, depends_on=depends_on, attributes=attributes)

        self._none_datasource: Optional[DataSource] = None
        self._datasource_name_map: Dict[str, Intrinsicable[str]] = {}
        self._function_id_map: Dict[str, Intrinsicable[str]] = {}

    @cw_timer
    def to_cloudformation(self, **kwargs: Any) -> List[Resource]:
        model = self.validate_properties_and_return_model(aws_serverless_graphqlapi.Properties)

        appsync_api, cloudwatch_role, auth_connectors = self._construct_appsync_api_resources(model)
        api_id = appsync_api.get_runtime_attr("api_id")
        appsync_schema = self._construct_appsync_schema(model, api_id)

        resources: List[Resource] = [appsync_api, appsync_schema]

        for connector in auth_connectors:
            resources.extend(connector.to_cloudformation(**kwargs))

        if cloudwatch_role:
            resources.append(cloudwatch_role)

        if model.ApiKeys:
            api_keys = self._construct_appsync_api_keys(model.ApiKeys, api_id)
            resources.extend(api_keys)

        if model.Cache:
            api_cache = self._construct_appsync_api_cache(model.Cache, api_id)
            resources.append(api_cache)

        if model.DataSources:
            datasource_resources = self._construct_datasource_resources(model.DataSources, api_id, kwargs)
            resources.extend(datasource_resources)

        if model.DomainName:
            domain_name_resources = self._construct_domain_name_resources(model.DomainName, api_id)
            resources.extend(domain_name_resources)

        if model.Functions:
            function_configurations = self._construct_appsync_function_configurations(model.Functions, api_id)
            resources.extend(function_configurations)

        if model.Resolvers:
            appsync_resolver_resources = self._construct_appsync_resolver_resources(
                model.Resolvers, api_id, appsync_schema.logical_id
            )
            resources.extend(appsync_resolver_resources)

        if self._none_datasource:
            resources.append(self._none_datasource)

        return resources

    def _construct_appsync_api_resources(
        self, model: aws_serverless_graphqlapi.Properties
    ) -> Tuple[GraphQLApi, Optional[IAMRole], List[SamConnector]]:
        api = GraphQLApi(logical_id=self.logical_id, depends_on=self.depends_on, attributes=self.resource_attributes)

        api.Name = model.Name or self.logical_id
        api.XrayEnabled = model.XrayEnabled

        lambda_auth_arns = self._parse_and_set_auth_properties(api, model.Auth)
        auth_connectors = [
            self._construct_lambda_auth_connector(api, arn, i) for i, arn in enumerate(lambda_auth_arns, 1)
        ]

        if model.Tags:
            api.Tags = get_tag_list(model.Tags)

        # Logging has 3 possible types: dict, bool, and None.
        # GraphQLApi will not include logging if and only if the user explicity sets Logging as false boolean.
        # It will for every other value (including true boolean which is essentially same as None).
        if isinstance(model.Logging, bool) and model.Logging is False:
            return api, None, auth_connectors

        api.LogConfig, cloudwatch_role = self._parse_logging_properties(model)

        return api, cloudwatch_role, auth_connectors

    def _parse_and_set_auth_properties(
        self, api: GraphQLApi, auth: aws_serverless_graphqlapi.Auth
    ) -> List[Intrinsicable[str]]:
        """
        Parse the Auth properties in a Serverless::GraphQLApi resource.

        Returns: List of Lambda Function arns of Lambda authorizers. If no Lambda authorizer is used, the list is empty.
        """
        # Keep all lambda authorizers together to create connectors later
        lambda_auth_arns: List[Intrinsicable[str]] = []

        # Default authoriser
        default_auth = aws_serverless_graphqlapi.Authorizer.parse_obj(
            {k: v for k, v in auth.dict().items() if k != "Additional"}
        )
        name, auth_dict = self._validate_and_extract_authorizer_config(default_auth)
        api.AuthenticationType = auth.Type

        # This would be much easier and type-safe if accessing the properties in Resource
        # was a dictionary. Currently, top level properties are class attributes, but nested
        # properties are dictionaries...
        # TODO: Access properties in Resource class as dict?
        if name and auth_dict:
            setattr(api, name, auth_dict)
            if name == "LambdaAuthorizerConfig":
                lambda_auth_arns.append(cast(LambdaAuthorizerConfigType, auth_dict)["AuthorizerUri"])

        # Additional authentication
        additional_auths: List[AdditionalAuthenticationProviderType] = []
        if auth.Additional:
            for index, additional in enumerate(auth.Additional):
                name, auth_dict = self._validate_and_extract_authorizer_config(additional, index)
                additional_auth: AdditionalAuthenticationProviderType = {"AuthenticationType": additional.Type}
                if name and auth_dict:
                    additional_auth[name] = auth_dict
                    if name == "LambdaAuthorizerConfig":
                        lambda_auth_arns.append(cast(LambdaAuthorizerConfigType, auth_dict)["AuthorizerUri"])

                additional_auths.append(additional_auth)

        if additional_auths:
            api.AdditionalAuthenticationProviders = additional_auths

        return lambda_auth_arns

    def _validate_and_extract_authorizer_config(
        self,
        auth: aws_serverless_graphqlapi.Authorizer,
        index: Optional[int] = None,
    ) -> Tuple[
        Optional[Literal["LambdaAuthorizerConfig", "OpenIDConnectConfig", "UserPoolConfig"]],
        Optional[Union[LambdaAuthorizerConfigType, OpenIDConnectConfigType, UserPoolConfigType]],
    ]:
        """
        Validates the authentication type and returns the name of the config property and the respective dictionary.

        The index parameter is only required if you are validating an AdditionalAuth, so that we can correctly
        format the key path for any errors that are thrown. It is not necessary for Auth.
        """
        # In each Auth index, you should only define a max of two properties. The "Type" property, and if
        # necessary the associated config as well.
        MAX_AUTH_PROPERTIES = 2

        keys = remove_none_values(auth.dict()).keys()
        if len(keys) > MAX_AUTH_PROPERTIES:
            key_path = "'Auth'" if not index else f"'Auth.Additional.{index}'"
            raise InvalidResourceException(
                self.logical_id, f"{key_path} has more than one authentication configuration defined."
            )

        if auth.Type == "AWS_LAMBDA":
            key_path = "Auth.LambdaAuthorizer" if not index else f"Auth.Additional.{index}.LambdaAuthorizer"
            lambda_authorizer = sam_expect(auth.LambdaAuthorizer, self.logical_id, key_path).to_not_be_none(
                "'LambdaAuthorizer' must be defined if type is 'AWS_LAMBDA'."
            )
            return "LambdaAuthorizerConfig", cast(
                LambdaAuthorizerConfigType, remove_none_values(lambda_authorizer.dict())
            )

        if auth.Type == "OPENID_CONNECT":
            key_path = "Auth.OpenIDConnect" if not index else f"Auth.Additional.{index}.OpenIDConnect"
            openid_connect = sam_expect(auth.OpenIDConnect, self.logical_id, key_path).to_not_be_none(
                "'OpenIDConnect' must be defined if type is 'OPENID_CONNECT'."
            )
            return "OpenIDConnectConfig", cast(OpenIDConnectConfigType, remove_none_values(openid_connect.dict()))

        # Last possible type is "AMAZON_COGNITO_USER_POOLS"
        if auth.Type == "AMAZON_COGNITO_USER_POOLS":
            key_path = "Auth.UserPool" if not index else f"Auth.Additional.{index}.UserPool"
            user_pool = sam_expect(auth.UserPool, self.logical_id, key_path).to_not_be_none(
                "'UserPool' must be defined if type is 'AMAZON_COGNITO_USER_POOLS'."
            )
            if index is not None:
                # UserPoolConfig does not have the DefaultAction property UNLESS it is the primary authentication
                # method (first index). If it is an additional authentication, we nullify this value.
                user_pool.DefaultAction = None
            return "UserPoolConfig", cast(UserPoolConfigType, remove_none_values(user_pool.dict()))

        return None, None

    @staticmethod
    def _construct_lambda_auth_connector(
        api: GraphQLApi,
        lambda_arn: Intrinsicable[str],
        auth_number: int,
    ) -> SamConnector:
        logical_id = f"{api.logical_id}ToLambdaAuthConnector{auth_number}"
        connector_dict = {
            "Type": "AWS::Serverless::Connector",
            "Properties": {
                "Source": {
                    "Type": "AWS::AppSync::GraphQLApi",
                    "Arn": ref(api.logical_id),
                    "ResourceId": fnGetAtt(api.logical_id, "ApiId"),
                },
                "Destination": {
                    "Type": "AWS::Lambda::Function",
                    "Arn": lambda_arn,
                },
                "Permissions": ["Write"],
            },
        }

        # mypy thinks from_dict method returns "Resource" class instead of the inheriting parent class "SamResourceMacro"
        return cast(
            SamConnector,
            SamConnector(logical_id=logical_id).from_dict(logical_id=logical_id, resource_dict=connector_dict),
        )

    def _create_logging_default(self) -> Tuple[LogConfigType, IAMRole]:
        """
        Create a default logging configuration.

        This function is used when "Logging" property is a False boolean or NoneType.
        """
        log_config: LogConfigType = {}
        log_config["FieldLogLevel"] = "ALL"
        cloudwatch_role = self._construct_cloudwatch_role()
        log_config["CloudWatchLogsRoleArn"] = cloudwatch_role.get_runtime_attr("arn")

        return log_config, cloudwatch_role

    def _parse_logging_properties(
        self, model: aws_serverless_graphqlapi.Properties
    ) -> Tuple[LogConfigType, Optional[IAMRole]]:
        """Parse logging properties from SAM template, and use defaults if required keys dont exist."""
        if not isinstance(model.Logging, aws_serverless_graphqlapi.Logging):
            return self._create_logging_default()

        log_config: LogConfigType = {}

        if model.Logging.ExcludeVerboseContent:
            log_config["ExcludeVerboseContent"] = cast(PassThrough, model.Logging.ExcludeVerboseContent)

        log_config["FieldLogLevel"] = model.Logging.FieldLogLevel or "ALL"
        log_config["CloudWatchLogsRoleArn"] = cast(PassThrough, model.Logging.CloudWatchLogsRoleArn)

        if log_config["CloudWatchLogsRoleArn"]:
            return log_config, None

        cloudwatch_role = self._construct_cloudwatch_role()
        log_config["CloudWatchLogsRoleArn"] = cloudwatch_role.get_runtime_attr("arn")

        return log_config, cloudwatch_role

    def _construct_cloudwatch_role(self) -> IAMRole:
        role = IAMRole(
            logical_id=f"{self.logical_id}CloudWatchRole",
            depends_on=self.depends_on,
            attributes=self.resource_attributes,
        )
        role.AssumeRolePolicyDocument = IAMRolePolicies.construct_assume_role_policy_for_service_principal(
            "appsync.amazonaws.com"
        )
        role.ManagedPolicyArns = [
            {"Fn::Sub": "arn:${AWS::Partition}:iam::aws:policy/service-role/AWSAppSyncPushToCloudWatchLogs"}
        ]
        return role

    def _construct_appsync_schema(
        self, model: aws_serverless_graphqlapi.Properties, api_id: Intrinsicable[str]
    ) -> GraphQLSchema:
        schema = GraphQLSchema(
            logical_id=f"{self.logical_id}Schema", depends_on=self.depends_on, attributes=self.resource_attributes
        )

        if not model.SchemaInline and not model.SchemaUri:
            raise InvalidResourceException(self.logical_id, "One of 'SchemaInline' or 'SchemaUri' must be set.")

        if model.SchemaInline and model.SchemaUri:
            raise InvalidResourceException(
                self.logical_id, "Both 'SchemaInline' and 'SchemaUri' cannot be defined at the same time."
            )

        schema.ApiId = api_id
        schema.Definition = passthrough_value(model.SchemaInline)
        schema.DefinitionS3Location = passthrough_value(model.SchemaUri)

        return schema

    def _construct_appsync_api_keys(
        self, api_keys: Dict[str, aws_serverless_graphqlapi.ApiKey], api_id: Intrinsicable[str]
    ) -> List[Resource]:
        resources: List[Resource] = []

        # TODO: Add datetime parsing for ExpiresOn; currently expects Unix timestamp
        for relative_id, api_key in api_keys.items():
            cfn_api_key = ApiKey(
                logical_id=f"{self.logical_id}{relative_id}",
                depends_on=self.depends_on,
                attributes=self.resource_attributes,
            )
            cfn_api_key.ApiId = api_id
            cfn_api_key.ApiKeyId = passthrough_value(api_key.ApiKeyId)
            cfn_api_key.Description = passthrough_value(api_key.Description)
            cfn_api_key.Expires = passthrough_value(api_key.ExpiresOn)
            resources.append(cfn_api_key)

        return resources

    def _construct_domain_name_resources(
        self, domain_name: aws_serverless_graphqlapi.DomainName, api_id: Intrinsicable[str]
    ) -> List[Resource]:
        cfn_domain_name = DomainName(
            logical_id=f"{self.logical_id}DomainName", depends_on=self.depends_on, attributes=self.resource_attributes
        )
        cfn_domain_name.CertificateArn = passthrough_value(domain_name.CertificateArn)
        cfn_domain_name.DomainName = passthrough_value(domain_name.DomainName)
        cfn_domain_name.Description = passthrough_value(domain_name.Description)

        cfn_domain_name_api_association = DomainNameApiAssociation(
            logical_id=f"{self.logical_id}DomainNameApiAssociation",
            depends_on=self.depends_on,
            attributes=self.resource_attributes,
        )
        cfn_domain_name_api_association.ApiId = api_id
        cfn_domain_name_api_association.DomainName = cfn_domain_name.get_runtime_attr("domain_name")

        return [cfn_domain_name, cfn_domain_name_api_association]

    def _construct_appsync_api_cache(
        self, cache: aws_serverless_graphqlapi.Cache, api_id: Intrinsicable[str]
    ) -> ApiCache:
        cfn_api_cache = ApiCache(
            logical_id=f"{self.logical_id}ApiCache", depends_on=self.depends_on, attributes=self.resource_attributes
        )

        cfn_api_cache.ApiId = api_id
        cfn_api_cache.ApiCachingBehavior = passthrough_value(cache.ApiCachingBehavior)
        cfn_api_cache.Type = passthrough_value(cache.Type)
        cfn_api_cache.Ttl = passthrough_value(cache.Ttl)
        cfn_api_cache.AtRestEncryptionEnabled = passthrough_value(cache.AtRestEncryptionEnabled)
        cfn_api_cache.TransitEncryptionEnabled = passthrough_value(cache.TransitEncryptionEnabled)

        return cfn_api_cache

    def _construct_datasource_resources(
        self,
        datasources: aws_serverless_graphqlapi.DataSources,
        api_id: Intrinsicable[str],
        kwargs: Dict[str, Any],
    ) -> List[Resource]:
        ddb_datasources = self._construct_ddb_datasources(datasources.DynamoDb, api_id, kwargs)
        lambda_datasources = self._construct_lambda_datasources(datasources.Lambda, api_id, kwargs)

        return [*ddb_datasources, *lambda_datasources]

    def _construct_ddb_datasources(
        self,
        ddb_datasources: Optional[Dict[str, aws_serverless_graphqlapi.DynamoDBDataSource]],
        api_id: Intrinsicable[str],
        kwargs: Dict[str, Any],
    ) -> List[Resource]:
        if not ddb_datasources:
            return []

        resources: List[Resource] = []

        for relative_id, ddb_datasource in ddb_datasources.items():
            datasource_logical_id = self._create_appsync_data_source_logical_id(
                self.logical_id, "DynamoDB", relative_id
            )
            cfn_datasource = DataSource(
                logical_id=datasource_logical_id, depends_on=self.depends_on, attributes=self.resource_attributes
            )

            # Datasource "Name" property must be unique from all other datasources.
            cfn_datasource.Name = ddb_datasource.Name or relative_id
            cfn_datasource.Type = "AMAZON_DYNAMODB"
            cfn_datasource.ApiId = api_id
            cfn_datasource.Description = passthrough_value(ddb_datasource.Description)
            cfn_datasource.DynamoDBConfig = self._parse_ddb_config(ddb_datasource)

            cfn_datasource.ServiceRoleArn, permissions_resources = self._parse_ddb_datasource_role(
                ddb_datasource, cfn_datasource.get_runtime_attr("arn"), relative_id, datasource_logical_id, kwargs
            )

            self._datasource_name_map[relative_id] = cfn_datasource.get_runtime_attr("name")

            resources.extend([cfn_datasource, *permissions_resources])

        return resources

    def _parse_ddb_datasource_role(
        self,
        ddb_datasource: aws_serverless_graphqlapi.DynamoDBDataSource,
        datasource_arn: Intrinsicable[str],
        relative_id: str,
        datasource_logical_id: str,
        kwargs: Dict[str, Any],
    ) -> Tuple[str, List[Resource]]:
        # If the user defined a role, then there's no need to generate role/policy for them, so we return fast.
        if ddb_datasource.ServiceRoleArn:
            return cast(PassThrough, ddb_datasource.ServiceRoleArn), []

        # If the user doesn't have their own role, then we will create for them if TableArn is defined.
        table_arn = passthrough_value(
            sam_expect(
                ddb_datasource.TableArn, relative_id, f"DataSources.DynamoDb.{relative_id}.TableArn"
            ).to_not_be_none(
                "'TableArn' must be defined to create the role and policy if 'ServiceRoleArn' is not defined."
            )
        )

        permissions = ddb_datasource.Permissions or ["Read", "Write"]

        role_id = f"{datasource_logical_id}Role"
        role = IAMRole(
            logical_id=role_id,
            depends_on=self.depends_on,
            attributes=self.resource_attributes,
        )
        role.AssumeRolePolicyDocument = IAMRolePolicies.construct_assume_role_policy_for_service_principal(
            "appsync.amazonaws.com"
        )
        role_arn = role.get_runtime_attr("arn")

        connector_resources = self._construct_ddb_datasource_connector_resources(
            datasource_logical_id, datasource_arn, table_arn, permissions, role.get_runtime_attr("name"), kwargs
        )

        return role_arn, [role, *connector_resources]

    def _parse_ddb_config(self, ddb_datasource: aws_serverless_graphqlapi.DynamoDBDataSource) -> DynamoDBConfigType:
        ddb_config: DynamoDBConfigType = {}

        ddb_config["AwsRegion"] = cast(PassThrough, ddb_datasource.Region) or ref("AWS::Region")
        ddb_config["TableName"] = passthrough_value(ddb_datasource.TableName)

        if ddb_datasource.UseCallerCredentials:
            ddb_config["UseCallerCredentials"] = cast(PassThrough, ddb_datasource.UseCallerCredentials)

        if ddb_datasource.Versioned:
            ddb_config["Versioned"] = cast(PassThrough, ddb_datasource.Versioned)

        if ddb_datasource.DeltaSync:
            deltasync_properties = ddb_datasource.DeltaSync.dict()
            ddb_config["DeltaSyncConfig"] = cast(PassThrough, deltasync_properties)

        return ddb_config

    @staticmethod
    def _construct_ddb_datasource_connector_resources(
        datasource_id: str,
        source_arn: Intrinsicable[str],
        destination_arn: str,
        permissions: PermissionsType,
        role_name: Intrinsicable[str],
        kwargs: Dict[str, Any],
    ) -> List[Resource]:
        logical_id = f"{datasource_id}ToTableConnector"
        connector_dict = {
            "Type": "AWS::Serverless::Connector",
            "Properties": {
                "Source": {"Type": "AWS::AppSync::DataSource", "Arn": source_arn, "RoleName": role_name},
                "Destination": {
                    "Type": "AWS::DynamoDB::Table",
                    "Arn": destination_arn,
                },
                "Permissions": permissions,
            },
        }

        # mypy thinks from_dict method returns "Resource" class instead of the inheriting parent class "SamResourceMacro"
        connector = cast(
            SamConnector,
            SamConnector(logical_id=logical_id).from_dict(logical_id=logical_id, resource_dict=connector_dict),
        )
        return connector.to_cloudformation(**kwargs)

    def _construct_lambda_datasources(
        self,
        lambda_datasources: Optional[Dict[str, aws_serverless_graphqlapi.LambdaDataSource]],
        api_id: Intrinsicable[str],
        kwargs: Dict[str, Any],
    ) -> List[Resource]:
        if not lambda_datasources:
            return []

        resources: List[Resource] = []

        for relative_id, lambda_datasource in lambda_datasources.items():
            datasource_logical_id = self._create_appsync_data_source_logical_id(self.logical_id, "Lambda", relative_id)
            cfn_datasource = DataSource(
                logical_id=datasource_logical_id, depends_on=self.depends_on, attributes=self.resource_attributes
            )

            cfn_datasource.Name = lambda_datasource.Name or relative_id
            cfn_datasource.Type = "AWS_LAMBDA"
            cfn_datasource.ApiId = api_id
            cfn_datasource.Description = passthrough_value(lambda_datasource.Description)
            cfn_datasource.LambdaConfig = {"LambdaFunctionArn": passthrough_value(lambda_datasource.FunctionArn)}

            cfn_datasource.ServiceRoleArn, permissions_resources = self._parse_lambda_datasource_role(
                lambda_datasource,
                cfn_datasource.get_runtime_attr("arn"),
                lambda_datasource.FunctionArn,
                datasource_logical_id,
                kwargs,
            )

            self._datasource_name_map[relative_id] = cfn_datasource.get_runtime_attr("name")

            resources.extend([cfn_datasource, *permissions_resources])

        return resources

    def _parse_lambda_datasource_role(
        self,
        lambda_datasource: aws_serverless_graphqlapi.LambdaDataSource,
        datasource_arn: Intrinsicable[str],
        function_arn: PassThrough,
        datasource_logical_id: str,
        kwargs: Dict[str, Any],
    ) -> Tuple[str, List[Resource]]:
        if lambda_datasource.ServiceRoleArn:
            return passthrough_value(lambda_datasource.ServiceRoleArn), []

        role_logical_id = f"{datasource_logical_id}Role"
        role = IAMRole(
            logical_id=role_logical_id,
            depends_on=self.depends_on,
            attributes=self.resource_attributes,
        )
        role.AssumeRolePolicyDocument = IAMRolePolicies.construct_assume_role_policy_for_service_principal(
            "appsync.amazonaws.com"
        )
        role_arn = role.get_runtime_attr("arn")

        connector_resources = self._construct_lambda_datasource_connector_resources(
            datasource_logical_id, datasource_arn, function_arn, role.get_runtime_attr("name"), kwargs
        )

        return role_arn, [role, *connector_resources]

    @staticmethod
    def _construct_lambda_datasource_connector_resources(
        datasource_id: str,
        source_arn: Intrinsicable[str],
        destination_arn: Intrinsicable[str],
        role_name: Intrinsicable[str],
        kwargs: Dict[str, Any],
    ) -> List[Resource]:
        logical_id = f"{datasource_id}ToLambdaConnector"
        connector_dict = {
            "Type": "AWS::Serverless::Connector",
            "Properties": {
                "Source": {"Type": "AWS::AppSync::DataSource", "Arn": source_arn, "RoleName": role_name},
                "Destination": {
                    "Type": "AWS::Lambda::Function",
                    "Arn": destination_arn,
                },
                "Permissions": ["Write"],
            },
        }

        # mypy thinks from_dict method returns "Resource" class instead of the inheriting parent class "SamResourceMacro"
        connector = cast(
            SamConnector,
            SamConnector(logical_id=logical_id).from_dict(logical_id=logical_id, resource_dict=connector_dict),
        )

        return connector.to_cloudformation(**kwargs)

    def _construct_appsync_function_configurations(
        self,
        functions: Dict[str, aws_serverless_graphqlapi.Function],
        api_id: Intrinsicable[str],
    ) -> List[FunctionConfiguration]:
        func_configs: List[FunctionConfiguration] = []

        for relative_id, function in functions.items():
            # "Id" refers to the "FunctionId" attribute for a "AppSync::FunctionConfiguration" resource.
            # "Id" is a mutually exclusive property to every other property. If this function has it
            # defined, then we make sure it's the only property, and continue to next function.
            if function.Id:
                keys = remove_none_values(function.dict()).keys()  # remove undefined properties, then get keys
                if len(keys) != 1:
                    raise InvalidResourceException(
                        relative_id, "'Id' cannot be defined with other properties in Function."
                    )
                self._function_id_map[relative_id] = passthrough_value(function.Id)
                continue

            func_config = FunctionConfiguration(
                logical_id=self.logical_id + relative_id,
                depends_on=self.depends_on,
                attributes=self.resource_attributes,
            )

            func_config.ApiId = api_id
            func_config.Name = function.Name or relative_id
            func_config.Code, func_config.CodeS3Location = self._parse_function_code_properties(function, relative_id)
            func_config.DataSourceName = self._parse_datasource_name(relative_id, function, api_id)
            func_config.MaxBatchSize = passthrough_value(function.MaxBatchSize)
            func_config.Description = passthrough_value(function.Description)
            func_config.Runtime = self._parse_runtime(function, relative_id)

            if function.Sync:
                func_config.SyncConfig = cast(SyncConfigType, remove_none_values(function.Sync.dict()))

            self._function_id_map[relative_id] = func_config.get_runtime_attr("function_id")
            func_configs.append(func_config)

        return func_configs

    @staticmethod
    def _is_none_datasource_input(datasource: Optional[str]) -> bool:
        return datasource is not None and datasource.lower() == "none"

    def _construct_none_datasource(
        self,
        api_id: Intrinsicable[str],
    ) -> DataSource:
        """
        Create DataSource with type "NONE".

        Within a Serverless::GraphQLApi Function or Resolver resource, customers can create
        a DataSource of Type "NONE" for quick use. To do so, a customer can input "none" case
        insensitive in the "DataSource" property. Only one DataSource will be created for each
        GraphQLApi, and all GraphQLApi functions and resolvers with this none input will reference it.

        If a datasource is created, it is assigned to the class variable "none_datasource". This is so
        we can reference when parsing both functions and resolvers. This function does not return any
        value itself.
        """
        none_datasource_logical_id = f"{self.logical_id}NoneDataSource"
        none_datasource = DataSource(
            logical_id=none_datasource_logical_id, depends_on=self.depends_on, attributes=self.resource_attributes
        )
        none_datasource.ApiId = api_id
        none_datasource.Name = none_datasource_logical_id
        none_datasource.Type = "NONE"

        return none_datasource

    def _parse_datasource_name(
        self, relative_id: str, function: aws_serverless_graphqlapi.Function, api_id: Intrinsicable[str]
    ) -> Intrinsicable[str]:
        """
        Parse DataSource name from a Serverless::GraphQLApi function or resolver.

        There are 3 different cases for the DataSource name:

        1. Customer defines the "DataSource" property as a string or intrinsics, and we can simply return this value.

        2. Customer defines "DataSource" propery as "NONE", so we return the name of the NoneDataSource
           for this Serverless::GraphQLApi resource.

        3. Customer defines "DataSource" property with a logical id of a datasource defined in
           Serverless::GraphQLApi. We can then search if this DataSource exists, and return the name.
           If it does not exist, throw an InvalidResourceException.
        """
        if not function.DataSource:
            raise InvalidResourceException(relative_id, "'DataSource' must be set.")

        if isinstance(function.DataSource, str):
            if self._is_none_datasource_input(function.DataSource):
                if not self._none_datasource:
                    self._none_datasource = self._construct_none_datasource(api_id)
                return cast(Intrinsicable[str], self._none_datasource.get_runtime_attr("name"))

            if function.DataSource in self._datasource_name_map:
                return self._datasource_name_map[function.DataSource]

            raise InvalidResourceException(
                relative_id,
                f"Either define DataSource '{function.DataSource}' in 'DataSources' or use intrinsic function like GetAtt, ImportValue, Sub or another one to reference a DataSource defined outside of this GraphQLApi resource.",
            )

        # if DataSource is intrinsic function like !GetAttr AppSyncDataSource.Name
        # but it can also be ImportValue or Sub or maybe something else
        return function.DataSource  # it's an intrinsic function Dict here

    @staticmethod
    def _parse_function_code_properties(
        function: aws_serverless_graphqlapi.Function,
        relative_id: str,
    ) -> Tuple[Optional[PassThrough], Optional[PassThrough]]:
        """
        Parses the code properties from Serverless::GraphQLApi function.

        This function parses the "CodeUri" and "InlineCode" properties for Function resources.
        It also raises exceptions when the customer template is invalid. The return is a tuple of the values
        (InlineCode, CodeUri).
        """
        if function.InlineCode and function.CodeUri:
            raise InvalidResourceException(
                relative_id, "Both 'InlineCode' and 'CodeUri' cannot be defined at the same time."
            )

        if function.InlineCode:
            return passthrough_value(function.InlineCode), None

        if function.CodeUri:
            return None, passthrough_value(function.CodeUri)

        raise InvalidResourceException(relative_id, "One of 'InlineCode' or 'CodeUri' must be set.")

    @staticmethod
    def _parse_runtime(
        resource: Union[aws_serverless_graphqlapi.Function, aws_serverless_graphqlapi.Resolver],
        relative_id: str,
    ) -> AppSyncRuntimeType:
        """
        Parse Runtime property of Function and Resolver.
        """
        if resource.Runtime:
            return {
                "Name": passthrough_value(resource.Runtime.Name),
                "RuntimeVersion": passthrough_value(resource.Runtime.Version),
            }

        # Runtime is not defined, raise error.
        raise InvalidResourceException(relative_id, f"'Runtime' must be defined as a property in {relative_id}.")

    def _construct_appsync_resolver_resources(
        self,
        resolvers: Dict[str, Dict[str, aws_serverless_graphqlapi.Resolver]],
        api_id: Intrinsicable[str],
        schema_logical_id: str,
    ) -> List[Resource]:
        resources: List[Resource] = []

        for type_name, relative_id_to_resolver in resolvers.items():
            for relative_id, resolver in relative_id_to_resolver.items():
                cfn_resolver = Resolver(
                    logical_id=self.logical_id + type_name + relative_id,
                    depends_on=[schema_logical_id],
                    attributes=self.resource_attributes,
                )

                if resolver.CodeUri and resolver.InlineCode:
                    raise InvalidResourceException(
                        relative_id, "Both 'InlineCode' and 'CodeUri' cannot be defined at the same time."
                    )

                cfn_resolver.Code = passthrough_value(resolver.InlineCode)
                cfn_resolver.CodeS3Location = passthrough_value(resolver.CodeUri)

                # If InlineCode and CodeUri were not defined, then we will set the resolver code
                # to a default snippet which has basic definition of request/response functions.
                if not cfn_resolver.Code and not cfn_resolver.CodeS3Location:
                    cfn_resolver.Code = APPSYNC_PIPELINE_RESOLVER_JS_CODE

                cfn_resolver.ApiId = api_id
                cfn_resolver.FieldName = resolver.FieldName or relative_id
                cfn_resolver.TypeName = type_name
                cfn_resolver.Runtime = self._parse_runtime(resolver, relative_id)

                if resolver.Pipeline:
                    cfn_resolver.Kind = "PIPELINE"
                    function_ids = self._parse_appsync_resolver_functions(resolver, relative_id)
                    cfn_resolver.PipelineConfig = {"Functions": function_ids}
                else:
                    raise InvalidResourceException(
                        relative_id,
                        f"Resolver '{relative_id}' must have Pipeline defined. Unit resolvers are not supported. If you need a Unit resolver you can use AppSync resource.",
                    )

                if resolver.Caching:
                    cfn_resolver.CachingConfig = cast(CachingConfigType, resolver.Caching.dict(exclude_none=True))

                if resolver.MaxBatchSize:
                    cfn_resolver.MaxBatchSize = passthrough_value(resolver.MaxBatchSize)

                resources.append(cfn_resolver)

        return resources

    def _parse_appsync_resolver_functions(
        self, appsync_resolver: aws_serverless_graphqlapi.Resolver, relative_id: str
    ) -> List[Intrinsicable[str]]:
        """
        Parse functions property in GraphQLApi Resolver.

        When a resolver has the functions property defined, it is a pipeline resolver. These functions are
        executed in the order they are listed in the template.
        """
        function_ids = []

        # This function is only called if it is a pipeline resolver, in which case this property is checked to exist before.
        # Because the type of the variable does not update, we must cast here.

        for resolver_function in appsync_resolver.Pipeline or []:
            if resolver_function not in self._function_id_map:
                raise InvalidResourceException(relative_id, f"Function '{resolver_function}' does not exist.")
            function_ids.append(self._function_id_map[resolver_function])

        return function_ids

    @staticmethod
    def _create_appsync_data_source_logical_id(api_id: str, data_source_type: str, data_source_relative_id: str) -> str:
        return f"{api_id}{data_source_relative_id}{data_source_type}DataSource"
