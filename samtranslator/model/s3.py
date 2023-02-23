from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt, ref


class S3Bucket(Resource):
    resource_type = "AWS::S3::Bucket"
    property_types = {
        "AccessControl": GeneratedProperty(),
        "AccelerateConfiguration": GeneratedProperty(),
        "AnalyticsConfigurations": GeneratedProperty(),
        "BucketEncryption": GeneratedProperty(),
        "BucketName": GeneratedProperty(),
        "CorsConfiguration": GeneratedProperty(),
        "IntelligentTieringConfigurations": GeneratedProperty(),
        "InventoryConfigurations": GeneratedProperty(),
        "LifecycleConfiguration": GeneratedProperty(),
        "LoggingConfiguration": GeneratedProperty(),
        "MetricsConfigurations": GeneratedProperty(),
        "NotificationConfiguration": GeneratedProperty(),
        "ObjectLockConfiguration": GeneratedProperty(),
        "ObjectLockEnabled": GeneratedProperty(),
        "OwnershipControls": GeneratedProperty(),
        "PublicAccessBlockConfiguration": GeneratedProperty(),
        "ReplicationConfiguration": GeneratedProperty(),
        "Tags": GeneratedProperty(),
        "VersioningConfiguration": GeneratedProperty(),
        "WebsiteConfiguration": GeneratedProperty(),
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}
