from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, one_of, is_str, list_of
from samtranslator.model.intrinsics import ref, fnSub
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.translator.arn_generator import ArnGenerator

APIGATEWAY_AUTHORIZER_KEY = "x-amazon-apigateway-authorizer"


class ApiGatewayV2HttpApi(Resource):
    resource_type = "AWS::ApiGatewayV2::Api"
    property_types = {
        "Body": PropertyType(False, is_type(dict)),
        "BodyS3Location": PropertyType(False, is_type(dict)),
        "Description": PropertyType(False, is_str()),
        "FailOnWarnings": PropertyType(False, is_type(bool)),
        "DisableExecuteApiEndpoint": PropertyType(False, is_type(bool)),
        "BasePath": PropertyType(False, is_str()),
        "CorsConfiguration": PropertyType(False, is_type(dict)),
    }

    runtime_attrs = {"http_api_id": lambda self: ref(self.logical_id)}


class ApiGatewayV2Stage(Resource):
    resource_type = "AWS::ApiGatewayV2::Stage"
    property_types = {
        "AccessLogSettings": PropertyType(False, is_type(dict)),
        "DefaultRouteSettings": PropertyType(False, is_type(dict)),
        "RouteSettings": PropertyType(False, is_type(dict)),
        "ClientCertificateId": PropertyType(False, is_str()),
        "Description": PropertyType(False, is_str()),
        "ApiId": PropertyType(True, is_str()),
        "StageName": PropertyType(False, one_of(is_str(), is_type(dict))),
        "Tags": PropertyType(False, is_type(dict)),
        "StageVariables": PropertyType(False, is_type(dict)),
        "AutoDeploy": PropertyType(False, is_type(bool)),
    }

    runtime_attrs = {"stage_name": lambda self: ref(self.logical_id)}


class ApiGatewayV2DomainName(Resource):
    resource_type = "AWS::ApiGatewayV2::DomainName"
    property_types = {
        "DomainName": PropertyType(True, is_str()),
        "DomainNameConfigurations": PropertyType(False, list_of(is_type(dict))),
        "MutualTlsAuthentication": PropertyType(False, is_type(dict)),
        "Tags": PropertyType(False, is_type(dict)),
    }


class ApiGatewayV2ApiMapping(Resource):
    resource_type = "AWS::ApiGatewayV2::ApiMapping"
    property_types = {
        "ApiId": PropertyType(True, is_str()),
        "ApiMappingKey": PropertyType(False, is_str()),
        "DomainName": PropertyType(True, is_str()),
        "Stage": PropertyType(True, is_str()),
    }


class ApiGatewayV2Authorizer(object):
    def __init__(
        self,
        api_logical_id=None,
        name=None,
        authorization_scopes=None,
        jwt_configuration=None,
        id_source=None,
        function_arn=None,
        function_invoke_role=None,
        identity=None,
        authorizer_payload_format_version=None,
        enable_simple_responses=None,
        is_aws_iam_authorizer=False,
    ):
        """
        Creates an authorizer for use in V2 Http Apis
        """
        self.api_logical_id = api_logical_id
        self.name = name
        self.authorization_scopes = authorization_scopes
        self.jwt_configuration = jwt_configuration
        self.id_source = id_source
        self.function_arn = function_arn
        self.function_invoke_role = function_invoke_role
        self.identity = identity
        self.authorizer_payload_format_version = authorizer_payload_format_version
        self.enable_simple_responses = enable_simple_responses
        self.is_aws_iam_authorizer = is_aws_iam_authorizer

        self._validate_input_parameters()

        authorizer_type = self._get_auth_type()

        # Validate necessary parameters exist
        if authorizer_type == "JWT":
            self._validate_jwt_authorizer()

        if authorizer_type == "REQUEST":
            self._validate_lambda_authorizer()

    def _get_auth_type(self):
        if self.is_aws_iam_authorizer:
            return "AWS_IAM"
        if self.jwt_configuration:
            return "JWT"
        return "REQUEST"

    def _validate_input_parameters(self):
        authorizer_type = self._get_auth_type()

        if self.authorization_scopes is not None and not isinstance(self.authorization_scopes, list):
            raise InvalidResourceException(self.api_logical_id, "AuthorizationScopes must be a list.")

        if self.authorization_scopes is not None and not authorizer_type == "JWT":
            raise InvalidResourceException(
                self.api_logical_id, "AuthorizationScopes must be defined only for OAuth2 Authorizer."
            )

        if self.jwt_configuration is not None and not authorizer_type == "JWT":
            raise InvalidResourceException(
                self.api_logical_id, "JwtConfiguration must be defined only for OAuth2 Authorizer."
            )

        if self.id_source is not None and not authorizer_type == "JWT":
            raise InvalidResourceException(
                self.api_logical_id, "IdentitySource must be defined only for OAuth2 Authorizer."
            )

        if self.function_arn is not None and not authorizer_type == "REQUEST":
            raise InvalidResourceException(
                self.api_logical_id, "FunctionArn must be defined only for Lambda Authorizer."
            )

        if self.function_invoke_role is not None and not authorizer_type == "REQUEST":
            raise InvalidResourceException(
                self.api_logical_id, "FunctionInvokeRole must be defined only for Lambda Authorizer."
            )

        if self.identity is not None and not authorizer_type == "REQUEST":
            raise InvalidResourceException(self.api_logical_id, "Identity must be defined only for Lambda Authorizer.")

        if self.authorizer_payload_format_version is not None and not authorizer_type == "REQUEST":
            raise InvalidResourceException(
                self.api_logical_id, "AuthorizerPayloadFormatVersion must be defined only for Lambda Authorizer."
            )

        if self.enable_simple_responses is not None and not authorizer_type == "REQUEST":
            raise InvalidResourceException(
                self.api_logical_id, "EnableSimpleResponses must be defined only for Lambda Authorizer."
            )

    def _validate_jwt_authorizer(self):
        if not self.jwt_configuration:
            raise InvalidResourceException(
                self.api_logical_id, f"{self.name} OAuth2 Authorizer must define 'JwtConfiguration'."
            )
        if not self.id_source:
            raise InvalidResourceException(
                self.api_logical_id, f"{self.name} OAuth2 Authorizer must define 'IdentitySource'."
            )

    def _validate_lambda_authorizer(self):
        if not self.function_arn:
            raise InvalidResourceException(
                self.api_logical_id, f"{self.name} Lambda Authorizer must define 'FunctionArn'."
            )
        if not self.authorizer_payload_format_version:
            raise InvalidResourceException(
                self.api_logical_id, f"{self.name} Lambda Authorizer must define 'AuthorizerPayloadFormatVersion'."
            )

        if self.identity:
            if not isinstance(self.identity, dict):
                raise InvalidResourceException(
                    self.api_logical_id, self.name + " Lambda Authorizer property 'identity' is of invalid type."
                )
            headers = self.identity.get("Headers")
            if headers:
                if not isinstance(headers, list) or any([not isinstance(header, str) for header in headers]):
                    raise InvalidResourceException(
                        self.api_logical_id,
                        self.name + " Lambda Authorizer property identity's 'Headers' is of invalid type.",
                    )

    def generate_openapi(self):
        """
        Generates OAS for the securitySchemes section
        """
        authorizer_type = self._get_auth_type()

        if authorizer_type == "AWS_IAM":
            openapi = {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "x-amazon-apigateway-authtype": "awsSigv4",
            }

        if authorizer_type == "JWT":
            openapi = {"type": "oauth2"}
            openapi[APIGATEWAY_AUTHORIZER_KEY] = {
                "jwtConfiguration": self.jwt_configuration,
                "identitySource": self.id_source,
                "type": "jwt",
            }

        if authorizer_type == "REQUEST":
            openapi = {
                "type": "apiKey",
                "name": "Unused",
                "in": "header",
            }
            openapi[APIGATEWAY_AUTHORIZER_KEY] = {"type": "request"}

            # Generate the lambda arn
            partition = ArnGenerator.get_partition_name()
            resource = "lambda:path/2015-03-31/functions/${__FunctionArn__}/invocations"
            authorizer_uri = fnSub(
                ArnGenerator.generate_arn(
                    partition=partition, service="apigateway", resource=resource, include_account_id=False
                ),
                {"__FunctionArn__": self.function_arn},
            )
            openapi[APIGATEWAY_AUTHORIZER_KEY]["authorizerUri"] = authorizer_uri

            # Set authorizerCredentials if present
            function_invoke_role = self._get_function_invoke_role()
            if function_invoke_role:
                openapi[APIGATEWAY_AUTHORIZER_KEY]["authorizerCredentials"] = function_invoke_role

            # Set authorizerResultTtlInSeconds if present
            reauthorize_every = self._get_reauthorize_every()
            if reauthorize_every is not None:
                openapi[APIGATEWAY_AUTHORIZER_KEY]["authorizerResultTtlInSeconds"] = reauthorize_every

            # Set identitySource if present
            if self.identity:
                openapi[APIGATEWAY_AUTHORIZER_KEY]["identitySource"] = self._get_identity_source()

            # Set authorizerPayloadFormatVersion. It's a required parameter
            openapi[APIGATEWAY_AUTHORIZER_KEY][
                "authorizerPayloadFormatVersion"
            ] = self.authorizer_payload_format_version

            # Set authorizerPayloadFormatVersion. It's a required parameter
            if self.enable_simple_responses:
                openapi[APIGATEWAY_AUTHORIZER_KEY]["enableSimpleResponses"] = self.enable_simple_responses

        return openapi

    def _get_function_invoke_role(self):
        if not self.function_invoke_role or self.function_invoke_role == "NONE":
            return None

        return self.function_invoke_role

    def _get_identity_source(self):
        identity_source_headers = []
        identity_source_query_strings = []
        identity_source_stage_variables = []
        identity_source_context = []

        if self.identity.get("Headers"):
            identity_source_headers = list(map(lambda h: "$request.header." + h, self.identity.get("Headers")))

        if self.identity.get("QueryStrings"):
            identity_source_query_strings = list(
                map(lambda qs: "$request.querystring." + qs, self.identity.get("QueryStrings"))
            )

        if self.identity.get("StageVariables"):
            identity_source_stage_variables = list(
                map(lambda sv: "$stageVariables." + sv, self.identity.get("StageVariables"))
            )

        if self.identity.get("Context"):
            identity_source_context = list(map(lambda c: "$context." + c, self.identity.get("Context")))

        identity_source = (
            identity_source_headers
            + identity_source_query_strings
            + identity_source_stage_variables
            + identity_source_context
        )

        return identity_source

    def _get_reauthorize_every(self):
        if not self.identity:
            return None

        return self.identity.get("ReauthorizeEvery")
