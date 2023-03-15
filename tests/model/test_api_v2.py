from unittest import TestCase, mock

import pytest
from samtranslator.model import InvalidResourceException
from samtranslator.model.apigatewayv2 import ApiGatewayV2Authorizer


class TestApiGatewayV2Authorizer(TestCase):
    def test_create_iam_auth(self):
        auth = ApiGatewayV2Authorizer(is_aws_iam_authorizer=True)
        self.assertEqual(auth.is_aws_iam_authorizer, True)

    def test_create_oauth2_auth(self):
        auth = ApiGatewayV2Authorizer(
            api_logical_id="logicalId",
            name="authName",
            jwt_configuration={"config": "value"},
            id_source="https://example.com",
            authorization_scopes=["scope1", "scope2"],
        )
        self.assertEqual(auth.api_logical_id, "logicalId")
        self.assertEqual(auth.name, "authName")
        self.assertEqual(auth.jwt_configuration, {"config": "value"})
        self.assertEqual(auth.id_source, "https://example.com")
        self.assertEqual(auth.authorization_scopes, ["scope1", "scope2"])

    def test_create_lambda_auth(self):
        auth = ApiGatewayV2Authorizer(
            api_logical_id="logicalId",
            name="lambdaAuth",
            function_arn="lambdaArn",
            function_invoke_role="iamRole",
            identity={"Headers": ["Authorization"], "ReauthorizeEvery": 42},
            authorizer_payload_format_version="2.0",
            enable_simple_responses=True,
        )
        self.assertEqual(auth.api_logical_id, "logicalId")
        self.assertEqual(auth.name, "lambdaAuth")
        self.assertEqual(auth.function_arn, "lambdaArn")
        self.assertEqual(auth.identity, {"Headers": ["Authorization"], "ReauthorizeEvery": 42})
        self.assertEqual(auth.authorizer_payload_format_version, "2.0")
        self.assertEqual(auth.enable_simple_responses, True)

    def test_create_authorizer_fails_with_string_authorization_scopes(self):
        with pytest.raises(InvalidResourceException) as e:
            ApiGatewayV2Authorizer(
                api_logical_id="logicalId",
                name="authName",
                jwt_configuration={"config": "value"},
                authorization_scopes="invalid_scope",
            )
        self.assertEqual(
            e.value.message,
            "Resource with id [logicalId] is invalid. " + "AuthorizationScopes must be a list.",
        )

    def test_create_authorizer_fails_with_authorization_scopes_non_oauth2(self):
        with pytest.raises(InvalidResourceException) as e:
            ApiGatewayV2Authorizer(
                api_logical_id="logicalId",
                name="authName",
                authorization_scopes=["scope1", "scope2"],
            )
        self.assertEqual(
            e.value.message,
            "Resource with id [logicalId] is invalid. "
            + "AuthorizationScopes must be defined only for OAuth2 Authorizer.",
        )

    @mock.patch(
        "samtranslator.model.apigatewayv2.ApiGatewayV2Authorizer._get_auth_type", mock.MagicMock(return_value="INVALID")
    )
    def test_create_authorizer_fails_with_jtw_configuration_non_oauth2(self):
        with pytest.raises(InvalidResourceException) as e:
            ApiGatewayV2Authorizer(
                api_logical_id="logicalId",
                name="authName",
                jwt_configuration={"config": "value"},
            )
        self.assertEqual(
            e.value.message,
            "Resource with id [logicalId] is invalid. "
            + "JwtConfiguration must be defined only for OAuth2 Authorizer.",
        )

    def test_create_authorizer_fails_with_id_source_non_oauth2(self):
        with pytest.raises(InvalidResourceException) as e:
            ApiGatewayV2Authorizer(
                api_logical_id="logicalId",
                name="authName",
                id_source="https://example.com",
            )
        self.assertEqual(
            e.value.message,
            "Resource with id [logicalId] is invalid. " + "IdentitySource must be defined only for OAuth2 Authorizer.",
        )

    def test_create_authorizer_fails_with_function_arn_non_lambda(self):
        with pytest.raises(InvalidResourceException) as e:
            ApiGatewayV2Authorizer(
                api_logical_id="logicalId",
                name="authName",
                jwt_configuration={"config": "value"},
                authorization_scopes=["scope1", "scope2"],
                function_arn="lambdaArn",
            )
        self.assertEqual(
            e.value.message,
            "Resource with id [logicalId] is invalid. " + "FunctionArn must be defined only for Lambda Authorizer.",
        )

    def test_create_authorizer_fails_with_function_invoke_role_non_lambda(self):
        with pytest.raises(InvalidResourceException) as e:
            ApiGatewayV2Authorizer(
                api_logical_id="logicalId",
                name="authName",
                jwt_configuration={"config": "value"},
                authorization_scopes=["scope1", "scope2"],
                function_invoke_role="iamRole",
            )
        self.assertEqual(
            e.value.message,
            "Resource with id [logicalId] is invalid. "
            + "FunctionInvokeRole must be defined only for Lambda Authorizer.",
        )

    def test_create_authorizer_fails_with_identity_non_lambda(self):
        with pytest.raises(InvalidResourceException) as e:
            ApiGatewayV2Authorizer(
                api_logical_id="logicalId",
                name="authName",
                jwt_configuration={"config": "value"},
                authorization_scopes=["scope1", "scope2"],
                identity={"Headers": ["Authorization"], "ReauthorizeEvery": 42},
            )
        self.assertEqual(
            e.value.message,
            "Resource with id [logicalId] is invalid. " + "Identity must be defined only for Lambda Authorizer.",
        )

    def test_create_authorizer_fails_with_authorizer_payload_format_version_non_lambda(self):
        with pytest.raises(InvalidResourceException) as e:
            ApiGatewayV2Authorizer(
                api_logical_id="logicalId",
                name="authName",
                jwt_configuration={"config": "value"},
                authorization_scopes=["scope1", "scope2"],
                authorizer_payload_format_version="2.0",
            )
        self.assertEqual(
            e.value.message,
            "Resource with id [logicalId] is invalid. "
            + "AuthorizerPayloadFormatVersion must be defined only for Lambda Authorizer.",
        )

    def test_create_authorizer_fails_with_enable_simple_responses_non_lambda(self):
        with pytest.raises(InvalidResourceException) as e:
            ApiGatewayV2Authorizer(
                api_logical_id="logicalId",
                name="authName",
                jwt_configuration={"config": "value"},
                authorization_scopes=["scope1", "scope2"],
                enable_simple_responses=True,
            )
        self.assertEqual(
            e.value.message,
            "Resource with id [logicalId] is invalid. "
            + "EnableSimpleResponses must be defined only for Lambda Authorizer.",
        )

    def test_create_authorizer_fails_with_enable_function_default_permissions_non_lambda(self):
        with pytest.raises(InvalidResourceException) as e:
            ApiGatewayV2Authorizer(
                api_logical_id="logicalId",
                name="authName",
                jwt_configuration={"config": "value"},
                authorization_scopes=["scope1", "scope2"],
                enable_function_default_permissions=True,
            )
        self.assertEqual(
            e.value.message,
            "Resource with id [logicalId] is invalid. "
            + "EnableFunctionDefaultPermissions must be defined only for Lambda Authorizer.",
        )

    @mock.patch(
        "samtranslator.model.apigatewayv2.ApiGatewayV2Authorizer._get_auth_type", mock.MagicMock(return_value="JWT")
    )
    def test_create_jwt_authorizer_no_jwt_configuration(self):
        with pytest.raises(InvalidResourceException) as e:
            ApiGatewayV2Authorizer(api_logical_id="logicalId", name="authName")
        self.assertEqual(
            e.value.message,
            "Resource with id [logicalId] is invalid. " + "authName OAuth2 Authorizer must define 'JwtConfiguration'.",
        )

    def test_create_jwt_authorizer_no_id_source(self):
        with pytest.raises(InvalidResourceException) as e:
            ApiGatewayV2Authorizer(api_logical_id="logicalId", name="authName", jwt_configuration={"config": "value"})
        self.assertEqual(
            e.value.message,
            "Resource with id [logicalId] is invalid. " + "authName OAuth2 Authorizer must define 'IdentitySource'.",
        )

    def test_create_lambda_auth_no_function_arn(self):
        with pytest.raises(InvalidResourceException) as e:
            ApiGatewayV2Authorizer(
                api_logical_id="logicalId",
                name="lambdaAuth",
            )
        self.assertEqual(
            e.value.message,
            "Resource with id [logicalId] is invalid. " + "lambdaAuth Lambda Authorizer must define 'FunctionArn'.",
        )

    def test_create_lambda_auth_no_authorizer_payload_format_version(self):
        with pytest.raises(InvalidResourceException) as e:
            ApiGatewayV2Authorizer(
                api_logical_id="logicalId",
                name="lambdaAuth",
                function_arn="lambdaArn",
            )
        self.assertEqual(
            e.value.message,
            "Resource with id [logicalId] is invalid. "
            + "lambdaAuth Lambda Authorizer must define 'AuthorizerPayloadFormatVersion'.",
        )
