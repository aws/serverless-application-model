from unittest import TestCase

from parameterized import parameterized
from samtranslator.model.eventsources.pull import SelfManagedKafka
from samtranslator.model.exceptions import InvalidEventException


class SelfManagedKafkaEventSource(TestCase):
    def setUp(self):
        self.logical_id = "SelfManagedKafkaEvent"
        self.kafka_event_source = SelfManagedKafka(self.logical_id)
        self.kafka_event_source.relative_id = "EventId"

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
                    ],
                    "Version": "2012-10-17",
                },
                "PolicyName": "SelfManagedKafkaExecutionRolePolicy",
            }
        ]

        self.assertEqual(policy_statements, expected_policy_document)

    def test_get_policy_statements_with_only_auth_mechanism(self):
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "BASIC_AUTH", "URI": "SECRET_URI"},
        ]
        self.kafka_event_source.Topics = ["Topics"]
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Enabled = True
        self.kafka_event_source.BatchSize = 1

        policy_statements = self.kafka_event_source.get_policy_statements()
        expected_policy_document = [
            {
                "PolicyDocument": {
                    "Statement": [
                        {"Action": ["secretsmanager:GetSecretValue"], "Effect": "Allow", "Resource": "SECRET_URI"},
                    ],
                    "Version": "2012-10-17",
                },
                "PolicyName": "SelfManagedKafkaExecutionRolePolicy",
            }
        ]

        self.assertEqual(policy_statements, expected_policy_document)

    def test_get_policy_statements_with_only_vpc_config(self):
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "VPC_SUBNET", "URI": "SECRET_URI"},
            {"Type": "VPC_SECURITY_GROUP", "URI": "SECRET_URI"},
        ]
        self.kafka_event_source.Topics = ["Topics"]
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Enabled = True
        self.kafka_event_source.BatchSize = 1

        policy_statements = self.kafka_event_source.get_policy_statements()
        expected_policy_document = [
            {
                "PolicyDocument": {
                    "Statement": [
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
                    ],
                    "Version": "2012-10-17",
                },
                "PolicyName": "SelfManagedKafkaExecutionRolePolicy",
            }
        ]
        self.assertEqual(policy_statements, expected_policy_document)

    def test_get_policy_statements_with_secrets_manager_kms_key_id(self):
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "SASL_SCRAM_256_AUTH", "URI": "SECRET_URI"},
            {"Type": "VPC_SUBNET", "URI": "SECRET_URI"},
            {"Type": "VPC_SECURITY_GROUP", "URI": "SECRET_URI"},
        ]
        self.kafka_event_source.Topics = ["Topics"]
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Enabled = True
        self.kafka_event_source.BatchSize = 1
        self.kafka_event_source.SecretsManagerKmsKeyId = "SECRET_KEY"

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
                            "Action": ["kms:Decrypt"],
                            "Effect": "Allow",
                            "Resource": {
                                "Fn::Sub": "arn:${AWS::Partition}:kms:${AWS::Region}:${AWS::AccountId}:key/"
                                + self.kafka_event_source.SecretsManagerKmsKeyId
                            },
                        },
                    ],
                    "Version": "2012-10-17",
                },
                "PolicyName": "SelfManagedKafkaExecutionRolePolicy",
            }
        ]
        self.assertEqual(policy_statements, expected_policy_document)

    def test_must_raise_for_missing_topics(self):
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

    def test_must_raise_for_empty_topics(self):
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "SASL_SCRAM_256_AUTH", "URI": "SECRET_URI"},
            {"Type": "VPC_SUBNET", "URI": "SECRET_URI"},
            {"Type": "VPC_SECURITY_GROUP", "URI": "SECRET_URI"},
        ]
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Enabled = True
        self.kafka_event_source.BatchSize = 1
        self.kafka_event_source.Topics = []

        with self.assertRaises(InvalidEventException):
            self.kafka_event_source.get_policy_statements()

    def test_must_raise_for_multiple_topics(self):
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "SASL_SCRAM_256_AUTH", "URI": "SECRET_URI"},
            {"Type": "VPC_SUBNET", "URI": "SECRET_URI"},
            {"Type": "VPC_SECURITY_GROUP", "URI": "SECRET_URI"},
        ]
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Topics = ["Topics1", "Topics2"]
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

    def test_must_raise_for_empty_bootstrap_server(self):
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "SASL_SCRAM_256_AUTH", "URI": "SECRET_URI"},
            {"Type": "VPC_SUBNET", "URI": "SECRET_URI"},
            {"Type": "VPC_SECURITY_GROUP", "URI": "SECRET_URI"},
        ]
        self.kafka_event_source.KafkaBootstrapServers = []
        self.kafka_event_source.Enabled = True
        self.kafka_event_source.Topics = ["Topics"]
        self.kafka_event_source.BatchSize = 1

        with self.assertRaises(InvalidEventException):
            self.kafka_event_source.get_policy_statements()

    def test_must_raise_for_missing_vpc_subnet(self):
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "SASL_SCRAM_256_AUTH", "URI": "SECRET_URI"},
            {"Type": "VPC_SECURITY_GROUP", "URI": "SECRET_URI"},
        ]
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Enabled = True
        self.kafka_event_source.Topics = ["Topics"]
        self.kafka_event_source.BatchSize = 1

        with self.assertRaises(InvalidEventException):
            self.kafka_event_source.get_policy_statements()

    def test_must_raise_for_missing_vpc_security_group(self):
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

    def test_must_raise_for_missing_source_access_configurations(self):
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Enabled = True
        self.kafka_event_source.Topics = ["Topics"]
        self.kafka_event_source.BatchSize = 1

        with self.assertRaises(InvalidEventException):
            self.kafka_event_source.get_policy_statements()

    def test_must_raise_for_unknown_source_access_configurations_type(self):
        test_credentials = [
            [{"Type": "BASIC_AUT", "URI": "SECRET_URI"}],
            [{"Type": "SASL_SCRAM_256_AUT", "URI": "SECRET_URI"}],
            [{"Type": None, "URI": "SECRET_URI"}],
            [{"Type": "VPC_SUB", "URI": "SECRET_URI"}, {"Type": "VPC_SECURITY_GROUP", "URI": "SECRET_URI"}],
            [{"Type": "VPC_SUBNET", "URI": "SECRET_URI"}, {"Type": None, "URI": None}],
        ]
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Enabled = True
        self.kafka_event_source.Topics = ["Topics"]
        self.kafka_event_source.BatchSize = 1

        for config in test_credentials:
            self.kafka_event_source.SourceAccessConfigurations = config
            with self.assertRaises(InvalidEventException):
                self.kafka_event_source.get_policy_statements()

    def test_must_raise_for_wrong_source_access_configurations_uri(self):
        test_credentials = [
            [{"Type": "BASIC_AUTH", "URI": 1}],
            [{"Type": "SASL_SCRAM_256_AUTH", "URI": 1}],
            [{"Type": "SASL_SCRAM_512_AUTH", "URI": 1}],
            [{"Type": "VPC_SUBNET", "URI": None}, {"Type": "VPC_SECURITY_GROUP", "URI": "SECRET_URI"}],
            [{"Type": "VPC_SUBNET", "URI": "SECRET_URI"}, {"Type": "VPC_SECURITY_GROUP", "URI": None}],
        ]
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Enabled = True
        self.kafka_event_source.Topics = ["Topics"]
        self.kafka_event_source.BatchSize = 1

        for config in test_credentials:
            self.kafka_event_source.SourceAccessConfigurations = config
            with self.assertRaises(InvalidEventException):
                self.kafka_event_source.get_policy_statements()

    @parameterized.expand(
        [
            (1,),
            (True,),
            (["1abc23d4-567f-8ab9-cde0-1fab234c5d67"],),
            ({"KmsKeyId": "1abc23d4-567f-8ab9-cde0-1fab234c5d67"},),
        ]
    )
    def test_must_validate_secrets_manager_kms_key_id(self, kms_key_id_value):
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "SASL_SCRAM_256_AUTH", "URI": "SECRET_URI"},
            {"Type": "VPC_SUBNET", "URI": "SECRET_URI"},
            {"Type": "VPC_SECURITY_GROUP", "URI": "SECRET_URI"},
        ]
        self.kafka_event_source.Topics = ["Topics"]
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Enabled = True
        self.kafka_event_source.BatchSize = 1
        self.kafka_event_source.SecretsManagerKmsKeyId = kms_key_id_value
        error_message = "('EventId', \"Property 'SecretsManagerKmsKeyId' should be a string.\")"
        with self.assertRaises(InvalidEventException) as error:
            self.kafka_event_source.get_policy_statements()
        self.assertEqual(error_message, str(error.exception))
