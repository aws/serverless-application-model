from unittest import TestCase

import pytest
from samtranslator.model import InvalidResourceException
from samtranslator.model.apigateway import ApiGatewayAuthorizer
from samtranslator.utils.py27hash_fix import Py27Dict


class TestApiGatewayAuthorizer(TestCase):
    def test_create_oauth2_auth(self):
        auth = ApiGatewayAuthorizer(
            api_logical_id="logicalId", name="authName", authorization_scopes=["scope1", "scope2"]
        )
        self.assertIsNotNone(auth)

    def test_create_authorizer_fails_with_string_authorization_scopes(self):
        with pytest.raises(InvalidResourceException):
            ApiGatewayAuthorizer(api_logical_id="logicalId", name="authName", authorization_scopes="invalid_scope")

    def test_create_authorizer_fails_with_missing_identity_values_and_not_cached(self):
        with pytest.raises(InvalidResourceException):
            ApiGatewayAuthorizer(
                api_logical_id="logicalId",
                name="authName",
                identity={"ReauthorizeEvery": 10},
                function_payload_type="REQUEST",
            )

    def test_create_authorizer_fails_with_invalid_function_payload_type(self):
        with self.assertRaises(InvalidResourceException):
            ApiGatewayAuthorizer(
                api_logical_id="logicalId",
                name="authName",
                function_payload_type=Py27Dict({"key": "value"}),
            )

    def test_create_authorizer_fails_with_empty_identity(self):
        with pytest.raises(InvalidResourceException):
            ApiGatewayAuthorizer(
                api_logical_id="logicalId", name="authName", identity={}, function_payload_type="REQUEST"
            )

    def test_create_authorizer_doesnt_fail_with_identity_reauthorization_every_as_zero(self):
        auth = ApiGatewayAuthorizer(
            api_logical_id="logicalId",
            name="authName",
            identity={"ReauthorizeEvery": 0},
            function_payload_type="REQUEST",
        )

        self.assertIsNotNone(auth)

    def test_create_authorizer_with_non_integer_identity(self):
        auth = ApiGatewayAuthorizer(
            api_logical_id="logicalId",
            name="authName",
            identity={"ReauthorizeEvery": [], "Headers": ["Accept"]},
            function_payload_type="REQUEST",
        )

        self.assertIsNotNone(auth)

    def test_create_authorizer_with_identity_intrinsic_is_valid_with_headers(self):
        auth = ApiGatewayAuthorizer(
            api_logical_id="logicalId",
            name="authName",
            identity={"ReauthorizeEvery": {"FN:If": ["isProd", 10, 0]}, "Headers": ["Accept"]},
            function_payload_type="REQUEST",
        )

        self.assertIsNotNone(auth)

    def test_create_authorizer_with_identity_intrinsic_is_invalid_if_no_querystring_stagevariables_context_headers(
        self,
    ):
        with pytest.raises(InvalidResourceException):
            ApiGatewayAuthorizer(
                api_logical_id="logicalId",
                name="authName",
                identity={"ReauthorizeEvery": {"FN:If": ["isProd", 10, 0]}},
                function_payload_type="REQUEST",
            )

    def test_create_authorizer_with_identity_intrinsic_is_valid_with_context(self):
        auth = ApiGatewayAuthorizer(
            api_logical_id="logicalId",
            name="authName",
            identity={"ReauthorizeEvery": {"FN:If": ["isProd", 10, 0]}, "Context": ["Accept"]},
            function_payload_type="REQUEST",
        )

        self.assertIsNotNone(auth)

    def test_create_authorizer_with_identity_intrinsic_is_valid_with_stage_variables(self):
        auth = ApiGatewayAuthorizer(
            api_logical_id="logicalId",
            name="authName",
            identity={"ReauthorizeEvery": {"FN:If": ["isProd", 10, 0]}, "StageVariables": ["Stage"]},
            function_payload_type="REQUEST",
        )

        self.assertIsNotNone(auth)

    def test_create_authorizer_with_identity_intrinsic_is_valid_with_query_strings(self):
        auth = ApiGatewayAuthorizer(
            api_logical_id="logicalId",
            name="authName",
            identity={"ReauthorizeEvery": {"FN:If": ["isProd", 10, 0]}, "QueryStrings": ["AQueryString"]},
            function_payload_type="REQUEST",
        )

        self.assertIsNotNone(auth)

    def test_create_authorizer_with_identity_ReauthorizeEvery_asNone_valid_with_query_strings(self):
        auth = ApiGatewayAuthorizer(
            api_logical_id="logicalId",
            name="authName",
            identity={"ReauthorizeEvery": None, "QueryStrings": ["AQueryString"]},
            function_payload_type="REQUEST",
        )

        self.assertIsNotNone(auth)
