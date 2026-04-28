from typing import Any

from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.model import Resource
from samtranslator.model.api.apiv2_generator import ApiV2Generator
from samtranslator.model.apigatewayv2 import (
    ApiGatewayV2Integration,
    ApiGatewayV2Route,
    ApiGatewayV2Stage,
    ApiGatewayV2WebSocketApi,
    ApiGatewayV2WSAuthorizer,
)
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.intrinsics import fnSub, is_intrinsic, ref
from samtranslator.model.lambda_ import LambdaPermission
from samtranslator.model.route53 import Route53RecordSetGroup
from samtranslator.utils.types import Intrinsicable

# Different stage name from `$default` used by http, to avoid confusion with $default route and to avoid bugs
DefaultStageName = "default"
WebSocketApiTagName = "websocketapi:createdBy"


class AuthType:
    NONE = "NONE"
    AWS_IAM = "AWS_IAM"
    CUSTOM = "CUSTOM"
    TYPES = (NONE, AWS_IAM, CUSTOM)


class WebSocketApiGenerator(ApiV2Generator):
    def __init__(  # noqa: PLR0913
        self,
        logical_id: str,
        stage_name: str | None,
        stage_variables: (
            dict[str, Intrinsicable[str]] | None
        ),  # I tried to keep presence of = None consistent with http
        depends_on: list[str] | None,
        name: str | None,
        routes: dict[str, dict[str, Any]],
        route_selection_expression: str,
        api_key_selection_expression: Intrinsicable[str] | None = None,
        access_log_settings: dict[str, Intrinsicable[str]] | None = None,
        auth_config: dict[str, Any] | None = None,
        default_route_settings: dict[str, Any] | None = None,
        description: Intrinsicable[str] | None = None,
        disable_execute_api_endpoint: Intrinsicable[bool] | None = None,
        domain: dict[str, Any] | None = None,
        disable_schema_validation: Intrinsicable[bool] | None = None,
        ip_address_type: Intrinsicable[str] | None = None,
        resource_attributes: dict[str, Intrinsicable[str]] | None = None,
        passthrough_resource_attributes: dict[str, Intrinsicable[str]] | None = None,
        route_settings: dict[str, Any] | None = None,
        tags: dict[str, Intrinsicable[str]] | None = None,
    ) -> None:
        """Constructs an API Generator class that generates API Gateway resources
        :param logical_id: Logical id of the SAM API Resource
        :param stage_name: Name of the Stage
        :param stage_variables: API Gateway Variables
        :param depends_on: Any resources that need to be depended on
        :param name: Name of the API Gateway "Api" resource
        :param routes: Route Key, Function, and other config for routes
        :param route_selection_expression: Used to determine method of selection routes
        :param api_key_selection_expression: Selection expression for API keys
        :param access_log_settings: Whether to send access logs and where for Stage
        :param auth_config: Authorizer configuration
        :param default_route_settings: DefaultRouteSettings on the stage
        :param description: Description of the API Gateway resource
        :param disable_execute_api_endpoint: DisableExecuteApiEndpoint property, to ensure that clients can access your API only by using a custom domain name
        :param domain: domain configuration
        :param disable_schema_validation:  value of DisableSchemaValidation for the API
        :param ip_address_type: "ipv4" or "dualstack"
        :param resource_attributes: Resource attributes to add to API resources
        :param passthrough_resource_attributes: Attributes such as 'Condition' that are added to derived resources
        :param tags: Stage and API tags
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
        # use logical id as name if none provided
        self.name = name if name is not None else self.logical_id
        self.stage_name = stage_name if stage_name is not None else DefaultStageName
        self.stage_variables = stage_variables
        self.routes = routes
        if not self.routes:
            raise InvalidResourceException(self.logical_id, "WebSocket API must have at least one route.")
        self.route_selection_expression = route_selection_expression
        self.api_key_selection_expression = api_key_selection_expression
        self.auth_config = auth_config
        self.default_tag_name = WebSocketApiTagName
        self.description = description
        self.disable_schema_validation = disable_schema_validation
        self.ip_address_type = ip_address_type
        if (
            self.ip_address_type is not None
            and not is_intrinsic(self.ip_address_type)
            and self.ip_address_type not in ("ipv4", "dualstack")
        ):
            raise InvalidResourceException(self.logical_id, "IpAddressType must be 'ipv4' or 'dualstack'.")

        # Validate that MTLS is not configured for WebSocket APIs
        if domain and domain.get("MutualTlsAuthentication"):
            raise InvalidResourceException(
                self.logical_id, "Mutual TLS domain name association is not supported for Websocket APIs."
            )

    def _construct_websocket_api(self) -> ApiGatewayV2WebSocketApi:
        websocket_api = ApiGatewayV2WebSocketApi(
            self.logical_id, depends_on=self.depends_on, attributes=self.resource_attributes
        )
        # Direct passes
        websocket_api.ApiKeySelectionExpression = self.api_key_selection_expression
        websocket_api.Description = self.description
        websocket_api.DisableExecuteApiEndpoint = self.disable_execute_api_endpoint
        websocket_api.DisableSchemaValidation = self.disable_schema_validation
        websocket_api.IpAddressType = self.ip_address_type
        if self.auth_config and "$connect" not in self.routes:
            raise InvalidResourceException(
                self.logical_id, "Authorization is only available if there is a $connect route."
            )
        websocket_api.Name = self.name
        websocket_api.RouteSelectionExpression = self.route_selection_expression
        if not self.tags:
            self.tags = {}
        self.tags[self.default_tag_name] = "SAM"
        websocket_api.Tags = self.tags

        # Static fields
        websocket_api.ProtocolType = "WEBSOCKET"
        return websocket_api

    def _construct_authorizer(self) -> ApiGatewayV2WSAuthorizer:
        # generate logical id for resource
        auth_name = self.logical_id + "ConnectAuthorizer"
        auth = ApiGatewayV2WSAuthorizer(auth_name, attributes=self.passthrough_resource_attributes)
        auth.ApiId = {"Ref": self.logical_id}
        if self.auth_config:  # unpacking
            if "InvokeRole" in self.auth_config:
                auth.AuthorizerCredentialsArn = self.auth_config["InvokeRole"]
            auth.AuthorizerType = "REQUEST"
            if "AuthArn" in self.auth_config:
                auth.AuthorizerUri = fnSub(
                    "arn:${AWS::Partition}:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${AuthArn}/invocations",
                    {"AuthArn": self.auth_config["AuthArn"]},
                )
            auth.IdentitySource = self.auth_config.get("IdentitySource")
            # use logical id if no name provided
            if self.auth_config.get("Name"):
                auth.Name = self.auth_config.get("Name")
            else:
                auth.Name = auth_name
        return auth

    def _construct_authorizer_permission(self, websocket_api: ApiGatewayV2WebSocketApi) -> LambdaPermission | None:
        """Constructs Lambda Permission allowing API Gateway to invoke the authorizer function.
        Only needed when InvokeRole is not provided (resource-based permissions)."""
        if not self.auth_config or self.auth_config.get("AuthType") != AuthType.CUSTOM:
            return None

        # If InvokeRole is provided, API Gateway uses role-based invocation, no permission needed
        if self.auth_config.get("InvokeRole"):
            return None

        auth_arn = self.auth_config.get("AuthArn")
        if not auth_arn:
            return None

        return self._get_authorizer_permission(
            self.logical_id + "AuthorizerPermission",
            auth_arn,
            websocket_api.get_runtime_attr("websocket_api_id"),
        )

    def _generate_route_resource_ids(self, route_key: str) -> tuple[str, str, str]:
        """Convert route key to a valid CloudFormation logical ID component."""
        ROUTE_SUFFIX = "Route"
        INTEGRATION_SUFFIX = "Integration"
        PERMISSION_SUFFIX = "Permission"

        # Clean and validate the route key
        clean_key = self._sanitize_route_key(route_key)

        # Generate IDs using a consistent pattern
        base_id = f"{self.logical_id}{clean_key}"
        return (f"{base_id}{ROUTE_SUFFIX}", f"{base_id}{INTEGRATION_SUFFIX}", f"{base_id}{PERMISSION_SUFFIX}")

    def _sanitize_route_key(self, route_key: str) -> str:
        # Handle special WebSocket routes
        special_routes = ["$connect", "$disconnect", "$default"]
        if route_key in special_routes:
            return route_key.replace("$", "").capitalize()
        if route_key.isalnum():
            return route_key.capitalize()
        raise InvalidResourceException(
            self.logical_id,
            f"Route key '{route_key}' must be alphanumeric. "
            "Only $connect, $disconnect, and $default special routes are supported.",
        )

    def _validate_auth(self, auth_config: dict[str, Any]) -> None:
        # Use parameter `auth_config` that we know is not None, instead of `self.auth_config`
        auth_type = auth_config.get("AuthType")
        if auth_type:
            auth_type = auth_type.upper()
            if auth_type not in AuthType.TYPES:
                raise InvalidResourceException(self.logical_id, "AuthType is not one of AWS_IAM, CUSTOM or NONE.")
            if auth_type == AuthType.CUSTOM and not auth_config.get("AuthArn"):
                raise InvalidResourceException(self.logical_id, "AuthArn must be specified if AuthType is CUSTOM.")
            if auth_type == AuthType.AWS_IAM and len(auth_config) > 1:
                raise InvalidResourceException(
                    self.logical_id, "No additional configurations supported for AuthType AWS_IAM."
                )
            if auth_type == AuthType.NONE and len(auth_config) > 1:
                raise InvalidResourceException(
                    self.logical_id, "No additional configurations supported for AuthType NONE."
                )
        else:
            raise InvalidResourceException(
                self.logical_id, "AuthType must be specified for additional auth configurations."
            )

    def _construct_route(
        self, route_key: str, route_id: str, integration_id: str, route_spec: dict[str, Any]
    ) -> ApiGatewayV2Route:
        apigw_route = ApiGatewayV2Route(route_id, attributes=self.passthrough_resource_attributes)
        apigw_route.RouteKey = route_key
        apigw_route.ApiId = ref(self.logical_id)
        apigw_route.ApiKeyRequired = route_spec.get("ApiKeyRequired")
        apigw_route.ModelSelectionExpression = route_spec.get("ModelSelectionExpression")
        apigw_route.OperationName = route_spec.get("OperationName")
        apigw_route.RequestModels = route_spec.get("RequestModels")
        if route_spec.get("RequestParameters"):
            if route_key != "$connect":
                raise InvalidResourceException(
                    self.logical_id, "Request parameters are only supported for the $connect route in WebSocket APIs."
                )
            apigw_route.RequestParameters = route_spec.get("RequestParameters")
        apigw_route.RouteResponseSelectionExpression = route_spec.get("RouteResponseSelectionExpression")
        apigw_route.Target = {"Fn::Join": ["/", ["integrations", ref(integration_id)]]}
        return apigw_route

    def _set_auth_type_and_return_custom_authorizer(
        self, route_key: str, route: ApiGatewayV2Route
    ) -> ApiGatewayV2WSAuthorizer | None:
        if not self.auth_config:
            return None
        self._validate_auth(self.auth_config)
        # set up auth if has config and has connect route
        if route_key == "$connect":
            if self.auth_config["AuthType"] == AuthType.CUSTOM:
                if self.auth_config["AuthArn"]:  # this is mostly to unpack the optional/for type checking purposes
                    apigw_authorizer = self._construct_authorizer()
                    route.AuthorizationType = AuthType.CUSTOM
                    route.AuthorizerId = {"Ref": apigw_authorizer.logical_id}
                    return apigw_authorizer
            elif self.auth_config["AuthType"] == AuthType.AWS_IAM:
                route.AuthorizationType = AuthType.AWS_IAM
            else:
                route.AuthorizationType = AuthType.NONE
        return None

    def _construct_integration(self, apigw_integration_id: str, route_spec: dict[str, Any]) -> ApiGatewayV2Integration:
        if "FunctionArn" not in route_spec:
            raise InvalidResourceException(self.logical_id, "Route must have associated function.")
        # set up integration
        apigw_integration = ApiGatewayV2Integration(
            apigw_integration_id, attributes=self.passthrough_resource_attributes
        )
        apigw_integration.ApiId = ref(self.logical_id)
        apigw_integration.IntegrationType = "AWS_PROXY"
        apigw_integration.IntegrationUri = fnSub(
            "arn:${AWS::Partition}:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${FunctionArn}/invocations",
            {"FunctionArn": route_spec["FunctionArn"]},
        )
        apigw_integration.TimeoutInMillis = route_spec.get("IntegrationTimeout")
        return apigw_integration

    def _construct_permission(self, route_key: str, perms_id: str, route_spec: dict[str, Any]) -> LambdaPermission:
        if "FunctionArn" not in route_spec:
            raise InvalidResourceException(self.logical_id, "Route must have associated function.")
        # set up permissions
        perms = LambdaPermission(perms_id, attributes=self.passthrough_resource_attributes)
        perms.Action = "lambda:InvokeFunction"
        perms.FunctionName = route_spec["FunctionArn"]
        perms.Principal = "apigateway.amazonaws.com"
        perms.SourceArn = fnSub(
            "arn:${AWS::Partition}:execute-api:${AWS::Region}:${AWS::AccountId}:${"
            + self.logical_id
            + ".ApiId}/"
            + self.stage_name
            + "/"
            + route_key
        )
        return perms

    def _construct_route_infr(self, route_key: str, route_spec: dict[str, Any]) -> tuple[
        ApiGatewayV2Route,
        ApiGatewayV2Integration,
        LambdaPermission,
        ApiGatewayV2WSAuthorizer | None,
    ]:
        # set up names
        apigw_route_id, apigw_integration_id, perms_id = self._generate_route_resource_ids(route_key)
        # set up route
        apigw_route = self._construct_route(route_key, apigw_route_id, apigw_integration_id, route_spec)
        apigw_auth = self._set_auth_type_and_return_custom_authorizer(route_key, apigw_route)
        apigw_integration = self._construct_integration(apigw_integration_id, route_spec)
        permissions = self._construct_permission(route_key, perms_id, route_spec)
        return apigw_route, apigw_integration, permissions, apigw_auth

    # Mostly taken from http
    def _construct_stage(self) -> ApiGatewayV2Stage | None:
        """Constructs and returns the ApiGatewayV2 Stage.

        :returns: the Stage to which this SAM Api corresponds
        :rtype: model.apigatewayv2.ApiGatewayV2Stage
        """
        # "Use default if no parameters passed" removed because default stage uses $default so we always need to at least change that

        # If StageName is some intrinsic function, then don't prefix the Stage's logical ID
        # This will NOT create duplicates because we allow only ONE stage per API resource
        if self.stage_name == "$default":
            raise InvalidResourceException(self.logical_id, "Stages cannot be named $default for WebSocket APIs.")
        stage_name_prefix = self.stage_name if isinstance(self.stage_name, str) else ""
        # This is also altered in that the original checks for alphanumeric because the $ in $default would make that false
        stage_logical_id = (
            self.logical_id + stage_name_prefix + "Stage"
            if stage_name_prefix != DefaultStageName
            else self.logical_id + "DefaultStage"
        )
        # since this is no longer the API Gateway default stage exactly (that would be $default) I change it to be just DefaultStage
        stage = ApiGatewayV2Stage(stage_logical_id, attributes=self.passthrough_resource_attributes)
        stage.ApiId = ref(self.logical_id)
        stage.StageName = self.stage_name
        stage.StageVariables = self.stage_variables
        stage.AccessLogSettings = self.access_log_settings
        stage.DefaultRouteSettings = self.default_route_settings
        stage.Tags = {self.default_tag_name: "SAM"}
        stage.AutoDeploy = True
        stage.RouteSettings = self.route_settings

        return stage

    @cw_timer(prefix="Generator", name="WebSocketApi")
    def _to_cloudformation(self, route53_record_set_groups: dict[str, Route53RecordSetGroup]) -> list[Resource]:
        """Generates CloudFormation resources from a SAM WebSocket API resource

        :returns: a tuple containing the WebSocketApi and Stage for an empty Api.
        :rtype: tuple"""
        websocket_api = self._construct_websocket_api()
        domain, basepath_mapping, route53 = self._construct_api_domain(websocket_api, route53_record_set_groups)
        stage = self._construct_stage()

        generated_resources_list: list[Resource] = [websocket_api]

        auth = None
        route_logical_ids: list[str] = []
        for key, value in self.routes.items():
            apigw_route, apigw_integration, permission, apigw_auth = self._construct_route_infr(key, value)
            # We keep all related route-integration-permission combos together
            generated_resources_list.append(apigw_route)
            generated_resources_list.append(apigw_integration)
            generated_resources_list.append(permission)
            route_logical_ids.append(apigw_route.logical_id)

            if apigw_auth:
                auth = apigw_auth

        if domain:
            generated_resources_list.append(domain)
        if basepath_mapping:
            generated_resources_list.extend(basepath_mapping)
        if route53:
            generated_resources_list.append(route53)

        if stage:
            # Stage must depend on routes when RouteSettings references specific route keys
            if self.route_settings and route_logical_ids:
                stage.depends_on = route_logical_ids
            generated_resources_list.append(stage)

        if auth:
            generated_resources_list.append(auth)
            auth_permission = self._construct_authorizer_permission(websocket_api)
            if auth_permission:
                generated_resources_list.append(auth_permission)

        return generated_resources_list
