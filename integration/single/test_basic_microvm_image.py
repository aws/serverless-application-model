import logging
from unittest.case import skipIf

from integration.helpers.base_test import BaseTest

LOG = logging.getLogger(__name__)


@skipIf(True, "MicroVMImage is not yet GA - enable when RIP feature flag is available")
class TestBasicMicroVMImage(BaseTest):
    """
    Basic AWS::Serverless::MicroVMImage tests
    """

    def test_basic_microvm_image(self):
        """
        Creates a MicroVMImage with auto-generated BuildRole
        """
        self.create_and_verify_stack("single/basic_microvm_image")

        # Verify the auto-generated BuildRole exists and has correct trust policy
        role_name = self.get_physical_id_by_logical_id("MyMicroVMImageBuildRole")
        iam_client = self.client_provider.iam_client
        role = iam_client.get_role(RoleName=role_name)

        # Verify trust policy principal
        trust_policy = role["Role"]["AssumeRolePolicyDocument"]
        principals = []
        for stmt in trust_policy["Statement"]:
            if stmt["Effect"] != "Allow":
                continue
            service = stmt["Principal"].get("Service", [])
            if isinstance(service, str):
                principals.append(service)
            else:
                principals.extend(service)
        self.assertIn(
            "lambda.amazonaws.com",
            principals,
            "BuildRole should trust lambda-microvms service",
        )

        # Verify inline policy exists with scoped S3 permissions
        role_policy = iam_client.get_role_policy(RoleName=role_name, PolicyName="MicrovmImageBuildPolicy")
        statements = role_policy["PolicyDocument"]["Statement"]
        s3_statement = next((s for s in statements if "s3:GetObject" in s["Action"]), None)
        logs_statement = next((s for s in statements if "logs:CreateLogGroup" in s["Action"]), None)

        self.assertIsNotNone(s3_statement, "Should have s3:GetObject statement")
        self.assertIsNotNone(logs_statement, "Should have logs statement")
        # S3 should be scoped (not wildcard)
        self.assertNotEqual(s3_statement["Resource"], "*", "s3:GetObject should not use wildcard resource")
        # Logs uses wildcard (expected)
        self.assertEqual(logs_statement["Resource"], "*", "logs should use wildcard resource")
        # kms:Decrypt should NOT be present
        all_actions = [action for stmt in statements for action in stmt["Action"]]
        self.assertNotIn("kms:Decrypt", all_actions, "kms:Decrypt should not be in auto-generated role")

    def test_microvm_image_with_custom_build_role(self):
        """
        Creates a MicroVMImage with customer-provided BuildRole (no auto-generation)
        """
        self.create_and_verify_stack("single/basic_microvm_image_with_build_role")

        # Verify only the customer-provided role exists (no auto-generated role)
        stack_resources = self.get_stack_resources("AWS::IAM::Role")
        role_logical_ids = [r["LogicalResourceId"] for r in stack_resources]

        self.assertIn("CustomBuildRole", role_logical_ids)
        self.assertNotIn(
            "MyMicroVMImageWithBuildRoleBuildRole",
            role_logical_ids,
            "Should NOT auto-generate BuildRole when BuildRoleArn is provided",
        )

    def test_basic_microvm_image_minimal(self):
        """
        Creates a MicroVMImage with only required fields — all optional fields omitted.
        Verifies SAM auto-injects defaults and generates BuildRole.
        """
        self.create_and_verify_stack("single/basic_microvm_image_minimal")
