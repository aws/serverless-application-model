from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt, ref


class DynamoDBTable(Resource):
    resource_type = "AWS::DynamoDB::Table"
    property_types = {
        "AttributeDefinitions": GeneratedProperty(),
        "GlobalSecondaryIndexes": GeneratedProperty(),
        "KeySchema": GeneratedProperty(),
        "LocalSecondaryIndexes": GeneratedProperty(),
        "PointInTimeRecoverySpecification": GeneratedProperty(),
        "ProvisionedThroughput": GeneratedProperty(),
        "StreamSpecification": GeneratedProperty(),
        "TableName": GeneratedProperty(),
        "Tags": GeneratedProperty(),
        "SSESpecification": GeneratedProperty(),
        "BillingMode": GeneratedProperty(),
    }

    runtime_attrs = {
        "name": lambda self: ref(self.logical_id),
        "arn": lambda self: fnGetAtt(self.logical_id, "Arn"),
        "stream_arn": lambda self: fnGetAtt(self.logical_id, "StreamArn"),
    }
