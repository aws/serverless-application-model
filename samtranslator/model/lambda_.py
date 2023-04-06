from typing import Any, Dict, List, Optional, Union

from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt, ref
from samtranslator.utils.types import Intrinsicable


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
    }

    Code: Dict[str, Any]
    PackageType: Optional[str]
    DeadLetterConfig: Optional[Dict[str, Any]]
    Description: Optional[Intrinsicable[str]]
    FunctionName: Optional[Intrinsicable[str]]
    Handler: Optional[str]
    MemorySize: Optional[Intrinsicable[int]]
    Role: Optional[Intrinsicable[str]]
    Runtime: Optional[str]
    Timeout: Optional[Intrinsicable[int]]
    VpcConfig: Optional[Dict[str, Any]]
    Environment: Optional[Dict[str, Any]]
    Tags: Optional[List[Dict[str, Any]]]
    TracingConfig: Optional[Dict[str, Any]]
    KmsKeyArn: Optional[Intrinsicable[str]]
    Layers: Optional[List[Any]]
    ReservedConcurrentExecutions: Optional[Any]
    FileSystemConfigs: Optional[Dict[str, Any]]
    CodeSigningConfigArn: Optional[Intrinsicable[str]]
    ImageConfig: Optional[Dict[str, Any]]
    Architectures: Optional[List[Any]]
    SnapStart: Optional[Dict[str, Any]]
    EphemeralStorage: Optional[Dict[str, Any]]
    RuntimeManagementConfig: Optional[Dict[str, Any]]

    runtime_attrs = {"name": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}


class LambdaVersion(Resource):
    resource_type = "AWS::Lambda::Version"
    property_types = {
        "CodeSha256": GeneratedProperty(),
        "Description": GeneratedProperty(),
        "FunctionName": GeneratedProperty(),
        "RuntimeManagementConfig": GeneratedProperty(),
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
        "AmazonManagedKafkaEventSourceConfig": GeneratedProperty(),
        "SelfManagedKafkaEventSourceConfig": GeneratedProperty(),
        "ScalingConfig": GeneratedProperty(),
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

    Content: Dict[str, Any]
    Description: Optional[Intrinsicable[str]]
    LayerName: Optional[Intrinsicable[str]]
    CompatibleArchitectures: Optional[List[Union[str, Dict[str, Any]]]]
    CompatibleRuntimes: Optional[List[Union[str, Dict[str, Any]]]]
    LicenseInfo: Optional[Intrinsicable[str]]

    runtime_attrs = {"name": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}


class LambdaUrl(Resource):
    resource_type = "AWS::Lambda::Url"
    property_types = {
        "TargetFunctionArn": GeneratedProperty(),
        "AuthType": GeneratedProperty(),
        "Cors": GeneratedProperty(),
        "InvokeMode": GeneratedProperty(),
    }
