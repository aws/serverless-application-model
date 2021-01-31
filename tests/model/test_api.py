from unittest import TestCase
import pytest

from samtranslator.model import InvalidResourceException
from samtranslator.model.apigateway import ApiGatewayAuthorizer, ApiGatewayDeployment


class TestApiGatewayAuthorizer(TestCase):
    def test_create_oauth2_auth(self):
        auth = ApiGatewayAuthorizer(
            api_logical_id="logicalId", name="authName", authorization_scopes=["scope1", "scope2"]
        )
        self.assertIsNotNone(auth)

    def test_create_authorizer_fails_with_string_authorization_scopes(self):
        with pytest.raises(InvalidResourceException):
            auth = ApiGatewayAuthorizer(
                api_logical_id="logicalId", name="authName", authorization_scopes="invalid_scope"
            )


class TestApiGatewayDeployment(TestCase):
    def test__make_hash_input_is_dict(self):
        deployment = ApiGatewayDeployment(logical_id="logicalIdDeployment")

        openapi_version = "3.0.0"
        swagger = {"foo": "bar", "nested": {"a": "b", "c": "d"}}
        domain = {"foo": "bar"}
        redeploy_restapi_parameters = {"function_names": {"logicalId": "functionName"}}

        expected = deployment._make_hash_input(openapi_version, swagger, domain, redeploy_restapi_parameters)

        self.assertIsInstance(expected, dict)
        self.assertIn("openapi_version", expected)
        self.assertIn("swagger", expected)
        self.assertIn("domain", expected)
        self.assertIn("function_names", expected)
