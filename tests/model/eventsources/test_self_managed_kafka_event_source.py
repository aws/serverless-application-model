from unittest import TestCase
from samtranslator.model.eventsources.pull import SelfManagedKafka
from samtranslator.model.exceptions import InvalidEventException


class SelfManagedKafkaEventSource(TestCase):
    def setUp(self):
        self.logical_id = "SelfManagedKafkaEvent"
        self.kafka_event_source = SelfManagedKafka(self.logical_id)

    def test_get_policy_arn(self):
        arn = self.kafka_event_source.get_policy_arn()
        expected_arn = None
        self.assertEqual(arn, expected_arn)

    def test_get_policy_statements(self):
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "SASL_SCRAM_256_AUTH", "URI": "SECRET_URI"},
            {"Type": "VPC_SUBNET", "URI": "SECRET_URI"},
            {"Type": "VPC_SECURITY_GROUP", "URI": "SECRET_URI"},
        ]
        self.kafka_event_source.Topics = ["Topics"]
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Enabled = True
        self.kafka_event_source.BatchSize = 1
        self.kafka_event_source.Broker = "SECRET_KEY"

        policy_statements = self.kafka_event_source.get_policy_statements()
        expected_policy_document = [
            {
                "PolicyDocument": {
                    "Statement": [
                        {"Action": ["secretsmanager:GetSecretValue"], "Effect": "Allow", "Resource": "SECRET_URI"},
                        {
                            "Action": [
                                "ec2:CreateNetworkInterface",
                                "ec2:DescribeNetworkInterfaces",
                                "ec2:DeleteNetworkInterface",
                                "ec2:DescribeVpcs",
                                "ec2:DescribeSubnets",
                                "ec2:DescribeSecurityGroups",
                            ],
                            "Effect": "Allow",
                            "Resource": "*",
                        },
                        {
                            "Action": [
                                "mq:DescribeBroker",
                            ],
                            "Effect": "Allow",
                            "Resource": self.kafka_event_source.Broker,
                        },
                    ],
                    "Version": "2012-10-17",
                },
                "PolicyName": "SelfManagedKafkaExecutionRolePolicy",
            }
        ]

        self.assertEqual(policy_statements, expected_policy_document)

    def test_get_policy_statements_with_required_auth_mechanism(self):
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "SASL_SCRAM_256_AUTH", "URI": "SECRET_URI"},
        ]
        self.kafka_event_source.Topics = ["Topics"]
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Enabled = True
        self.kafka_event_source.BatchSize = 1
        self.kafka_event_source.Broker = "SECRET_KEY"

        policy_statements = self.kafka_event_source.get_policy_statements()
        expected_policy_document = [
            {
                "PolicyDocument": {
                    "Statement": [
                        {"Action": ["secretsmanager:GetSecretValue"], "Effect": "Allow", "Resource": "SECRET_URI"},
                        {
                            "Action": [
                                "ec2:CreateNetworkInterface",
                                "ec2:DescribeNetworkInterfaces",
                                "ec2:DeleteNetworkInterface",
                                "ec2:DescribeVpcs",
                                "ec2:DescribeSubnets",
                                "ec2:DescribeSecurityGroups",
                            ],
                            "Effect": "Allow",
                            "Resource": "*",
                        },
                        {
                            "Action": [
                                "mq:DescribeBroker",
                            ],
                            "Effect": "Allow",
                            "Resource": self.kafka_event_source.Broker,
                        },
                    ],
                    "Version": "2012-10-17",
                },
                "PolicyName": "SelfManagedKafkaExecutionRolePolicy",
            }
        ]

        self.assertEqual(policy_statements, expected_policy_document)

    def test_must_raise_for_missing_topic(self):
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "SASL_SCRAM_256_AUTH", "URI": "SECRET_URI"},
            {"Type": "VPC_SUBNET", "URI": "SECRET_URI"},
            {"Type": "VPC_SECURITY_GROUP", "URI": "SECRET_URI"},
        ]
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Enabled = True
        self.kafka_event_source.BatchSize = 1

        with self.assertRaises(InvalidEventException):
            self.kafka_event_source.get_policy_statements()

    def test_must_raise_for_missing_endpoints(self):
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "SASL_SCRAM_256_AUTH", "URI": "SECRET_URI"},
            {"Type": "VPC_SUBNET", "URI": "SECRET_URI"},
            {"Type": "VPC_SECURITY_GROUP", "URI": "SECRET_URI"},
        ]
        self.kafka_event_source.Enabled = True
        self.kafka_event_source.Topics = ["Topics"]
        self.kafka_event_source.BatchSize = 1

        with self.assertRaises(InvalidEventException):
            self.kafka_event_source.get_policy_statements()

    def test_must_raise_for_missing_vpc_config(self):
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "SASL_SCRAM_256_AUTH", "URI": "SECRET_URI"},
            {"Type": "VPC_SUBNET", "URI": "SECRET_URI"},
        ]
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Enabled = True
        self.kafka_event_source.Topics = ["Topics"]
        self.kafka_event_source.BatchSize = 1

        with self.assertRaises(InvalidEventException):
            self.kafka_event_source.get_policy_statements()
