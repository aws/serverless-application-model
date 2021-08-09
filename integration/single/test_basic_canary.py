from integration.helpers.base_test import BaseTest


class TestBasicCanary(BaseTest):
    """
    Basic AWS::Synthetics::Canary tests
    """

    def test_basic_canary(self):
        """
        Creates a basic synthetics canary
        """
        self.create_and_verify_stack("basic_canary")

        self.assertEqual(self.get_resource_status_by_logical_id("SyntheticsCanary"), "CREATE_COMPLETE")

        # since the auto generated bucket has a "Retain" deletion policy if the integration test fails before this
        # point the bucket won't be deleted with the integration test stack
        bucket_name = self.get_physical_id_by_type("AWS::S3::Bucket")
        self._clean_bucket(bucket_name)

        canary_name = self.get_physical_id_by_type("AWS::Synthetics::Canary")
        get_canary_result = self.client_provider.synthetics_client.get_canary(Name=canary_name)["Canary"]
        name = get_canary_result["Name"]
        self.assertEqual(name, canary_name)

        role_name = self.get_physical_id_by_type("AWS::IAM::Role")
        get_role_results = self.client_provider.iam_client.list_role_policies(RoleName=role_name)

        # Check that all the required policies to execute the canary are added to the role
        policy_names = get_role_results["PolicyNames"]
        canary_logical_id = self.get_logical_id_by_type("AWS::Synthetics::Canary")
        self.assertIn(canary_logical_id + "CanaryLogsPolicy", policy_names)
        self.assertIn(canary_logical_id + "CanaryMetricPolicy", policy_names)
        self.assertIn(canary_logical_id + "CanaryS3Policy", policy_names)

    def test_canary_with_tags(self):
        """
        Creates a basic synthetics canary with tags
        """
        self.create_and_verify_stack("basic_canary_with_tags")

        # delete bucket after stack is verified
        bucket_name = self.get_physical_id_by_type("AWS::S3::Bucket")
        self._clean_bucket(bucket_name)

        canary_name = self.get_physical_id_by_type("AWS::Synthetics::Canary")
        get_canary_results = self.client_provider.synthetics_client.get_canary(Name=canary_name)["Canary"]
        tags = get_canary_results["Tags"]

        self.assertIsNotNone(tags, "Expecting tags on Canary.")
        self.assertTrue("lambda:createdBy" in tags, "Expected 'lambda:CreatedBy' tag key, but not found.")
        self.assertEqual("SAM", tags["lambda:createdBy"], "Expected 'SAM' tag value, but not found.")
        self.assertTrue("TagKey1" in tags)
        self.assertEqual(tags["TagKey1"], "TagValue1")
        self.assertTrue("TagKey2" in tags)
        self.assertEqual(tags["TagKey2"], "")

    def test_canary_with_artifact_location_and_role(self):
        """
        Creates a basic synthetics canary with the ArtifactS3Location property defined
        """
        s3_name_prefix = "sam-integration-test-bucket"
        role_name_prefix = "sam-integration-test-role"

        self.create_and_verify_stack("basic_canary_with_role_and_artifact_location")

        # delete bucket after stack is verified
        bucket_name = self.get_physical_id_by_type("AWS::S3::Bucket")
        self._clean_bucket(bucket_name)

        canary_name = self.get_physical_id_by_type("AWS::Synthetics::Canary")
        get_canary_result = self.client_provider.synthetics_client.get_canary(Name=canary_name)["Canary"]
        artifact_location = get_canary_result["ArtifactS3Location"]
        role = get_canary_result["ExecutionRoleArn"]

        self.assertTrue(s3_name_prefix in artifact_location)
        self.assertTrue(role_name_prefix in role)

    def test_canary_with_vpc_and_tracing(self):
        """
        Creates a basic synthetics canary with the VPC and Tracing
        """
        self.create_and_verify_stack("basic_canary_with_vpc_and_tracing")

        # delete bucket after stack is verified
        bucket_name = self.get_physical_id_by_type("AWS::S3::Bucket")
        self._clean_bucket(bucket_name)

        # make sure tracing is activated on the canary
        canary_name = self.get_physical_id_by_type("AWS::Synthetics::Canary")
        get_canary_result = self.client_provider.synthetics_client.get_canary(Name=canary_name)["Canary"]
        self.assertEqual(get_canary_result["RunConfig"]["ActiveTracing"], True)

        # make sure the right service policies are attached to the role
        role_name = self.get_physical_id_by_type("AWS::IAM::Role")
        attached_policies = self.client_provider.iam_client.list_attached_role_policies(RoleName=role_name)

        # since we activated VPC and Tracing and added no other policies, there should only be 2 service policies
        # attached to this role
        self.assertEqual(len(attached_policies["AttachedPolicies"]), 2)
        self.assertTrue(
            # Service policy for Tracing can be AWSXrayWriteOnlyAccess or AWSXRayDaemonWriteAccess based on the region
            attached_policies["AttachedPolicies"][0]["PolicyName"],
            {"AWSXrayWriteOnlyAccess", "AWSXRayDaemonWriteAccess"},
        )
        self.assertTrue(attached_policies["AttachedPolicies"][1]["PolicyName"], "AWSLambdaVPCAccessExecutionRole")

    def test_canary_with_policies(self):
        policy_expected = {"Statement": [{"Effect": "Allow", "Action": ["cloudwatch:PutMetricData"], "Resource": "*"}]}
        self.create_and_verify_stack("basic_canary_with_policies")

        # delete bucket after stack is verified
        bucket_name = self.get_physical_id_by_type("AWS::S3::Bucket")
        self._clean_bucket(bucket_name)

        role_name = self.get_physical_id_by_type("AWS::IAM::Role")
        role_policies = self.client_provider.iam_client.list_role_policies(RoleName=role_name)

        # Since ArtifactS3Location is defined Role must only have the policy from Policies property
        self.assertEqual(len(role_policies["PolicyNames"]), 1)

        policy_found = self.client_provider.iam_client.get_role_policy(
            RoleName=role_name, PolicyName=role_policies["PolicyNames"][0]
        )["PolicyDocument"]
        self.assertEqual(policy_found, policy_expected)

    def test_canary_with_alarms(self):
        self.create_and_verify_stack("basic_canary_with_alarms")

        # delete bucket after stack is verified
        bucket_name = self.get_physical_id_by_type("AWS::S3::Bucket")
        self._clean_bucket(bucket_name)
