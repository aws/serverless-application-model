from unittest import TestCase
from unittest.mock import Mock

from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.model.eventsources.pull import MSK
from samtranslator.model.lambda_ import LambdaFunction


class MSKEventSource(TestCase):
    def setUp(self):
        self.logical_id = "MSKEvent"
        self.kafka_event_source = MSK(self.logical_id)

    def test_get_policy_arn(self):
        arn = self.kafka_event_source.get_policy_arn()
        expected_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaMSKExecutionRole"
        self.assertEqual(arn, expected_arn)

    def test_get_policy_statements(self):
        self.kafka_event_source.SourceAccessConfigurations = [
            {"Type": "CLIENT_CERTIFICATE_TLS_AUTH", "URI": "SECRET_URI"},
        ]

        policy_statements = self.kafka_event_source.get_policy_statements()
        expected_policy_document = [
            {
                "PolicyName": "MSKExecutionRolePolicy",
                "PolicyDocument": {
                    "Statement": [
                        {
                            "Action": [
                                "secretsmanager:GetSecretValue",
                            ],
                            "Effect": "Allow",
                            "Resource": "SECRET_URI",
                        }
                    ]
                },
            }
        ]

        self.assertEqual(policy_statements, expected_policy_document)

    def test_get_policy_statements_with_glue_schema_registry(self):
        self.kafka_event_source.SchemaRegistryConfig = {
            "SchemaRegistryURI": "arn:aws:glue:us-west-2:123456789012:registry/example",
            "EventRecordFormat": "JSON",
            "SchemaValidationConfigs": [
                {
                    "Attribute": "KEY",
                    "ValidSchemas": ["schema1"],
                }
            ],
            "AccessConfigs": [
                {"Type": "BASIC_AUTH", "URI": "SCHEMA_SECRET_URI"},
                {"Type": "SERVER_ROOT_CA_CERTIFICATE", "URI": "CA_SECRET_URI"},
            ],
        }

        policy_statements = self.kafka_event_source.get_policy_statements(IntrinsicsResolver({}))
        expected_policy_document = [
            {
                "PolicyName": "MSKExecutionRolePolicy",
                "PolicyDocument": {
                    "Statement": [
                        {
                            "Action": [
                                "secretsmanager:GetSecretValue",
                            ],
                            "Effect": "Allow",
                            "Resource": "SCHEMA_SECRET_URI",
                        },
                        {
                            "Action": [
                                "secretsmanager:GetSecretValue",
                            ],
                            "Effect": "Allow",
                            "Resource": "CA_SECRET_URI",
                        },
                        {
                            "Action": ["glue:GetRegistry"],
                            "Effect": "Allow",
                            "Resource": "arn:aws:glue:us-west-2:123456789012:registry/example",
                        },
                        {
                            "Action": ["glue:GetSchemaVersion"],
                            "Effect": "Allow",
                            "Resource": [
                                {
                                    "Fn::Sub": "arn:${AWS::Partition}:glue:${AWS::Region}:${AWS::AccountId}:schema/example/*"
                                }
                            ],
                        },
                    ]
                },
            }
        ]

        self.assertEqual(policy_statements, expected_policy_document)

    def test_get_policy_statements_with_non_glue_schema_registry(self):
        self.kafka_event_source.SchemaRegistryConfig = {
            "SchemaRegistryURI": "https://example.com/testRegistry",
            "EventRecordFormat": "JSON",
            "SchemaValidationConfigs": [
                {
                    "Attribute": "KEY",
                    "ValidSchemas": ["schema1"],
                }
            ],
            "AccessConfigs": [
                {"Type": "SERVER_ROOT_CA_CERTIFICATE", "URI": "CA_SECRET_URI"},
            ],
        }

        policy_statements = self.kafka_event_source.get_policy_statements(IntrinsicsResolver({}))
        expected_policy_document = [
            {
                "PolicyName": "MSKExecutionRolePolicy",
                "PolicyDocument": {
                    "Statement": [
                        {
                            "Action": [
                                "secretsmanager:GetSecretValue",
                            ],
                            "Effect": "Allow",
                            "Resource": "CA_SECRET_URI",
                        }
                    ]
                },
            }
        ]

        self.assertEqual(policy_statements, expected_policy_document)

    def test_get_policy_statements_with_no_auth_mechanism(self):
        self.kafka_event_source.SourceAccessConfigurations = []

        policy_statements = self.kafka_event_source.get_policy_statements()
        expected_policy_document = None

        self.assertEqual(policy_statements, expected_policy_document)

    def test_validate_schema_registry_config_missing_required_fields(self):
        self.kafka_event_source.SchemaRegistryConfig = {
            "SchemaRegistryURI": "arn:aws:glue:us-west-2:123456789012:registry/example"
        }
        with self.assertRaises(Exception) as context:
            self.kafka_event_source.validate_schema_registry_config()
        self.assertTrue("Missing required field EventRecordFormat in SchemaRegistryConfig" in str(context.exception))

    def test_validate_schema_registry_config_invalid_format(self):
        self.kafka_event_source.SchemaRegistryConfig = {
            "SchemaRegistryURI": "arn:aws:glue:us-west-2:123456789012:registry/example",
            "EventRecordFormat": "INVALID",
            "SchemaValidationConfigs": [],
        }
        with self.assertRaises(Exception) as context:
            self.kafka_event_source.validate_schema_registry_config()
        self.assertTrue(
            "EventRecordFormat in SchemaRegistryConfig must be either 'JSON' or 'SOURCE'" in str(context.exception)
        )

    def test_validate_schema_registry_config_invalid_validation_configs(self):
        self.kafka_event_source.SchemaRegistryConfig = {
            "SchemaRegistryURI": "arn:aws:glue:us-west-2:123456789012:registry/example",
            "EventRecordFormat": "JSON",
            "SchemaValidationConfigs": "not-a-list",
        }
        with self.assertRaises(Exception) as context:
            self.kafka_event_source.validate_schema_registry_config()
        self.assertTrue("SchemaValidationConfigs must be a list" in str(context.exception))

    def test_validate_schema_registry_config_when_access_config_is_empty(self):
        self.kafka_event_source.SchemaRegistryConfig = {
            "SchemaRegistryURI": "arn:aws:glue:us-west-2:123456789012:registry/example",
            "EventRecordFormat": "JSON",
            "SchemaValidationConfigs": [
                {
                    "Attribute": "KEY",
                    "ValidSchemas": ["schema1"],
                }
            ],
            "AccessConfigs": "not- a list",
        }
        with self.assertRaises(Exception) as context:
            self.kafka_event_source.validate_schema_registry_config()
        self.assertTrue("AccessConfigs in SchemaRegistryConfig must be a list" in str(context.exception))

    def test_to_cloudformation_with_kafka_destination_type_acceptance(self):
        """Test that MSK accepts 'Kafka' as a valid destination type and no additional IAM policies are generated."""
        # Set up MSK event source with Kafka destination
        self.kafka_event_source.DestinationConfig = {
            "OnFailure": {"Type": "Kafka", "Destination": "kafka://failure-topic"}
        }

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
        # The role should only have the base MSK execution role policy
        expected_base_policy = "arn:aws:iam::aws:policy/service-role/AWSLambdaMSKExecutionRole"
        self.assertIn(expected_base_policy, mock_role.ManagedPolicyArns)

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
        # Set up MSK event source with Kafka destination using kafka:// URI
        kafka_uri = "kafka://my-kafka-cluster:9092/failure-topic"
        self.kafka_event_source.DestinationConfig = {"OnFailure": {"Type": "Kafka", "Destination": kafka_uri}}

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

    def test_to_cloudformation_with_all_error_handling_properties(self):
        self.kafka_event_source.Stream = "arn:aws:kafka:us-east-1:123456789012:cluster/test/abc"
        self.kafka_event_source.StartingPosition = "LATEST"
        self.kafka_event_source.Topics = ["test-topic"]
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
        self.kafka_event_source.Stream = "arn:aws:kafka:us-east-1:123456789012:cluster/test/abc"
        self.kafka_event_source.StartingPosition = "LATEST"
        self.kafka_event_source.Topics = ["test-topic"]

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

        # Set up the MSK event source with ProvisionedPollerConfig including PollerGroupName
        self.kafka_event_source.Stream = "arn:aws:kafka:us-west-2:012345678901:cluster/mycluster/abc123"
        self.kafka_event_source.StartingPosition = "LATEST"
        self.kafka_event_source.Topics = ["MyTopic"]
        self.kafka_event_source.ProvisionedPollerConfig = {
            "MinimumPollers": 5,
            "MaximumPollers": 10,
            "PollerGroupName": "my-poller-group",
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
        expected_config = {"MinimumPollers": 5, "MaximumPollers": 10, "PollerGroupName": "my-poller-group"}
        self.assertEqual(event_source_mapping.ProvisionedPollerConfig, expected_config)
