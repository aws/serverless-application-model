import re
from collections import namedtuple
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.model.apigatewayv2 import (
    ApiGatewayV2ApiMapping,
    ApiGatewayV2Authorizer,
    ApiGatewayV2DomainName,
    ApiGatewayV2HttpApi,
    ApiGatewayV2Stage,
)
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.intrinsics import fnGetAtt, fnSub, is_intrinsic, is_intrinsic_no_value, ref
from samtranslator.model.lambda_ import LambdaPermission
from samtranslator.model.route53 import Route53RecordSetGroup
from samtranslator.model.s3_utils.uri_parser import parse_s3_uri
from samtranslator.open_api.open_api import OpenApiEditor
from samtranslator.translator.arn_generator import ArnGenerator
from samtranslator.translator.logical_id_generator import LogicalIdGenerator
from samtranslator.utils.types import Intrinsicable
from samtranslator.utils.utils import InvalidValueType, dict_deep_get
from samtranslator.validator.value_validator import sam_expect

_CORS_WILDCARD = "*"
CorsProperties = namedtuple(
    "CorsProperties", ["AllowMethods", "AllowHeaders", "AllowOrigins", "MaxAge", "ExposeHeaders", "AllowCredentials"]
)
CorsProperties.__new__.__defaults__ = (None, None, None, None, None, False)

AuthProperties = namedtuple("AuthProperties", ["Authorizers", "DefaultAuthorizer", "EnableIamAuthorizer"])
AuthProperties.__new__.__defaults__ = (None, None, False)
DefaultStageName = "$default"
HttpApiTagName = "httpapi:createdBy"


class HttpApiGenerator:
    def __init__(  # noqa: too-many-arguments
        self,
        logical_id: str,
        stage_variables: Optional[Dict[str, Intrinsicable[str]]],
        depends_on: Optional[List[str]],
        definition_body: Optional[Dict[str, Any]],
        definition_uri: Optional[Intrinsicable[str]],
        name: Optional[Any],
        stage_name: Optional[Intrinsicable[str]],
        tags: Optional[Dict[str, Intrinsicable[str]]] = None,
        auth: Optional[Dict[str, Intrinsicable[str]]] = None,
        cors_configuration: Optional[Union[bool, Dict[str, Any]]] = None,
        access_log_settings: Optional[Dict[str, Intrinsicable[str]]] = None,
        route_settings: Optional[Dict[str, Any]] = None,
        default_route_settings: Optional[Dict[str, Any]] = None,
        resource_attributes: Optional[Dict[str, Intrinsicable[str]]] = None,
        passthrough_resource_attributes: Optional[Dict[str, Intrinsicable[str]]] = None,
        domain: Optional[Dict[str, Any]] = None,
        fail_on_warnings: Optional[Intrinsicable[bool]] = None,
        description: Optional[Intrinsicable[str]] = None,
        disable_execute_api_endpoint: Optional[Intrinsicable[bool]] = None,
    ) -> None:
        """Constructs an API Generator class that generates API Gateway resources

        :param logical_id: Logical id of the SAM API Resource
        :param stage_variables: API Gateway Variables
        :param depends_on: Any resources that need to be depended on
        :param definition_body: API definition
        :param definition_uri: URI to API definition
        :param name: Name of the API Gateway resource
        :param stage_name: Name of the Stage
        :param tags: Stage and API Tags
        :param access_log_settings: Whether to send access logs and where for Stage
        :param resource_attributes: Resource attributes to add to API resources
        :param passthrough_resource_attributes: Attributes such as `Condition` that are added to derived resources
        :param description: Description of the API Gateway resource
        """
        self.logical_id = logical_id
        self.stage_variables = stage_variables
        self.depends_on = depends_on
        self.definition_body = definition_body
        self.definition_uri = definition_uri
        self.stage_name = stage_name
        self.name = name
        if not self.stage_name:
            self.stage_name = DefaultStageName
        self.auth = auth
        self.cors_configuration = cors_configuration
        self.tags = tags
        self.access_log_settings = access_log_settings
        self.route_settings = route_settings
        self.default_route_settings = default_route_settings
        self.resource_attributes = resource_attributes
        self.passthrough_resource_attributes = passthrough_resource_attributes
        self.domain = domain
        self.fail_on_warnings = fail_on_warnings
        self.description = description
        self.disable_execute_api_endpoint = disable_execute_api_endpoint

    def _construct_http_api(self) -> ApiGatewayV2HttpApi:
        """Constructs and returns the ApiGatewayV2 HttpApi.

        :returns: the HttpApi to which this SAM Api corresponds
        :rtype: model.apigatewayv2.ApiGatewayHttpApi
        """
        http_api = ApiGatewayV2HttpApi(self.logical_id, depends_on=self.depends_on, attributes=self.resource_attributes)

        if self.definition_uri and self.definition_body:
            raise InvalidResourceException(
                self.logical_id, "Specify either 'DefinitionUri' or 'DefinitionBody' property and not both."
            )
        if self.cors_configuration:
            # call this method to add cors in open api
            self._add_cors()

        self._add_auth()
        self._add_tags()

        if self.fail_on_warnings:
            http_api.FailOnWarnings = self.fail_on_warnings

        if self.disable_execute_api_endpoint is not None:
            self._add_endpoint_configuration()

        self._add_title()
        self._add_description()
        self._update_default_path()

        if self.definition_uri:
            http_api.BodyS3Location = self._construct_body_s3_dict(self.definition_uri)
        elif self.definition_body:
            http_api.Body = self.definition_body
        else:
            raise InvalidResourceException(
                self.logical_id,
                "'DefinitionUri' or 'DefinitionBody' are required properties of an "
                "'AWS::Serverless::HttpApi'. Add a value for one of these properties or "
                "add a 'HttpApi' event to an 'AWS::Serverless::Function'.",
            )

        return http_api

    def _add_endpoint_configuration(self) -> None:
        """Add disableExecuteApiEndpoint if it is set in SAM
        HttpApi doesn't have vpcEndpointIds

        Note:
        DisableExecuteApiEndpoint as a property of AWS::ApiGatewayV2::Api needs both DefinitionBody and
        DefinitionUri to be None. However, if neither DefinitionUri nor DefinitionBody are specified,
        SAM will generate a openapi definition body based on template configuration.
        https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-resource-api.html#sam-api-definitionbody
        For this reason, we always put DisableExecuteApiEndpoint into openapi object.

        """
        if self.disable_execute_api_endpoint is not None and not self.definition_body:
            raise InvalidResourceException(
                self.logical_id, "DisableExecuteApiEndpoint works only within 'DefinitionBody' property."
            )
        editor = OpenApiEditor(self.definition_body)

        # if DisableExecuteApiEndpoint is set in both definition_body and as a property,
        # SAM merges and overrides the disableExecuteApiEndpoint in definition_body with headers of
        # "x-amazon-apigateway-endpoint-configuration"
        editor.add_endpoint_config(self.disable_execute_api_endpoint)

        # Assign the OpenApi back to template
        self.definition_body = editor.openapi

    def _add_cors(self) -> None:
        """
        Add CORS configuration if CORSConfiguration property is set in SAM.
        Adds CORS configuration only if DefinitionBody is present and
        APIGW extension for CORS is not present in the DefinitionBody
        """

        if self.cors_configuration and not self.definition_body:
            raise InvalidResourceException(
                self.logical_id, "Cors works only with inline OpenApi specified in 'DefinitionBody' property."
            )

        # If cors configuration is set to true add * to the allow origins.
        # This also support referencing the value as a parameter
        if isinstance(self.cors_configuration, bool):
            # if cors config is true add Origins as "'*'"
            properties = CorsProperties(AllowOrigins=[_CORS_WILDCARD])  # type: ignore[call-arg]

        elif is_intrinsic(self.cors_configuration):
            # Just set Origin property. Intrinsics will be handledOthers will be defaults
            properties = CorsProperties(AllowOrigins=self.cors_configuration)  # type: ignore[call-arg]

        elif isinstance(self.cors_configuration, dict):
            # Make sure keys in the dict are recognized
            if not all(key in CorsProperties._fields for key in self.cors_configuration):
                raise InvalidResourceException(self.logical_id, "Invalid value for 'Cors' property.")

            properties = CorsProperties(**self.cors_configuration)

        else:
            raise InvalidResourceException(self.logical_id, "Invalid value for 'Cors' property.")

        if not OpenApiEditor.is_valid(self.definition_body):
            raise InvalidResourceException(
                self.logical_id,
                "Unable to add Cors configuration because "
                "'DefinitionBody' does not contain a valid "
                "OpenApi definition.",
            )

        if properties.AllowCredentials is True and properties.AllowOrigins == [_CORS_WILDCARD]:
            raise InvalidResourceException(
                self.logical_id,
                "Unable to add Cors configuration because "
                "'AllowCredentials' can not be true when "
                "'AllowOrigin' is \"'*'\" or not set.",
            )

        editor = OpenApiEditor(self.definition_body)
        # if CORS is set in both definition_body and as a CorsConfiguration property,
        # SAM merges and overrides the cors headers in definition_body with headers of CorsConfiguration
        editor.add_cors(  # type: ignore[no-untyped-call]
            properties.AllowOrigins,
            properties.AllowHeaders,
            properties.AllowMethods,
            properties.ExposeHeaders,
            properties.MaxAge,
            properties.AllowCredentials,
        )

        # Assign the OpenApi back to template
        self.definition_body = editor.openapi

    def _update_default_path(self) -> None:
        # Only do the following if FailOnWarnings is enabled for backward compatibility.
        if not self.fail_on_warnings or not self.definition_body:
            return

        # Using default stage name generate warning during deployment
        #   Warnings found during import: Parse issue: attribute paths.
        #   Resource $default should start with / (Service: AmazonApiGatewayV2; Status Code: 400;
        # Deployment fails when FailOnWarnings is true: https://github.com/aws/serverless-application-model/issues/2297
        paths: Dict[str, Any] = self.definition_body.get("paths", {})
        if DefaultStageName in paths:
            paths[f"/{DefaultStageName}"] = paths.pop(DefaultStageName)

    def _construct_api_domain(  # noqa: too-many-branches
        self, http_api: ApiGatewayV2HttpApi, route53_record_set_groups: Dict[str, Route53RecordSetGroup]
    ) -> Tuple[
        Optional[ApiGatewayV2DomainName],
        Optional[List[ApiGatewayV2ApiMapping]],
        Optional[Route53RecordSetGroup],
    ]:
        """
        Constructs and returns the ApiGateway Domain and BasepathMapping
        """
        if self.domain is None:
            return None, None, None

        custom_domain_config = self.domain  # not creating a copy as we will mutate it
        domain_name = custom_domain_config.get("DomainName")

        domain_name_config = {}

        certificate_arn = custom_domain_config.get("CertificateArn")
        if domain_name is None or certificate_arn is None:
            raise InvalidResourceException(
                self.logical_id, "Custom Domains only works if both DomainName and CertificateArn are provided."
            )
        domain_name_config["CertificateArn"] = certificate_arn

        api_domain_name = "{}{}".format("ApiGatewayDomainNameV2", LogicalIdGenerator("", domain_name).gen())
        custom_domain_config["ApiDomainName"] = api_domain_name

        domain = ApiGatewayV2DomainName(api_domain_name, attributes=self.passthrough_resource_attributes)
        domain.DomainName = domain_name
        domain.Tags = self.tags

        endpoint_config = custom_domain_config.get("EndpointConfiguration")
        if endpoint_config is None:
            endpoint_config = "REGIONAL"
            # to make sure that default is always REGIONAL
            custom_domain_config["EndpointConfiguration"] = "REGIONAL"
        elif endpoint_config not in ["REGIONAL"]:
            raise InvalidResourceException(
                self.logical_id,
                "EndpointConfiguration for Custom Domains must be one of {}.".format(["REGIONAL"]),
            )
        domain_name_config["EndpointType"] = endpoint_config

        ownership_verification_certificate_arn = custom_domain_config.get("OwnershipVerificationCertificateArn")
        if ownership_verification_certificate_arn:
            domain_name_config["OwnershipVerificationCertificateArn"] = ownership_verification_certificate_arn

        security_policy = custom_domain_config.get("SecurityPolicy")
        if security_policy:
            domain_name_config["SecurityPolicy"] = security_policy

        domain.DomainNameConfigurations = [domain_name_config]

        mutual_tls_auth = custom_domain_config.get("MutualTlsAuthentication", None)
        if mutual_tls_auth:
            if isinstance(mutual_tls_auth, dict):
                if not set(mutual_tls_auth.keys()).issubset({"TruststoreUri", "TruststoreVersion"}):
                    invalid_keys = []
                    for key in mutual_tls_auth:
                        if key not in {"TruststoreUri", "TruststoreVersion"}:
                            invalid_keys.append(key)
                    invalid_keys.sort()
                    raise InvalidResourceException(
                        ",".join(invalid_keys),
                        "Available MutualTlsAuthentication fields are {}.".format(
                            ["TruststoreUri", "TruststoreVersion"]
                        ),
                    )
                domain.MutualTlsAuthentication = {}
                if mutual_tls_auth.get("TruststoreUri", None):
                    domain.MutualTlsAuthentication["TruststoreUri"] = mutual_tls_auth["TruststoreUri"]
                if mutual_tls_auth.get("TruststoreVersion", None):
                    domain.MutualTlsAuthentication["TruststoreVersion"] = mutual_tls_auth["TruststoreVersion"]
            else:
                raise InvalidResourceException(
                    self.logical_id,
                    "MutualTlsAuthentication must be a map with at least one of the following fields {}.".format(
                        ["TruststoreUri", "TruststoreVersion"]
                    ),
                )

        # Create BasepathMappings
        basepaths: Optional[List[str]]
        basepath_value = self.domain.get("BasePath")
        if basepath_value and isinstance(basepath_value, str):
            basepaths = [basepath_value]
        elif basepath_value and isinstance(basepath_value, list):
            basepaths = cast(Optional[List[str]], basepath_value)
        else:
            basepaths = None
        basepath_resource_list = self._construct_basepath_mappings(basepaths, http_api, api_domain_name)

        # Create the Route53 RecordSetGroup resource
        record_set_group = self._construct_route53_recordsetgroup(
            self.domain, route53_record_set_groups, api_domain_name
        )

        return domain, basepath_resource_list, record_set_group

    def _construct_route53_recordsetgroup(
        self,
        custom_domain_config: Dict[str, Any],
        route53_record_set_groups: Dict[str, Route53RecordSetGroup],
        api_domain_name: str,
    ) -> Optional[Route53RecordSetGroup]:
        route53_config = custom_domain_config.get("Route53")
        if route53_config is None:
            return None
        sam_expect(route53_config, self.logical_id, "Domain.Route53").to_be_a_map()
        if route53_config.get("HostedZoneId") is None and route53_config.get("HostedZoneName") is None:
            raise InvalidResourceException(
                self.logical_id,
                "HostedZoneId or HostedZoneName is required to enable Route53 support on Custom Domains.",
            )

        logical_id_suffix = LogicalIdGenerator(
            "", route53_config.get("HostedZoneId") or route53_config.get("HostedZoneName")
        ).gen()
        logical_id = "RecordSetGroup" + logical_id_suffix

        matching_record_set_group = route53_record_set_groups.get(logical_id)
        if matching_record_set_group:
            record_set_group = matching_record_set_group
        else:
            record_set_group = Route53RecordSetGroup(logical_id, attributes=self.passthrough_resource_attributes)
            if "HostedZoneId" in route53_config:
                record_set_group.HostedZoneId = route53_config.get("HostedZoneId")
            elif "HostedZoneName" in route53_config:
                record_set_group.HostedZoneName = route53_config.get("HostedZoneName")
            record_set_group.RecordSets = []
            route53_record_set_groups[logical_id] = record_set_group

        if record_set_group.RecordSets is None:
            record_set_group.RecordSets = []
        record_set_group.RecordSets += self._construct_record_sets_for_domain(
            custom_domain_config, route53_config, api_domain_name
        )
        return record_set_group

    def _construct_basepath_mappings(
        self, basepaths: Optional[List[str]], http_api: ApiGatewayV2HttpApi, api_domain_name: str
    ) -> List[ApiGatewayV2ApiMapping]:
        basepath_resource_list: List[ApiGatewayV2ApiMapping] = []

        if basepaths is None:
            basepath_mapping = ApiGatewayV2ApiMapping(
                self.logical_id + "ApiMapping", attributes=self.passthrough_resource_attributes
            )
            basepath_mapping.DomainName = ref(api_domain_name)
            basepath_mapping.ApiId = ref(http_api.logical_id)
            basepath_mapping.Stage = ref(http_api.logical_id + ".Stage")
            basepath_resource_list.extend([basepath_mapping])
        else:
            for path in basepaths:
                # search for invalid characters in the path and raise error if there are
                invalid_regex = r"[^0-9a-zA-Z\/\-\_]+"

                if not isinstance(path, str):
                    raise InvalidResourceException(self.logical_id, "Basepath must be a string.")

                if re.search(invalid_regex, path) is not None:
                    raise InvalidResourceException(self.logical_id, "Invalid Basepath name provided.")

                logical_id = "{}{}{}".format(self.logical_id, re.sub(r"[\-_/]+", "", path), "ApiMapping")
                basepath_mapping = ApiGatewayV2ApiMapping(logical_id, attributes=self.passthrough_resource_attributes)
                basepath_mapping.DomainName = ref(api_domain_name)
                basepath_mapping.ApiId = ref(http_api.logical_id)
                basepath_mapping.Stage = ref(http_api.logical_id + ".Stage")
                # ignore leading and trailing `/` in the path name
                basepath_mapping.ApiMappingKey = path.strip("/")
                basepath_resource_list.extend([basepath_mapping])
        return basepath_resource_list

    def _construct_record_sets_for_domain(
        self, custom_domain_config: Dict[str, Any], route53_config: Dict[str, Any], api_domain_name: str
    ) -> List[Dict[str, Any]]:
        recordset_list = []

        recordset = {}
        recordset["Name"] = custom_domain_config.get("DomainName")
        recordset["Type"] = "A"
        recordset["AliasTarget"] = self._construct_alias_target(custom_domain_config, route53_config, api_domain_name)
        self._update_route53_routing_policy_properties(route53_config, recordset)
        recordset_list.append(recordset)

        if route53_config.get("IpV6") is not None and route53_config.get("IpV6") is True:
            recordset_ipv6 = {}
            recordset_ipv6["Name"] = custom_domain_config.get("DomainName")
            recordset_ipv6["Type"] = "AAAA"
            recordset_ipv6["AliasTarget"] = self._construct_alias_target(
                custom_domain_config, route53_config, api_domain_name
            )
            self._update_route53_routing_policy_properties(route53_config, recordset_ipv6)
            recordset_list.append(recordset_ipv6)

        return recordset_list

    @staticmethod
    def _update_route53_routing_policy_properties(route53_config: Dict[str, Any], recordset: Dict[str, Any]) -> None:
        if route53_config.get("Region") is not None:
            recordset["Region"] = route53_config.get("Region")
        if route53_config.get("SetIdentifier") is not None:
            recordset["SetIdentifier"] = route53_config.get("SetIdentifier")

    def _construct_alias_target(
        self, domain_config: Dict[str, Any], route53_config: Dict[str, Any], api_domain_name: str
    ) -> Dict[str, Any]:
        alias_target = {}
        target_health = route53_config.get("EvaluateTargetHealth")

        if target_health is not None:
            alias_target["EvaluateTargetHealth"] = target_health
        if domain_config.get("EndpointConfiguration") == "REGIONAL":
            alias_target["HostedZoneId"] = fnGetAtt(api_domain_name, "RegionalHostedZoneId")
            alias_target["DNSName"] = fnGetAtt(api_domain_name, "RegionalDomainName")
        else:
            raise InvalidResourceException(
                self.logical_id,
                "Only REGIONAL endpoint is supported on HTTP APIs.",
            )
        return alias_target

    def _add_auth(self) -> None:
        """
        Add Auth configuration to the OAS file, if necessary
        """
        if not self.auth:
            return

        if self.auth and not self.definition_body:
            raise InvalidResourceException(
                self.logical_id, "Auth works only with inline OpenApi specified in the 'DefinitionBody' property."
            )

        # Make sure keys in the dict are recognized
        if not all(key in AuthProperties._fields for key in self.auth):
            raise InvalidResourceException(self.logical_id, "Invalid value for 'Auth' property")

        if not OpenApiEditor.is_valid(self.definition_body):
            raise InvalidResourceException(
                self.logical_id,
                "Unable to add Auth configuration because 'DefinitionBody' does not contain a valid OpenApi definition.",
            )
        open_api_editor = OpenApiEditor(self.definition_body)
        auth_properties = AuthProperties(**self.auth)
        authorizers = self._get_authorizers(auth_properties.Authorizers, auth_properties.EnableIamAuthorizer)

        # authorizers is guaranteed to return a value or raise an exception
        open_api_editor.add_authorizers_security_definitions(authorizers)
        self._set_default_authorizer(open_api_editor, authorizers, auth_properties.DefaultAuthorizer)
        self.definition_body = open_api_editor.openapi

    def _add_tags(self) -> None:
        """
        Adds tags to the Http Api, including a default SAM tag.
        """
        if self.tags and not self.definition_body:
            raise InvalidResourceException(
                self.logical_id, "Tags works only with inline OpenApi specified in the 'DefinitionBody' property."
            )

        if not self.definition_body:
            return

        if self.tags and not OpenApiEditor.is_valid(self.definition_body):
            raise InvalidResourceException(
                self.logical_id,
                "Unable to add `Tags` because 'DefinitionBody' does not contain a valid OpenApi definition.",
            )
        if not OpenApiEditor.is_valid(self.definition_body):
            return

        if not self.tags:
            self.tags = {}
        self.tags[HttpApiTagName] = "SAM"

        open_api_editor = OpenApiEditor(self.definition_body)

        # authorizers is guaranteed to return a value or raise an exception
        open_api_editor.add_tags(self.tags)
        self.definition_body = open_api_editor.openapi

    def _get_permission(
        self, authorizer_name: str, authorizer_lambda_function_arn: str, api_arn: str
    ) -> LambdaPermission:
        """Constructs and returns the Lambda Permission resource allowing the Authorizer to invoke the function.

        :returns: the permission resource
        :rtype: model.lambda_.LambdaPermission
        """

        resource = "${__ApiId__}/authorizers/*"
        source_arn = fnSub(
            ArnGenerator.generate_arn(partition="${AWS::Partition}", service="execute-api", resource=resource),
            {"__ApiId__": api_arn},
        )

        lambda_permission = LambdaPermission(
            self.logical_id + authorizer_name + "AuthorizerPermission", attributes=self.passthrough_resource_attributes
        )
        lambda_permission.Action = "lambda:InvokeFunction"
        lambda_permission.FunctionName = authorizer_lambda_function_arn
        lambda_permission.Principal = "apigateway.amazonaws.com"
        lambda_permission.SourceArn = source_arn

        return lambda_permission

    def _construct_authorizer_lambda_permission(self, http_api: ApiGatewayV2HttpApi) -> List[LambdaPermission]:
        if not self.auth:
            return []

        auth_properties = AuthProperties(**self.auth)
        authorizers = self._get_authorizers(auth_properties.Authorizers, auth_properties.EnableIamAuthorizer)

        if not authorizers:
            return []

        permissions: List[LambdaPermission] = []

        for authorizer_name, authorizer in authorizers.items():
            # Construct permissions for Lambda Authorizers only
            # Http Api shouldn't create the permissions by default (when its none)
            if (
                not authorizer.function_arn
                or authorizer.enable_function_default_permissions is None
                or not authorizer.enable_function_default_permissions
            ):
                continue

            permission = self._get_permission(
                authorizer_name, authorizer.function_arn, http_api.get_runtime_attr("http_api_id")
            )
            permissions.append(permission)

        return permissions

    def _set_default_authorizer(
        self,
        open_api_editor: OpenApiEditor,
        authorizers: Dict[str, ApiGatewayV2Authorizer],
        default_authorizer: Optional[Any],
    ) -> None:
        """
        Sets the default authorizer if one is given in the template
        :param open_api_editor: editor object that contains the OpenApi definition
        :param authorizers: authorizer definitions converted from the API auth section
        :param default_authorizer: name of the default authorizer
        :param api_authorizers: API auth section authorizer defintions
        """
        if not default_authorizer:
            return

        if is_intrinsic_no_value(default_authorizer):
            return

        sam_expect(default_authorizer, self.logical_id, "Auth.DefaultAuthorizer").to_be_a_string()

        if not authorizers.get(default_authorizer):
            raise InvalidResourceException(
                self.logical_id,
                "Unable to set DefaultAuthorizer because '"
                + default_authorizer
                + "' was not defined in 'Authorizers'.",
            )

        for path in open_api_editor.iter_on_path():
            open_api_editor.set_path_default_authorizer(path, default_authorizer, authorizers)

    def _get_authorizers(
        self, authorizers_config: Any, enable_iam_authorizer: bool = False
    ) -> Dict[str, ApiGatewayV2Authorizer]:
        """
        Returns all authorizers for an API as an ApiGatewayV2Authorizer object
        :param authorizers_config: authorizer configuration from the API Auth section
        :param enable_iam_authorizer: if True add an "AWS_IAM" authorizer
        """
        authorizers: Dict[str, ApiGatewayV2Authorizer] = {}

        if enable_iam_authorizer is True:
            authorizers["AWS_IAM"] = ApiGatewayV2Authorizer(is_aws_iam_authorizer=True)  # type: ignore[no-untyped-call]

        # If all the customer wants to do is enable the IAM authorizer the authorizers_config will be None.
        if not authorizers_config:
            return authorizers

        sam_expect(authorizers_config, self.logical_id, "Auth.Authorizers").to_be_a_map()

        for authorizer_name, authorizer in authorizers_config.items():
            sam_expect(authorizer, self.logical_id, f"Auth.Authorizers.{authorizer_name}").to_be_a_map()

            if "OpenIdConnectUrl" in authorizer:
                raise InvalidResourceException(
                    self.logical_id,
                    "'OpenIdConnectUrl' is no longer a supported property for authorizer '%s'. Please refer to the AWS SAM documentation."
                    % (authorizer_name),
                )
            authorizers[authorizer_name] = ApiGatewayV2Authorizer(  # type: ignore[no-untyped-call]
                api_logical_id=self.logical_id,
                name=authorizer_name,
                authorization_scopes=authorizer.get("AuthorizationScopes"),
                jwt_configuration=authorizer.get("JwtConfiguration"),
                id_source=authorizer.get("IdentitySource"),
                function_arn=authorizer.get("FunctionArn"),
                function_invoke_role=authorizer.get("FunctionInvokeRole"),
                identity=authorizer.get("Identity"),
                authorizer_payload_format_version=authorizer.get("AuthorizerPayloadFormatVersion"),
                enable_simple_responses=authorizer.get("EnableSimpleResponses"),
                enable_function_default_permissions=authorizer.get("EnableFunctionDefaultPermissions"),
            )
        return authorizers

    def _construct_body_s3_dict(self, definition_url: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Constructs the HttpApi's `BodyS3Location property`, from the SAM Api's DefinitionUri property.
        :returns: a BodyS3Location dict, containing the S3 Bucket, Key, and Version of the OpenApi definition
        :rtype: dict
        """
        if isinstance(definition_url, dict):
            if not definition_url.get("Bucket", None) or not definition_url.get("Key", None):
                # DefinitionUri is a dictionary but does not contain Bucket or Key property
                raise InvalidResourceException(
                    self.logical_id, "'DefinitionUri' requires Bucket and Key properties to be specified."
                )
            s3_pointer = definition_url

        else:
            # DefinitionUri is a string
            _parsed_s3_pointer = parse_s3_uri(definition_url)
            if _parsed_s3_pointer is None:
                raise InvalidResourceException(
                    self.logical_id,
                    "'DefinitionUri' is not a valid S3 Uri of the form "
                    "'s3://bucket/key' with optional versionId query parameter.",
                )
            s3_pointer = _parsed_s3_pointer

        body_s3 = {"Bucket": s3_pointer["Bucket"], "Key": s3_pointer["Key"]}
        if "Version" in s3_pointer:
            body_s3["Version"] = s3_pointer["Version"]
        return body_s3

    def _construct_stage(self) -> Optional[ApiGatewayV2Stage]:
        """Constructs and returns the ApiGatewayV2 Stage.

        :returns: the Stage to which this SAM Api corresponds
        :rtype: model.apigatewayv2.ApiGatewayV2Stage
        """

        # If there are no special configurations, don't create a stage and use the default
        if (
            not self.stage_name
            and not self.stage_variables
            and not self.access_log_settings
            and not self.default_route_settings
            and not self.route_settings
        ):
            return None

        # If StageName is some intrinsic function, then don't prefix the Stage's logical ID
        # This will NOT create duplicates because we allow only ONE stage per API resource
        stage_name_prefix = self.stage_name if isinstance(self.stage_name, str) else ""
        if stage_name_prefix.isalnum():
            stage_logical_id = self.logical_id + stage_name_prefix + "Stage"
        elif stage_name_prefix == DefaultStageName:
            stage_logical_id = self.logical_id + "ApiGatewayDefaultStage"
        else:
            generator = LogicalIdGenerator(self.logical_id + "Stage", stage_name_prefix)
            stage_logical_id = generator.gen()
        stage = ApiGatewayV2Stage(stage_logical_id, attributes=self.passthrough_resource_attributes)
        stage.ApiId = ref(self.logical_id)
        stage.StageName = self.stage_name
        stage.StageVariables = self.stage_variables
        stage.AccessLogSettings = self.access_log_settings
        stage.DefaultRouteSettings = self.default_route_settings
        stage.Tags = self.tags
        stage.AutoDeploy = True
        stage.RouteSettings = self.route_settings

        return stage

    def _add_description(self) -> None:
        """Add description to DefinitionBody if Description property is set in SAM"""
        if not self.description:
            return

        if not self.definition_body:
            raise InvalidResourceException(
                self.logical_id,
                "Description works only with inline OpenApi specified in the 'DefinitionBody' property.",
            )
        try:
            description_in_definition_body = dict_deep_get(self.definition_body, "info.description")
        except InvalidValueType as ex:
            raise InvalidResourceException(
                self.logical_id,
                f"Invalid 'DefinitionBody': {str(ex)}'.",
            ) from ex
        if description_in_definition_body:
            raise InvalidResourceException(
                self.logical_id,
                "Unable to set Description because it is already defined within inline OpenAPI specified in the "
                "'DefinitionBody' property.",
            )

        open_api_editor = OpenApiEditor(self.definition_body)
        open_api_editor.add_description(self.description)
        self.definition_body = open_api_editor.openapi

    def _add_title(self) -> None:
        if not self.name:
            return

        if not self.definition_body:
            raise InvalidResourceException(
                self.logical_id,
                "Name works only with inline OpenApi specified in the 'DefinitionBody' property.",
            )

        try:
            title_in_definition_body = dict_deep_get(self.definition_body, "info.title")
        except InvalidValueType as ex:
            raise InvalidResourceException(
                self.logical_id,
                f"Invalid 'DefinitionBody': {str(ex)}.",
            ) from ex
        if title_in_definition_body != OpenApiEditor._DEFAULT_OPENAPI_TITLE:
            raise InvalidResourceException(
                self.logical_id,
                "Unable to set Name because it is already defined within inline OpenAPI specified in the "
                "'DefinitionBody' property.",
            )

        open_api_editor = OpenApiEditor(self.definition_body)
        open_api_editor.add_title(self.name)
        self.definition_body = open_api_editor.openapi

    @cw_timer(prefix="Generator", name="HttpApi")
    def to_cloudformation(
        self, route53_record_set_groups: Dict[str, Route53RecordSetGroup]
    ) -> Tuple[
        ApiGatewayV2HttpApi,
        Optional[ApiGatewayV2Stage],
        Optional[ApiGatewayV2DomainName],
        Optional[List[ApiGatewayV2ApiMapping]],
        Optional[Route53RecordSetGroup],
        Optional[List[LambdaPermission]],
    ]:
        """Generates CloudFormation resources from a SAM HTTP API resource

        :returns: a tuple containing the HttpApi and Stage for an empty Api.
        :rtype: tuple
        """
        http_api = self._construct_http_api()
        domain, basepath_mapping, route53 = self._construct_api_domain(http_api, route53_record_set_groups)
        permissions = self._construct_authorizer_lambda_permission(http_api)
        stage = self._construct_stage()

        return http_api, stage, domain, basepath_mapping, route53, permissions
