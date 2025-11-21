from unittest import TestCase
from unittest.mock import Mock

from parameterized import parameterized
from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.model.eventsources.pull import SelfManagedKafka
from samtranslator.model.exceptions import InvalidEventException
from samtranslator.model.lambda_ import LambdaFunction


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

    def test_validate_schema_registry_config_missing_required_fields(self):
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "SASL_SCRAM_256_AUTH", "URI": "SECRET_URI"},
            {"Type": "VPC_SUBNET", "URI": "SECRET_URI"},
            {"Type": "VPC_SECURITY_GROUP", "URI": "SECRET_URI"},
        ]
        self.kafka_event_source.Topics = ["Topics"]
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.SchemaRegistryConfig = {
            "SchemaRegistryURI": "arn:aws:glue:us-west-2:123456789012:registry/example"
        }
        with self.assertRaises(InvalidEventException) as context:
            self.kafka_event_source.get_policy_statements(IntrinsicsResolver({}))
        self.assertTrue("Missing required field EventRecordFormat in SchemaRegistryConfig" in str(context.exception))

    def test_validate_schema_registry_config_invalid_format(self):
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "SASL_SCRAM_256_AUTH", "URI": "SECRET_URI"},
            {"Type": "VPC_SUBNET", "URI": "SECRET_URI"},
            {"Type": "VPC_SECURITY_GROUP", "URI": "SECRET_URI"},
        ]
        self.kafka_event_source.Topics = ["Topics"]
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.SchemaRegistryConfig = {
            "SchemaRegistryURI": "arn:aws:glue:us-west-2:123456789012:registry/example",
            "EventRecordFormat": "INVALID",
            "SchemaValidationConfigs": [],
        }
        with self.assertRaises(InvalidEventException) as context:
            self.kafka_event_source.get_policy_statements(IntrinsicsResolver({}))
        self.assertTrue(
            "EventRecordFormat in SchemaRegistryConfig must be either 'JSON' or 'SOURCE'" in str(context.exception)
        )

    def test_validate_schema_registry_config_invalid_validation_configs(self):
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "SASL_SCRAM_256_AUTH", "URI": "SECRET_URI"},
            {"Type": "VPC_SUBNET", "URI": "SECRET_URI"},
            {"Type": "VPC_SECURITY_GROUP", "URI": "SECRET_URI"},
        ]
        self.kafka_event_source.Topics = ["Topics"]
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.SchemaRegistryConfig = {
            "SchemaRegistryURI": "arn:aws:glue:us-west-2:123456789012:registry/example",
            "EventRecordFormat": "JSON",
            "SchemaValidationConfigs": "not-a-list",
        }
        with self.assertRaises(InvalidEventException) as context:
            self.kafka_event_source.get_policy_statements(IntrinsicsResolver({}))
        self.assertTrue("SchemaValidationConfigs must be a list" in str(context.exception))

    def test_get_policy_statements_with_schema_registry(self):
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "BASIC_AUTH", "URI": "SECRET_URI"},
            {"Type": "VPC_SUBNET", "URI": "SECRET_URI"},
            {"Type": "VPC_SECURITY_GROUP", "URI": "SECRET_URI"},
        ]
        self.kafka_event_source.Topics = ["Topics"]
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.SchemaRegistryConfig = {
            "SchemaRegistryURI": "arn:aws:glue:us-west-2:123456789012:registry/example",
            "EventRecordFormat": "JSON",
            "SchemaValidationConfigs": [{"Attribute": "KEY"}],
            "AccessConfigs": [{"Type": "BASIC_AUTH", "URI": "BASIC_AUTH_URI"}],
        }

        policy_statements = self.kafka_event_source.get_policy_statements(IntrinsicsResolver({}))
        expected_statements = [
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
            {"Action": ["secretsmanager:GetSecretValue"], "Effect": "Allow", "Resource": "BASIC_AUTH_URI"},
            {
                "Action": ["glue:GetRegistry"],
                "Effect": "Allow",
                "Resource": "arn:aws:glue:us-west-2:123456789012:registry/example",
            },
            {
                "Action": ["glue:GetSchemaVersion"],
                "Effect": "Allow",
                "Resource": [
                    {"Fn::Sub": "arn:${AWS::Partition}:glue:${AWS::Region}:${AWS::AccountId}:schema/example/*"}
                ],
            },
        ]
        self.assertEqual(len(policy_statements), 1)
        self.assertEqual(len(policy_statements[0]["PolicyDocument"]["Statement"]), len(expected_statements))
        for statement in expected_statements:
            self.assertIn(statement, policy_statements[0]["PolicyDocument"]["Statement"])

    def test_get_policy_statements_with_non_glue_schema_registry(self):
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "BASIC_AUTH", "URI": "SECRET_URI"},
            {"Type": "VPC_SUBNET", "URI": "SECRET_URI"},
            {"Type": "VPC_SECURITY_GROUP", "URI": "SECRET_URI"},
        ]
        self.kafka_event_source.Topics = ["Topics"]
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.SchemaRegistryConfig = {
            "SchemaRegistryURI": "https://example.com/testRegistry",
            "EventRecordFormat": "JSON",
            "SchemaValidationConfigs": [{"Attribute": "KEY"}],
            "AccessConfigs": [
                {"Type": "SERVER_ROOT_CA_CERTIFICATE", "URI": "CA_SECRET_URI"},
            ],
        }

        policy_statements = self.kafka_event_source.get_policy_statements(IntrinsicsResolver({}))
        expected_statements = [
            {
                "Action": [
                    "secretsmanager:GetSecretValue",
                ],
                "Effect": "Allow",
                "Resource": "SECRET_URI",
            },
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
                    "secretsmanager:GetSecretValue",
                ],
                "Effect": "Allow",
                "Resource": "CA_SECRET_URI",
            },
        ]

        self.assertEqual(len(policy_statements[0]["PolicyDocument"]["Statement"]), len(expected_statements))
        for statement in expected_statements:
            self.assertIn(statement, policy_statements[0]["PolicyDocument"]["Statement"])

    def test_to_cloudformation_with_kafka_destination_type_acceptance(self):
        """Test that SelfManagedKafka accepts 'Kafka' as a valid destination type and no additional IAM policies are generated."""
        # Set up SelfManagedKafka event source with Kafka destination
        self.kafka_event_source.DestinationConfig = {
            "OnFailure": {"Type": "Kafka", "Destination": "kafka://failure-topic"}
        }

        # Set up required properties for SelfManagedKafka
        self.kafka_event_source.KafkaBootstrapServers = ["localhost:9092"]
        self.kafka_event_source.Topics = ["test-topic"]
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "BASIC_AUTH", "URI": "SECRET_URI"},
            {"Type": "VPC_SUBNET", "URI": "SECRET_URI"},
            {"Type": "VPC_SECURITY_GROUP", "URI": "SECRET_URI"},
        ]

        # Mock function
        mock_function = Mock()
        mock_function.get_runtime_attr.return_value = "test-function"
        mock_function.get_passthrough_resource_attributes.return_value = {}

        # Mock role
        mock_role = Mock()
        mock_role.ManagedPolicyArns = []
        mock_role.Policies = None

        # Call to_cloudformation
        resources = self.kafka_event_source.to_cloudformation(function=mock_function, role=mock_role)

        # Verify that the method completes without raising an exception
        self.assertIsNotNone(resources)
        self.assertEqual(len(resources), 1)

        # Verify that the EventSourceMapping resource is created
        event_source_mapping = resources[0]
        self.assertEqual(event_source_mapping.resource_type, "AWS::Lambda::EventSourceMapping")

        # Verify that DestinationConfig is set correctly (without the Type field)
        expected_destination_config = {"OnFailure": {"Destination": "kafka://failure-topic"}}
        self.assertEqual(event_source_mapping.DestinationConfig, expected_destination_config)

        # Verify that no additional IAM policies were added for Kafka destination
        # SelfManagedKafka doesn't have a base managed policy, so ManagedPolicyArns should remain empty
        self.assertEqual(len(mock_role.ManagedPolicyArns), 0)

        # Verify no destination-specific policies were added
        if mock_role.Policies:
            # Check that no SQS, SNS, or S3 policies were added
            for policy in mock_role.Policies:
                policy_doc = policy.get("PolicyDocument", {})
                statements = policy_doc.get("Statement", [])
                for statement in statements:
                    actions = statement.get("Action", [])
                    # Ensure no destination-specific actions are present
                    destination_actions = ["sqs:SendMessage", "sns:Publish", "s3:PutObject"]
                    for action in actions:
                        self.assertNotIn(action, destination_actions)

    def test_to_cloudformation_with_kafka_destination_config_pass_through(self):
        """Test that DestinationConfig is passed through unchanged and kafka:// URI is preserved."""
        # Set up SelfManagedKafka event source with Kafka destination using kafka:// URI
        kafka_uri = "kafka://my-kafka-cluster:9092/failure-topic"
        self.kafka_event_source.DestinationConfig = {"OnFailure": {"Type": "Kafka", "Destination": kafka_uri}}

        # Set up required properties for SelfManagedKafka
        self.kafka_event_source.KafkaBootstrapServers = ["localhost:9092"]
        self.kafka_event_source.Topics = ["test-topic"]
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "BASIC_AUTH", "URI": "SECRET_URI"},
            {"Type": "VPC_SUBNET", "URI": "SECRET_URI"},
            {"Type": "VPC_SECURITY_GROUP", "URI": "SECRET_URI"},
        ]

        # Mock function
        mock_function = Mock()
        mock_function.get_runtime_attr.return_value = "test-function"
        mock_function.get_passthrough_resource_attributes.return_value = {}

        # Mock role
        mock_role = Mock()
        mock_role.ManagedPolicyArns = []
        mock_role.Policies = None

        # Call to_cloudformation
        resources = self.kafka_event_source.to_cloudformation(function=mock_function, role=mock_role)

        # Verify that the EventSourceMapping resource is created
        self.assertEqual(len(resources), 1)
        event_source_mapping = resources[0]

        # Verify that DestinationConfig is passed through with the kafka:// URI preserved
        # The Type field should be removed, but Destination should remain unchanged
        expected_destination_config = {"OnFailure": {"Destination": kafka_uri}}
        self.assertEqual(event_source_mapping.DestinationConfig, expected_destination_config)

        # Verify that the original kafka:// URI is preserved exactly as provided
        actual_destination = event_source_mapping.DestinationConfig["OnFailure"]["Destination"]
        self.assertEqual(actual_destination, kafka_uri)

        # Verify that the URI format is not modified or validated
        self.assertTrue(actual_destination.startswith("kafka://"))
        self.assertIn("my-kafka-cluster:9092/failure-topic", actual_destination)

    def test_to_cloudformation_with_bisect_batch_on_function_error(self):
        # Test with True value
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Topics = ["test-topic"]
        self.kafka_event_source.SourceAccessConfigurations = [{"Type": "BASIC_AUTH", "URI": "SECRET_URI"}]
        self.kafka_event_source.BisectBatchOnFunctionError = True

        mock_function = LambdaFunction("TestFunction")
        resources = self.kafka_event_source.to_cloudformation(function=mock_function)

        self.assertEqual(len(resources), 1)
        event_source_mapping = resources[0]
        self.assertEqual(event_source_mapping.BisectBatchOnFunctionError, True)

        # Test with False value
        self.kafka_event_source.BisectBatchOnFunctionError = False
        resources = self.kafka_event_source.to_cloudformation(function=mock_function)

        self.assertEqual(len(resources), 1)
        event_source_mapping = resources[0]
        self.assertEqual(event_source_mapping.BisectBatchOnFunctionError, False)

    def test_to_cloudformation_with_max_record_age_in_seconds(self):
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Topics = ["test-topic"]
        self.kafka_event_source.SourceAccessConfigurations = [{"Type": "BASIC_AUTH", "URI": "SECRET_URI"}]
        self.kafka_event_source.MaximumRecordAgeInSeconds = 3600

        mock_function = LambdaFunction("TestFunction")
        resources = self.kafka_event_source.to_cloudformation(function=mock_function)

        self.assertEqual(len(resources), 1)
        event_source_mapping = resources[0]
        self.assertEqual(event_source_mapping.MaximumRecordAgeInSeconds, 3600)

    def test_to_cloudformation_with_max_retry_attempts(self):
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Topics = ["test-topic"]
        self.kafka_event_source.SourceAccessConfigurations = [{"Type": "BASIC_AUTH", "URI": "SECRET_URI"}]
        self.kafka_event_source.MaximumRetryAttempts = 3

        mock_function = LambdaFunction("TestFunction")
        resources = self.kafka_event_source.to_cloudformation(function=mock_function)

        self.assertEqual(len(resources), 1)
        event_source_mapping = resources[0]
        self.assertEqual(event_source_mapping.MaximumRetryAttempts, 3)

    def test_to_cloudformation_with_function_response_types(self):
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Topics = ["test-topic"]
        self.kafka_event_source.SourceAccessConfigurations = [{"Type": "BASIC_AUTH", "URI": "SECRET_URI"}]
        self.kafka_event_source.FunctionResponseTypes = ["ReportBatchItemFailures"]

        mock_function = LambdaFunction("TestFunction")
        resources = self.kafka_event_source.to_cloudformation(function=mock_function)

        self.assertEqual(len(resources), 1)
        event_source_mapping = resources[0]
        self.assertEqual(event_source_mapping.FunctionResponseTypes, ["ReportBatchItemFailures"])

    def test_to_cloudformation_with_all_error_handling_properties(self):
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Topics = ["test-topic"]
        self.kafka_event_source.SourceAccessConfigurations = [{"Type": "BASIC_AUTH", "URI": "SECRET_URI"}]
        self.kafka_event_source.BisectBatchOnFunctionError = True
        self.kafka_event_source.MaximumRecordAgeInSeconds = 3600
        self.kafka_event_source.MaximumRetryAttempts = 3
        self.kafka_event_source.FunctionResponseTypes = ["ReportBatchItemFailures"]

        mock_function = LambdaFunction("TestFunction")
        resources = self.kafka_event_source.to_cloudformation(function=mock_function)

        self.assertEqual(len(resources), 1)
        event_source_mapping = resources[0]
        self.assertEqual(event_source_mapping.BisectBatchOnFunctionError, True)
        self.assertEqual(event_source_mapping.MaximumRecordAgeInSeconds, 3600)
        self.assertEqual(event_source_mapping.MaximumRetryAttempts, 3)
        self.assertEqual(event_source_mapping.FunctionResponseTypes, ["ReportBatchItemFailures"])

    def test_to_cloudformation_without_error_handling_properties(self):
        self.kafka_event_source.KafkaBootstrapServers = ["endpoint1", "endpoint2"]
        self.kafka_event_source.Topics = ["test-topic"]
        self.kafka_event_source.SourceAccessConfigurations = [{"Type": "BASIC_AUTH", "URI": "SECRET_URI"}]

        mock_function = LambdaFunction("TestFunction")
        resources = self.kafka_event_source.to_cloudformation(function=mock_function)

        self.assertEqual(len(resources), 1)
        event_source_mapping = resources[0]
        self.assertIsNone(event_source_mapping.BisectBatchOnFunctionError)
        self.assertIsNone(event_source_mapping.MaximumRecordAgeInSeconds)
        self.assertIsNone(event_source_mapping.MaximumRetryAttempts)
        self.assertIsNone(event_source_mapping.FunctionResponseTypes)

    def test_to_cloudformation_with_provisioned_poller_config_including_poller_group_name(self):
        """Test that PollerGroupName is correctly passed through in ProvisionedPollerConfig"""

        # Set up the SelfManagedKafka event source with ProvisionedPollerConfig including PollerGroupName
        self.kafka_event_source.KafkaBootstrapServers = ["broker1:9092", "broker2:9092"]
        self.kafka_event_source.Topics = ["MyTopic"]
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "SASL_SCRAM_256_AUTH", "URI": "arn:aws:secretsmanager:us-west-2:123456789012:secret:my-secret"},
            {"Type": "VPC_SUBNET", "URI": "subnet-12345"},
            {"Type": "VPC_SECURITY_GROUP", "URI": "sg-67890"},
        ]
        self.kafka_event_source.ProvisionedPollerConfig = {
            "MinimumPollers": 3,
            "MaximumPollers": 15,
            "PollerGroupName": "self-managed-poller-group",
        }

        # Create a mock function
        function = Mock()
        function.get_runtime_attr = Mock()
        function.get_runtime_attr.return_value = "arn:aws:lambda:mock"
        function.resource_attributes = {}
        function.get_passthrough_resource_attributes = Mock()
        function.get_passthrough_resource_attributes.return_value = {}

        # Convert to CloudFormation
        resources = self.kafka_event_source.to_cloudformation(function=function)

        # Verify that the EventSourceMapping resource is created
        self.assertEqual(len(resources), 1)
        event_source_mapping = resources[0]

        # Verify that ProvisionedPollerConfig is correctly set with all properties including PollerGroupName
        expected_config = {"MinimumPollers": 3, "MaximumPollers": 15, "PollerGroupName": "self-managed-poller-group"}
        self.assertEqual(event_source_mapping.ProvisionedPollerConfig, expected_config)
