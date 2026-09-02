from unittest import TestCase

from samtranslator.model.log import LogGroup, SubscriptionFilter


class TestLogGroup(TestCase):
    def test_resource_type(self):
        log_group = LogGroup("MyFunctionLogGroup")
        self.assertEqual(log_group.resource_type, "AWS::Logs::LogGroup")

    def test_to_dict_with_properties(self):
        log_group = LogGroup(
            "MyFunctionLogGroup",
            attributes={"DeletionPolicy": "Retain", "UpdateReplacePolicy": "Retain"},
        )
        log_group.LogGroupName = {"Fn::Sub": "/aws/lambda/${MyFunction}"}
        log_group.RetentionInDays = 7

        self.assertEqual(
            log_group.to_dict(),
            {
                "MyFunctionLogGroup": {
                    "Type": "AWS::Logs::LogGroup",
                    "DeletionPolicy": "Retain",
                    "UpdateReplacePolicy": "Retain",
                    "Properties": {
                        "LogGroupName": {"Fn::Sub": "/aws/lambda/${MyFunction}"},
                        "RetentionInDays": 7,
                    },
                }
            },
        )

    def test_runtime_attrs(self):
        log_group = LogGroup("MyFunctionLogGroup")
        self.assertEqual(log_group.get_runtime_attr("name"), {"Ref": "MyFunctionLogGroup"})
        self.assertEqual(
            log_group.get_runtime_attr("arn"),
            {"Fn::GetAtt": ["MyFunctionLogGroup", "Arn"]},
        )

    def test_supported_properties(self):
        # LogGroup and SubscriptionFilter live in the same module; make sure the
        # LogGroup exposes the CloudFormation properties we rely on.
        self.assertIn("LogGroupName", LogGroup.property_types)
        self.assertIn("RetentionInDays", LogGroup.property_types)
        self.assertIn("Tags", LogGroup.property_types)
        self.assertIn("KmsKeyId", LogGroup.property_types)
        self.assertIn("DataProtectionPolicy", LogGroup.property_types)
        self.assertIn("LogGroupClass", LogGroup.property_types)
        # Sanity check the neighbouring resource is untouched.
        self.assertEqual(SubscriptionFilter.resource_type, "AWS::Logs::SubscriptionFilter")
