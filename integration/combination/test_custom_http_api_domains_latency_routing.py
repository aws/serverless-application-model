from unittest.case import skipIf

from integration.config.service_names import CUSTOM_DOMAIN
from integration.helpers.base_internal_test import BaseInternalTest
from integration.helpers.resource import current_region_not_included


@skipIf(
    current_region_not_included([CUSTOM_DOMAIN]),
    "CustomDomain is not supported in this testing region",
)
class TestCustomHttpApiDomainsLatencyRouting(BaseInternalTest):
    def test_custom_http_api_domains_regional(self):
        self.create_and_verify_stack("combination/api_with_custom_domains_regional_latency_routing")

        route53_list = self.get_stack_resources("AWS::Route53::RecordSetGroup")
        self.assertEqual(1, len(route53_list))

        client = self.client_provider.route53_client
        result = client.list_resource_record_sets(HostedZoneId="xyz")
        record_set_list = result["ResourceRecordSets"]
        record_set = next(r for r in record_set_list if r["Name"] == "test.domain.com" & r["Type"] == "A")

        self.assertIsNotNone(record_set["SetIdentifier"])
        self.assertIsNotNone(record_set["Region"])
