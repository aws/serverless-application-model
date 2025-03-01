import json
from unittest.case import skipIf

from botocore.exceptions import ClientError

from integration.config.service_names import LAYERS, REST_API
from integration.helpers.base_test import LOG, BaseTest
from integration.helpers.common_api import get_function_versions
from integration.helpers.resource import current_region_does_not_support


class TestFunctionWithAlias(BaseTest):
    def test_updating_version_by_changing_property_value(self):
        self.create_and_verify_stack("combination/function_with_alias")
        alias_name = "Live"
        function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        version_ids = self.get_function_version_by_name(function_name)
        self.assertEqual(["1"], version_ids)

        alias = self.get_alias(function_name, alias_name)
        self.assertEqual("1", alias["FunctionVersion"])

        # Changing CodeUri should create a new version, and leave the existing version in tact
        self.set_template_resource_property("MyLambdaFunction", "CodeUri", self.file_to_s3_uri_map["code2.zip"]["uri"])
        self.update_stack()

        version_ids = self.get_function_version_by_name(function_name)
        self.assertEqual(["1", "2"], version_ids)

        alias = self.get_alias(function_name, alias_name)
        self.assertEqual("2", alias["FunctionVersion"])

        # Make sure the stack has only One Version & One Alias resource
        alias = self.get_stack_resources("AWS::Lambda::Alias")
        versions = self.get_stack_resources("AWS::Lambda::Version")
        self.assertEqual(len(alias), 1)
        self.assertEqual(len(versions), 1)

    def test_updating_version_by_changing_property_value_additional_properties(self):
        self.create_and_verify_stack("combination/function_with_alias_and_all_properties_property")
        alias_name = "Live"
        function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        version_ids = self.get_function_version_by_name(function_name)
        self.assertEqual(["1"], version_ids)

        alias = self.get_alias(function_name, alias_name)
        self.assertEqual("1", alias["FunctionVersion"])

        # Changing Handler should create a new version, and leave the existing version intact
        self.set_template_resource_property("MyLambdaFunction", "Handler", "not_index.handler")
        self.update_stack()

        version_ids = self.get_function_version_by_name(function_name)
        self.assertEqual(["1", "2"], version_ids)

        alias = self.get_alias(function_name, alias_name)
        self.assertEqual("2", alias["FunctionVersion"])

        # Changing Description should create a new version, and leave the existing version intact
        self.set_template_resource_property("MyLambdaFunction", "Description", "bar")
        self.update_stack()

        version_ids = self.get_function_version_by_name(function_name)
        self.assertEqual(["1", "2", "3"], version_ids)

        alias = self.get_alias(function_name, alias_name)
        self.assertEqual("3", alias["FunctionVersion"])

        # Make sure the stack has only One Version & One Alias resource
        alias = self.get_stack_resources("AWS::Lambda::Alias")
        versions = self.get_stack_resources("AWS::Lambda::Version")
        self.assertEqual(len(alias), 1)
        self.assertEqual(len(versions), 1)

    def test_alias_deletion_must_retain_version(self):
        self.create_and_verify_stack("combination/function_with_alias")
        function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        version_ids = self.get_function_version_by_name(function_name)
        self.assertEqual(["1"], version_ids)

        # Check that the DeletionPolicy on Lambda Version holds good
        # Remove alias, update stack, and verify the version still exists by calling Lambda APIs
        self.remove_template_resource_property("MyLambdaFunction", "AutoPublishAlias")
        self.update_stack()

        # Make sure both Lambda version & alias resource does not exist in stack
        alias = self.get_stack_resources("AWS::Lambda::Alias")
        versions = self.get_stack_resources("AWS::Lambda::Version")
        self.assertEqual(len(alias), 0)
        self.assertEqual(len(versions), 0)

        # Make sure the version still exists in Lambda
        version_ids = self.get_function_version_by_name(function_name)
        self.assertEqual(["1"], version_ids)

    def test_function_with_alias_with_intrinsics(self):
        parameters = self.get_default_test_template_parameters()
        self.create_and_verify_stack("combination/function_with_alias_intrinsics", parameters)
        alias_name = "Live"

        function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        version_ids = get_function_versions(function_name, self.client_provider.lambda_client)
        self.assertEqual(["1"], version_ids)

        alias = self.get_alias(function_name, alias_name)
        self.assertEqual("1", alias["FunctionVersion"])

        # Let's change Key by updating the template parameter, but keep template same
        # This should create a new version and leave existing version intact
        parameters[1]["ParameterValue"] = "code2.zip"

        self.update_stack(parameters)
        version_ids = get_function_versions(function_name, self.client_provider.lambda_client)
        self.assertEqual(["1", "2"], version_ids)

        alias = self.get_alias(function_name, alias_name)
        self.assertEqual("2", alias["FunctionVersion"])

    def test_alias_in_globals_with_overrides(self):
        # It is good enough if we can create a stack. Globals are pre-processed on the SAM template and don't
        # add any extra runtime behavior that needs to be verified
        self.create_and_verify_stack("combination/function_with_alias_globals")

    @skipIf(current_region_does_not_support([REST_API]), "Rest API is not supported in this testing region")
    def test_alias_with_event_sources_get_correct_permissions(self):
        # There are two parts to testing Event Source integrations:
        #    1. Check if all event sources get wired to the alias
        #    2. Check if Lambda::Permissions for the event sources are applied on the Alias
        #
        # This test checks #2 only because the former is easy to validate directly by looking at the CFN template in unit tests
        # Also #1 requires calls to many different services which is hard.
        self.create_and_verify_stack("combination/function_with_alias_and_event_sources")
        alias_name = "Live"

        # Verify the permissions on the Alias are setup correctly. There should be as many resource policies as the Lambda::Permission resources
        function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        alias_arn = self.get_alias(function_name, alias_name)["AliasArn"]
        permission_resources = self.get_stack_resources("AWS::Lambda::Permission")

        # Get the policies on both function & alias
        # Alias should have as many policies as the Lambda::Permissions resource
        alias_policy_str = self.get_function_policy(alias_arn)
        alias_policy = json.loads(alias_policy_str)
        self.assertIsNotNone(alias_policy.get("Statement"))
        self.assertEqual(len(alias_policy["Statement"]), len(permission_resources))
        # Function should have *no* policies
        function_policy_str = self.get_function_policy(function_name)
        self.assertIsNone(function_policy_str)

        # Remove the alias, deploy the stack, and verify that *all* permission entities transfer to the function
        self.remove_template_resource_property("MyAwesomeFunction", "AutoPublishAlias")
        self.update_stack()

        # Get the policies on both function & alias
        # Alias should have *no* policies
        alias_policy_str = self.get_function_policy(alias_arn)
        self.assertIsNone(alias_policy_str)
        # Function should have as many policies as the Lambda::Permissions resource
        function_policy_str = self.get_function_policy(function_name)
        function_policy = json.loads(function_policy_str)
        self.assertEqual(len(function_policy["Statement"]), len(permission_resources))

    @skipIf(current_region_does_not_support([LAYERS]), "Layers is not supported in this testing region")
    def test_function_with_alias_and_layer_version(self):
        self.create_and_verify_stack("combination/function_with_alias_all_properties_and_layer_version")
        alias_name = "Live"
        function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        version_ids = self.get_function_version_by_name(function_name)
        self.assertEqual(["1"], version_ids)

        alias = self.get_alias(function_name, alias_name)
        self.assertEqual("1", alias["FunctionVersion"])

        # Changing Description in the LayerVersion should create a new version, and leave the existing version intact
        self.set_template_resource_property("MyLayer", "Description", "test123")
        self.update_stack()

        version_ids = self.get_function_version_by_name(function_name)
        self.assertEqual(["1", "2"], version_ids)

        alias = self.get_alias(function_name, alias_name)
        self.assertEqual("2", alias["FunctionVersion"])

        # Changing ContentUri in LayerVersion should create a new version, and leave the existing version intact
        self.set_template_resource_property("MyLayer", "ContentUri", self.file_to_s3_uri_map["layer2.zip"]["uri"])
        self.update_stack()

        version_ids = self.get_function_version_by_name(function_name)
        self.assertEqual(["1", "2", "3"], version_ids)

        alias = self.get_alias(function_name, alias_name)
        self.assertEqual("3", alias["FunctionVersion"])

        # Make sure the stack has only One Version & One Alias resource
        alias = self.get_stack_resources("AWS::Lambda::Alias")
        versions = self.get_stack_resources("AWS::Lambda::Version")
        self.assertEqual(len(alias), 1)
        self.assertEqual(len(versions), 1)

    def get_function_version_by_name(self, function_name):
        lambda_client = self.client_provider.lambda_client
        versions = lambda_client.list_versions_by_function(FunctionName=function_name)["Versions"]

        # Exclude $LATEST from the list and simply return all the version numbers.
        filtered_versions = [version["Version"] for version in versions if version["Version"] != "$LATEST"]
        return filtered_versions

    def get_alias(self, function_name, alias_name):
        lambda_client = self.client_provider.lambda_client
        return lambda_client.get_alias(FunctionName=function_name, Name=alias_name)

    def get_function_policy(self, function_arn):
        lambda_client = self.client_provider.lambda_client
        try:
            policy_result = lambda_client.get_policy(FunctionName=function_arn)
            return policy_result["Policy"]
        except ClientError as error:
            if error.response["Error"]["Code"] == "ResourceNotFoundException":
                LOG.debug("The resource you requested does not exist.")
                return None
            else:
                raise error

    def get_default_test_template_parameters(self):
        parameters = [
            {
                "ParameterKey": "Bucket",
                "ParameterValue": self.s3_bucket_name,
                "UsePreviousValue": False,
                "ResolvedValue": "string",
            },
            {
                "ParameterKey": "CodeKey",
                "ParameterValue": "code.zip",
                "UsePreviousValue": False,
                "ResolvedValue": "string",
            },
            {
                "ParameterKey": "SwaggerKey",
                "ParameterValue": "swagger1.json",
                "UsePreviousValue": False,
                "ResolvedValue": "string",
            },
        ]
        return parameters
