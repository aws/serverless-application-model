import re
from typing import Any, cast

from samtranslator.model.apigatewayv2 import ApiGatewayV2Api, ApiGatewayV2ApiMapping, ApiGatewayV2DomainName
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.intrinsics import fnGetAtt, fnSub, ref
from samtranslator.model.lambda_ import LambdaPermission
from samtranslator.model.route53 import Route53RecordSetGroup
from samtranslator.translator.arn_generator import ArnGenerator
from samtranslator.translator.logical_id_generator import LogicalIdGenerator
from samtranslator.utils.types import Intrinsicable
from samtranslator.validator.value_validator import sam_expect


class ApiV2Generator:
    def __init__(  # noqa: PLR0913
        self,
        logical_id: str,
        stage_variables: dict[str, Intrinsicable[str]] | None,
        depends_on: list[str] | None,
        access_log_settings: dict[str, Intrinsicable[str]] | None = None,
        default_route_settings: dict[str, Any] | None = None,
        description: Intrinsicable[str] | None = None,
        disable_execute_api_endpoint: Intrinsicable[bool] | None = None,
        domain: dict[str, Any] | None = None,
        # ip address type?
        passthrough_resource_attributes: dict[str, Intrinsicable[str]] | None = None,
        resource_attributes: dict[str, Intrinsicable[str]] | None = None,
        route_settings: dict[str, Any] | None = None,
        tags: dict[str, Intrinsicable[str]] | None = None,
    ) -> None:
        """Constructs an API Generator class that generates API Gateway resources

        :param logical_id: Logical id of the SAM API Resource
        :param stage_variables: API Gateway Variables
        :param depends_on: Any resources that need to be depended on
        :param description: Description of the API Gateway resource
        :param access_log_settings: Whether to send access logs and where for Stage
        :param passthrough_resource_attributes: Attributes such as 'Condition' that are added to derived resources
        :param resource_attributes: Resource attributes to add to API resources
        :param tags: Stage and API Tags
        """
        self.logical_id = logical_id
        self.stage_variables = stage_variables
        self.depends_on = depends_on
        self.access_log_settings = access_log_settings
        self.default_route_settings = default_route_settings
        self.description = description
        self.disable_execute_api_endpoint = disable_execute_api_endpoint
        self.domain = domain
        self.passthrough_resource_attributes = passthrough_resource_attributes
        self.resource_attributes = resource_attributes
        self.route_settings = route_settings
        self.tags = tags
        self.default_tag_name = ""

    def _construct_api_domain(  # noqa: PLR0912, PLR0915
        self, api: ApiGatewayV2Api, route53_record_set_groups: dict[str, Route53RecordSetGroup]
    ) -> tuple[
        ApiGatewayV2DomainName | None,
        list[ApiGatewayV2ApiMapping] | None,
        Route53RecordSetGroup | None,
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
        if self.default_tag_name != "":
            domain.Tags = {self.default_tag_name: "SAM"}

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
        basepaths: list[str] | None
        basepath_value = self.domain.get("BasePath")
        if basepath_value and isinstance(basepath_value, str):
            basepaths = [basepath_value]
        elif basepath_value and isinstance(basepath_value, list):
            basepaths = cast(list[str] | None, basepath_value)
        else:
            basepaths = None
        basepath_resource_list = self._construct_basepath_mappings(basepaths, api, api_domain_name)

        # Create the Route53 RecordSetGroup resource
        record_set_group = self._construct_route53_recordsetgroup(
            self.domain, route53_record_set_groups, api_domain_name
        )

        return domain, basepath_resource_list, record_set_group

    def _construct_route53_recordsetgroup(
        self,
        custom_domain_config: dict[str, Any],
        route53_record_set_groups: dict[str, Route53RecordSetGroup],
        api_domain_name: str,
    ) -> Route53RecordSetGroup | None:
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
        self, basepaths: list[str] | None, api: ApiGatewayV2Api, api_domain_name: str
    ) -> list[ApiGatewayV2ApiMapping]:
        basepath_resource_list: list[ApiGatewayV2ApiMapping] = []

        if basepaths is None:
            basepath_mapping = ApiGatewayV2ApiMapping(
                self.logical_id + "ApiMapping", attributes=self.passthrough_resource_attributes
            )
            basepath_mapping.DomainName = ref(api_domain_name)
            basepath_mapping.ApiId = ref(api.logical_id)
            basepath_mapping.Stage = ref(api.logical_id + ".Stage")
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
                basepath_mapping.ApiId = ref(api.logical_id)
                basepath_mapping.Stage = ref(api.logical_id + ".Stage")
                # ignore leading and trailing `/` in the path name
                basepath_mapping.ApiMappingKey = path.strip("/")
                basepath_resource_list.extend([basepath_mapping])
        return basepath_resource_list

    def _construct_record_sets_for_domain(
        self, custom_domain_config: dict[str, Any], route53_config: dict[str, Any], api_domain_name: str
    ) -> list[dict[str, Any]]:
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
    def _update_route53_routing_policy_properties(route53_config: dict[str, Any], recordset: dict[str, Any]) -> None:
        if route53_config.get("Region") is not None:
            recordset["Region"] = route53_config.get("Region")
        if route53_config.get("SetIdentifier") is not None:
            recordset["SetIdentifier"] = route53_config.get("SetIdentifier")

    def _construct_alias_target(
        self, domain_config: dict[str, Any], route53_config: dict[str, Any], api_domain_name: str
    ) -> dict[str, Any]:
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

    def _get_authorizer_permission(
        self, permission_name: str, authorizer_lambda_function_arn: str, api_id: Any
    ) -> LambdaPermission:
        """Constructs and returns the Lambda Permission resource allowing API Gateway to invoke the authorizer.

        :param permission_name: logical ID for the permission resource
        :param authorizer_lambda_function_arn: ARN of the authorizer Lambda function
        :param api_id: API resource reference (Ref or GetAtt)
        :returns: the permission resource
        """
        resource = "${__ApiId__}/authorizers/*"
        source_arn = fnSub(
            ArnGenerator.generate_arn(partition="${AWS::Partition}", service="execute-api", resource=resource),
            {"__ApiId__": api_id},
        )

        lambda_permission = LambdaPermission(permission_name, attributes=self.passthrough_resource_attributes)
        lambda_permission.Action = "lambda:InvokeFunction"
        lambda_permission.FunctionName = authorizer_lambda_function_arn
        lambda_permission.Principal = "apigateway.amazonaws.com"
        lambda_permission.SourceArn = source_arn

        return lambda_permission
