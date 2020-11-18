from parameterized import parameterized
from tests_integ.helpers.base_test import BaseTest


class TestBasicApi(BaseTest):
    def test_basic_api(self):
        self.create_and_verify_stack("basic_api")

        first_dep_ids = self.get_deployment_ids()

        self.set_template_resource("MyApi", "DefinitionUri", self.get_s3_uri("swagger2.json"))
        self.transform_template()
        self.deploy_stack()

        second_dep_ids = self.get_deployment_ids()

        self.assertEqual(len(set(first_dep_ids).intersection(second_dep_ids)), 0)

    @parameterized.expand(
        [
            "basic_api_inline_openapi",
            "basic_api_inline_swagger",
            "basic_api_with_tags"
        ]
    )
    def test_basic_api_others(self, file_name):
        self.create_and_verify_stack(file_name)
