from unittest import TestCase

from samtranslator.model.network_connector.resources import LambdaNetworkConnector


class TestLambdaNetworkConnector(TestCase):
    def test_resource_type(self):
        connector = LambdaNetworkConnector("MyConnector")
        self.assertEqual(connector.resource_type, "AWS::Lambda::NetworkConnector")

    def test_properties(self):
        connector = LambdaNetworkConnector("MyConnector")

        connector.Name = "prod-vpc"
        connector.Configuration = {
            "VpcEgressConfiguration": {
                "SubnetIds": ["subnet-abc"],
                "SecurityGroupIds": ["sg-123"],
                "NetworkProtocol": "IPv4",
                "AssociatedComputeResourceTypes": ["MicroVm"],
            }
        }
        connector.OperatorRole = "arn:aws:iam::123456789012:role/OperatorRole"
        connector.Tags = [
            {"Key": "lambda:createdBy", "Value": "SAM"},
            {"Key": "Environment", "Value": "Production"},
        ]

        self.assertEqual(connector.Name, "prod-vpc")
        self.assertEqual(
            connector.Configuration["VpcEgressConfiguration"]["AssociatedComputeResourceTypes"], ["MicroVm"]
        )
        self.assertEqual(connector.OperatorRole, "arn:aws:iam::123456789012:role/OperatorRole")
        self.assertEqual(len(connector.Tags), 2)
