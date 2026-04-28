from collections import namedtuple
from typing import Any, Union

from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.model.api.apiv2_generator import ApiV2Generator
from samtranslator.model.apigatewayv2 import (
    ApiGatewayV2ApiMapping,
    ApiGatewayV2Authorizer,
    ApiGatewayV2DomainName,
    ApiGatewayV2HttpApi,
    ApiGatewayV2Stage,
)
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.intrinsics import is_intrinsic, is_intrinsic_no_value, ref
from samtranslator.model.lambda_ import LambdaPermission
from samtranslator.model.route53 import Route53RecordSetGroup
from samtranslator.model.s3_utils.uri_parser import parse_s3_uri
from samtranslator.open_api.open_api import OpenApiEditor
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


class HttpApiGenerator(ApiV2Generator):
    def __init__(  # noqa: PLR0913
        self,
        logical_id: str,
        stage_variables: dict[str, Intrinsicable[str]] | None,
        depends_on: list[str] | None,
        definition_body: dict[str, Any] | None,
        definition_uri: Intrinsicable[str] | None,
        name: Any | None,
        stage_name: Intrinsicable[str] | None,
        tags: dict[str, Intrinsicable[str]] | None = None,
        auth: dict[str, Intrinsicable[str]] | None = None,
        cors_configuration: Union[bool, dict[str, Any]] | None = None,
        access_log_settings: dict[str, Intrinsicable[str]] | None = None,
        route_settings: dict[str, Any] | None = None,
        default_route_settings: dict[str, Any] | None = None,
        resource_attributes: dict[str, Intrinsicable[str]] | None = None,
        passthrough_resource_attributes: dict[str, Intrinsicable[str]] | None = None,
        domain: dict[str, Any] | None = None,
        fail_on_warnings: Intrinsicable[bool] | None = None,
        description: Intrinsicable[str] | None = None,
        disable_execute_api_endpoint: Intrinsicable[bool] | None = None,
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
        super().__init__(
            logical_id,
            stage_variables,
            depends_on,
            access_log_settings,
            default_route_settings,
            description,
            disable_execute_api_endpoint,
            domain,
            passthrough_resource_attributes,
            resource_attributes,
            route_settings,
            tags,
        )
        self.definition_body = definition_body
        self.definition_uri = definition_uri
        self.fail_on_warnings = fail_on_warnings
        self.name = name
        self.stage_name = stage_name
        if not self.stage_name:
            self.stage_name = DefaultStageName
        self.auth = auth
        self.cors_configuration = cors_configuration
        self.default_tag_name = HttpApiTagName

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
            for key in self.cors_configuration:
                if key not in CorsProperties._fields:
                    raise InvalidResourceException(self.logical_id, f"Invalid key '{key}' for 'Cors' property.")

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
        paths: dict[str, Any] = self.definition_body.get("paths", {})
        if DefaultStageName in paths:
            paths[f"/{DefaultStageName}"] = paths.pop(DefaultStageName)

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
        self.tags[self.default_tag_name] = "SAM"

        open_api_editor = OpenApiEditor(self.definition_body)

        # authorizers is guaranteed to return a value or raise an exception
        open_api_editor.add_tags(self.tags)
        self.definition_body = open_api_editor.openapi

    def _construct_authorizer_lambda_permission(self, http_api: ApiGatewayV2HttpApi) -> list[LambdaPermission]:
        if not self.auth:
            return []

        auth_properties = AuthProperties(**self.auth)
        authorizers = self._get_authorizers(auth_properties.Authorizers, auth_properties.EnableIamAuthorizer)

        if not authorizers:
            return []

        permissions: list[LambdaPermission] = []

        for authorizer_name, authorizer in authorizers.items():
            # Construct permissions for Lambda Authorizers only
            # Http Api shouldn't create the permissions by default (when its none)
            if (
                not authorizer.function_arn
                or authorizer.enable_function_default_permissions is None
                or not authorizer.enable_function_default_permissions
            ):
                continue

            permission = self._get_authorizer_permission(
                self.logical_id + authorizer_name + "AuthorizerPermission",
                authorizer.function_arn,
                http_api.get_runtime_attr("http_api_id"),
            )
            permissions.append(permission)

        return permissions

    def _set_default_authorizer(
        self,
        open_api_editor: OpenApiEditor,
        authorizers: dict[str, ApiGatewayV2Authorizer],
        default_authorizer: Any | None,
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
    ) -> dict[str, ApiGatewayV2Authorizer]:
        """
        Returns all authorizers for an API as an ApiGatewayV2Authorizer object
        :param authorizers_config: authorizer configuration from the API Auth section
        :param enable_iam_authorizer: if True add an "AWS_IAM" authorizer
        """
        authorizers: dict[str, ApiGatewayV2Authorizer] = {}

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
                    f"'OpenIdConnectUrl' is no longer a supported property for authorizer '{authorizer_name}'. Please refer to the AWS SAM documentation.",
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

    def _construct_body_s3_dict(self, definition_url: Union[str, dict[str, Any]]) -> dict[str, Any]:
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

    def _construct_stage(self) -> ApiGatewayV2Stage | None:
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
                f"Invalid 'DefinitionBody': {ex!s}'.",
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
                f"Invalid 'DefinitionBody': {ex!s}.",
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
    def to_cloudformation(self, route53_record_set_groups: dict[str, Route53RecordSetGroup]) -> tuple[
        ApiGatewayV2HttpApi,
        ApiGatewayV2Stage | None,
        ApiGatewayV2DomainName | None,
        list[ApiGatewayV2ApiMapping] | None,
        Route53RecordSetGroup | None,
        list[LambdaPermission] | None,
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
