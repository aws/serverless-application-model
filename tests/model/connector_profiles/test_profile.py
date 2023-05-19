from unittest import TestCase

from parameterized import parameterized
from samtranslator.model.connector_profiles.profile import (
    get_profile,
    profile_replace,
    replace_cfn_resource_properties,
    verify_profile_variables_replaced,
)


class TestProfile(TestCase):
    def test_profile_replace_str_input(self):
        input = "%{SourceArn}TestingExample"
        result = profile_replace(input, {"SourceArn": "arn:aws:iam:policy/service-role/AWSLambdaBasicExecutionRole"})

        self.assertEqual(
            result,
            {
                "Fn::Sub": [
                    "${SourceArn}TestingExample",
                    {"SourceArn": "arn:aws:iam:policy/service-role/AWSLambdaBasicExecutionRole"},
                ]
            },
        )

    def test_profile_replace_multiple_str_input(self):
        input = "%{SourceArn}TestingExample%{DestinationArn}"
        result = profile_replace(
            input,
            {
                "SourceArn": "arn:aws:iam:policy/service-role/AWSLambdaBasicExecutionRole",
                "DestinationArn": "destinationArn",
            },
        )

        self.assertEqual(
            result,
            {
                "Fn::Sub": [
                    "${SourceArn}TestingExample${DestinationArn}",
                    {
                        "DestinationArn": "destinationArn",
                        "SourceArn": "arn:aws:iam:policy/service-role/AWSLambdaBasicExecutionRole",
                    },
                ]
            },
        )

    def test_profile_replace_multiple_direct_replace_str_input(self):
        input = "%{SourceArn}%{DestinationArn}"
        result = profile_replace(
            input,
            {
                "SourceArn": "arn:aws:iam:policy/service-role/AWSLambdaBasicExecutionRole",
                "DestinationArn": "destinationArn",
            },
        )

        self.assertEqual(
            result,
            {
                "Fn::Sub": [
                    "${SourceArn}${DestinationArn}",
                    {
                        "DestinationArn": "destinationArn",
                        "SourceArn": "arn:aws:iam:policy/service-role/AWSLambdaBasicExecutionRole",
                    },
                ]
            },
        )

    def test_profile_replace_invalid_replacement_str_input(self):
        input = "%{SourceArn}TestingExample%{DestinationArn}"
        result = profile_replace(
            input,
            {
                "Source1Arn": "arn:aws:iam:policy/service-role/AWSLambdaBasicExecutionRole",
                "Destina1tionArn": "destinationArn",
            },
        )

        self.assertEqual(result, "%{SourceArn}TestingExample%{DestinationArn}")

    def test_profile_replace_list_input(self):
        input = ["%{SourceArn}TestingExample", "%{DestinationArn}", "%DestinationArn"]
        result = profile_replace(
            input,
            {
                "SourceArn": "arn:aws:iam:policy/service-role/AWSLambdaBasicExecutionRole",
                "DestinationArn": "random_fake_arn",
            },
        )

        self.assertEqual(
            result,
            [
                {
                    "Fn::Sub": [
                        "${SourceArn}TestingExample",
                        {"SourceArn": "arn:aws:iam:policy/service-role/AWSLambdaBasicExecutionRole"},
                    ],
                },
                "random_fake_arn",
                "%DestinationArn",
            ],
        )

    def test_replace_cfn_resource_properties(self):
        output = replace_cfn_resource_properties("AWS::Lambda::Function", "hello-world")
        self.assertEqual(
            output, {"Inputs": {"Role": "Role"}, "Outputs": {"Arn": {"Fn::GetAtt": ["hello-world", "Arn"]}}}
        )

        output = replace_cfn_resource_properties("AWS::Fake::Resource", "hello-world")
        self.assertEqual(output, {})

    def test_profile_replace_dict_input(self):
        input = {
            "Permissions": {
                "AWS::DynamoDB::Table": {
                    "AWS::Lambda::Function": {
                        "Type": "%{TypeName}Type",
                        "Properties": {
                            "SourcePolicy": False,
                            "Permissions": {
                                "Read": {
                                    "Statement": [
                                        {
                                            "Effect": "Allow",
                                            "Action": [
                                                "%{ActionName}",
                                                "dynamodb:GetRecords",
                                                "dynamodb:GetShardIterator",
                                                "dynamodb:ListStreams",
                                            ],
                                            "Resource": ["%{SourceArn}/stream/*"],
                                        }
                                    ]
                                }
                            },
                        },
                    }
                },
                "AWS::Events::Rule": {
                    "AWS::Events::EventBus": {
                        "Type": "AWS_IAM_ROLE_INLINE_POLICY",
                        "Properties": {
                            "SourcePolicy": True,
                            "Permissions": {
                                "Write": {
                                    "Statement": [
                                        {
                                            "Effect": "Allow",
                                            "Action": ["events:PutEvents"],
                                            "Resource": ["%{DestinationArn}"],
                                        }
                                    ]
                                }
                            },
                        },
                    }
                },
            }
        }
        result = profile_replace(
            input,
            {
                "SourceArn": "dynamodb_table_arn",
                "TypeName": "AWS_IAM_ROLE_INLINE_POLICY",
                "ActionName": "dynamodb:DescribeStream",
                "DestinationArn": "random_destination_arn",
            },
        )

        self.assertEqual(
            result,
            {
                "Permissions": {
                    "AWS::DynamoDB::Table": {
                        "AWS::Lambda::Function": {
                            "Properties": {
                                "Permissions": {
                                    "Read": {
                                        "Statement": [
                                            {
                                                "Action": [
                                                    "dynamodb:DescribeStream",
                                                    "dynamodb:GetRecords",
                                                    "dynamodb:GetShardIterator",
                                                    "dynamodb:ListStreams",
                                                ],
                                                "Effect": "Allow",
                                                "Resource": [
                                                    {
                                                        "Fn::Sub": [
                                                            "${SourceArn}/stream/*",
                                                            {"SourceArn": "dynamodb_table_arn"},
                                                        ]
                                                    }
                                                ],
                                            }
                                        ]
                                    }
                                },
                                "SourcePolicy": False,
                            },
                            "Type": {"Fn::Sub": ["${TypeName}Type", {"TypeName": "AWS_IAM_ROLE_INLINE_POLICY"}]},
                        }
                    },
                    "AWS::Events::Rule": {
                        "AWS::Events::EventBus": {
                            "Properties": {
                                "Permissions": {
                                    "Write": {
                                        "Statement": [
                                            {
                                                "Action": ["events:PutEvents"],
                                                "Effect": "Allow",
                                                "Resource": ["random_destination_arn"],
                                            }
                                        ]
                                    }
                                },
                                "SourcePolicy": True,
                            },
                            "Type": "AWS_IAM_ROLE_INLINE_POLICY",
                        }
                    },
                }
            },
        )

    def test_verify_replaced(self):
        verify_profile_variables_replaced({"Foo": {"Bar": "${AllGood}something What"}})
        verify_profile_variables_replaced({"Foo": {"Bar": "${All.Good}something %{What"}})
        verify_profile_variables_replaced({"Foo": {"${AllGood}": "something %{What"}})

    @parameterized.expand(
        [
            ({"Foo": {"Bar": "%{NotGood}something What"}}, "%{NotGood}"),
            ({"Foo": {"Bar": "%{Not.Good}something What"}}, "%{Not.Good}"),
            ({"Foo": {"%{NotGood}": "something What"}}, "%{NotGood}"),
            ({"Foo": {"%{NotGood}": "something %{What.No}"}}, "['%{NotGood}', '%{What.No}']"),
        ]
    )
    def test_verify_not_replaced(self, profile, error_includes):
        with self.assertRaises(ValueError) as ctx:
            verify_profile_variables_replaced(profile)
        self.assertIn(error_includes, str(ctx.exception))

    def test_get_profile_copied(self):
        d1 = get_profile("AWS::Lambda::Function", "AWS::DynamoDB::Table")
        d1["Type"] = "overridden"
        d2 = get_profile("AWS::Lambda::Function", "AWS::DynamoDB::Table")
        self.assertNotEqual(d1, d2)
