from integration.helpers.base_test import BaseTest


class TestBasicApi(BaseTest):
    """
    Basic AWS::Serverless::Api tests
    """

    def test_basic_api(self):
        """
        Creates an API and updates its DefinitionUri
        """
        self.create_and_verify_stack("basic_api")

        first_dep_ids = self.get_stack_deployment_ids()
        self.assertEqual(len(first_dep_ids), 1)

        self.set_template_resource_property("MyApi", "DefinitionUri", self.get_s3_uri("swagger2.json"))
        self.transform_template()
        self.deploy_stack()

        second_dep_ids = self.get_stack_deployment_ids()
        self.assertEqual(len(second_dep_ids), 1)

        self.assertEqual(len(set(first_dep_ids).intersection(second_dep_ids)), 0)

    def test_basic_api_inline_openapi(self):
        """
        Creates an API with and inline OpenAPI and updates its DefinitionBody basePath
        """
        self.create_and_verify_stack("basic_api_inline_openapi")

        first_dep_ids = self.get_stack_deployment_ids()
        self.assertEqual(len(first_dep_ids), 1)

        body = self.get_template_resource_property("MyApi", "DefinitionBody")
        body["basePath"] = "/newDemo"
        self.set_template_resource_property("MyApi", "DefinitionBody", body)
        self.transform_template()
        self.deploy_stack()

        second_dep_ids = self.get_stack_deployment_ids()
        self.assertEqual(len(second_dep_ids), 1)

        self.assertEqual(len(set(first_dep_ids).intersection(second_dep_ids)), 0)

    def test_basic_api_inline_swagger(self):
        """
        Creates an API with an inline Swagger and updates its DefinitionBody basePath
        """
        self.create_and_verify_stack("basic_api_inline_swagger")

        first_dep_ids = self.get_stack_deployment_ids()
        self.assertEqual(len(first_dep_ids), 1)

        body = self.get_template_resource_property("MyApi", "DefinitionBody")
        body["basePath"] = "/newDemo"
        self.set_template_resource_property("MyApi", "DefinitionBody", body)
        self.transform_template()
        self.deploy_stack()

        second_dep_ids = self.get_stack_deployment_ids()
        self.assertEqual(len(second_dep_ids), 1)

        self.assertEqual(len(set(first_dep_ids).intersection(second_dep_ids)), 0)

    def test_basic_api_with_tags(self):
        """
        Creates an API with tags
        """
        self.create_and_verify_stack("basic_api_with_tags")

        stages = self.get_api_stack_stages()
        self.assertEqual(len(stages), 2)

        stage = next((s for s in stages if s["stageName"] == "my-new-stage-name"))
        self.assertIsNotNone(stage)
        self.assertEqual(stage["tags"]["TagKey1"], "TagValue1")
        self.assertEqual(stage["tags"]["TagKey2"], "")
