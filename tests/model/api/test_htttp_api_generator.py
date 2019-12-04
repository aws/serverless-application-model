from unittest import TestCase
from mock import patch
import pytest

from samtranslator.model import InvalidResourceException
from samtranslator.model.api.http_api_generator import HttpApiGenerator
from samtranslator.open_api.open_api import OpenApiEditor


class TestHttpApiGenerator(TestCase):
    kwargs = {
        'logical_id': "HttpApiId",
        'stage_variables': None,
        'depends_on': None,
        'definition_body': None,
        'definition_uri': None,
        'stage_name': None,
        'tags': None,
        'auth': None,
        'access_log_settings': None,
        'resource_attributes': None,
        'passthrough_resource_attributes': None
    }
    authorizers = {
        "Authorizers": {
            "OAuth2": {
                "AuthorizationScopes": ["scope"],
                "JwtConfiguration": {"config": "value"},
                "IdentitySource": "https://example.com"
            }
        }
    }

    def test_auth_no_def_body(self):
        self.kwargs["auth"] = {"Authorizers": "configuration"}
        self.kwargs["definition_body"] = None
        with pytest.raises(InvalidResourceException):
            HttpApiGenerator(**self.kwargs)._construct_http_api()

    def test_auth_wrong_properties(self):
        self.kwargs["auth"] = {"Invalid": "auth"}
        self.kwargs["definition_body"] = OpenApiEditor.gen_skeleton()
        with pytest.raises(InvalidResourceException):
            HttpApiGenerator(**self.kwargs)._construct_http_api()

    def test_auth_invalid_def_body(self):
        self.kwargs["auth"] = {"Authorizers": "auth"}
        self.kwargs["definition_body"] = {"Invalid": "open_api"}
        with pytest.raises(InvalidResourceException):
            HttpApiGenerator(**self.kwargs)._construct_http_api()

    def test_auth_invalid_auth_dict(self):
        self.kwargs["auth"] = {"Authorizers": "auth"}
        self.kwargs["definition_body"] = OpenApiEditor.gen_skeleton()
        with pytest.raises(InvalidResourceException):
            HttpApiGenerator(**self.kwargs)._construct_http_api()

    def test_auth_invalid_auth_strategy(self):
        self.kwargs["auth"] = {"Authorizers": {"Auth1": "invalid"}}
        self.kwargs["definition_body"] = OpenApiEditor.gen_skeleton()
        with pytest.raises(InvalidResourceException):
            HttpApiGenerator(**self.kwargs)._construct_http_api()

    def test_auth_missing_default_auth(self):
        self.kwargs["auth"] = self.authorizers
        self.kwargs["auth"]["DefaultAuthorizer"] = "DNE"
        self.kwargs["definition_body"] = OpenApiEditor.gen_skeleton()
        with pytest.raises(InvalidResourceException):
            HttpApiGenerator(**self.kwargs)._construct_http_api()

    def test_def_uri_invalid_dict(self):
        self.kwargs["auth"] = None
        self.kwargs["definition_body"] = None
        self.kwargs["definition_uri"] = {"Invalid": "key"}
        with pytest.raises(InvalidResourceException):
            HttpApiGenerator(**self.kwargs)._construct_http_api()

    def test_def_uri_invalid_uri(self):
        self.kwargs["auth"] = None
        self.kwargs["definition_body"] = None
        self.kwargs["definition_uri"] = "invalid_uri"
        with pytest.raises(InvalidResourceException):
            HttpApiGenerator(**self.kwargs)._construct_http_api()

    def test_no_def_body_or_uri(self):
        self.kwargs["auth"] = None
        self.kwargs["definition_body"] = None
        self.kwargs["definition_uri"] = None
        with pytest.raises(InvalidResourceException):
            HttpApiGenerator(**self.kwargs)._construct_http_api()
