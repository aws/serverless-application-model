from unittest import TestCase

import pytest
from samtranslator.model import InvalidResourceException
from samtranslator.model.api.http_api_generator import HttpApiGenerator
from samtranslator.model.api.websocket_api_generator import WebSocketApiGenerator


class TestCustomDomains(TestCase):
    http_kwargs = {
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

    websocket_kwargs = {
        "logical_id": "WebSocketApiId",
        "stage_variables": None,
        "depends_on": None,
        "name": "WebSocketApi",
        "stage_name": None,
        "tags": None,
        "auth_config": None,
        "access_log_settings": None,
        "resource_attributes": None,
        "routes": {"$default": {"FunctionName": {"Ref": "DefaultFunction"}}},
        "route_selection_expression": "$request.body.action",
        "passthrough_resource_attributes": None,
        "domain": None,
    }

    def setUp(self) -> None:
        self.route53_record_set_groups = {}

    def test_no_domain(self):
        self.http_kwargs["domain"] = None
        http_api = HttpApiGenerator(**self.http_kwargs)._construct_http_api()
        domain, basepath, route = HttpApiGenerator(**self.http_kwargs)._construct_api_domain(
            http_api, self.route53_record_set_groups
        )
        self.assertIsNone(domain)
        self.assertIsNone(basepath)
        self.assertIsNone(route)
        self.websocket_kwargs["domain"] = None
        websocket_api = WebSocketApiGenerator(**self.websocket_kwargs)._construct_websocket_api()
        domain, basepath, route = WebSocketApiGenerator(**self.websocket_kwargs)._construct_api_domain(
            websocket_api, self.route53_record_set_groups
        )
        self.assertIsNone(domain)
        self.assertIsNone(basepath)
        self.assertIsNone(route)

    def test_no_domain_name(self):
        self.http_kwargs["domain"] = {"CertificateArn": "someurl"}
        http_api = HttpApiGenerator(**self.http_kwargs)._construct_http_api()
        with pytest.raises(InvalidResourceException) as e:
            HttpApiGenerator(**self.http_kwargs)._construct_api_domain(http_api, self.route53_record_set_groups)
        self.assertEqual(
            e.value.message,
            "Resource with id [HttpApiId] is invalid. "
            + "Custom Domains only works if both DomainName and CertificateArn are provided.",
        )
        self.websocket_kwargs["domain"] = {"CertificateArn": "someurl"}
        websocket_api = WebSocketApiGenerator(**self.websocket_kwargs)._construct_websocket_api()
        with pytest.raises(InvalidResourceException) as e:
            WebSocketApiGenerator(**self.websocket_kwargs)._construct_api_domain(
                websocket_api, self.route53_record_set_groups
            )
        self.assertEqual(
            e.value.message,
            "Resource with id [WebSocketApiId] is invalid. "
            + "Custom Domains only works if both DomainName and CertificateArn are provided.",
        )

    def test_no_cert_arn(self):
        self.http_kwargs["domain"] = {"DomainName": "example.com"}
        http_api = HttpApiGenerator(**self.http_kwargs)._construct_http_api()
        with pytest.raises(InvalidResourceException) as e:
            HttpApiGenerator(**self.http_kwargs)._construct_api_domain(http_api, self.route53_record_set_groups)
        self.assertEqual(
            e.value.message,
            "Resource with id [HttpApiId] is invalid. "
            + "Custom Domains only works if both DomainName and CertificateArn are provided.",
        )
        self.websocket_kwargs["domain"] = {"DomainName": "example.com"}
        websocket_api = WebSocketApiGenerator(**self.websocket_kwargs)._construct_websocket_api()
        with pytest.raises(InvalidResourceException) as e:
            WebSocketApiGenerator(**self.websocket_kwargs)._construct_api_domain(
                websocket_api, self.route53_record_set_groups
            )
        self.assertEqual(
            e.value.message,
            "Resource with id [WebSocketApiId] is invalid. "
            + "Custom Domains only works if both DomainName and CertificateArn are provided.",
        )

    def test_basic_domain_default_endpoint(self):
        self.http_kwargs["domain"] = {"DomainName": "example.com", "CertificateArn": "some-url"}
        http_api = HttpApiGenerator(**self.http_kwargs)._construct_http_api()
        domain, basepath, route = HttpApiGenerator(**self.http_kwargs)._construct_api_domain(
            http_api, self.route53_record_set_groups
        )
        self.assertIsNotNone(domain, None)
        self.assertIsNotNone(basepath, None)
        self.assertEqual(len(basepath), 1)
        self.assertIsNone(route, None)
        self.assertEqual(domain.DomainNameConfigurations[0].get("EndpointType"), "REGIONAL")
        self.websocket_kwargs["domain"] = {"DomainName": "example.com", "CertificateArn": "some-url"}
        websocket_api = WebSocketApiGenerator(**self.websocket_kwargs)._construct_websocket_api()  # throws an erri
        domain, basepath, route = WebSocketApiGenerator(**self.websocket_kwargs)._construct_api_domain(
            websocket_api, self.route53_record_set_groups
        )
        self.assertIsNotNone(domain, None)
        self.assertIsNotNone(basepath, None)
        self.assertEqual(len(basepath), 1)
        self.assertIsNone(route, None)
        self.assertEqual(domain.DomainNameConfigurations[0].get("EndpointType"), "REGIONAL")

    def test_basic_domain_regional_endpoint(self):
        self.http_kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "EndpointConfiguration": "REGIONAL",
        }
        http_api = HttpApiGenerator(**self.http_kwargs)._construct_http_api()
        domain, basepath, route = HttpApiGenerator(**self.http_kwargs)._construct_api_domain(
            http_api, self.route53_record_set_groups
        )
        self.assertIsNotNone(domain, None)
        self.assertIsNotNone(basepath, None)
        self.assertEqual(len(basepath), 1)
        self.assertIsNone(route, None)
        self.assertEqual(domain.DomainNameConfigurations[0].get("EndpointType"), "REGIONAL")
        self.websocket_kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "EndpointConfiguration": "REGIONAL",
        }
        websocket_api = WebSocketApiGenerator(**self.websocket_kwargs)._construct_websocket_api()
        domain, basepath, route = WebSocketApiGenerator(**self.websocket_kwargs)._construct_api_domain(
            websocket_api, self.route53_record_set_groups
        )
        self.assertIsNotNone(domain, None)
        self.assertIsNotNone(basepath, None)
        self.assertEqual(len(basepath), 1)
        self.assertIsNone(route, None)
        self.assertEqual(domain.DomainNameConfigurations[0].get("EndpointType"), "REGIONAL")

    def test_basic_domain_edge_endpoint(self):
        self.http_kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "EndpointConfiguration": "EDGE",
        }
        http_api = HttpApiGenerator(**self.http_kwargs)._construct_http_api()
        with pytest.raises(InvalidResourceException) as e:
            HttpApiGenerator(**self.http_kwargs)._construct_api_domain(http_api, self.route53_record_set_groups)
        self.assertEqual(
            e.value.message,
            "Resource with id [HttpApiId] is invalid. EndpointConfiguration for Custom Domains must be one of ['REGIONAL'].",
        )
        self.websocket_kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "EndpointConfiguration": "EDGE",
        }
        websocket_api = WebSocketApiGenerator(**self.websocket_kwargs)._construct_websocket_api()
        with pytest.raises(InvalidResourceException) as e:
            WebSocketApiGenerator(**self.websocket_kwargs)._construct_api_domain(
                websocket_api, self.route53_record_set_groups
            )
        self.assertEqual(
            e.value.message,
            "Resource with id [WebSocketApiId] is invalid. EndpointConfiguration for Custom Domains must be one of ['REGIONAL'].",
        )

    def test_bad_endpoint(self):
        self.http_kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "EndpointConfiguration": "INVALID",
        }
        http_api = HttpApiGenerator(**self.http_kwargs)._construct_http_api()
        with pytest.raises(InvalidResourceException) as e:
            HttpApiGenerator(**self.http_kwargs)._construct_api_domain(http_api, self.route53_record_set_groups)
        self.assertEqual(
            e.value.message,
            "Resource with id [HttpApiId] is invalid. "
            + "EndpointConfiguration for Custom Domains must be one of ['REGIONAL'].",
        )
        self.websocket_kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "EndpointConfiguration": "INVALID",
        }
        websocket_api = WebSocketApiGenerator(**self.websocket_kwargs)._construct_websocket_api()
        with pytest.raises(InvalidResourceException) as e:
            WebSocketApiGenerator(**self.websocket_kwargs)._construct_api_domain(
                websocket_api, self.route53_record_set_groups
            )
        self.assertEqual(
            e.value.message,
            "Resource with id [WebSocketApiId] is invalid. "
            + "EndpointConfiguration for Custom Domains must be one of ['REGIONAL'].",
        )

    def test_basic_route53(self):
        self.http_kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "Route53": {"HostedZoneId": "xyz"},
        }
        http_api = HttpApiGenerator(**self.http_kwargs)._construct_http_api()
        domain, basepath, route = HttpApiGenerator(**self.http_kwargs)._construct_api_domain(
            http_api, self.route53_record_set_groups
        )
        self.assertIsNotNone(domain, None)
        self.assertIsNotNone(basepath, None)
        self.assertEqual(len(basepath), 1)
        self.assertIsNotNone(route, None)
        self.assertEqual(domain.DomainNameConfigurations[0].get("EndpointType"), "REGIONAL")
        self.websocket_kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "Route53": {"HostedZoneId": "xyz"},
        }
        websocket_api = WebSocketApiGenerator(**self.websocket_kwargs)._construct_websocket_api()
        domain, basepath, route = WebSocketApiGenerator(**self.websocket_kwargs)._construct_api_domain(
            websocket_api, self.route53_record_set_groups
        )
        self.assertIsNotNone(domain, None)
        self.assertIsNotNone(basepath, None)
        self.assertEqual(len(basepath), 1)
        self.assertIsNotNone(route, None)
        self.assertEqual(domain.DomainNameConfigurations[0].get("EndpointType"), "REGIONAL")

    def test_basepaths(self):
        self.http_kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "BasePath": ["one", "two", "three"],
            "Route53": {"HostedZoneId": "xyz"},
        }
        http_api = HttpApiGenerator(**self.http_kwargs)._construct_http_api()
        domain, basepath, route = HttpApiGenerator(**self.http_kwargs)._construct_api_domain(
            http_api, self.route53_record_set_groups
        )
        self.assertIsNotNone(domain, None)
        self.assertIsNotNone(basepath, None)
        self.assertEqual(len(basepath), 3)
        self.assertIsNotNone(route, None)
        self.assertEqual(domain.DomainNameConfigurations[0].get("EndpointType"), "REGIONAL")
        self.websocket_kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "BasePath": ["one", "two", "three"],
            "Route53": {"HostedZoneId": "xyz"},
        }
        websocket_api = WebSocketApiGenerator(**self.websocket_kwargs)._construct_websocket_api()
        domain, basepath, route = WebSocketApiGenerator(**self.websocket_kwargs)._construct_api_domain(
            websocket_api, self.route53_record_set_groups
        )
        self.assertIsNotNone(domain, None)
        self.assertIsNotNone(basepath, None)
        self.assertEqual(len(basepath), 3)
        self.assertIsNotNone(route, None)
        self.assertEqual(domain.DomainNameConfigurations[0].get("EndpointType"), "REGIONAL")

    def test_invalid_basepaths(self):
        self.http_kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "BasePath": ["inv*alid"],
            "Route53": {"HostedZoneId": "xyz"},
        }
        http_api = HttpApiGenerator(**self.http_kwargs)._construct_http_api()
        with pytest.raises(InvalidResourceException) as e:
            HttpApiGenerator(**self.http_kwargs)._construct_api_domain(http_api, self.route53_record_set_groups)
        self.assertEqual(
            e.value.message, "Resource with id [HttpApiId] is invalid. " + "Invalid Basepath name provided."
        )
        self.websocket_kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "BasePath": ["inv*alid"],
            "Route53": {"HostedZoneId": "xyz"},
        }
        websocket_api = WebSocketApiGenerator(**self.websocket_kwargs)._construct_websocket_api()
        with pytest.raises(InvalidResourceException) as e:
            WebSocketApiGenerator(**self.websocket_kwargs)._construct_api_domain(
                websocket_api, self.route53_record_set_groups
            )
        self.assertEqual(
            e.value.message, "Resource with id [WebSocketApiId] is invalid. " + "Invalid Basepath name provided."
        )

    def test_basepaths_complex(self):
        self.http_kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "BasePath": ["one-1", "two_2", "three", "/", "/api", "api/v1", "api/v1/", "/api/v1/"],
            "Route53": {"HostedZoneId": "xyz", "HostedZoneName": "abc", "IpV6": True},
        }
        http_api = HttpApiGenerator(**self.http_kwargs)._construct_http_api()
        domain, basepath, route = HttpApiGenerator(**self.http_kwargs)._construct_api_domain(
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
        self.websocket_kwargs["domain"] = {
            "DomainName": "example.com",
            "CertificateArn": "some-url",
            "BasePath": ["one-1", "two_2", "three", "/", "/api", "api/v1", "api/v1/", "/api/v1/"],
            "Route53": {"HostedZoneId": "xyz", "HostedZoneName": "abc", "IpV6": True},
        }
        self.route53_record_set_groups = {}  # This needs to be reset because it is edited within the function
        websocket_api = WebSocketApiGenerator(**self.websocket_kwargs)._construct_websocket_api()
        domain, basepath, route = WebSocketApiGenerator(**self.websocket_kwargs)._construct_api_domain(
            websocket_api, self.route53_record_set_groups
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
