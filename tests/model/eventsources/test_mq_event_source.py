from unittest import TestCase

from parameterized import parameterized
from samtranslator.model.eventsources.pull import MQ
from samtranslator.model.exceptions import InvalidEventException


class MQEventSource(TestCase):
    def setUp(self):
        self.logical_id = "MQEvent"
        self.mq_event_source = MQ(self.logical_id)
        self.mq_event_source.relative_id = "EventId"

    def test_get_policy_arn(self):
        source_arn = self.mq_event_source.get_policy_arn()
        expected_source_arn = None
        self.assertEqual(source_arn, expected_source_arn)

    def test_get_policy_statements(self):
        self.mq_event_source.SourceAccessConfigurations = [{"Type": "BASIC_AUTH", "URI": "SECRET_URI"}]
        self.mq_event_source.Broker = "BROKER_ARN"
        policy_statements = self.mq_event_source.get_policy_statements()
        expected_policy_document = [
            {
                "PolicyName": self.mq_event_source._policy_name,
                "PolicyDocument": {
                    "Statement": [
                        {
                            "Action": [
                                "secretsmanager:GetSecretValue",
                            ],
                            "Effect": "Allow",
                            "Resource": "SECRET_URI",
                        },
                        {
                            "Action": [
                                "mq:DescribeBroker",
                            ],
                            "Effect": "Allow",
                            "Resource": "BROKER_ARN",
                        },
                    ]
                },
            }
        ]
        self.assertEqual(policy_statements, expected_policy_document)

    @parameterized.expand(
        [
            (1,),
            (True,),
            (["1abc23d4-567f-8ab9-cde0-1fab234c5d67"],),
            ({"KmsKeyId": "1abc23d4-567f-8ab9-cde0-1fab234c5d67"},),
        ]
    )
    def test_must_validate_secrets_manager_kms_key_id(self, kms_key_id_value):
        self.mq_event_source.SourceAccessConfigurations = [{"Type": "BASIC_AUTH", "URI": "SECRET_URI"}]
        self.mq_event_source.Broker = "BROKER_ARN"
        self.mq_event_source.SecretsManagerKmsKeyId = kms_key_id_value
        error_message = "('EventId', \"Property 'SecretsManagerKmsKeyId' should be a string.\")"
        with self.assertRaises(InvalidEventException) as error:
            self.mq_event_source.get_policy_statements()
        self.assertEqual(error_message, str(error.exception))

    def test_get_policy_statements_with_secrets_manager_kms_key_id(self):
        self.mq_event_source.SourceAccessConfigurations = [{"Type": "BASIC_AUTH", "URI": "SECRET_URI"}]
        self.mq_event_source.Broker = "BROKER_ARN"
        self.mq_event_source.SecretsManagerKmsKeyId = "1abc23d4-567f-8ab9-cde0-1fab234c5d67"
        policy_statements = self.mq_event_source.get_policy_statements()
        expected_policy_document = [
            {
                "PolicyName": self.mq_event_source._policy_name,
                "PolicyDocument": {
                    "Statement": [
                        {
                            "Action": [
                                "secretsmanager:GetSecretValue",
                            ],
                            "Effect": "Allow",
                            "Resource": "SECRET_URI",
                        },
                        {
                            "Action": [
                                "mq:DescribeBroker",
                            ],
                            "Effect": "Allow",
                            "Resource": "BROKER_ARN",
                        },
                        {
                            "Action": "kms:Decrypt",
                            "Effect": "Allow",
                            "Resource": {
                                "Fn::Sub": "arn:${AWS::Partition}:kms:${AWS::Region}:${AWS::AccountId}:key/1abc23d4-567f-8ab9-cde0-1fab234c5d67"
                            },
                        },
                    ]
                },
            }
        ]
        self.assertEqual(policy_statements, expected_policy_document)
