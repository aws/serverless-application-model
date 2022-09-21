from unittest.case import skipIf

import pytest

from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


class TestBasicApplication(BaseTest):
    """
    Basic AWS::Serverless::Application tests
    """

    @pytest.fixture(autouse=True)
    def companion_stack_outputs(self, get_serverless_application_repository_app):
        self.sar_app_id = get_serverless_application_repository_app

    @skipIf(
        current_region_does_not_support(["ServerlessRepo"]), "ServerlessRepo is not supported in this testing region"
    )
    def test_basic_application_s3_location(self):
        """
        Creates an application with its properties defined as a template
        file in a S3 bucket
        """
        self.create_and_verify_stack("single/basic_application_s3_location")

        nested_stack_resource = self.get_stack_nested_stack_resources()
        tables = self.get_stack_resources("AWS::DynamoDB::Table", nested_stack_resource)

        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0]["LogicalResourceId"], "MyTable")

    @skipIf(
        current_region_does_not_support(["ServerlessRepo"]), "ServerlessRepo is not supported in this testing region"
    )
    def test_basic_application_sar_location(self):
        """
        Creates an application with a lamda function
        """
        parameters = [self.generate_parameter("SarApplicationId", self.sar_app_id)]
        self.create_and_verify_stack("single/basic_application_sar_location", parameters)

        nested_stack_resource = self.get_stack_nested_stack_resources()
        functions = self.get_stack_resources("AWS::Lambda::Function", nested_stack_resource)

        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0]["LogicalResourceId"], "HelloWorldPython3")

    @skipIf(
        current_region_does_not_support(["ServerlessRepo"]), "ServerlessRepo is not supported in this testing region"
    )
    def test_basic_application_sar_location_with_intrinsics(self):
        """
        Creates an application with a lambda function with intrinsics
        """
        expected_function_name = "HelloWorldPython3"
        parameters = [self.generate_parameter("SarApplicationId", self.sar_app_id)]
        self.create_and_verify_stack("single/basic_application_sar_location_with_intrinsics", parameters)

        nested_stack_resource = self.get_stack_nested_stack_resources()
        functions = self.get_stack_resources("AWS::Lambda::Function", nested_stack_resource)

        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0]["LogicalResourceId"], expected_function_name)
