import logging
import time
from unittest.case import skipIf

from parameterized import parameterized

from integration.config.service_names import WEB_FUNCTION
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_not_included

LOG = logging.getLogger(__name__)

# AWS::Lambda::WebFunction is only available in a subset of regions; only run these deploy-and-invoke
# tests where it is supported (see integration/config/region_service_inclusion.yaml).
_WEB_FUNCTION_UNSUPPORTED = current_region_not_included([WEB_FUNCTION])


@skipIf(_WEB_FUNCTION_UNSUPPORTED, "WebFunction is not supported in this testing region")
class TestBasicWebFunction(BaseTest):
    """
    Basic deployment tests for AWS::Serverless::WebFunction
    """

    @parameterized.expand(
        [
            "single/basic_web_function",
            "single/web_function_with_env_and_timeout",
        ]
    )
    def test_basic_web_function(self, file_name):
        self.create_and_verify_stack(file_name)

    def test_web_function_with_multi_region(self):
        # A MultiRegion endpoint requires AutoDeploymentMode: Disabled, which in turn requires RevisionWeights.
        # RevisionWeights must reference an existing revision, so this is a two-step flow: first deploy a
        # single-region (LatestRevision) function, then update it to MultiRegion routing 100% of traffic to
        # the revision the first deploy created.
        self.create_and_verify_stack("single/web_function_with_multi_region")

        revision_id = self.get_stack_output("RevisionId")["OutputValue"]

        self.set_template_resource_property("MyWebFunction", "EndpointType", "MultiRegion")
        self.set_template_resource_property("MyWebFunction", "AutoDeploymentMode", "Disabled")
        self.set_template_resource_property(
            "MyWebFunction", "ReplicaRegions", {"IncludeRegions": ["us-east-1", "us-west-2"]}
        )
        self.set_template_resource_property("MyWebFunction", "RevisionWeights", {revision_id: 100})
        self.update_stack()

        self.assertEqual(self.get_resource_status_by_logical_id("MyWebFunctionEndpoint"), "UPDATE_COMPLETE")


@skipIf(_WEB_FUNCTION_UNSUPPORTED, "WebFunction is not supported in this testing region")
class TestWebFunctionEndpointResponse(BaseTest):
    """
    Functional verification tests - verify endpoints respond correctly
    """

    def test_endpoint_returns_200(self):
        """Verify the endpoint responds with 200 and correct body"""
        self.create_and_verify_stack("single/web_function_endpoint_response")

        endpoint = self.get_stack_output("Endpoint")["OutputValue"]
        url = f"https://{endpoint}"

        # Give endpoint time to become active
        time.sleep(5)
        response = self.verify_get_request_response(url, 200)
        self.assertEqual(response.text, "hello")

    def test_env_vars_in_response(self):
        """Verify environment variables are accessible in the function"""
        self.create_and_verify_stack("single/web_function_env_vars_response")

        endpoint = self.get_stack_output("Endpoint")["OutputValue"]
        url = f"https://{endpoint}/env"

        time.sleep(5)
        response = self.verify_get_request_response(url, 200)
        env_vars = response.json()
        self.assertEqual(env_vars.get("MY_VAR"), "my_value")
        self.assertEqual(env_vars.get("ANOTHER_VAR"), "another_value")

    def test_timeout_allows_fast_request(self):
        """Verify a request that completes within timeout succeeds"""
        self.create_and_verify_stack("single/web_function_timeout_verify")

        endpoint = self.get_stack_output("Endpoint")["OutputValue"]
        url = f"https://{endpoint}/timeout"

        time.sleep(5)
        response = self.verify_get_request_response(url, 200)
        self.assertEqual(response.text, "completed")


@skipIf(_WEB_FUNCTION_UNSUPPORTED, "WebFunction is not supported in this testing region")
class TestWebFunctionConfigurations(BaseTest):
    """
    Configuration variation tests
    """

    def test_custom_execution_role(self):
        """Verify WebFunction works with an explicit ExecutionRoleArn (no auto-generated role)"""
        self.create_and_verify_stack("single/web_function_custom_role")

    def test_custom_endpoint_name(self):
        """Verify WebFunction with a custom EndpointName"""
        self.create_and_verify_stack("single/web_function_custom_endpoint")

    def test_iam_auth(self):
        """Verify WebFunction with AuthType: IamAuth deploys successfully"""
        self.create_and_verify_stack("single/web_function_iam_auth")


@skipIf(_WEB_FUNCTION_UNSUPPORTED, "WebFunction is not supported in this testing region")
class TestWebFunctionUpdates(BaseTest):
    """
    Update scenario tests
    """

    def test_update_timeout(self):
        """Verify updating Timeout creates a new revision"""
        self.create_and_verify_stack("single/web_function_update_timeout")

        # Update timeout from 30 to 120
        self.set_template_resource_property("MyWebFunction", "Timeout", 120)
        self.update_stack()
        self.assertEqual(self.get_resource_status_by_logical_id("MyWebFunctionRevision"), "UPDATE_COMPLETE")

    def test_update_code(self):
        """Verify updating CodeUri deploys new code"""
        self.create_and_verify_stack("single/web_function_update_code")

        endpoint = self.get_stack_output("Endpoint")["OutputValue"]
        url = f"https://{endpoint}"

        time.sleep(5)
        response = self.verify_get_request_response(url, 200)
        self.assertEqual(response.text, "hello")

        # Update to new code
        self.set_template_resource_property("MyWebFunction", "CodeUri", self.get_code_key_s3_uri("webfunccodeuri2"))
        self.update_stack()

        time.sleep(5)
        response = self.verify_get_request_response(url, 200)
        self.assertEqual(response.text, "updated")
