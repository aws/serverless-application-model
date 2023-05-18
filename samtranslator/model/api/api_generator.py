import logging
from collections import namedtuple
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.model import Resource
from samtranslator.model.apigateway import (
    ApiGatewayApiKey,
    ApiGatewayAuthorizer,
    ApiGatewayBasePathMapping,
    ApiGatewayDeployment,
    ApiGatewayDomainName,
    ApiGatewayResponse,
    ApiGatewayRestApi,
    ApiGatewayStage,
    ApiGatewayUsagePlan,
    ApiGatewayUsagePlanKey,
)
from samtranslator.model.exceptions import (
    ExpectedType,
    InvalidDocumentException,
    InvalidResourceException,
    InvalidTemplateException,
)
from samtranslator.model.intrinsics import fnGetAtt, fnSub, is_intrinsic, make_or_condition, ref
from samtranslator.model.lambda_ import LambdaPermission
from samtranslator.model.route53 import Route53RecordSetGroup
from samtranslator.model.s3_utils.uri_parser import parse_s3_uri
from samtranslator.model.tags.resource_tagging import get_tag_list
from samtranslator.model.types import PassThrough
from samtranslator.region_configuration import RegionConfiguration
from samtranslator.swagger.swagger import SwaggerEditor
from samtranslator.translator.arn_generator import ArnGenerator
from samtranslator.translator.logical_id_generator import LogicalIdGenerator
from samtranslator.utils.py27hash_fix import Py27Dict, Py27UniStr
from samtranslator.utils.types import Intrinsicable
from samtranslator.utils.utils import InvalidValueType, dict_deep_get
from samtranslator.validator.value_validator import sam_expect

LOG = logging.getLogger(__name__)

_CORS_WILDCARD = "'*'"
CorsProperties = namedtuple(
    "CorsProperties", ["AllowMethods", "AllowHeaders", "AllowOrigin", "MaxAge", "AllowCredentials"]
)
# Default the Cors Properties to '*' wildcard and False AllowCredentials. Other properties are actually Optional
CorsProperties.__new__.__defaults__ = (None, None, _CORS_WILDCARD, None, False)

AuthProperties = namedtuple(
    "AuthProperties",
    [
        "Authorizers",
        "DefaultAuthorizer",
        "InvokeRole",
        "AddDefaultAuthorizerToCorsPreflight",
        "AddApiKeyRequiredToCorsPreflight",
        "ApiKeyRequired",
        "ResourcePolicy",
        "UsagePlan",
    ],
)
AuthProperties.__new__.__defaults__ = (None, None, None, True, True, None, None, None)
UsagePlanProperties = namedtuple(
    "UsagePlanProperties", ["CreateUsagePlan", "Description", "Quota", "Tags", "Throttle", "UsagePlanName"]
)
UsagePlanProperties.__new__.__defaults__ = (None, None, None, None, None, None)

GatewayResponseProperties = ["ResponseParameters", "ResponseTemplates", "StatusCode"]


@dataclass
class ApiDomainResponse:
    domain: Optional[ApiGatewayDomainName]
    apigw_basepath_mapping_list: Optional[List[ApiGatewayBasePathMapping]]
    recordset_group: Any


class SharedApiUsagePlan:
    """
    Collects API information from different API resources in the same template,
    so that these information can be used in the shared usage plan
    """

    SHARED_USAGE_PLAN_CONDITION_NAME = "SharedUsagePlanCondition"

    def __init__(self) -> None:
        self.usage_plan_shared = False
        self.stage_keys_shared: List[str] = []
        self.api_stages_shared: List[str] = []
        self.depends_on_shared: List[str] = []

        # shared resource level attributes
        self.conditions: Set[str] = set()
        self.any_api_without_condition = False
        self.deletion_policy: Optional[str] = None
        self.update_replace_policy: Optional[str] = None

    def get_combined_resource_attributes(self, resource_attributes, conditions):  # type: ignore[no-untyped-def]
        """
        This method returns a dictionary which combines 'DeletionPolicy', 'UpdateReplacePolicy' and 'Condition'
        values of API definitions that could be used in Shared Usage Plan resources.

        Parameters
        ----------
        resource_attributes: Dict[str]
            A dictionary of resource level attributes of the API resource
        conditions: Dict[str]
            Conditions section of the template
        """
        self._set_deletion_policy(resource_attributes.get("DeletionPolicy"))  # type: ignore[no-untyped-call]
        self._set_update_replace_policy(resource_attributes.get("UpdateReplacePolicy"))  # type: ignore[no-untyped-call]
        self._set_condition(resource_attributes.get("Condition"), conditions)  # type: ignore[no-untyped-call]

        combined_resource_attributes = {}
        if self.deletion_policy:
            combined_resource_attributes["DeletionPolicy"] = self.deletion_policy
        if self.update_replace_policy:
            combined_resource_attributes["UpdateReplacePolicy"] = self.update_replace_policy
        # do not set Condition if any of the API resource does not have Condition in it
        if self.conditions and not self.any_api_without_condition:
            combined_resource_attributes["Condition"] = SharedApiUsagePlan.SHARED_USAGE_PLAN_CONDITION_NAME

        return combined_resource_attributes

    def _set_deletion_policy(self, deletion_policy):  # type: ignore[no-untyped-def]
        if deletion_policy:
            if self.deletion_policy:
                # update only if new deletion policy is Retain
                if deletion_policy == "Retain":
                    self.deletion_policy = deletion_policy
            else:
                self.deletion_policy = deletion_policy

    def _set_update_replace_policy(self, update_replace_policy):  # type: ignore[no-untyped-def]
        if update_replace_policy:
            if self.update_replace_policy:
                # if new value is Retain or
                # new value is retain and current value is Delete then update its value
                if (update_replace_policy == "Retain") or (
                    update_replace_policy == "Snapshot" and self.update_replace_policy == "Delete"
                ):
                    self.update_replace_policy = update_replace_policy
            else:
                self.update_replace_policy = update_replace_policy

    def _set_condition(self, condition, template_conditions):  # type: ignore[no-untyped-def]
        # if there are any API without condition, then skip
        if self.any_api_without_condition:
            return

        if condition and condition not in self.conditions:
            if template_conditions is None:
                raise InvalidTemplateException(
                    "Can't have condition without having 'Conditions' section in the template"
                )

            if self.conditions:
                self.conditions.add(condition)
                or_condition = make_or_condition(self.conditions)
                template_conditions[SharedApiUsagePlan.SHARED_USAGE_PLAN_CONDITION_NAME] = or_condition
            else:
                self.conditions.add(condition)
                template_conditions[SharedApiUsagePlan.SHARED_USAGE_PLAN_CONDITION_NAME] = condition
        elif condition is None:
            self.any_api_without_condition = True
            if template_conditions and SharedApiUsagePlan.SHARED_USAGE_PLAN_CONDITION_NAME in template_conditions:
                del template_conditions[SharedApiUsagePlan.SHARED_USAGE_PLAN_CONDITION_NAME]


class ApiGenerator:
    def __init__(  # noqa: too-many-arguments
        self,
        logical_id: str,
        cache_cluster_enabled: Optional[Intrinsicable[bool]],
        cache_cluster_size: Optional[Intrinsicable[str]],
        variables: Optional[Dict[str, Any]],
        depends_on: Optional[List[str]],
        definition_body: Optional[Dict[str, Any]],
        definition_uri: Optional[Intrinsicable[str]],
        name: Optional[Intrinsicable[str]],
        stage_name: Optional[Intrinsicable[str]],
        shared_api_usage_plan: Any,
        template_conditions: Any,
        merge_definitions: Optional[bool] = None,
        tags: Optional[Dict[str, Any]] = None,
        endpoint_configuration: Optional[Dict[str, Any]] = None,
        method_settings: Optional[List[Any]] = None,
        binary_media: Optional[List[Any]] = None,
        minimum_compression_size: Optional[Intrinsicable[int]] = None,
        disable_execute_api_endpoint: Optional[Intrinsicable[bool]] = None,
        cors: Optional[Intrinsicable[str]] = None,
        auth: Optional[Dict[str, Any]] = None,
        gateway_responses: Optional[Dict[str, Any]] = None,
        access_log_setting: Optional[Dict[str, Any]] = None,
        canary_setting: Optional[Dict[str, Any]] = None,
        tracing_enabled: Optional[Intrinsicable[bool]] = None,
        resource_attributes: Optional[Dict[str, Any]] = None,
        passthrough_resource_attributes: Optional[Dict[str, Any]] = None,
        open_api_version: Optional[Intrinsicable[str]] = None,
        models: Optional[Dict[str, Any]] = None,
        domain: Optional[Dict[str, Any]] = None,
        fail_on_warnings: Optional[Intrinsicable[bool]] = None,
        description: Optional[Intrinsicable[str]] = None,
        mode: Optional[Intrinsicable[str]] = None,
        api_key_source_type: Optional[Intrinsicable[str]] = None,
        always_deploy: Optional[bool] = False,
    ):
        """Constructs an API Generator class that generates API Gateway resources

        :param logical_id: Logical id of the SAM API Resource
        :param cache_cluster_enabled: Whether cache cluster is enabled
        :param cache_cluster_size: Size of the cache cluster
        :param variables: API Gateway Variables
        :param depends_on: Any resources that need to be depended on
        :param definition_body: API definition
        :param definition_uri: URI to API definition
        :param name: Name of the API Gateway resource
        :param stage_name: Name of the Stage
        :param tags: Stage Tags
        :param access_log_setting: Whether to send access logs and where for Stage
        :param canary_setting: Canary Setting for Stage
        :param tracing_enabled: Whether active tracing with X-ray is enabled
        :param resource_attributes: Resource attributes to add to API resources
        :param passthrough_resource_attributes: Attributes such as `Condition` that are added to derived resources
        :param models: Model definitions to be used by API methods
        :param description: Description of the API Gateway resource
        """
        self.logical_id = logical_id
        self.cache_cluster_enabled = cache_cluster_enabled
        self.cache_cluster_size = cache_cluster_size
        self.variables = variables
        self.depends_on = depends_on
        self.definition_body = definition_body
        self.definition_uri = definition_uri
        self.merge_definitions = merge_definitions
        self.name = name
        self.stage_name = stage_name
        self.tags = tags
        self.endpoint_configuration = endpoint_configuration
        self.method_settings = method_settings
        self.binary_media = binary_media
        self.minimum_compression_size = minimum_compression_size
        self.disable_execute_api_endpoint = disable_execute_api_endpoint
        self.cors = cors
        self.auth = auth
        self.gateway_responses = gateway_responses
        self.access_log_setting = access_log_setting
        self.canary_setting = canary_setting
        self.tracing_enabled = tracing_enabled
        self.resource_attributes = resource_attributes
        self.passthrough_resource_attributes = passthrough_resource_attributes
        self.open_api_version = open_api_version
        self.remove_extra_stage = open_api_version
        self.models = models
        self.domain = domain
        self.fail_on_warnings = fail_on_warnings
        self.description = description
        self.shared_api_usage_plan = shared_api_usage_plan
        self.template_conditions = template_conditions
        self.mode = mode
        self.api_key_source_type = api_key_source_type
        self.always_deploy = always_deploy

    def _construct_rest_api(self) -> ApiGatewayRestApi:
        """Constructs and returns the ApiGateway RestApi.

        :returns: the RestApi to which this SAM Api corresponds
        :rtype: model.apigateway.ApiGatewayRestApi
        """
        self._validate_properties()
        rest_api = ApiGatewayRestApi(self.logical_id, depends_on=self.depends_on, attributes=self.resource_attributes)
        # NOTE: For backwards compatibility we need to retain BinaryMediaTypes on the CloudFormation Property
        # Removing this and only setting x-amazon-apigateway-binary-media-types results in other issues.
        rest_api.BinaryMediaTypes = self.binary_media
        rest_api.MinimumCompressionSize = self.minimum_compression_size

        if self.endpoint_configuration:
            self._set_endpoint_configuration(rest_api, self.endpoint_configuration)

        elif not RegionConfiguration.is_apigw_edge_configuration_supported():
            # Since this region does not support EDGE configuration, we explicitly set the endpoint type
            # to Regional which is the only supported config.
            self._set_endpoint_configuration(rest_api, "REGIONAL")

        self._add_cors()
        self._add_auth()
        self._add_gateway_responses()
        self._add_binary_media_types()
        self._add_models()

        if self.fail_on_warnings:
            rest_api.FailOnWarnings = self.fail_on_warnings

        if self.disable_execute_api_endpoint is not None:
            self._add_endpoint_extension()

        if self.definition_uri:
            rest_api.BodyS3Location = self._construct_body_s3_dict()
        elif self.definition_body:
            # # Post Process OpenApi Auth Settings
            self.definition_body = self._openapi_postprocess(self.definition_body)
            rest_api.Body = self.definition_body

        if self.name:
            rest_api.Name = self.name

        if self.description:
            rest_api.Description = self.description

        if self.mode:
            rest_api.Mode = self.mode

        if self.api_key_source_type:
            rest_api.ApiKeySourceType = self.api_key_source_type

        return rest_api

    def _validate_properties(self) -> None:
        if self.definition_uri and self.definition_body:
            raise InvalidResourceException(
                self.logical_id, "Specify either 'DefinitionUri' or 'DefinitionBody' property and not both."
            )

        if self.definition_uri and self.merge_definitions:
            raise InvalidResourceException(
                self.logical_id, "Cannot set 'MergeDefinitions' to True when using `DefinitionUri`."
            )

        if self.open_api_version and not SwaggerEditor.safe_compare_regex_with_string(
            SwaggerEditor.get_openapi_versions_supported_regex(), self.open_api_version
        ):
            raise InvalidResourceException(self.logical_id, "The OpenApiVersion value must be of the format '3.0.0'.")

    def _add_endpoint_extension(self) -> None:
        """Add disableExecuteApiEndpoint if it is set in SAM
        Note:
        If neither DefinitionUri nor DefinitionBody are specified,
        SAM will generate a openapi definition body based on template configuration.
        https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-resource-api.html#sam-api-definitionbody
        For this reason, we always put DisableExecuteApiEndpoint into openapi object irrespective of origin of DefinitionBody.
        """
        if self.disable_execute_api_endpoint is not None and not self.definition_body:
            raise InvalidResourceException(
                self.logical_id, "DisableExecuteApiEndpoint works only within 'DefinitionBody' property."
            )
        editor = SwaggerEditor(self.definition_body)
        editor.add_disable_execute_api_endpoint_extension(self.disable_execute_api_endpoint)
        self.definition_body = editor.swagger

    def _construct_body_s3_dict(self) -> Dict[str, Any]:
        """Constructs the RestApi's `BodyS3Location property`_, from the SAM Api's DefinitionUri property.

        :returns: a BodyS3Location dict, containing the S3 Bucket, Key, and Version of the Swagger definition
        :rtype: dict
        """
        if isinstance(self.definition_uri, dict):
            if not self.definition_uri.get("Bucket", None) or not self.definition_uri.get("Key", None):
                # DefinitionUri is a dictionary but does not contain Bucket or Key property
                raise InvalidResourceException(
                    self.logical_id, "'DefinitionUri' requires Bucket and Key properties to be specified."
                )
            s3_pointer = self.definition_uri

        else:
            # DefinitionUri is a string
            _parsed_s3_pointer = parse_s3_uri(self.definition_uri)
            if _parsed_s3_pointer is None:
                raise InvalidResourceException(
                    self.logical_id,
                    "'DefinitionUri' is not a valid S3 Uri of the form "
                    "'s3://bucket/key' with optional versionId query parameter.",
                )
            s3_pointer = _parsed_s3_pointer

            if isinstance(self.definition_uri, Py27UniStr):
                # self.defintion_uri is a Py27UniStr instance if it is defined in the template
                # we need to preserve the Py27UniStr type
                s3_pointer["Bucket"] = Py27UniStr(s3_pointer["Bucket"])
                s3_pointer["Key"] = Py27UniStr(s3_pointer["Key"])
                if "Version" in s3_pointer:
                    s3_pointer["Version"] = Py27UniStr(s3_pointer["Version"])

        # Construct body_s3 as py27 dict
        body_s3 = Py27Dict()
        body_s3["Bucket"] = s3_pointer["Bucket"]
        body_s3["Key"] = s3_pointer["Key"]
        if "Version" in s3_pointer:
            body_s3["Version"] = s3_pointer["Version"]
        return body_s3

    def _construct_deployment(self, rest_api: ApiGatewayRestApi) -> ApiGatewayDeployment:
        """Constructs and returns the ApiGateway Deployment.

        :param model.apigateway.ApiGatewayRestApi rest_api: the RestApi for this Deployment
        :returns: the Deployment to which this SAM Api corresponds
        :rtype: model.apigateway.ApiGatewayDeployment
        """
        deployment = ApiGatewayDeployment(
            self.logical_id + "Deployment", attributes=self.passthrough_resource_attributes
        )
        deployment.RestApiId = rest_api.get_runtime_attr("rest_api_id")
        if not self.remove_extra_stage:
            deployment.StageName = "Stage"

        return deployment

    def _construct_stage(
        self, deployment: ApiGatewayDeployment, swagger: Optional[Dict[str, Any]], redeploy_restapi_parameters: Any
    ) -> ApiGatewayStage:
        """Constructs and returns the ApiGateway Stage.

        :param model.apigateway.ApiGatewayDeployment deployment: the Deployment for this Stage
        :returns: the Stage to which this SAM Api corresponds
        :rtype: model.apigateway.ApiGatewayStage
        """

        # If StageName is some intrinsic function, then don't prefix the Stage's logical ID
        # This will NOT create duplicates because we allow only ONE stage per API resource
        stage_name_prefix = self.stage_name if isinstance(self.stage_name, str) else ""
        if stage_name_prefix.isalnum():
            stage_logical_id = self.logical_id + stage_name_prefix + "Stage"
        else:
            generator = LogicalIdGenerator(self.logical_id + "Stage", stage_name_prefix)
            stage_logical_id = generator.gen()
        stage = ApiGatewayStage(stage_logical_id, attributes=self.passthrough_resource_attributes)
        stage.RestApiId = ref(self.logical_id)
        stage.update_deployment_ref(deployment.logical_id)
        stage.StageName = self.stage_name
        stage.CacheClusterEnabled = self.cache_cluster_enabled
        stage.CacheClusterSize = self.cache_cluster_size
        stage.Variables = self.variables
        stage.MethodSettings = self.method_settings
        stage.AccessLogSetting = self.access_log_setting
        stage.CanarySetting = self.canary_setting
        stage.TracingEnabled = self.tracing_enabled

        if swagger is not None:
            deployment.make_auto_deployable(
                stage,
                self.remove_extra_stage,
                swagger,
                self.domain,
                redeploy_restapi_parameters,
                self.always_deploy,
            )

        if self.tags is not None:
            stage.Tags = get_tag_list(self.tags)

        return stage

    def _construct_api_domain(  # noqa: too-many-branches
        self, rest_api: ApiGatewayRestApi, route53_record_set_groups: Any
    ) -> ApiDomainResponse:
        """
        Constructs and returns the ApiGateway Domain and BasepathMapping
        """
        if self.domain is None:
            return ApiDomainResponse(None, None, None)

        sam_expect(self.domain, self.logical_id, "Domain").to_be_a_map()
        domain_name: PassThrough = sam_expect(
            self.domain.get("DomainName"), self.logical_id, "Domain.DomainName"
        ).to_not_be_none()
        certificate_arn: PassThrough = sam_expect(
            self.domain.get("CertificateArn"), self.logical_id, "Domain.CertificateArn"
        ).to_not_be_none()

        api_domain_name = "{}{}".format("ApiGatewayDomainName", LogicalIdGenerator("", domain_name).gen())
        self.domain["ApiDomainName"] = api_domain_name

        domain = ApiGatewayDomainName(api_domain_name, attributes=self.passthrough_resource_attributes)
        domain.DomainName = domain_name
        endpoint = self.domain.get("EndpointConfiguration")

        if endpoint is None:
            endpoint = "REGIONAL"
            self.domain["EndpointConfiguration"] = "REGIONAL"
        elif endpoint not in ["EDGE", "REGIONAL", "PRIVATE"]:
            raise InvalidResourceException(
                self.logical_id,
                "EndpointConfiguration for Custom Domains must be"
                " one of {}.".format(["EDGE", "REGIONAL", "PRIVATE"]),
            )

        if endpoint == "REGIONAL":
            domain.RegionalCertificateArn = certificate_arn
        else:
            domain.CertificateArn = certificate_arn

        domain.EndpointConfiguration = {"Types": [endpoint]}

        mutual_tls_auth = self.domain.get("MutualTlsAuthentication", None)
        if mutual_tls_auth:
            sam_expect(mutual_tls_auth, self.logical_id, "Domain.MutualTlsAuthentication").to_be_a_map()
            if not set(mutual_tls_auth.keys()).issubset({"TruststoreUri", "TruststoreVersion"}):
                invalid_keys = []
                for key in mutual_tls_auth:
                    if key not in {"TruststoreUri", "TruststoreVersion"}:
                        invalid_keys.append(key)
                invalid_keys.sort()
                raise InvalidResourceException(
                    self.logical_id,
                    "Available Domain.MutualTlsAuthentication fields are {}.".format(
                        ["TruststoreUri", "TruststoreVersion"]
                    ),
                )
            domain.MutualTlsAuthentication = {}
            if mutual_tls_auth.get("TruststoreUri", None):
                domain.MutualTlsAuthentication["TruststoreUri"] = mutual_tls_auth["TruststoreUri"]
            if mutual_tls_auth.get("TruststoreVersion", None):
                domain.MutualTlsAuthentication["TruststoreVersion"] = mutual_tls_auth["TruststoreVersion"]

        if self.domain.get("SecurityPolicy", None):
            domain.SecurityPolicy = self.domain["SecurityPolicy"]

        if self.domain.get("OwnershipVerificationCertificateArn", None):
            domain.OwnershipVerificationCertificateArn = self.domain["OwnershipVerificationCertificateArn"]

        basepaths: Optional[List[str]]
        basepath_value = self.domain.get("BasePath")
        # Create BasepathMappings
        if self.domain.get("BasePath") and isinstance(basepath_value, str):
            basepaths = [basepath_value]
        elif self.domain.get("BasePath") and isinstance(basepath_value, list):
            basepaths = cast(Optional[List[Any]], basepath_value)
        else:
            basepaths = None

        # Boolean to allow/disallow symbols in BasePath property
        normalize_basepath = self.domain.get("NormalizeBasePath", True)

        basepath_resource_list: List[ApiGatewayBasePathMapping] = []

        if basepaths is None:
            basepath_mapping = ApiGatewayBasePathMapping(
                self.logical_id + "BasePathMapping", attributes=self.passthrough_resource_attributes
            )
            basepath_mapping.DomainName = ref(api_domain_name)
            basepath_mapping.RestApiId = ref(rest_api.logical_id)
            basepath_mapping.Stage = ref(rest_api.logical_id + ".Stage")
            basepath_resource_list.extend([basepath_mapping])
        else:
            sam_expect(basepaths, self.logical_id, "Domain.BasePath").to_be_a_list_of(ExpectedType.STRING)
            for basepath in basepaths:
                # Remove possible leading and trailing '/' because a base path may only
                # contain letters, numbers, and one of "$-_.+!*'()"
                path = "".join(e for e in basepath if e.isalnum())
                logical_id = "{}{}{}".format(self.logical_id, path, "BasePathMapping")
                basepath_mapping = ApiGatewayBasePathMapping(
                    logical_id, attributes=self.passthrough_resource_attributes
                )
                basepath_mapping.DomainName = ref(api_domain_name)
                basepath_mapping.RestApiId = ref(rest_api.logical_id)
                basepath_mapping.Stage = ref(rest_api.logical_id + ".Stage")
                basepath_mapping.BasePath = path if normalize_basepath else basepath
                basepath_resource_list.extend([basepath_mapping])

        # Create the Route53 RecordSetGroup resource
        record_set_group = None
        route53 = self.domain.get("Route53")
        if route53 is not None:
            sam_expect(route53, self.logical_id, "Domain.Route53").to_be_a_map()
            if route53.get("HostedZoneId") is None and route53.get("HostedZoneName") is None:
                raise InvalidResourceException(
                    self.logical_id,
                    "HostedZoneId or HostedZoneName is required to enable Route53 support on Custom Domains.",
                )

            logical_id_suffix = LogicalIdGenerator(
                "", route53.get("HostedZoneId") or route53.get("HostedZoneName")
            ).gen()
            logical_id = "RecordSetGroup" + logical_id_suffix

            record_set_group = route53_record_set_groups.get(logical_id)

            if route53.get("SeparateRecordSetGroup"):
                sam_expect(
                    route53.get("SeparateRecordSetGroup"), self.logical_id, "Domain.Route53.SeparateRecordSetGroup"
                ).to_be_a_bool()
                return ApiDomainResponse(
                    domain,
                    basepath_resource_list,
                    self._construct_single_record_set_group(self.domain, api_domain_name, route53),
                )

            if not record_set_group:
                record_set_group = Route53RecordSetGroup(logical_id, attributes=self.passthrough_resource_attributes)
                if "HostedZoneId" in route53:
                    record_set_group.HostedZoneId = route53.get("HostedZoneId")
                if "HostedZoneName" in route53:
                    record_set_group.HostedZoneName = route53.get("HostedZoneName")
                record_set_group.RecordSets = []
                route53_record_set_groups[logical_id] = record_set_group

            record_set_group.RecordSets += self._construct_record_sets_for_domain(self.domain, api_domain_name, route53)

        return ApiDomainResponse(domain, basepath_resource_list, record_set_group)

    def _construct_single_record_set_group(
        self, domain: Dict[str, Any], api_domain_name: str, route53: Any
    ) -> Route53RecordSetGroup:
        hostedZoneId = route53.get("HostedZoneId")
        hostedZoneName = route53.get("HostedZoneName")
        domainName = domain.get("DomainName")
        logical_id = logical_id = LogicalIdGenerator(
            "RecordSetGroup", [hostedZoneId or hostedZoneName, domainName]
        ).gen()

        record_set_group = Route53RecordSetGroup(logical_id, attributes=self.passthrough_resource_attributes)
        if hostedZoneId:
            record_set_group.HostedZoneId = hostedZoneId
        if hostedZoneName:
            record_set_group.HostedZoneName = hostedZoneName

        record_set_group.RecordSets = []
        record_set_group.RecordSets += self._construct_record_sets_for_domain(domain, api_domain_name, route53)

        return record_set_group

    def _construct_record_sets_for_domain(
        self, custom_domain_config: Dict[str, Any], api_domain_name: str, route53_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        recordset_list = []
        alias_target = self._construct_alias_target(custom_domain_config, api_domain_name, route53_config)
        recordset = {}
        recordset["Name"] = custom_domain_config.get("DomainName")
        recordset["Type"] = "A"
        recordset["AliasTarget"] = alias_target
        self._update_route53_routing_policy_properties(route53_config, recordset)
        recordset_list.append(recordset)

        if route53_config.get("IpV6") is not None and route53_config.get("IpV6") is True:
            recordset_ipv6 = {}
            recordset_ipv6["Name"] = custom_domain_config.get("DomainName")
            recordset_ipv6["Type"] = "AAAA"
            recordset_ipv6["AliasTarget"] = alias_target
            self._update_route53_routing_policy_properties(route53_config, recordset_ipv6)
            recordset_list.append(recordset_ipv6)

        return recordset_list

    @staticmethod
    def _update_route53_routing_policy_properties(route53_config: Dict[str, Any], recordset: Dict[str, Any]) -> None:
        if route53_config.get("Region") is not None:
            recordset["Region"] = route53_config.get("Region")
        if route53_config.get("SetIdentifier") is not None:
            recordset["SetIdentifier"] = route53_config.get("SetIdentifier")

    def _construct_alias_target(self, domain: Dict[str, Any], api_domain_name: str, route53: Any) -> Dict[str, Any]:
        alias_target = {}
        target_health = route53.get("EvaluateTargetHealth")

        if target_health is not None:
            alias_target["EvaluateTargetHealth"] = target_health
        if domain.get("EndpointConfiguration") == "REGIONAL":
            alias_target["HostedZoneId"] = fnGetAtt(api_domain_name, "RegionalHostedZoneId")
            alias_target["DNSName"] = fnGetAtt(api_domain_name, "RegionalDomainName")
        else:
            if route53.get("DistributionDomainName") is None:
                route53["DistributionDomainName"] = fnGetAtt(api_domain_name, "DistributionDomainName")
            alias_target["HostedZoneId"] = "Z2FDTNDATAQYW2"
            alias_target["DNSName"] = route53.get("DistributionDomainName")
        return alias_target

    @cw_timer(prefix="Generator", name="Api")
    def to_cloudformation(
        self, redeploy_restapi_parameters: Optional[Any], route53_record_set_groups: Dict[str, Route53RecordSetGroup]
    ) -> List[Resource]:
        """Generates CloudFormation resources from a SAM API resource

        :returns: a tuple containing the RestApi, Deployment, and Stage for an empty Api.
        :rtype: tuple
        """
        rest_api = self._construct_rest_api()
        api_domain_response = self._construct_api_domain(rest_api, route53_record_set_groups)
        domain = api_domain_response.domain
        basepath_mapping = api_domain_response.apigw_basepath_mapping_list
        route53_recordsetGroup = api_domain_response.recordset_group

        deployment = self._construct_deployment(rest_api)

        swagger = None
        if rest_api.Body is not None:
            swagger = rest_api.Body
        elif rest_api.BodyS3Location is not None:
            swagger = rest_api.BodyS3Location

        stage = self._construct_stage(deployment, swagger, redeploy_restapi_parameters)
        permissions = self._construct_authorizer_lambda_permission()
        usage_plan = self._construct_usage_plan(rest_api_stage=stage)

        # mypy complains if the type in List doesn't match exactly
        # TODO: refactor to have a list of single resource
        generated_resources: List[
            Union[
                Optional[Resource],
                List[Resource],
                Tuple[Resource],
                List[LambdaPermission],
                List[ApiGatewayBasePathMapping],
            ],
        ] = []

        generated_resources.extend(
            [
                rest_api,
                deployment,
                stage,
                permissions,
                domain,
                basepath_mapping,
                route53_recordsetGroup,
                usage_plan,
            ]
        )

        # Make a list of single resources
        generated_resources_list: List[Resource] = []
        for resource in generated_resources:
            if resource:
                if isinstance(resource, (list, tuple)):
                    generated_resources_list.extend(resource)
                else:
                    generated_resources_list.extend([resource])

        return generated_resources_list

    def _add_cors(self) -> None:
        """
        Add CORS configuration to the Swagger file, if necessary
        """

        INVALID_ERROR = "Invalid value for 'Cors' property"

        if not self.cors:
            return

        if self.cors and not self.definition_body:
            raise InvalidResourceException(
                self.logical_id, "Cors works only with inline Swagger specified in 'DefinitionBody' property."
            )

        if isinstance(self.cors, str) or is_intrinsic(self.cors):
            # Just set Origin property. Others will be defaults
            properties = CorsProperties(AllowOrigin=self.cors)  # type: ignore[call-arg]
        elif isinstance(self.cors, dict):
            # Make sure keys in the dict are recognized
            if not all(key in CorsProperties._fields for key in self.cors):
                raise InvalidResourceException(self.logical_id, INVALID_ERROR)

            properties = CorsProperties(**self.cors)

        else:
            raise InvalidResourceException(self.logical_id, INVALID_ERROR)

        if not SwaggerEditor.is_valid(self.definition_body):
            raise InvalidResourceException(
                self.logical_id,
                "Unable to add Cors configuration because "
                "'DefinitionBody' does not contain a valid Swagger definition.",
            )

        if properties.AllowCredentials is True and properties.AllowOrigin == _CORS_WILDCARD:
            raise InvalidResourceException(
                self.logical_id,
                "Unable to add Cors configuration because "
                "'AllowCredentials' can not be true when "
                "'AllowOrigin' is \"'*'\" or not set",
            )

        editor = SwaggerEditor(self.definition_body)
        for path in editor.iter_on_path():
            try:
                editor.add_cors(  # type: ignore[no-untyped-call]
                    path,
                    properties.AllowOrigin,
                    properties.AllowHeaders,
                    properties.AllowMethods,
                    max_age=properties.MaxAge,
                    allow_credentials=properties.AllowCredentials,
                )
            except InvalidTemplateException as ex:
                raise InvalidResourceException(self.logical_id, ex.message) from ex

        # Assign the Swagger back to template
        self.definition_body = editor.swagger

    def _add_binary_media_types(self) -> None:
        """
        Add binary media types to Swagger
        """

        if not self.binary_media:
            return

        # We don't raise an error here like we do for similar cases because that would be backwards incompatible
        if self.binary_media and not self.definition_body:
            return

        editor = SwaggerEditor(self.definition_body)
        editor.add_binary_media_types(self.binary_media)  # type: ignore[no-untyped-call]

        # Assign the Swagger back to template
        self.definition_body = editor.swagger

    def _add_auth(self) -> None:
        """
        Add Auth configuration to the Swagger file, if necessary
        """

        if not self.auth:
            return

        if self.auth and not self.definition_body:
            raise InvalidResourceException(
                self.logical_id, "Auth works only with inline Swagger specified in 'DefinitionBody' property."
            )

        # Make sure keys in the dict are recognized
        if not all(key in AuthProperties._fields for key in self.auth):
            raise InvalidResourceException(self.logical_id, "Invalid value for 'Auth' property")

        if not SwaggerEditor.is_valid(self.definition_body):
            raise InvalidResourceException(
                self.logical_id,
                "Unable to add Auth configuration because "
                "'DefinitionBody' does not contain a valid Swagger definition.",
            )
        swagger_editor = SwaggerEditor(self.definition_body)
        auth_properties = AuthProperties(**self.auth)
        authorizers = self._get_authorizers(auth_properties.Authorizers, auth_properties.DefaultAuthorizer)  # type: ignore[no-untyped-call]

        if authorizers:
            swagger_editor.add_authorizers_security_definitions(authorizers)  # type: ignore[no-untyped-call]
            self._set_default_authorizer(
                swagger_editor,
                authorizers,
                auth_properties.DefaultAuthorizer,
                auth_properties.AddDefaultAuthorizerToCorsPreflight,
            )

        if auth_properties.ApiKeyRequired:
            swagger_editor.add_apikey_security_definition()
            self._set_default_apikey_required(swagger_editor, auth_properties.AddApiKeyRequiredToCorsPreflight)

        if auth_properties.ResourcePolicy:
            SwaggerEditor.validate_is_dict(
                auth_properties.ResourcePolicy, "ResourcePolicy must be a map (ResourcePolicyStatement)."
            )
            for path in swagger_editor.iter_on_path():
                swagger_editor.add_resource_policy(auth_properties.ResourcePolicy, path, self.stage_name)
            if auth_properties.ResourcePolicy.get("CustomStatements"):
                swagger_editor.add_custom_statements(auth_properties.ResourcePolicy.get("CustomStatements"))  # type: ignore[no-untyped-call]

        self.definition_body = self._openapi_postprocess(swagger_editor.swagger)

    def _construct_usage_plan(self, rest_api_stage: Optional[ApiGatewayStage] = None) -> Any:  # noqa: too-many-branches
        """Constructs and returns the ApiGateway UsagePlan, ApiGateway UsagePlanKey, ApiGateway ApiKey for Auth.

        :param model.apigateway.ApiGatewayStage stage: the stage of rest api
        :returns: UsagePlan, UsagePlanKey, ApiKey for this rest Api
        :rtype: model.apigateway.ApiGatewayUsagePlan, model.apigateway.ApiGatewayUsagePlanKey,
                model.apigateway.ApiGatewayApiKey
        """
        create_usage_plans_accepted_values = ["SHARED", "PER_API", "NONE"]
        if not self.auth:
            return []
        auth_properties = AuthProperties(**self.auth)
        if auth_properties.UsagePlan is None:
            return []
        usage_plan_properties = auth_properties.UsagePlan
        # throws error if UsagePlan is not a dict
        if not isinstance(usage_plan_properties, dict):
            raise InvalidResourceException(self.logical_id, "'UsagePlan' must be a dictionary")
        # throws error if the property invalid/ unsupported for UsagePlan
        if not all(key in UsagePlanProperties._fields for key in usage_plan_properties):
            raise InvalidResourceException(self.logical_id, "Invalid property for 'UsagePlan'")

        create_usage_plan = usage_plan_properties.get("CreateUsagePlan")
        usage_plan: Optional[ApiGatewayUsagePlan] = None
        api_key = None
        usage_plan_key = None

        if create_usage_plan is None:
            raise InvalidResourceException(self.logical_id, "'CreateUsagePlan' is a required field for UsagePlan.")
        if create_usage_plan not in create_usage_plans_accepted_values:
            raise InvalidResourceException(
                self.logical_id, f"'CreateUsagePlan' accepts one of {create_usage_plans_accepted_values}."
            )

        if create_usage_plan == "NONE":
            return []
        if not rest_api_stage:
            return []

        # create usage plan for this api only
        if usage_plan_properties.get("CreateUsagePlan") == "PER_API":
            usage_plan_logical_id = self.logical_id + "UsagePlan"
            usage_plan = ApiGatewayUsagePlan(
                logical_id=usage_plan_logical_id,
                depends_on=[self.logical_id],
                attributes=self.passthrough_resource_attributes,
            )
            api_stages = []
            api_stage = {}
            api_stage["ApiId"] = ref(self.logical_id)
            api_stage["Stage"] = ref(rest_api_stage.logical_id)
            api_stages.append(api_stage)
            usage_plan.ApiStages = api_stages

            api_key = self._construct_api_key(usage_plan_logical_id, create_usage_plan, rest_api_stage)
            usage_plan_key = self._construct_usage_plan_key(usage_plan_logical_id, create_usage_plan, api_key)

        # create a usage plan for all the Apis
        elif create_usage_plan == "SHARED":
            LOG.info("Creating SHARED usage plan for all the Apis")
            usage_plan_logical_id = "ServerlessUsagePlan"
            if self.logical_id not in self.shared_api_usage_plan.depends_on_shared:
                self.shared_api_usage_plan.depends_on_shared.append(self.logical_id)
            usage_plan = ApiGatewayUsagePlan(
                logical_id=usage_plan_logical_id,
                depends_on=self.shared_api_usage_plan.depends_on_shared,
                attributes=self.shared_api_usage_plan.get_combined_resource_attributes(
                    self.passthrough_resource_attributes, self.template_conditions
                ),
            )
            api_stage = {}
            api_stage["ApiId"] = ref(self.logical_id)
            api_stage["Stage"] = ref(rest_api_stage.logical_id)
            if api_stage not in self.shared_api_usage_plan.api_stages_shared:
                self.shared_api_usage_plan.api_stages_shared.append(api_stage)
            usage_plan.ApiStages = self.shared_api_usage_plan.api_stages_shared

            api_key = self._construct_api_key(usage_plan_logical_id, create_usage_plan, rest_api_stage)
            usage_plan_key = self._construct_usage_plan_key(usage_plan_logical_id, create_usage_plan, api_key)

        for name in ["UsagePlanName", "Description", "Quota", "Tags", "Throttle"]:
            if usage_plan and usage_plan_properties.get(name):
                setattr(usage_plan, name, usage_plan_properties.get(name))
        return usage_plan, api_key, usage_plan_key

    def _construct_api_key(
        self, usage_plan_logical_id: str, create_usage_plan: Any, rest_api_stage: ApiGatewayStage
    ) -> ApiGatewayApiKey:
        """
        :param usage_plan_logical_id: String
        :param create_usage_plan: String
        :param rest_api_stage: model.apigateway.ApiGatewayStage stage: the stage of rest api
        :return: api_key model.apigateway.ApiGatewayApiKey resource which is created for the given usage plan
        """
        if create_usage_plan == "SHARED":
            # create an api key resource for all the apis
            LOG.info("Creating api key resource for all the Apis from SHARED usage plan")
            api_key_logical_id = "ServerlessApiKey"
            api_key = ApiGatewayApiKey(
                logical_id=api_key_logical_id,
                depends_on=[usage_plan_logical_id],
                attributes=self.shared_api_usage_plan.get_combined_resource_attributes(
                    self.passthrough_resource_attributes, self.template_conditions
                ),
            )
            api_key.Enabled = True
            stage_key = {}
            stage_key["RestApiId"] = ref(self.logical_id)
            stage_key["StageName"] = ref(rest_api_stage.logical_id)
            if stage_key not in self.shared_api_usage_plan.stage_keys_shared:
                self.shared_api_usage_plan.stage_keys_shared.append(stage_key)
            api_key.StageKeys = self.shared_api_usage_plan.stage_keys_shared
        # for create_usage_plan = "PER_API"
        else:
            # create an api key resource for this api
            api_key_logical_id = self.logical_id + "ApiKey"
            api_key = ApiGatewayApiKey(
                logical_id=api_key_logical_id,
                depends_on=[usage_plan_logical_id],
                attributes=self.passthrough_resource_attributes,
            )
            api_key.Enabled = True
            stage_keys = []
            stage_key = {}
            stage_key["RestApiId"] = ref(self.logical_id)
            stage_key["StageName"] = ref(rest_api_stage.logical_id)
            stage_keys.append(stage_key)
            api_key.StageKeys = stage_keys
        return api_key

    def _construct_usage_plan_key(
        self, usage_plan_logical_id: str, create_usage_plan: Any, api_key: ApiGatewayApiKey
    ) -> ApiGatewayUsagePlanKey:
        """
        :param usage_plan_logical_id: String
        :param create_usage_plan: String
        :param api_key: model.apigateway.ApiGatewayApiKey resource
        :return: model.apigateway.ApiGatewayUsagePlanKey resource that contains the mapping between usage plan and api key
        """
        if create_usage_plan == "SHARED":
            # create a mapping between api key and the usage plan
            usage_plan_key_logical_id = "ServerlessUsagePlanKey"
            resource_attributes = self.shared_api_usage_plan.get_combined_resource_attributes(
                self.passthrough_resource_attributes, self.template_conditions
            )
        # for create_usage_plan = "PER_API"
        else:
            # create a mapping between api key and the usage plan
            usage_plan_key_logical_id = self.logical_id + "UsagePlanKey"
            resource_attributes = self.passthrough_resource_attributes

        usage_plan_key = ApiGatewayUsagePlanKey(
            logical_id=usage_plan_key_logical_id,
            depends_on=[api_key.logical_id],
            attributes=resource_attributes,
        )
        usage_plan_key.KeyId = ref(api_key.logical_id)
        usage_plan_key.KeyType = "API_KEY"
        usage_plan_key.UsagePlanId = ref(usage_plan_logical_id)

        return usage_plan_key

    def _add_gateway_responses(self) -> None:
        """
        Add Gateway Response configuration to the Swagger file, if necessary
        """

        if not self.gateway_responses:
            return

        if self.gateway_responses and not self.definition_body:
            raise InvalidResourceException(
                self.logical_id,
                "GatewayResponses works only with inline Swagger specified in 'DefinitionBody' property.",
            )

        # Make sure keys in the dict are recognized
        for responses_key, responses_value in self.gateway_responses.items():
            if is_intrinsic(responses_value):
                # TODO: Add intrinsic support for this field.
                raise InvalidResourceException(
                    self.logical_id,
                    "Unable to set GatewayResponses attribute because "
                    "intrinsic functions are not supported for this field.",
                )
            if not isinstance(responses_value, dict):
                raise InvalidResourceException(
                    self.logical_id,
                    "Invalid property type '{}' for GatewayResponses. "
                    "Expected an object of type 'GatewayResponse'.".format(type(responses_value).__name__),
                )
            for response_key in responses_value:
                if response_key not in GatewayResponseProperties:
                    raise InvalidResourceException(
                        self.logical_id,
                        "Invalid property '{}' in 'GatewayResponses' property '{}'.".format(
                            response_key, responses_key
                        ),
                    )

        if not SwaggerEditor.is_valid(self.definition_body):
            raise InvalidResourceException(
                self.logical_id,
                "Unable to add Auth configuration because "
                "'DefinitionBody' does not contain a valid Swagger definition.",
            )

        swagger_editor = SwaggerEditor(self.definition_body)

        # The dicts below will eventually become part of swagger/openapi definition, thus requires using Py27Dict()
        gateway_responses = Py27Dict()
        for response_type, response in self.gateway_responses.items():
            sam_expect(response, self.logical_id, f"GatewayResponses.{response_type}").to_be_a_map()
            response_parameters = response.get("ResponseParameters", Py27Dict())
            response_templates = response.get("ResponseTemplates", Py27Dict())
            if response_parameters:
                sam_expect(
                    response_parameters, self.logical_id, f"GatewayResponses.{response_type}.ResponseParameters"
                ).to_be_a_map()
            gateway_responses[response_type] = ApiGatewayResponse(
                api_logical_id=self.logical_id,
                response_parameters=response_parameters,
                response_templates=response_templates,
                status_code=response.get("StatusCode", None),
            )

        if gateway_responses:
            swagger_editor.add_gateway_responses(gateway_responses)  # type: ignore[no-untyped-call]

        # Assign the Swagger back to template
        self.definition_body = swagger_editor.swagger

    def _add_models(self) -> None:
        """
        Add Model definitions to the Swagger file, if necessary
        :return:
        """

        if not self.models:
            return

        if self.models and not self.definition_body:
            raise InvalidResourceException(
                self.logical_id, "Models works only with inline Swagger specified in 'DefinitionBody' property."
            )

        if not SwaggerEditor.is_valid(self.definition_body):
            raise InvalidResourceException(
                self.logical_id,
                "Unable to add Models definitions because "
                "'DefinitionBody' does not contain a valid Swagger definition.",
            )

        if not all(isinstance(model, dict) for model in self.models.values()):
            raise InvalidResourceException(self.logical_id, "Invalid value for 'Models' property")

        swagger_editor = SwaggerEditor(self.definition_body)
        swagger_editor.add_models(self.models)  # type: ignore[no-untyped-call]

        # Assign the Swagger back to template

        self.definition_body = self._openapi_postprocess(swagger_editor.swagger)

    def _openapi_postprocess(self, definition_body: Dict[str, Any]) -> Dict[str, Any]:  # noqa: too-many-branches
        """
        Convert definitions to openapi 3 in definition body if OpenApiVersion flag is specified.

        If the is swagger defined in the definition body, we treat it as a swagger spec and do not
        make any openapi 3 changes to it
        """
        if definition_body.get("swagger") is not None:
            return definition_body

        if definition_body.get("openapi") is not None and self.open_api_version is None:
            self.open_api_version = definition_body.get("openapi")

        if self.open_api_version and SwaggerEditor.safe_compare_regex_with_string(
            SwaggerEditor._OPENAPI_VERSION_3_REGEX, self.open_api_version
        ):
            if definition_body.get("securityDefinitions"):
                components = definition_body.get("components", Py27Dict())
                # In the previous line, the default value `Py27Dict()` will be only returned only if `components`
                # property is not in definition_body dict, but if it exist, and its value is None, so None will be
                # returned and not the default value. That is why the below line is required.
                components = components if components else Py27Dict()
                components["securitySchemes"] = definition_body["securityDefinitions"]
                definition_body["components"] = components
                del definition_body["securityDefinitions"]
            if definition_body.get("definitions"):
                components = definition_body.get("components", Py27Dict())
                # the following line to check if components is None
                # is copied from the previous if...
                # In the previous line, the default value `Py27Dict()` will be only returned only if `components`
                # property is not in definition_body dict, but if it exist, and its value is None, so None will be
                # returned and not the default value. That is why the below line is required.
                components = components if components else Py27Dict()
                components["schemas"] = definition_body["definitions"]
                definition_body["components"] = components
                del definition_body["definitions"]
            # removes `consumes` and `produces` options for CORS in openapi3 and
            # adds `schema` for the headers in responses for openapi3
            paths = definition_body.get("paths")
            if paths:
                SwaggerEditor.validate_is_dict(
                    paths,
                    "Value of paths must be a dictionary according to Swagger spec.",
                )
                for path, path_item in paths.items():
                    SwaggerEditor.validate_path_item_is_dict(path_item, path)
                    if path_item.get("options"):
                        SwaggerEditor.validate_is_dict(
                            path_item.get("options"),
                            "Value of options method for path {} must be a "
                            "dictionary according to Swagger spec.".format(path),
                        )
                        options = path_item.get("options").copy()
                        for field, field_val in options.items():
                            # remove unsupported produces and consumes in options for openapi3
                            if field in ["produces", "consumes"]:
                                del definition_body["paths"][path]["options"][field]
                            # add schema for the headers in options section for openapi3
                            if field in ["responses"]:
                                try:
                                    response_200_headers = dict_deep_get(field_val, "200.headers")
                                except InvalidValueType as ex:
                                    raise InvalidDocumentException(
                                        [
                                            InvalidTemplateException(
                                                f"Invalid responses in options method for path {path}: {ex!s}.",
                                            )
                                        ]
                                    ) from ex
                                if not response_200_headers:
                                    continue
                                SwaggerEditor.validate_is_dict(
                                    response_200_headers,
                                    "Value of response's headers in options method for path {} must be a "
                                    "dictionary according to Swagger spec.".format(path),
                                )
                                for header, header_val in response_200_headers.items():
                                    new_header_val_with_schema = Py27Dict()
                                    new_header_val_with_schema["schema"] = header_val
                                    definition_body["paths"][path]["options"][field]["200"]["headers"][
                                        header
                                    ] = new_header_val_with_schema

        return definition_body

    def _get_authorizers(self, authorizers_config, default_authorizer=None):  # type: ignore[no-untyped-def]
        # The dict below will eventually become part of swagger/openapi definition, thus requires using Py27Dict()
        authorizers = Py27Dict()
        if default_authorizer == "AWS_IAM":
            authorizers[default_authorizer] = ApiGatewayAuthorizer(
                api_logical_id=self.logical_id, name=default_authorizer, is_aws_iam_authorizer=True
            )

        if not authorizers_config:
            if "AWS_IAM" in authorizers:
                return authorizers
            return None

        sam_expect(authorizers_config, self.logical_id, "Auth.Authorizers").to_be_a_map()

        for authorizer_name, authorizer in authorizers_config.items():
            sam_expect(authorizer, self.logical_id, f"Auth.Authorizers.{authorizer_name}").to_be_a_map()

            authorizers[authorizer_name] = ApiGatewayAuthorizer(
                api_logical_id=self.logical_id,
                name=authorizer_name,
                user_pool_arn=authorizer.get("UserPoolArn"),
                function_arn=authorizer.get("FunctionArn"),
                identity=authorizer.get("Identity"),
                function_payload_type=authorizer.get("FunctionPayloadType"),
                function_invoke_role=authorizer.get("FunctionInvokeRole"),
                authorization_scopes=authorizer.get("AuthorizationScopes"),
                disable_function_default_permissions=authorizer.get("DisableFunctionDefaultPermissions"),
            )
        return authorizers

    def _get_permission(self, authorizer_name, authorizer_lambda_function_arn):  # type: ignore[no-untyped-def]
        """Constructs and returns the Lambda Permission resource allowing the Authorizer to invoke the function.

        :returns: the permission resource
        :rtype: model.lambda_.LambdaPermission
        """
        rest_api = ApiGatewayRestApi(self.logical_id, depends_on=self.depends_on, attributes=self.resource_attributes)
        api_id = rest_api.get_runtime_attr("rest_api_id")

        partition = ArnGenerator.get_partition_name()
        resource = "${__ApiId__}/authorizers/*"
        source_arn = fnSub(
            ArnGenerator.generate_arn(partition=partition, service="execute-api", resource=resource),
            {"__ApiId__": api_id},
        )

        lambda_permission = LambdaPermission(
            self.logical_id + authorizer_name + "AuthorizerPermission", attributes=self.passthrough_resource_attributes
        )
        lambda_permission.Action = "lambda:InvokeFunction"
        lambda_permission.FunctionName = authorizer_lambda_function_arn
        lambda_permission.Principal = "apigateway.amazonaws.com"
        lambda_permission.SourceArn = source_arn

        return lambda_permission

    def _construct_authorizer_lambda_permission(self) -> List[LambdaPermission]:
        if not self.auth:
            return []

        auth_properties = AuthProperties(**self.auth)
        authorizers = self._get_authorizers(auth_properties.Authorizers)  # type: ignore[no-untyped-call]

        if not authorizers:
            return []

        permissions = []

        for authorizer_name, authorizer in authorizers.items():
            # Construct permissions for Lambda Authorizers only
            if not authorizer.function_arn or authorizer.disable_function_default_permissions:
                continue

            permission = self._get_permission(authorizer_name, authorizer.function_arn)  # type: ignore[no-untyped-call]
            permissions.append(permission)

        return permissions

    def _set_default_authorizer(
        self,
        swagger_editor: SwaggerEditor,
        authorizers: Dict[str, ApiGatewayAuthorizer],
        default_authorizer: str,
        add_default_auth_to_preflight: bool = True,
    ) -> None:
        if not default_authorizer:
            return

        if not isinstance(default_authorizer, str):
            raise InvalidResourceException(
                self.logical_id,
                "DefaultAuthorizer is not a string.",
            )

        if not authorizers.get(default_authorizer) and default_authorizer != "AWS_IAM":
            raise InvalidResourceException(
                self.logical_id,
                "Unable to set DefaultAuthorizer because '"
                + default_authorizer
                + "' was not defined in 'Authorizers'.",
            )

        for path in swagger_editor.iter_on_path():
            swagger_editor.set_path_default_authorizer(
                path,
                default_authorizer,
                authorizers=authorizers,
                add_default_auth_to_preflight=add_default_auth_to_preflight,
            )

    def _set_default_apikey_required(self, swagger_editor: SwaggerEditor, required_options_api_key: bool) -> None:
        for path in swagger_editor.iter_on_path():
            swagger_editor.set_path_default_apikey_required(path, required_options_api_key)

    def _set_endpoint_configuration(self, rest_api: ApiGatewayRestApi, value: Union[str, Dict[str, Any]]) -> None:
        """
        Sets endpoint configuration property of AWS::ApiGateway::RestApi resource
        :param rest_api: RestApi resource
        :param string/dict value: Value to be set
        """
        if isinstance(value, dict) and value.get("Type"):
            rest_api.Parameters = {"endpointConfigurationTypes": value.get("Type")}
            rest_api.EndpointConfiguration = {"Types": [value.get("Type")]}
            if "VPCEndpointIds" in value:
                rest_api.EndpointConfiguration["VpcEndpointIds"] = value.get("VPCEndpointIds")
        else:
            rest_api.EndpointConfiguration = {"Types": [value]}
            rest_api.Parameters = {"endpointConfigurationTypes": value}
