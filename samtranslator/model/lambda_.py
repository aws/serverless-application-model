from typing import Any, Union

from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt, ref
from samtranslator.utils.types import Intrinsicable

LAMBDA_TRACING_CONFIG_DISABLED = "Disabled"


class LambdaFunction(Resource):
    resource_type = "AWS::Lambda::Function"
    property_types = {
        "Code": GeneratedProperty(),
        "PackageType": GeneratedProperty(),
        "DeadLetterConfig": GeneratedProperty(),
        "Description": GeneratedProperty(),
        "FunctionName": GeneratedProperty(),
        "Handler": GeneratedProperty(),
        "MemorySize": GeneratedProperty(),
        "Role": GeneratedProperty(),
        "Runtime": GeneratedProperty(),
        "Timeout": GeneratedProperty(),
        "VpcConfig": GeneratedProperty(),
        "Environment": GeneratedProperty(),
        "Tags": GeneratedProperty(),
        "TracingConfig": GeneratedProperty(),
        "KmsKeyArn": GeneratedProperty(),
        "Layers": GeneratedProperty(),
        "ReservedConcurrentExecutions": GeneratedProperty(),
        "FileSystemConfigs": GeneratedProperty(),
        "CodeSigningConfigArn": GeneratedProperty(),
        "ImageConfig": GeneratedProperty(),
        "Architectures": GeneratedProperty(),
        "SnapStart": GeneratedProperty(),
        "EphemeralStorage": GeneratedProperty(),
        "RuntimeManagementConfig": GeneratedProperty(),
        "LoggingConfig": GeneratedProperty(),
        "RecursiveLoop": GeneratedProperty(),
        "CapacityProviderConfig": GeneratedProperty(),
        "FunctionScalingConfig": GeneratedProperty(),
        "PublishToLatestPublished": GeneratedProperty(),
        "TenancyConfig": GeneratedProperty(),
        "DurableConfig": GeneratedProperty(),
    }

    Code: dict[str, Any]
    PackageType: str | None
    DeadLetterConfig: dict[str, Any] | None
    Description: Intrinsicable[str] | None
    FunctionName: Intrinsicable[str] | None
    Handler: str | None
    MemorySize: Intrinsicable[int] | None
    Role: Intrinsicable[str] | None
    Runtime: str | None
    Timeout: Intrinsicable[int] | None
    VpcConfig: dict[str, Any] | None
    Environment: dict[str, Any] | None
    Tags: list[dict[str, Any]] | None
    TracingConfig: dict[str, Any] | None
    KmsKeyArn: Intrinsicable[str] | None
    Layers: list[Any] | None
    ReservedConcurrentExecutions: Any | None
    FileSystemConfigs: dict[str, Any] | None
    CodeSigningConfigArn: Intrinsicable[str] | None
    ImageConfig: dict[str, Any] | None
    Architectures: list[Any] | None
    SnapStart: dict[str, Any] | None
    EphemeralStorage: dict[str, Any] | None
    RuntimeManagementConfig: dict[str, Any] | None
    LoggingConfig: dict[str, Any] | None
    RecursiveLoop: str | None
    CapacityProviderConfig: dict[str, Any] | None
    FunctionScalingConfig: dict[str, Any] | None
    PublishToLatestPublished: dict[str, Any] | None
    TenancyConfig: dict[str, Any] | None
    DurableConfig: dict[str, Any] | None

    runtime_attrs = {"name": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}


class LambdaVersion(Resource):
    resource_type = "AWS::Lambda::Version"
    property_types = {
        "CodeSha256": GeneratedProperty(),
        "Description": GeneratedProperty(),
        "FunctionName": GeneratedProperty(),
        "FunctionScalingConfig": GeneratedProperty(),
    }

    runtime_attrs = {
        "arn": lambda self: ref(self.logical_id),
        "version": lambda self: fnGetAtt(self.logical_id, "Version"),
    }


class LambdaAlias(Resource):
    resource_type = "AWS::Lambda::Alias"
    property_types = {
        "Description": GeneratedProperty(),
        "Name": GeneratedProperty(),
        "FunctionName": GeneratedProperty(),
        "FunctionVersion": GeneratedProperty(),
        "ProvisionedConcurrencyConfig": GeneratedProperty(),
    }

    runtime_attrs = {"arn": lambda self: ref(self.logical_id)}


class LambdaEventSourceMapping(Resource):
    resource_type = "AWS::Lambda::EventSourceMapping"
    property_types = {
        "BatchSize": GeneratedProperty(),
        "DocumentDBEventSourceConfig": GeneratedProperty(),
        "Enabled": GeneratedProperty(),
        "EventSourceArn": GeneratedProperty(),
        "FunctionName": GeneratedProperty(),
        "MaximumBatchingWindowInSeconds": GeneratedProperty(),
        "MaximumRetryAttempts": GeneratedProperty(),
        "BisectBatchOnFunctionError": GeneratedProperty(),
        "MaximumRecordAgeInSeconds": GeneratedProperty(),
        "DestinationConfig": GeneratedProperty(),
        "ParallelizationFactor": GeneratedProperty(),
        "StartingPosition": GeneratedProperty(),
        "StartingPositionTimestamp": GeneratedProperty(),
        "Topics": GeneratedProperty(),
        "Queues": GeneratedProperty(),
        "SourceAccessConfigurations": GeneratedProperty(),
        "TumblingWindowInSeconds": GeneratedProperty(),
        "FunctionResponseTypes": GeneratedProperty(),
        "SelfManagedEventSource": GeneratedProperty(),
        "FilterCriteria": GeneratedProperty(),
        "KmsKeyArn": GeneratedProperty(),
        "AmazonManagedKafkaEventSourceConfig": GeneratedProperty(),
        "SelfManagedKafkaEventSourceConfig": GeneratedProperty(),
        "ScalingConfig": GeneratedProperty(),
        "ProvisionedPollerConfig": GeneratedProperty(),
        "MetricsConfig": GeneratedProperty(),
        "LoggingConfig": GeneratedProperty(),
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id)}


class LambdaPermission(Resource):
    resource_type = "AWS::Lambda::Permission"
    property_types = {
        "Action": GeneratedProperty(),
        "FunctionName": GeneratedProperty(),
        "Principal": GeneratedProperty(),
        "SourceAccount": GeneratedProperty(),
        "SourceArn": GeneratedProperty(),
        "EventSourceToken": GeneratedProperty(),
        "FunctionUrlAuthType": GeneratedProperty(),
        "InvokedViaFunctionUrl": GeneratedProperty(),
    }


class LambdaEventInvokeConfig(Resource):
    resource_type = "AWS::Lambda::EventInvokeConfig"
    property_types = {
        "DestinationConfig": GeneratedProperty(),
        "FunctionName": GeneratedProperty(),
        "MaximumEventAgeInSeconds": GeneratedProperty(),
        "MaximumRetryAttempts": GeneratedProperty(),
        "Qualifier": GeneratedProperty(),
    }


class LambdaLayerVersion(Resource):
    """Lambda layer version resource"""

    resource_type = "AWS::Lambda::LayerVersion"
    property_types = {
        "Content": GeneratedProperty(),
        "Description": GeneratedProperty(),
        "LayerName": GeneratedProperty(),
        "CompatibleArchitectures": GeneratedProperty(),
        "CompatibleRuntimes": GeneratedProperty(),
        "LicenseInfo": GeneratedProperty(),
    }

    Content: dict[str, Any]
    Description: Intrinsicable[str] | None
    LayerName: Intrinsicable[str] | None
    CompatibleArchitectures: list[Union[str, dict[str, Any]]] | None
    CompatibleRuntimes: list[Union[str, dict[str, Any]]] | None
    LicenseInfo: Intrinsicable[str] | None

    runtime_attrs = {"name": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}


class LambdaUrl(Resource):
    resource_type = "AWS::Lambda::Url"
    property_types = {
        "TargetFunctionArn": GeneratedProperty(),
        "AuthType": GeneratedProperty(),
        "Cors": GeneratedProperty(),
        "InvokeMode": GeneratedProperty(),
    }
