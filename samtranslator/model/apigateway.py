import json
import time
from re import match
from typing import Any, Dict, List, Optional, Union

from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.intrinsics import fnSub, ref
from samtranslator.model.types import PassThrough
from samtranslator.translator import logical_id_generator
from samtranslator.translator.arn_generator import ArnGenerator
from samtranslator.utils.py27hash_fix import Py27Dict, Py27UniStr
from samtranslator.validator.value_validator import sam_expect


class ApiGatewayRestApi(Resource):
    resource_type = "AWS::ApiGateway::RestApi"
    property_types = {
        "Body": GeneratedProperty(),
        "BodyS3Location": GeneratedProperty(),
        "CloneFrom": GeneratedProperty(),
        "Description": GeneratedProperty(),
        "FailOnWarnings": GeneratedProperty(),
        "Name": GeneratedProperty(),
        "Parameters": GeneratedProperty(),
        "EndpointConfiguration": GeneratedProperty(),
        "BinaryMediaTypes": GeneratedProperty(),
        "MinimumCompressionSize": GeneratedProperty(),
        "Mode": GeneratedProperty(),
        "ApiKeySourceType": GeneratedProperty(),
        "Tags": GeneratedProperty(),
    }

    Body: Optional[Dict[str, Any]]
    BodyS3Location: Optional[Dict[str, Any]]
    CloneFrom: Optional[PassThrough]
    Description: Optional[PassThrough]
    FailOnWarnings: Optional[PassThrough]
    Name: Optional[PassThrough]
    Parameters: Optional[Dict[str, Any]]
    EndpointConfiguration: Optional[Dict[str, Any]]
    BinaryMediaTypes: Optional[List[Any]]
    MinimumCompressionSize: Optional[PassThrough]
    Mode: Optional[PassThrough]
    ApiKeySourceType: Optional[PassThrough]
    Tags: Optional[PassThrough]

    runtime_attrs = {"rest_api_id": lambda self: ref(self.logical_id)}


class ApiGatewayStage(Resource):
    resource_type = "AWS::ApiGateway::Stage"
    property_types = {
        "AccessLogSetting": GeneratedProperty(),
        "CacheClusterEnabled": GeneratedProperty(),
        "CacheClusterSize": GeneratedProperty(),
        "CanarySetting": GeneratedProperty(),
        "ClientCertificateId": GeneratedProperty(),
        "DeploymentId": GeneratedProperty(),
        "Description": GeneratedProperty(),
        "RestApiId": GeneratedProperty(),
        "StageName": GeneratedProperty(),
        "Tags": GeneratedProperty(),
        "TracingEnabled": GeneratedProperty(),
        "Variables": GeneratedProperty(),
        "MethodSettings": GeneratedProperty(),
    }

    runtime_attrs = {"stage_name": lambda self: ref(self.logical_id)}

    def update_deployment_ref(self, deployment_logical_id: str) -> None:
        self.DeploymentId = ref(deployment_logical_id)


class ApiGatewayAccount(Resource):
    resource_type = "AWS::ApiGateway::Account"
    property_types = {
        "CloudWatchRoleArn": GeneratedProperty(),
    }


class ApiGatewayDeployment(Resource):
    _X_HASH_DELIMITER = "||"

    resource_type = "AWS::ApiGateway::Deployment"
    property_types = {
        "Description": GeneratedProperty(),
        "RestApiId": GeneratedProperty(),
        "StageDescription": GeneratedProperty(),
        "StageName": GeneratedProperty(),
    }

    runtime_attrs = {"deployment_id": lambda self: ref(self.logical_id)}

    def make_auto_deployable(  # noqa: PLR0913
        self,
        stage: ApiGatewayStage,
        openapi_version: Optional[Union[Dict[str, Any], str]] = None,
        swagger: Optional[Dict[str, Any]] = None,
        domain: Optional[Dict[str, Any]] = None,
        redeploy_restapi_parameters: Optional[Any] = None,
        always_deploy: Optional[bool] = False,
    ) -> None:
        """
        Sets up the resource such that it will trigger a re-deployment when Swagger changes or always_deploy is true
        or the openapi version changes or a domain resource changes.

        :param stage: The ApiGatewayStage object which will be re-deployed
        :param swagger: Dictionary containing the Swagger definition of the API
        :param openapi_version: string containing value of OpenApiVersion flag in the template
        :param domain: Dictionary containing the custom domain configuration for the API
        :param redeploy_restapi_parameters: Dictionary containing the properties for which rest api will be redeployed
        """
        if not swagger:
            return

        # CloudFormation does NOT redeploy the API unless it has a new deployment resource
        # that points to latest RestApi resource. Append a hash of Swagger Body location to
        # redeploy only when the API data changes. First 10 characters of hash is good enough
        # to prevent redeployment when API has not changed

        # NOTE: `str(swagger)` is for backwards compatibility. Changing it to a JSON or something will break compat
        hash_input = [str(swagger)]
        if openapi_version:
            hash_input.append(str(openapi_version))
        if domain:
            hash_input.append(json.dumps(domain))
        function_names = redeploy_restapi_parameters.get("function_names") if redeploy_restapi_parameters else None
        # The deployment logical id is <api logicalId> + "Deployment"
        # The keyword "Deployment" is removed and all the function names associated with api is obtained
        if function_names and function_names.get(self.logical_id[:-10], None):
            hash_input.append(function_names.get(self.logical_id[:-10], ""))
        if always_deploy:
            # We just care that the hash changes every time
            # Using int so tests are a little more robust; don't think the Python spec defines default precision
            hash_input = [str(int(time.time()))]
        data = self._X_HASH_DELIMITER.join(hash_input)
        generator = logical_id_generator.LogicalIdGenerator(self.logical_id, data)
        self.logical_id = generator.gen()
        digest = generator.get_hash(length=40)
        self.Description = f"RestApi deployment id: {digest}"
        stage.update_deployment_ref(self.logical_id)


class ApiGatewayResponse:
    ResponseParameterProperties = ["Headers", "Paths", "QueryStrings"]

    def __init__(
        self,
        api_logical_id: str,
        response_parameters: Optional[Dict[str, Any]] = None,
        response_templates: Optional[PassThrough] = None,
        status_code: Optional[str] = None,
    ) -> None:
        if response_parameters:
            # response_parameters has been validated in ApiGenerator._add_gateway_responses()
            for response_parameter_key in response_parameters:
                if response_parameter_key not in ApiGatewayResponse.ResponseParameterProperties:
                    raise InvalidResourceException(
                        api_logical_id, f"Invalid gateway response parameter '{response_parameter_key}'"
                    )

        status_code_str = self._status_code_string(status_code)  # type: ignore[no-untyped-call]
        # status_code must look like a status code, if present. Let's not be judgmental; just check 0-999.
        if status_code and not match(r"^[0-9]{1,3}$", status_code_str):
            raise InvalidResourceException(api_logical_id, "Property 'StatusCode' must be numeric")

        self.api_logical_id = api_logical_id
        # Defaults to Py27Dict() as these will go into swagger
        self.response_parameters = response_parameters or Py27Dict()
        self.response_templates = response_templates or Py27Dict()
        self.status_code = status_code_str

    def generate_swagger(self) -> Py27Dict:
        # Applying Py27Dict here as this goes into swagger
        swagger = Py27Dict()
        swagger["responseParameters"] = self._add_prefixes(self.response_parameters)
        swagger["responseTemplates"] = self.response_templates

        # Prevent "null" being written.
        if self.status_code:
            swagger["statusCode"] = self.status_code

        return swagger

    def _add_prefixes(self, response_parameters: Dict[str, Any]) -> Dict[str, str]:
        GATEWAY_RESPONSE_PREFIX = "gatewayresponse."
        # applying Py27Dict as this is part of swagger
        prefixed_parameters = Py27Dict()

        parameter_prefix_pairs = [("Headers", "header."), ("Paths", "path."), ("QueryStrings", "querystring.")]
        for parameter_property_name, prefix in parameter_prefix_pairs:
            parameter_property_value = response_parameters.get(parameter_property_name, {})
            sam_expect(
                parameter_property_value, self.api_logical_id, f"ResponseParameters.{parameter_property_name}"
            ).to_be_a_map()
            for key, value in parameter_property_value.items():
                param_key = GATEWAY_RESPONSE_PREFIX + prefix + key
                if isinstance(key, Py27UniStr):
                    # if key is from template, we need to convert param_key to Py27UniStr
                    param_key = Py27UniStr(param_key)
                prefixed_parameters[param_key] = value

        return prefixed_parameters

    def _status_code_string(self, status_code):  # type: ignore[no-untyped-def]
        return None if status_code is None else str(status_code)


class ApiGatewayDomainName(Resource):
    resource_type = "AWS::ApiGateway::DomainName"
    property_types = {
        "RegionalCertificateArn": GeneratedProperty(),
        "DomainName": GeneratedProperty(),
        "EndpointConfiguration": GeneratedProperty(),
        "MutualTlsAuthentication": GeneratedProperty(),
        "SecurityPolicy": GeneratedProperty(),
        "CertificateArn": GeneratedProperty(),
        "Tags": GeneratedProperty(),
        "OwnershipVerificationCertificateArn": GeneratedProperty(),
    }

    RegionalCertificateArn: Optional[PassThrough]
    DomainName: PassThrough
    EndpointConfiguration: Optional[PassThrough]
    MutualTlsAuthentication: Optional[Dict[str, Any]]
    SecurityPolicy: Optional[PassThrough]
    CertificateArn: Optional[PassThrough]
    Tags: Optional[PassThrough]
    OwnershipVerificationCertificateArn: Optional[PassThrough]


class ApiGatewayBasePathMapping(Resource):
    resource_type = "AWS::ApiGateway::BasePathMapping"
    property_types = {
        "BasePath": GeneratedProperty(),
        "DomainName": GeneratedProperty(),
        "RestApiId": GeneratedProperty(),
        "Stage": GeneratedProperty(),
    }


class ApiGatewayUsagePlan(Resource):
    resource_type = "AWS::ApiGateway::UsagePlan"
    property_types = {
        "ApiStages": GeneratedProperty(),
        "Description": GeneratedProperty(),
        "Quota": GeneratedProperty(),
        "Tags": GeneratedProperty(),
        "Throttle": GeneratedProperty(),
        "UsagePlanName": GeneratedProperty(),
    }
    runtime_attrs = {"usage_plan_id": lambda self: ref(self.logical_id)}


class ApiGatewayUsagePlanKey(Resource):
    resource_type = "AWS::ApiGateway::UsagePlanKey"
    property_types = {
        "KeyId": GeneratedProperty(),
        "KeyType": GeneratedProperty(),
        "UsagePlanId": GeneratedProperty(),
    }


class ApiGatewayApiKey(Resource):
    resource_type = "AWS::ApiGateway::ApiKey"
    property_types = {
        "CustomerId": GeneratedProperty(),
        "Description": GeneratedProperty(),
        "Enabled": GeneratedProperty(),
        "GenerateDistinctId": GeneratedProperty(),
        "Name": GeneratedProperty(),
        "Tags": GeneratedProperty(),
        "StageKeys": GeneratedProperty(),
        "Value": GeneratedProperty(),
    }

    runtime_attrs = {"api_key_id": lambda self: ref(self.logical_id)}


class ApiGatewayAuthorizer:
    _VALID_FUNCTION_PAYLOAD_TYPES = [None, "TOKEN", "REQUEST"]

    def __init__(  # type: ignore[no-untyped-def]# noqa: PLR0913
        self,
        api_logical_id=None,
        name=None,
        user_pool_arn=None,
        function_arn=None,
        identity=None,
        function_payload_type: Optional[str] = None,
        function_invoke_role=None,
        is_aws_iam_authorizer=False,
        authorization_scopes=None,
        disable_function_default_permissions=False,
    ):
        if authorization_scopes is None:
            authorization_scopes = []

        self.api_logical_id = api_logical_id
        self.name = name
        self.user_pool_arn = user_pool_arn
        self.function_arn = function_arn
        self.identity = identity
        self.function_payload_type = function_payload_type
        self.function_invoke_role = function_invoke_role
        self.is_aws_iam_authorizer = is_aws_iam_authorizer
        self.authorization_scopes = authorization_scopes
        self.disable_function_default_permissions = disable_function_default_permissions

        if function_payload_type not in ApiGatewayAuthorizer._VALID_FUNCTION_PAYLOAD_TYPES:
            raise InvalidResourceException(
                api_logical_id,
                f"{name} Authorizer has invalid 'FunctionPayloadType': {function_payload_type}.",
            )

        if function_payload_type == "REQUEST" and self._is_missing_identity_source(identity):
            raise InvalidResourceException(
                api_logical_id,
                f"{name} Authorizer must specify Identity with at least one "
                "of Headers, QueryStrings, StageVariables, or Context.",
            )

        if authorization_scopes is not None:
            sam_expect(authorization_scopes, api_logical_id, f"Authorizers.{name}.AuthorizationScopes").to_be_a_list()

        if disable_function_default_permissions is not None:
            sam_expect(
                disable_function_default_permissions,
                api_logical_id,
                f"Authorizers.{name}.DisableFunctionDefaultPermissions",
            ).to_be_a_bool()

    def _is_missing_identity_source(self, identity: Dict[str, Any]) -> bool:
        if not identity:
            return True

        sam_expect(identity, self.api_logical_id, f"Authorizer.{self.name}.Identity").to_be_a_map()

        headers = identity.get("Headers")
        query_strings = identity.get("QueryStrings")
        stage_variables = identity.get("StageVariables")
        context = identity.get("Context")
        ttl = identity.get("ReauthorizeEvery")

        required_properties_missing = not headers and not query_strings and not stage_variables and not context

        if ttl is None:
            return required_properties_missing
        try:
            ttl_int = int(ttl)
        # this will catch if and not convertable to an int
        except (TypeError, ValueError):
            # previous behavior before trying to read ttl
            return required_properties_missing

        # If we can resolve ttl, attempt to see if things are valid
        return ttl_int > 0 and required_properties_missing

    def generate_swagger(self) -> Py27Dict:
        authorizer_type = self._get_type()
        APIGATEWAY_AUTHORIZER_KEY = "x-amazon-apigateway-authorizer"
        swagger = Py27Dict()
        swagger["type"] = "apiKey"
        swagger["name"] = self._get_swagger_header_name()
        swagger["in"] = "header"
        swagger["x-amazon-apigateway-authtype"] = self._get_swagger_authtype()

        if authorizer_type == "COGNITO_USER_POOLS":
            authorizer_dict = Py27Dict()
            authorizer_dict["type"] = self._get_swagger_authorizer_type()
            authorizer_dict["providerARNs"] = self._get_user_pool_arn_array()
            swagger[APIGATEWAY_AUTHORIZER_KEY] = authorizer_dict

        elif authorizer_type == "LAMBDA":
            swagger[APIGATEWAY_AUTHORIZER_KEY] = Py27Dict({"type": self._get_swagger_authorizer_type()})
            partition = ArnGenerator.get_partition_name()
            resource = "lambda:path/2015-03-31/functions/${__FunctionArn__}/invocations"
            authorizer_uri = fnSub(
                ArnGenerator.generate_arn(
                    partition=partition, service="apigateway", resource=resource, include_account_id=False
                ),
                {"__FunctionArn__": self.function_arn},
            )

            swagger[APIGATEWAY_AUTHORIZER_KEY]["authorizerUri"] = authorizer_uri
            reauthorize_every = self._get_reauthorize_every()
            function_invoke_role = self._get_function_invoke_role()

            if reauthorize_every is not None:
                swagger[APIGATEWAY_AUTHORIZER_KEY]["authorizerResultTtlInSeconds"] = reauthorize_every

            if function_invoke_role:
                swagger[APIGATEWAY_AUTHORIZER_KEY]["authorizerCredentials"] = function_invoke_role

            if self._get_function_payload_type() == "REQUEST":
                identity_source = self._get_identity_source()
                if identity_source:
                    swagger[APIGATEWAY_AUTHORIZER_KEY]["identitySource"] = self._get_identity_source()

        # Authorizer Validation Expression is only allowed on COGNITO_USER_POOLS and LAMBDA_TOKEN
        is_lambda_token_authorizer = authorizer_type == "LAMBDA" and self._get_function_payload_type() == "TOKEN"

        if authorizer_type == "COGNITO_USER_POOLS" or is_lambda_token_authorizer:
            identity_validation_expression = self._get_identity_validation_expression()

            if identity_validation_expression:
                swagger[APIGATEWAY_AUTHORIZER_KEY]["identityValidationExpression"] = identity_validation_expression

        return swagger

    def _get_identity_validation_expression(self) -> Optional[PassThrough]:
        return self.identity and self.identity.get("ValidationExpression")

    @staticmethod
    def _build_identity_source_item(item_prefix: str, prop_value: str) -> str:
        item = item_prefix + prop_value
        if isinstance(prop_value, Py27UniStr):
            return Py27UniStr(item)
        return item

    def _build_identity_source_item_array(self, prop_key: str, item_prefix: str) -> List[str]:
        arr: List[str] = []
        prop_value_list = self.identity.get(prop_key)
        if prop_value_list:
            prop_path = f"Auth.Authorizers.{self.name}.Identity.{prop_key}"
            sam_expect(prop_value_list, self.api_logical_id, prop_path).to_be_a_list()
            for index, prop_value in enumerate(prop_value_list):
                sam_expect(prop_value, self.api_logical_id, f"{prop_path}[{index}]").to_be_a_string()
                arr.append(self._build_identity_source_item(item_prefix, prop_value))
        return arr

    def _get_identity_source(self) -> str:
        key_prefix_pairs = [
            ("Headers", "method.request.header."),
            ("QueryStrings", "method.request.querystring."),
            ("StageVariables", "stageVariables."),
            ("Context", "context."),
        ]

        identity_source_array = []
        for prop_key, item_prefix in key_prefix_pairs:
            identity_source_array.extend(self._build_identity_source_item_array(prop_key, item_prefix))

        identity_source = ", ".join(identity_source_array)
        if any(isinstance(i, Py27UniStr) for i in identity_source_array):
            # Convert identity_source to Py27UniStr if any part of it is Py27UniStr
            return Py27UniStr(identity_source)

        return identity_source

    def _get_user_pool_arn_array(self) -> List[PassThrough]:
        return self.user_pool_arn if isinstance(self.user_pool_arn, list) else [self.user_pool_arn]

    def _get_swagger_header_name(self) -> Optional[str]:
        authorizer_type = self._get_type()
        payload_type = self._get_function_payload_type()

        if authorizer_type == "LAMBDA" and payload_type == "REQUEST":
            return "Unused"

        return self._get_identity_header()

    def _get_type(self) -> str:
        if self.is_aws_iam_authorizer:
            return "AWS_IAM"

        if self.user_pool_arn:
            return "COGNITO_USER_POOLS"

        return "LAMBDA"

    def _get_identity_header(self) -> Optional[str]:
        if self.identity and not isinstance(self.identity, dict):
            raise InvalidResourceException(
                self.api_logical_id,
                "Auth.Authorizers.<Authorizer>.Identity must be a dict (LambdaTokenAuthorizationIdentity, "
                "LambdaRequestAuthorizationIdentity or CognitoAuthorizationIdentity).",
            )

        if not self.identity or not self.identity.get("Header"):
            return "Authorization"

        return self.identity.get("Header")

    def _get_reauthorize_every(self) -> Optional[PassThrough]:
        if not self.identity:
            return None

        return self.identity.get("ReauthorizeEvery")

    def _get_function_invoke_role(self) -> Optional[PassThrough]:
        if not self.function_invoke_role or self.function_invoke_role == "NONE":
            return None

        return self.function_invoke_role

    def _get_swagger_authtype(self) -> str:
        authorizer_type = self._get_type()
        if authorizer_type == "AWS_IAM":
            return "awsSigv4"

        if authorizer_type == "COGNITO_USER_POOLS":
            return "cognito_user_pools"

        return "custom"

    def _get_function_payload_type(self) -> str:
        return "TOKEN" if not self.function_payload_type else self.function_payload_type

    def _get_swagger_authorizer_type(self) -> Optional[str]:
        authorizer_type = self._get_type()

        if authorizer_type == "COGNITO_USER_POOLS":
            return "cognito_user_pools"

        payload_type = self._get_function_payload_type()

        if payload_type == "REQUEST":
            return "request"

        if payload_type == "TOKEN":
            return "token"

        return None  # should we raise validation error here?
