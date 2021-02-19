from unittest.case import skipIf

from integration.helpers.base_test import BaseTest
from integration.helpers.resource import should_exclude_test_in_region


class TestBasicHttpApi(BaseTest):
    """
    Basic AWS::Serverless::HttpApi tests
    """

    @skipIf(should_exclude_test_in_region("HttpApi"), "HttpApi is not supported in this testing region")
    def test_basic_http_api(self):
        """
        Creates a HTTP API
        """
        self.create_and_verify_stack("basic_http_api")

        stages = self.get_api_v2_stack_stages()

        self.assertEqual(len(stages), 1)
        self.assertEqual(stages[0]["StageName"], "$default")
