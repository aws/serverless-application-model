from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, is_str, list_of, one_of

class SyntheticsCanary(Resource):
    resource_type = "AWS::Synthetics::Canary"

    property_types = {
        "ArtifactS3Location": PropertyType(True, is_str()),
        "Code": PropertyType(True, is_type(dict)),
        "ExecutionRoleArn": PropertyType(True, is_str()),
        "FailureRetentionPeriod": PropertyType(False, is_type(int)),
        "Name": PropertyType(True, is_str()),
        "RunConfig": PropertyType(False, is_type(dict)),
        "RuntimeVersion": PropertyType(True, is_str()),
        "Schedule": PropertyType(True, is_type(dict)),
        "StartCanaryAfterCreation": PropertyType(True, is_type(bool)),
        "SuccessRetentionPeriod": PropertyType(False, is_type(int)),
        "Tags": PropertyType(False, list_of(is_type(dict))),
        "VPCConfig": PropertyType(False, is_type(dict)),
    }