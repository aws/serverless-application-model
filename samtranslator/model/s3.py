from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, is_str, any_type
from samtranslator.model.intrinsics import ref, fnGetAtt


class S3Bucket(Resource):
    resource_type = "AWS::S3::Bucket"
    property_types = {
        "AccessControl": PropertyType(False, any_type()),
        "AccelerateConfiguration": PropertyType(False, any_type()),
        "AnalyticsConfigurations": PropertyType(False, any_type()),
        "BucketEncryption": PropertyType(False, any_type()),
        "BucketName": PropertyType(False, is_str()),
        "CorsConfiguration": PropertyType(False, any_type()),
        "IntelligentTieringConfigurations": PropertyType(False, any_type()),
        "InventoryConfigurations": PropertyType(False, any_type()),
        "LifecycleConfiguration": PropertyType(False, any_type()),
        "LoggingConfiguration": PropertyType(False, any_type()),
        "MetricsConfigurations": PropertyType(False, any_type()),
        "NotificationConfiguration": PropertyType(False, is_type(dict)),
        "ObjectLockConfiguration": PropertyType(False, any_type()),
        "ObjectLockEnabled": PropertyType(False, any_type()),
        "OwnershipControls": PropertyType(False, any_type()),
        "PublicAccessBlockConfiguration": PropertyType(False, is_type(dict)),
        "ReplicationConfiguration": PropertyType(False, any_type()),
        "Tags": PropertyType(False, is_type(list)),
        "VersioningConfiguration": PropertyType(False, any_type()),
        "WebsiteConfiguration": PropertyType(False, any_type()),
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}
