from typing import Any, Dict, List, Optional, Union

from samtranslator.model import PassThroughProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt, ref
from samtranslator.utils.types import Intrinsicable


class LambdaFunction(Resource):
    resource_type = "AWS::Lambda::Function"
    property_types = {
        "Code": PassThroughProperty(True),
        "PackageType": PassThroughProperty(False),
        "DeadLetterConfig": PassThroughProperty(False),
        "Description": PassThroughProperty(False),
        "FunctionName": PassThroughProperty(False),
        "Handler": PassThroughProperty(False),
        "MemorySize": PassThroughProperty(False),
        "Role": PassThroughProperty(False),
        "Runtime": PassThroughProperty(False),
        "Timeout": PassThroughProperty(False),
        "VpcConfig": PassThroughProperty(False),
        "Environment": PassThroughProperty(False),
        "Tags": PassThroughProperty(False),
        "TracingConfig": PassThroughProperty(False),
        "KmsKeyArn": PassThroughProperty(False),
        "Layers": PassThroughProperty(False),
        "ReservedConcurrentExecutions": PassThroughProperty(False),
        "FileSystemConfigs": PassThroughProperty(False),
        "CodeSigningConfigArn": PassThroughProperty(False),
        "ImageConfig": PassThroughProperty(False),
        "Architectures": PassThroughProperty(False),
        "SnapStart": PassThroughProperty(False),
        "EphemeralStorage": PassThroughProperty(False),
        "RuntimeManagementConfig": PassThroughProperty(False),
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
        "CodeSha256": PassThroughProperty(False),
        "Description": PassThroughProperty(False),
        "FunctionName": PassThroughProperty(True),
        "RuntimeManagementConfig": PassThroughProperty(False),
    }

    runtime_attrs = {
        "arn": lambda self: ref(self.logical_id),
        "version": lambda self: fnGetAtt(self.logical_id, "Version"),
    }


class LambdaAlias(Resource):
    resource_type = "AWS::Lambda::Alias"
    property_types = {
        "Description": PassThroughProperty(False),
        "Name": PassThroughProperty(False),
        "FunctionName": PassThroughProperty(True),
        "FunctionVersion": PassThroughProperty(True),
        "ProvisionedConcurrencyConfig": PassThroughProperty(False),
    }

    runtime_attrs = {"arn": lambda self: ref(self.logical_id)}


class LambdaEventSourceMapping(Resource):
    resource_type = "AWS::Lambda::EventSourceMapping"
    property_types = {
        "BatchSize": PassThroughProperty(False),
        "Enabled": PassThroughProperty(False),
        "EventSourceArn": PassThroughProperty(False),
        "FunctionName": PassThroughProperty(True),
        "MaximumBatchingWindowInSeconds": PassThroughProperty(False),
        "MaximumRetryAttempts": PassThroughProperty(False),
        "BisectBatchOnFunctionError": PassThroughProperty(False),
        "MaximumRecordAgeInSeconds": PassThroughProperty(False),
        "DestinationConfig": PassThroughProperty(False),
        "ParallelizationFactor": PassThroughProperty(False),
        "StartingPosition": PassThroughProperty(False),
        "StartingPositionTimestamp": PassThroughProperty(False),
        "Topics": PassThroughProperty(False),
        "Queues": PassThroughProperty(False),
        "SourceAccessConfigurations": PassThroughProperty(False),
        "TumblingWindowInSeconds": PassThroughProperty(False),
        "FunctionResponseTypes": PassThroughProperty(False),
        "SelfManagedEventSource": PassThroughProperty(False),
        "FilterCriteria": PassThroughProperty(False),
        "AmazonManagedKafkaEventSourceConfig": PassThroughProperty(False),
        "SelfManagedKafkaEventSourceConfig": PassThroughProperty(False),
        "ScalingConfig": PassThroughProperty(False),
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id)}


class LambdaPermission(Resource):
    resource_type = "AWS::Lambda::Permission"
    property_types = {
        "Action": PassThroughProperty(True),
        "FunctionName": PassThroughProperty(True),
        "Principal": PassThroughProperty(True),
        "SourceAccount": PassThroughProperty(False),
        "SourceArn": PassThroughProperty(False),
        "EventSourceToken": PassThroughProperty(False),
        "FunctionUrlAuthType": PassThroughProperty(False),
    }


class LambdaEventInvokeConfig(Resource):
    resource_type = "AWS::Lambda::EventInvokeConfig"
    property_types = {
        "DestinationConfig": PassThroughProperty(False),
        "FunctionName": PassThroughProperty(True),
        "MaximumEventAgeInSeconds": PassThroughProperty(False),
        "MaximumRetryAttempts": PassThroughProperty(False),
        "Qualifier": PassThroughProperty(True),
    }


class LambdaLayerVersion(Resource):
    """Lambda layer version resource"""

    resource_type = "AWS::Lambda::LayerVersion"
    property_types = {
        "Content": PassThroughProperty(True),
        "Description": PassThroughProperty(False),
        "LayerName": PassThroughProperty(False),
        "CompatibleArchitectures": PassThroughProperty(False),
        "CompatibleRuntimes": PassThroughProperty(False),
        "LicenseInfo": PassThroughProperty(False),
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
        "TargetFunctionArn": PassThroughProperty(True),
        "AuthType": PassThroughProperty(True),
        "Cors": PassThroughProperty(False),
    }
