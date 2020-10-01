from unittest import TestCase
import pytest

from samtranslator.model import InvalidResourceException
from samtranslator.model.apigatewayv2 import ApiGatewayV2Authorizer, ApiGatewayV2HttpApi, ApiGatewayV2Stage


class TestApiGatewayV2Authorizer(TestCase):
    def test_create_oauth2_auth(self):
        auth = ApiGatewayV2Authorizer(
            api_logical_id="logicalId",
            name="authName",
            jwt_configuration={"config": "value"},
            id_source="https://example.com",
            authorization_scopes=["scope1", "scope2"],
        )
        self.assertEquals(auth.api_logical_id, "logicalId")
        self.assertEquals(auth.name, "authName")
        self.assertEquals(auth.jwt_configuration, {"config": "value"})
        self.assertEquals(auth.id_source, "https://example.com")
        self.assertEquals(auth.authorization_scopes, ["scope1", "scope2"])

    def test_create_authorizer_no_id_source(self):
        with pytest.raises(InvalidResourceException):
            auth = ApiGatewayV2Authorizer(
                api_logical_id="logicalId", name="authName", jwt_configuration={"config": "value"}
            )

    def test_create_authorizer_no_jwt_config(self):
        with pytest.raises(InvalidResourceException):
            auth = ApiGatewayV2Authorizer(api_logical_id="logicalId", name="authName", id_source="https://example.com")

    def test_create_authorizer_fails_with_string_authorization_scopes(self):
        with pytest.raises(InvalidResourceException):
            auth = ApiGatewayV2Authorizer(
                api_logical_id="logicalId",
                name="authName",
                jwt_configuration={"config": "value"},
                authorization_scopes="invalid_scope",
            )

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
        self.assertEquals(auth.api_logical_id, "logicalId")
        self.assertEquals(auth.name, "lambdaAuth")
        self.assertEquals(auth.function_arn, "lambdaArn")
        self.assertEquals(auth.identity, {"Headers": ["Authorization"], "ReauthorizeEvery": 42})
        self.assertEquals(auth.authorizer_payload_format_version, "2.0")
        self.assertEquals(auth.enable_simple_responses, True)

    def test_create_lambda_auth_no_function_arn(self):
        with pytest.raises(InvalidResourceException):
            auth = ApiGatewayV2Authorizer(
                api_logical_id="logicalId",
                name="lambdaAuth",
            )

    def test_create_lambda_auth_no_authorizer_payload_format_version(self):
        with pytest.raises(InvalidResourceException):
            auth = ApiGatewayV2Authorizer(
                api_logical_id="logicalId",
                name="lambdaAuth",
                function_arn="lambdaArn",
            )
