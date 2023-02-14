from unittest.case import skipIf

from integration.config.service_names import S3_EVENTS
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([S3_EVENTS]), "S3 Events feature is not supported in this testing region")
class TestFunctionWithS3Bucket(BaseTest):
    def test_function_with_s3_bucket_trigger(self):
        self.create_and_verify_stack("combination/function_with_s3")

        # Get the notification configuration and make sure Lambda Function connection is added
        s3_client = self.client_provider.s3_client
        s3_bucket_name = self.get_physical_id_by_type("AWS::S3::Bucket")
        configurations = s3_client.get_bucket_notification_configuration(Bucket=s3_bucket_name)[
            "LambdaFunctionConfigurations"
        ]

        # There should be only One notification configuration for the event
        self.assertEqual(len(configurations), 1)
        config = configurations[0]
        self.assertEqual(config["Events"], ["s3:ObjectCreated:*"])

    def test_function_with_s3_bucket_intrinsics(self):
        self.create_and_verify_stack("combination/function_with_s3_intrinsics")

        s3_client = self.client_provider.s3_client
        s3_bucket_name = self.get_physical_id_by_type("AWS::S3::Bucket")
        configurations = s3_client.get_bucket_notification_configuration(Bucket=s3_bucket_name)[
            "LambdaFunctionConfigurations"
        ]

        self.assertEqual(len(configurations), 1)
        config = configurations[0]
        self.assertEqual(config["Events"], ["s3:ObjectCreated:*"])
        self.assertEqual(config["Filter"]["Key"]["FilterRules"], [{"Name": "Suffix", "Value": "object_suffix"}])
