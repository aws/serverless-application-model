from unittest import TestCase
from unittest.mock import Mock, patch

from parameterized import parameterized
from samtranslator.model import InvalidResourceException
from samtranslator.model.api.api_generator import ApiGenerator


class TestApiGenerator(TestCase):
    @parameterized.expand([("this should be a dict",), ("123",), ([{}],)])
    @patch("samtranslator.model.api.api_generator.AuthProperties")
    def test_construct_usage_plan_with_invalid_usage_plan_type(self, invalid_usage_plan, AuthProperties_mock):
        AuthProperties_mock.return_value = Mock(UsagePlan=invalid_usage_plan)
        api_generator = ApiGenerator(
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            auth={"some": "value"},
        )
        with self.assertRaises(InvalidResourceException) as cm:
            api_generator._construct_usage_plan()
            self.assertIn("Invalid type", str(cm.exception))

    @patch("samtranslator.model.api.api_generator.AuthProperties")
    def test_construct_usage_plan_with_invalid_usage_plan_fields(self, AuthProperties_mock):
        AuthProperties_mock.return_value = Mock(UsagePlan={"Unknown_field": "123"})
        api_generator = ApiGenerator(
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            auth={"some": "value"},
        )
        with self.assertRaises(InvalidResourceException) as cm:
            api_generator._construct_usage_plan()
            self.assertIn("Invalid property for", str(cm.exception))

    def test_latency_based_routing_route53(self):
        api_generator = ApiGenerator(
            logical_id="ApiId",
            cache_cluster_enabled=None,
            cache_cluster_size=None,
            variables=None,
            depends_on=None,
            definition_body=None,
            definition_uri="s3://bucket/key",
            name=None,
            stage_name=None,
            shared_api_usage_plan=None,
            template_conditions=None,
            domain={
                "DomainName": "example.com",
                "CertificateArn": "some-url",
                "Route53": {"HostedZoneId": "xyz", "SetIdentifier": "eu-west-2", "Region": "eu-west-2"},
            },
        )
        (
            rest_api,
            deployment,
            stage,
            permissions,
            domain,
            basepath_mapping,
            route53,
            usage_plan,
        ) = api_generator.to_cloudformation(None, {})

        self.assertIsNotNone(route53, None)
        self.assertEqual(len(route53.RecordSets), 1)
        self.assertEqual(route53.RecordSets[0].get("SetIdentifier"), "eu-west-2")
        self.assertEqual(route53.RecordSets[0].get("Region"), "eu-west-2")

    def test_latency_based_routing_route53_ipv6(self):
        api_generator = ApiGenerator(
            logical_id="ApiId",
            cache_cluster_enabled=None,
            cache_cluster_size=None,
            variables=None,
            depends_on=None,
            definition_body=None,
            definition_uri="s3://bucket/key",
            name=None,
            stage_name=None,
            shared_api_usage_plan=None,
            template_conditions=None,
            domain={
                "DomainName": "example.com",
                "CertificateArn": "some-url",
                "Route53": {"HostedZoneId": "xyz", "SetIdentifier": "eu-west-2", "Region": "eu-west-2", "IpV6": True},
            },
        )
        (
            rest_api,
            deployment,
            stage,
            permissions,
            domain,
            basepath_mapping,
            route53,
            usage_plan,
        ) = api_generator.to_cloudformation(None, {})

        self.assertIsNotNone(route53, None)
        self.assertEqual(len(route53.RecordSets), 2)
        self.assertEqual(route53.RecordSets[1].get("SetIdentifier"), "eu-west-2")
        self.assertEqual(route53.RecordSets[1].get("Region"), "eu-west-2")

    @patch("boto3.session.Session.region_name", "eu-west-2")
    def test_latency_based_routing_route53_ipv6_invalid(self):
        api_generator = ApiGenerator(
            logical_id="ApiId",
            cache_cluster_enabled=None,
            cache_cluster_size=None,
            variables=None,
            depends_on=None,
            definition_body=None,
            definition_uri="s3://bucket/key",
            name=None,
            stage_name=None,
            shared_api_usage_plan=None,
            template_conditions=None,
            domain={
                "DomainName": "example.com",
                "CertificateArn": "some-url",
                "Route53": {"HostedZoneId": "xyz", "Region": "eu-west-2", "IpV6": True},
            },
        )
        with self.assertRaises(InvalidResourceException) as cm:
            api_generator.to_cloudformation(None, {})
            self.assertIn("SetIdentifier is required", str(cm.exception))

    @patch("boto3.session.Session.region_name", "eu-west-2")
    def test_latency_based_routing_route53_ipv6_invalid2(self):
        api_generator = ApiGenerator(
            logical_id="ApiId",
            cache_cluster_enabled=None,
            cache_cluster_size=None,
            variables=None,
            depends_on=None,
            definition_body=None,
            definition_uri="s3://bucket/key",
            name=None,
            stage_name=None,
            shared_api_usage_plan=None,
            template_conditions=None,
            domain={
                "DomainName": "example.com",
                "CertificateArn": "some-url",
                "Route53": {
                    "HostedZoneId": "xyz",
                    "SetIdentifier": "eu-west-2",
                    "IpV6": True,
                },
            },
        )
        (
            rest_api,
            deployment,
            stage,
            permissions,
            domain,
            basepath_mapping,
            route53,
            usage_plan,
        ) = api_generator.to_cloudformation(None, {})

        self.assertIsNotNone(route53, None)
        self.assertEqual(len(route53.RecordSets), 2)
        self.assertEqual(route53.RecordSets[0].get("SetIdentifier"), None)
        self.assertEqual(route53.RecordSets[0].get("Region"), None)
        self.assertEqual(route53.RecordSets[1].get("SetIdentifier"), None)
        self.assertEqual(route53.RecordSets[1].get("Region"), None)
