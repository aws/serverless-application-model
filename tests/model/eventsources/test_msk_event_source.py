from unittest import TestCase

from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.model.eventsources.pull import MSK


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
