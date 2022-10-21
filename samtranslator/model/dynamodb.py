from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, dict_of, list_of, is_str, one_of
from samtranslator.model.intrinsics import fnGetAtt, ref


class DynamoDBTable(Resource):
    resource_type = "AWS::DynamoDB::Table"
    property_types = {
        "AttributeDefinitions": PropertyType(True, list_of(is_type(dict))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call]
        "GlobalSecondaryIndexes": PropertyType(False, list_of(is_type(dict))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call]
        "KeySchema": PropertyType(False, list_of(is_type(dict))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call]
        "LocalSecondaryIndexes": PropertyType(False, list_of(is_type(dict))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call]
        "ProvisionedThroughput": PropertyType(False, dict_of(is_str(), one_of(is_type(int), is_type(dict)))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call, no-untyped-call, no-untyped-call]
        "StreamSpecification": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "TableName": PropertyType(False, one_of(is_str(), is_type(dict))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call, no-untyped-call]
        "Tags": PropertyType(False, list_of(is_type(dict))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call]
        "SSESpecification": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "BillingMode": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
    }

    runtime_attrs = {
        "name": lambda self: ref(self.logical_id),  # type: ignore[no-untyped-call]
        "arn": lambda self: fnGetAtt(self.logical_id, "Arn"),  # type: ignore[no-untyped-call]
        "stream_arn": lambda self: fnGetAtt(self.logical_id, "StreamArn"),  # type: ignore[no-untyped-call]
    }
