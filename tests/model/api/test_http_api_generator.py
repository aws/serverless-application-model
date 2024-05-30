from unittest import TestCase

import pytest
from samtranslator.model import InvalidResourceException
from samtranslator.model.api.http_api_generator import HttpApiGenerator
from samtranslator.open_api.open_api import OpenApiEditor


class TestHttpApiGenerator(TestCase):
    kwargs = {
        "logical_id": "HttpApiId",
        "stage_variables": None,
        "depends_on": None,
        "definition_body": None,
        "definition_uri": None,
        "name": None,
        "stage_name": None,
        "tags": None,
        "auth": None,
        "access_log_settings": None,
        "resource_attributes": None,
        "passthrough_resource_attributes": None,
    }
    authorizers = {
        "Authorizers": {
            "OAuth2": {
                "AuthorizationScopes": ["scope"],
                "JwtConfiguration": {"config": "value"},
                "IdentitySource": "https://example.com",
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

    def test_auth_intrinsic_default_auth(self):
        self.kwargs["auth"] = self.authorizers
        self.kwargs["auth"]["DefaultAuthorizer"] = {"Ref": "SomeValue"}
        self.kwargs["definition_body"] = OpenApiEditor.gen_skeleton()
        with pytest.raises(InvalidResourceException):
            HttpApiGenerator(**self.kwargs)._construct_http_api()

    def test_auth_iam_enabled(self):
        self.kwargs["auth"] = {
            "EnableIamAuthorizer": True,
        }
        self.kwargs["definition_body"] = OpenApiEditor.gen_skeleton()
        http_api = HttpApiGenerator(**self.kwargs)._construct_http_api()
        self.assertEqual(
            http_api.Body["components"]["securitySchemes"],
            {
                "AWS_IAM": {
                    "type": "apiKey",
                    "name": "Authorization",
                    "in": "header",
                    "x-amazon-apigateway-authtype": "awsSigv4",
                }
            },
        )

    def test_enabling_auth_iam_does_not_clobber_conflicting_custom_authorizer(self):
        self.kwargs["auth"] = {
            "EnableIamAuthorizer": True,
            "Authorizers": {
                "AWS_IAM": {
                    "AuthorizationScopes": ["scope"],
                    "JwtConfiguration": {"config": "value"},
                    "IdentitySource": "https://example.com",
                }
            },
        }
        self.kwargs["definition_body"] = OpenApiEditor.gen_skeleton()
        self.kwargs["definition_uri"] = None
        http_api = HttpApiGenerator(**self.kwargs)._construct_http_api()
        self.assertEqual(
            http_api.Body["components"]["securitySchemes"],
            {
                "AWS_IAM": {
                    "type": "oauth2",
                    "x-amazon-apigateway-authorizer": {
                        "jwtConfiguration": {"config": "value"},
                        "identitySource": "https://example.com",
                        "type": "jwt",
                    },
                }
            },
        )

    def test_auth_iam_enabled_with_default(self):
        self.kwargs["auth"] = {
            "DefaultAuthorizer": "AWS_IAM",
            "EnableIamAuthorizer": True,
        }
        self.kwargs["definition_body"] = OpenApiEditor.gen_skeleton()
        http_api = HttpApiGenerator(**self.kwargs)._construct_http_api()
        self.assertEqual(
            http_api.Body["components"]["securitySchemes"],
            {
                "AWS_IAM": {
                    "type": "apiKey",
                    "name": "Authorization",
                    "in": "header",
                    "x-amazon-apigateway-authtype": "awsSigv4",
                }
            },
        )

    def test_auth_missing_iam_enablement(self):
        self.kwargs["auth"] = {
            "DefaultAuthorizer": "AWS_IAM",
            "EnableIamAuthorizer": False,
        }
        self.kwargs["definition_body"] = OpenApiEditor.gen_skeleton()
        with pytest.raises(InvalidResourceException) as e:
            HttpApiGenerator(**self.kwargs)._construct_http_api()
        self.assertEqual(
            e.value.message,
            "Resource with id [HttpApiId] is invalid. "
            + "Unable to set DefaultAuthorizer because 'AWS_IAM' was not defined in 'Authorizers'.",
        )

    def test_auth_iam_disabled(self):
        self.kwargs["auth"] = {
            "EnableIamAuthorizer": False,
        }
        self.kwargs["definition_body"] = OpenApiEditor.gen_skeleton()
        http_api = HttpApiGenerator(**self.kwargs)._construct_http_api()
        self.assertNotIn("components", http_api.Body)

    def test_auth_iam_not_enabled_with_unsupported_values(self):
        unsupported_values = [1, "", [], {}, {"Ref": "MyVar"}, "True", None]
        for val in unsupported_values:
            self.kwargs["auth"] = {
                "EnableIamAuthorizer": val,
            }
            self.kwargs["definition_body"] = OpenApiEditor.gen_skeleton()
            http_api = HttpApiGenerator(**self.kwargs)._construct_http_api()
            self.assertNotIn("components", http_api.Body, f"EnableIamAuthorizer value: {val}")

    def test_auth_novalue_default_does_not_raise(self):
        self.kwargs["auth"] = self.authorizers
        self.kwargs["auth"]["DefaultAuthorizer"] = {"Ref": "AWS::NoValue"}
        self.kwargs["definition_body"] = OpenApiEditor.gen_skeleton()
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


class TestCustomDomains(TestCase):
    kwargs = {
        "logical_id": "HttpApiId",
        "stage_variables": None,
        "depends_on": None,
        "definition_body": None,
        "definition_uri": "s3://bucket/key",
        "name": None,
        "stage_name": None,
        "tags": None,
        "auth": None,
        "access_log_settings": None,
        "resource_attributes": None,
        "passthrough_resource_attributes": None,
        "domain": None,
    }

    def setUp(self) -> None:
        self.route53_record_set_groups = {}

    def test_no_domain(self):
        self.kwargs["domain"] = None
        http_api = HttpApiGenerator(**self.kwargs)._construct_http_api()
        domain, basepath, route = HttpApiGenerator(**self.kwargs)._construct_api_domain(
            http_api, self.route53_record_set_groups
        )
        self.assertIsNone(domain)
        self.assertIsNone(basepath)
        self.assertIsNone(route)

    def test_no_domain_name(self):
        self.kwargs["domain"] = {"CertificateArn": "someurl"}
        http_api = HttpApiGenerator(**self.kwargs)._construct_http_api()
        with pytest.raises(InvalidResourceException) as e:
            HttpApiGenerator(**self.kwargs)._construct_api_domain(http_api, self.route53_record_set_groups)
        self.assertEqual(
            e.value.message,
            "Resource with id [HttpApiId] is invalid. "
            + "Custom Domains only works if both DomainName and CertificateArn are provided.",
        )

    def test_no_cert_arn(self):
        self.kwargs["domain"] = {"DomainName": "example.com"}
        http_api = HttpApiGenerator(**self.kwargs)._construct_http_api()
        with pytest.raises(InvalidResourceException) as e:
            HttpApiGenerator(**self.kwargs)._construct_api_domain(http_api, self.route53_record_set_groups)
        self.assertEqual(
            e.value.message,
            "Resource with id [HttpApiId] is invalid. "
            + "Custom Domains only works if both DomainName and CertificateArn are provided.",
        )

    def test_basic_domain_default_endpoint(self):
        self.kwargs["domain"] = {"DomainName": "example.com", "CertificateArn": "some-url"}
        http_api = HttpApiGenerator(**self.kwargs)._construct_http_api()
        domain, basepath, route = HttpApiGenerator(**self.kwargs)._construct_api_domain(
            http_api, self.route53_record_set_groups
        )
        self.assertIsNotNone(domain, None)
        self.assertIsNotNone(basepath, None)
        self.assertEqual(len(basepath), 1)
        self.assertIsNone(route, None)
        self.assertEqual(domain.DomainNameConfigurations[0].get("EndpointType"), "REGIONAL")

    def test_basic_domain_regional_endpoint(self):
        self.kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "EndpointConfiguration": "REGIONAL",
        }
        http_api = HttpApiGenerator(**self.kwargs)._construct_http_api()
        domain, basepath, route = HttpApiGenerator(**self.kwargs)._construct_api_domain(
            http_api, self.route53_record_set_groups
        )
        self.assertIsNotNone(domain, None)
        self.assertIsNotNone(basepath, None)
        self.assertEqual(len(basepath), 1)
        self.assertIsNone(route, None)
        self.assertEqual(domain.DomainNameConfigurations[0].get("EndpointType"), "REGIONAL")

    def test_basic_domain_edge_endpoint(self):
        self.kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "EndpointConfiguration": "EDGE",
        }
        http_api = HttpApiGenerator(**self.kwargs)._construct_http_api()
        with pytest.raises(InvalidResourceException) as e:
            HttpApiGenerator(**self.kwargs)._construct_api_domain(http_api, self.route53_record_set_groups)
        self.assertEqual(
            e.value.message,
            "Resource with id [HttpApiId] is invalid. EndpointConfiguration for Custom Domains must be one of ['REGIONAL'].",
        )

    def test_bad_endpoint(self):
        self.kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "EndpointConfiguration": "INVALID",
        }
        http_api = HttpApiGenerator(**self.kwargs)._construct_http_api()
        with pytest.raises(InvalidResourceException) as e:
            HttpApiGenerator(**self.kwargs)._construct_api_domain(http_api, self.route53_record_set_groups)
        self.assertEqual(
            e.value.message,
            "Resource with id [HttpApiId] is invalid. "
            + "EndpointConfiguration for Custom Domains must be one of ['REGIONAL'].",
        )

    def test_basic_route53(self):
        self.kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "Route53": {"HostedZoneId": "xyz"},
        }
        http_api = HttpApiGenerator(**self.kwargs)._construct_http_api()
        domain, basepath, route = HttpApiGenerator(**self.kwargs)._construct_api_domain(
            http_api, self.route53_record_set_groups
        )
        self.assertIsNotNone(domain, None)
        self.assertIsNotNone(basepath, None)
        self.assertEqual(len(basepath), 1)
        self.assertIsNotNone(route, None)
        self.assertEqual(domain.DomainNameConfigurations[0].get("EndpointType"), "REGIONAL")

    def test_basepaths(self):
        self.kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "BasePath": ["one", "two", "three"],
            "Route53": {"HostedZoneId": "xyz"},
        }
        http_api = HttpApiGenerator(**self.kwargs)._construct_http_api()
        domain, basepath, route = HttpApiGenerator(**self.kwargs)._construct_api_domain(
            http_api, self.route53_record_set_groups
        )
        self.assertIsNotNone(domain, None)
        self.assertIsNotNone(basepath, None)
        self.assertEqual(len(basepath), 3)
        self.assertIsNotNone(route, None)
        self.assertEqual(domain.DomainNameConfigurations[0].get("EndpointType"), "REGIONAL")

    def test_invalid_basepaths(self):
        self.kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "BasePath": ["inv*alid"],
            "Route53": {"HostedZoneId": "xyz"},
        }
        http_api = HttpApiGenerator(**self.kwargs)._construct_http_api()
        with pytest.raises(InvalidResourceException) as e:
            HttpApiGenerator(**self.kwargs)._construct_api_domain(http_api, self.route53_record_set_groups)
        self.assertEqual(
            e.value.message, "Resource with id [HttpApiId] is invalid. " + "Invalid Basepath name provided."
        )

    def test_basepaths_complex(self):
        self.kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "BasePath": ["one-1", "two_2", "three", "/", "/api", "api/v1", "api/v1/", "/api/v1/"],
            "Route53": {"HostedZoneId": "xyz", "HostedZoneName": "abc", "IpV6": True},
        }
        http_api = HttpApiGenerator(**self.kwargs)._construct_http_api()
        domain, basepath, route = HttpApiGenerator(**self.kwargs)._construct_api_domain(
            http_api, self.route53_record_set_groups
        )
        self.assertIsNotNone(domain, None)
        self.assertIsNotNone(basepath, None)
        self.assertEqual(len(basepath), 8)
        self.assertIsNotNone(route, None)
        self.assertEqual(route.HostedZoneName, None)
        self.assertEqual(route.HostedZoneId, "xyz")
        self.assertEqual(len(route.RecordSets), 2)
        self.assertEqual(
            list(map(lambda base: base.ApiMappingKey, basepath)),
            ["one-1", "two_2", "three", "", "api", "api/v1", "api/v1", "api/v1"],
        )
