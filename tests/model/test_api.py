from unittest import TestCase
import pytest

from samtranslator.model import InvalidResourceException
from samtranslator.model.apigateway import ApiGatewayAuthorizer


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

    def test_create_authorizer_fails_with_missing_identity_values_and_not_cached(self):
        with pytest.raises(InvalidResourceException):
            auth = ApiGatewayAuthorizer(
                api_logical_id="logicalId",
                name="authName",
                identity={"ReauthorizeEvery": 10},
                function_payload_type="REQUEST",
            )

    def test_create_authorizer_fails_with_empty_identity(self):
        with pytest.raises(InvalidResourceException):
            auth = ApiGatewayAuthorizer(
                api_logical_id="logicalId", name="authName", identity={}, function_payload_type="REQUEST"
            )
