from unittest import TestCase

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

    def test_get_policy_statements_with_no_auth_mechanism(self):
        self.kafka_event_source.SourceAccessConfigurations = []

        policy_statements = self.kafka_event_source.get_policy_statements()
        expected_policy_document = None

        self.assertEqual(policy_statements, expected_policy_document)
