from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, is_str, any_type
from samtranslator.model.intrinsics import ref, fnGetAtt


class S3Bucket(Resource):
    resource_type = "AWS::S3::Bucket"
    property_types = {
        "AccessControl": PropertyType(False, any_type()),  # type: ignore[no-untyped-call, no-untyped-call]
        "AccelerateConfiguration": PropertyType(False, any_type()),  # type: ignore[no-untyped-call, no-untyped-call]
        "AnalyticsConfigurations": PropertyType(False, any_type()),  # type: ignore[no-untyped-call, no-untyped-call]
        "BucketEncryption": PropertyType(False, any_type()),  # type: ignore[no-untyped-call, no-untyped-call]
        "BucketName": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "CorsConfiguration": PropertyType(False, any_type()),  # type: ignore[no-untyped-call, no-untyped-call]
        "IntelligentTieringConfigurations": PropertyType(False, any_type()),  # type: ignore[no-untyped-call, no-untyped-call]
        "InventoryConfigurations": PropertyType(False, any_type()),  # type: ignore[no-untyped-call, no-untyped-call]
        "LifecycleConfiguration": PropertyType(False, any_type()),  # type: ignore[no-untyped-call, no-untyped-call]
        "LoggingConfiguration": PropertyType(False, any_type()),  # type: ignore[no-untyped-call, no-untyped-call]
        "MetricsConfigurations": PropertyType(False, any_type()),  # type: ignore[no-untyped-call, no-untyped-call]
        "NotificationConfiguration": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "ObjectLockConfiguration": PropertyType(False, any_type()),  # type: ignore[no-untyped-call, no-untyped-call]
        "ObjectLockEnabled": PropertyType(False, any_type()),  # type: ignore[no-untyped-call, no-untyped-call]
        "OwnershipControls": PropertyType(False, any_type()),  # type: ignore[no-untyped-call, no-untyped-call]
        "PublicAccessBlockConfiguration": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "ReplicationConfiguration": PropertyType(False, any_type()),  # type: ignore[no-untyped-call, no-untyped-call]
        "Tags": PropertyType(False, is_type(list)),  # type: ignore[no-untyped-call, no-untyped-call]
        "VersioningConfiguration": PropertyType(False, any_type()),  # type: ignore[no-untyped-call, no-untyped-call]
        "WebsiteConfiguration": PropertyType(False, any_type()),  # type: ignore[no-untyped-call, no-untyped-call]
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}  # type: ignore[no-untyped-call, no-untyped-call]
