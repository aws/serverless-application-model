from typing import Any, Dict, List, Optional, Union

from samtranslator.model import GeneratedProperty, GeneratedProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt, ref
from samtranslator.utils.types import Intrinsicable


class LambdaFunction(Resource):
    resource_type = "AWS::Lambda::Function"
    property_types = {
        "Code": GeneratedProperty(True),
        "PackageType": GeneratedProperty(False),
        "DeadLetterConfig": GeneratedProperty(False),
        "Description": GeneratedProperty(False),
        "FunctionName": GeneratedProperty(False),
        "Handler": GeneratedProperty(False),
        "MemorySize": GeneratedProperty(False),
        "Role": GeneratedProperty(False),
        "Runtime": GeneratedProperty(False),
        "Timeout": GeneratedProperty(False),
        "VpcConfig": GeneratedProperty(False),
        "Environment": GeneratedProperty(False),
        "Tags": GeneratedProperty(False),
        "TracingConfig": GeneratedProperty(False),
        "KmsKeyArn": GeneratedProperty(False),
        "Layers": GeneratedProperty(False),
        "ReservedConcurrentExecutions": GeneratedProperty(False),
        "FileSystemConfigs": GeneratedProperty(False),
        "CodeSigningConfigArn": GeneratedProperty(False),
        "ImageConfig": GeneratedProperty(False),
        "Architectures": GeneratedProperty(False),
        "SnapStart": GeneratedProperty(False),
        "EphemeralStorage": GeneratedProperty(False),
        "RuntimeManagementConfig": GeneratedProperty(False),
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
        "CodeSha256": GeneratedProperty(False),
        "Description": GeneratedProperty(False),
        "FunctionName": GeneratedProperty(True),
        "RuntimeManagementConfig": GeneratedProperty(False),
    }

    runtime_attrs = {
        "arn": lambda self: ref(self.logical_id),
        "version": lambda self: fnGetAtt(self.logical_id, "Version"),
    }


class LambdaAlias(Resource):
    resource_type = "AWS::Lambda::Alias"
    property_types = {
        "Description": GeneratedProperty(False),
        "Name": GeneratedProperty(False),
        "FunctionName": GeneratedProperty(True),
        "FunctionVersion": GeneratedProperty(True),
        "ProvisionedConcurrencyConfig": GeneratedProperty(False),
    }

    runtime_attrs = {"arn": lambda self: ref(self.logical_id)}


class LambdaEventSourceMapping(Resource):
    resource_type = "AWS::Lambda::EventSourceMapping"
    property_types = {
        "BatchSize": GeneratedProperty(False),
        "Enabled": GeneratedProperty(False),
        "EventSourceArn": GeneratedProperty(False),
        "FunctionName": GeneratedProperty(True),
        "MaximumBatchingWindowInSeconds": GeneratedProperty(False),
        "MaximumRetryAttempts": GeneratedProperty(False),
        "BisectBatchOnFunctionError": GeneratedProperty(False),
        "MaximumRecordAgeInSeconds": GeneratedProperty(False),
        "DestinationConfig": GeneratedProperty(False),
        "ParallelizationFactor": GeneratedProperty(False),
        "StartingPosition": GeneratedProperty(False),
        "StartingPositionTimestamp": GeneratedProperty(False),
        "Topics": GeneratedProperty(False),
        "Queues": GeneratedProperty(False),
        "SourceAccessConfigurations": GeneratedProperty(False),
        "TumblingWindowInSeconds": GeneratedProperty(False),
        "FunctionResponseTypes": GeneratedProperty(False),
        "SelfManagedEventSource": GeneratedProperty(False),
        "FilterCriteria": GeneratedProperty(False),
        "AmazonManagedKafkaEventSourceConfig": GeneratedProperty(False),
        "SelfManagedKafkaEventSourceConfig": GeneratedProperty(False),
        "ScalingConfig": GeneratedProperty(False),
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id)}


class LambdaPermission(Resource):
    resource_type = "AWS::Lambda::Permission"
    property_types = {
        "Action": GeneratedProperty(True),
        "FunctionName": GeneratedProperty(True),
        "Principal": GeneratedProperty(True),
        "SourceAccount": GeneratedProperty(False),
        "SourceArn": GeneratedProperty(False),
        "EventSourceToken": GeneratedProperty(False),
        "FunctionUrlAuthType": GeneratedProperty(False),
    }


class LambdaEventInvokeConfig(Resource):
    resource_type = "AWS::Lambda::EventInvokeConfig"
    property_types = {
        "DestinationConfig": GeneratedProperty(False),
        "FunctionName": GeneratedProperty(True),
        "MaximumEventAgeInSeconds": GeneratedProperty(False),
        "MaximumRetryAttempts": GeneratedProperty(False),
        "Qualifier": GeneratedProperty(True),
    }


class LambdaLayerVersion(Resource):
    """Lambda layer version resource"""

    resource_type = "AWS::Lambda::LayerVersion"
    property_types = {
        "Content": GeneratedProperty(True),
        "Description": GeneratedProperty(False),
        "LayerName": GeneratedProperty(False),
        "CompatibleArchitectures": GeneratedProperty(False),
        "CompatibleRuntimes": GeneratedProperty(False),
        "LicenseInfo": GeneratedProperty(False),
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
        "TargetFunctionArn": GeneratedProperty(True),
        "AuthType": GeneratedProperty(True),
        "Cors": GeneratedProperty(False),
    }
