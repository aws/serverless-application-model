from tests_integ.helpers.base_test import BaseTest


class TestBasicHttpApi(BaseTest):
    """
    Basic AWS::Serverless::HttpApi tests
    """
    def test_basic_http_api(self):
        """
        Creates a HTTP API
        """
        self.create_and_verify_stack("basic_http_api")

        stages = self.get_stack_stages_v2()

        self.assertEqual(len(stages), 1)
        self.assertEqual(stages[0]["StageName"], "$default")
