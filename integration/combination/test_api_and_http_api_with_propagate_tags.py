from unittest.case import skipIf

from integration.config.service_names import HTTP_API, REST_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(
    current_region_does_not_support([HTTP_API, REST_API]),
    "REST_API or HTTP_API is not supported in this testing region",
)
class TestApiAndHttpiWithPropagateTags(BaseTest):
    def test_api_and_httpapi_with_propagate_tags(self):
        self.create_and_verify_stack("combination/api_with_propagate_tags")

        outputs = self.get_stack_outputs()

        api_client = self.client_provider.api_client
        api_v2_client = self.client_provider.api_v2_client

        tags = api_client.get_tags(resourceArn=outputs["ApiArn"])
        self.assertEqual(tags["tags"]["Key1"], "Value1")
        self.assertEqual(tags["tags"]["Key2"], "Value2")

        tags = api_v2_client.get_tags(ResourceArn=outputs["HttpApiArn"])
        self.assertEqual(tags["Tags"]["Tag1"], "value1")
        self.assertEqual(tags["Tags"]["Tag2"], "value2")
