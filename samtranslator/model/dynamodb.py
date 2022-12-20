from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import IS_DICT, is_type, dict_of, list_of, IS_STR, one_of
from samtranslator.model.intrinsics import fnGetAtt, ref


class DynamoDBTable(Resource):
    resource_type = "AWS::DynamoDB::Table"
    property_types = {
        "AttributeDefinitions": PropertyType(True, list_of(IS_DICT)),
        "GlobalSecondaryIndexes": PropertyType(False, list_of(IS_DICT)),
        "KeySchema": PropertyType(False, list_of(IS_DICT)),
        "LocalSecondaryIndexes": PropertyType(False, list_of(IS_DICT)),
        "ProvisionedThroughput": PropertyType(False, dict_of(IS_STR, one_of(is_type(int), IS_DICT))),
        "StreamSpecification": PropertyType(False, IS_DICT),
        "TableName": PropertyType(False, one_of(IS_STR, IS_DICT)),
        "Tags": PropertyType(False, list_of(IS_DICT)),
        "SSESpecification": PropertyType(False, IS_DICT),
        "BillingMode": PropertyType(False, IS_STR),
    }

    runtime_attrs = {
        "name": lambda self: ref(self.logical_id),
        "arn": lambda self: fnGetAtt(self.logical_id, "Arn"),
        "stream_arn": lambda self: fnGetAtt(self.logical_id, "StreamArn"),
    }
