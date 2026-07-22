"""Unit tests for NetworkConnector generator"""

from unittest import TestCase

from samtranslator.model.network_connector.generators import NetworkConnectorGenerator


class TestNetworkConnectorGenerator(TestCase):
    def test_auto_generates_operator_role(self):
        gen = NetworkConnectorGenerator(
            logical_id="MyConnector",
            vpc_config={"SubnetIds": ["subnet-abc"], "SecurityGroupIds": ["sg-123"], "NetworkProtocol": "IPv4"},
        )
        resources = gen.to_cloudformation()

        self.assertEqual(len(resources), 2)
        role = resources[0]
        connector = resources[1]

        self.assertEqual(role.logical_id, "MyConnectorOperatorRole")
        self.assertEqual(role.resource_type, "AWS::IAM::Role")
        self.assertEqual(connector.logical_id, "MyConnector")
        self.assertEqual(connector.resource_type, "AWS::Lambda::NetworkConnector")
        self.assertEqual(connector.OperatorRole, {"Fn::GetAtt": ["MyConnectorOperatorRole", "Arn"]})

    def test_with_provided_operator_role(self):
        gen = NetworkConnectorGenerator(
            logical_id="MyConnector",
            vpc_config={"SubnetIds": ["subnet-abc"], "SecurityGroupIds": ["sg-123"], "NetworkProtocol": "IPv4"},
            operator_role="arn:aws:iam::123456789012:role/CustomRole",
        )
        resources = gen.to_cloudformation()

        self.assertEqual(len(resources), 1)
        connector = resources[0]
        self.assertEqual(connector.OperatorRole, "arn:aws:iam::123456789012:role/CustomRole")

    def test_vpc_config_wrapped_into_configuration(self):
        gen = NetworkConnectorGenerator(
            logical_id="MyConnector",
            vpc_config={"SubnetIds": ["subnet-abc"], "SecurityGroupIds": ["sg-123"], "NetworkProtocol": "IPv4"},
            operator_role="arn:aws:iam::123456789012:role/Role",
        )
        resources = gen.to_cloudformation()
        connector = resources[0]

        self.assertEqual(
            connector.Configuration,
            {
                "VpcEgressConfiguration": {
                    "SubnetIds": ["subnet-abc"],
                    "SecurityGroupIds": ["sg-123"],
                    "NetworkProtocol": "IPv4",
                    "AssociatedComputeResourceTypes": ["MicroVm"],
                }
            },
        )

    def test_name_optional(self):
        gen = NetworkConnectorGenerator(
            logical_id="MyConnector",
            vpc_config={"SubnetIds": ["subnet-abc"], "SecurityGroupIds": ["sg-123"], "NetworkProtocol": "IPv4"},
            operator_role="arn:aws:iam::123456789012:role/Role",
        )
        resources = gen.to_cloudformation()
        connector = resources[0]

        output = connector.to_dict()
        self.assertNotIn("Name", output["MyConnector"]["Properties"])

    def test_name_provided(self):
        gen = NetworkConnectorGenerator(
            logical_id="MyConnector",
            vpc_config={"SubnetIds": ["subnet-abc"], "SecurityGroupIds": ["sg-123"], "NetworkProtocol": "IPv4"},
            operator_role="arn:aws:iam::123456789012:role/Role",
            name="prod-vpc",
        )
        resources = gen.to_cloudformation()
        connector = resources[0]

        self.assertEqual(connector.Name, "prod-vpc")

    def test_tags_converted_to_array_with_sam_tag(self):
        gen = NetworkConnectorGenerator(
            logical_id="MyConnector",
            vpc_config={"SubnetIds": ["subnet-abc"], "SecurityGroupIds": ["sg-123"], "NetworkProtocol": "IPv4"},
            operator_role="arn:aws:iam::123456789012:role/Role",
            tags={"Environment": "Production"},
        )
        resources = gen.to_cloudformation()
        connector = resources[0]

        self.assertIn({"Key": "Environment", "Value": "Production"}, connector.Tags)
        self.assertIn({"Key": "lambda:createdBy", "Value": "SAM"}, connector.Tags)

    def test_connector_tagged_without_user_tags(self):
        gen = NetworkConnectorGenerator(
            logical_id="MyConnector",
            vpc_config={"SubnetIds": ["subnet-abc"], "SecurityGroupIds": ["sg-123"], "NetworkProtocol": "IPv4"},
            operator_role="arn:aws:iam::123456789012:role/Role",
        )
        resources = gen.to_cloudformation()
        connector = resources[0]

        self.assertIn({"Key": "lambda:createdBy", "Value": "SAM"}, connector.Tags)

    def test_operator_role_trust_policy(self):
        gen = NetworkConnectorGenerator(
            logical_id="MyConnector",
            vpc_config={"SubnetIds": ["subnet-abc"], "SecurityGroupIds": ["sg-123"], "NetworkProtocol": "IPv4"},
        )
        resources = gen.to_cloudformation()
        role = resources[0]

        statement = role.AssumeRolePolicyDocument["Statement"][0]
        self.assertEqual(statement["Principal"]["Service"], ["lambda.amazonaws.com"])

    def test_operator_role_policy(self):
        gen = NetworkConnectorGenerator(
            logical_id="MyConnector",
            vpc_config={"SubnetIds": ["subnet-abc"], "SecurityGroupIds": ["sg-123"], "NetworkProtocol": "IPv4"},
        )
        resources = gen.to_cloudformation()
        role = resources[0]

        managed_policy_arns = role.ManagedPolicyArns
        self.assertEqual(len(managed_policy_arns), 1)
        self.assertIn("AWSLambdaNetworkConnectorOperatorPolicy", managed_policy_arns[0])

    def test_operator_role_has_sam_marker_tag(self):
        gen = NetworkConnectorGenerator(
            logical_id="MyConnector",
            vpc_config={"SubnetIds": ["subnet-abc"], "SecurityGroupIds": ["sg-123"], "NetworkProtocol": "IPv4"},
            tags={"Team": "Platform"},
        )
        resources = gen.to_cloudformation()
        role = resources[0]

        self.assertIsNotNone(role.Tags)
        self.assertIn({"Key": "lambda:createdBy", "Value": "SAM"}, role.Tags)
