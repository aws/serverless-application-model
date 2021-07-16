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

        canary_name = self.get_physical_id_by_type("AWS::Synthetics::Canary")
        get_canary_result = self.client_provider.synthetics_client.get_canary(Name=canary_name)["Canary"]
        name = get_canary_result["Name"]

        bucket_name = self.get_physical_id_by_type("AWS::S3::Bucket")
        self.client_provider.s3_client.delete_bucket(Bucket=bucket_name)

        self.assertEqual(name, canary_name)

    def test_canary_with_tags(self):
        """
        Creates a basic synthetics canary with tags
        """
        self.create_and_verify_stack("basic_canary_with_tags")

        canary_name = self.get_physical_id_by_type("AWS::Synthetics::Canary")
        get_function_result = self.client_provider.synthetics_client.get_canary(Name=canary_name)["Canary"]
        tags = get_function_result["Tags"]

        self.assertIsNotNone(tags, "Expecting tags on function.")
        self.assertTrue("lambda:createdBy" in tags, "Expected 'lambda:CreatedBy' tag key, but not found.")
        self.assertEqual("SAM", tags["lambda:createdBy"], "Expected 'SAM' tag value, but not found.")
        self.assertTrue("TagKey1" in tags)
        self.assertEqual(tags["TagKey1"], "TagValue1")
        self.assertTrue("TagKey2" in tags)
        self.assertEqual(tags["TagKey2"], "")

        bucket_name = self.get_physical_id_by_type("AWS::S3::Bucket")
        self.client_provider.s3_client.delete_bucket(Bucket=bucket_name)

    def test_canary_with_artifact_location_defined(self):
        """
        Creates a basic synthetics canary with the ArtifactS3Location property defined
        """
        self.create_and_verify_stack("basic_canary_with_artifact_location")

        self.assertEqual(self.get_resource_status_by_logical_id("ArtifactBucket"), None)

        canary_name = self.get_physical_id_by_type("AWS::Synthetics::Canary")
        get_function_result = self.client_provider.synthetics_client.get_canary(Name=canary_name)["Canary"]
        artifact_location = get_function_result["ArtifactS3Location"]

        self.assertTrue("sam-integration-test" in artifact_location)
