from typing import Optional, Dict, Any, List, Union
from samtranslator.model import PropertyType, Resource, PassThroughProperty
from samtranslator.model.types import IS_DICT, is_type, one_of, IS_STR, list_of, any_type
from samtranslator.model.intrinsics import fnGetAtt, ref
from samtranslator.utils.types import Intrinsicable


class LambdaFunction(Resource):
    resource_type = "AWS::Lambda::Function"
    property_types = {
        "Code": PropertyType(True, IS_DICT),
        "PackageType": PropertyType(False, IS_STR),
        "DeadLetterConfig": PropertyType(False, IS_DICT),
        "Description": PropertyType(False, IS_STR),
        "FunctionName": PropertyType(False, IS_STR),
        "Handler": PropertyType(False, IS_STR),
        "MemorySize": PropertyType(False, is_type(int)),
        "Role": PropertyType(False, IS_STR),
        "Runtime": PropertyType(False, IS_STR),
        "Timeout": PropertyType(False, is_type(int)),
        "VpcConfig": PropertyType(False, IS_DICT),
        "Environment": PropertyType(False, IS_DICT),
        "Tags": PropertyType(False, list_of(IS_DICT)),
        "TracingConfig": PropertyType(False, IS_DICT),
        "KmsKeyArn": PropertyType(False, one_of(IS_DICT, IS_STR)),
        "Layers": PropertyType(False, list_of(one_of(IS_STR, IS_DICT))),
        "ReservedConcurrentExecutions": PropertyType(False, any_type()),
        "FileSystemConfigs": PropertyType(False, list_of(IS_DICT)),
        "CodeSigningConfigArn": PropertyType(False, IS_STR),
        "ImageConfig": PropertyType(False, IS_DICT),
        "Architectures": PropertyType(False, list_of(one_of(IS_STR, IS_DICT))),
        "SnapStart": PropertyType(False, IS_DICT),
        "EphemeralStorage": PropertyType(False, IS_DICT),
        "RuntimeManagementConfig": PropertyType(False, IS_DICT),
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
        "CodeSha256": PropertyType(False, IS_STR),
        "Description": PropertyType(False, IS_STR),
        "FunctionName": PropertyType(True, one_of(IS_STR, IS_DICT)),
        "RuntimeManagementConfig": PropertyType(False, IS_DICT),
    }

    runtime_attrs = {
        "arn": lambda self: ref(self.logical_id),
        "version": lambda self: fnGetAtt(self.logical_id, "Version"),
    }


class LambdaAlias(Resource):
    resource_type = "AWS::Lambda::Alias"
    property_types = {
        "Description": PropertyType(False, IS_STR),
        "Name": PropertyType(False, IS_STR),
        "FunctionName": PropertyType(True, one_of(IS_STR, IS_DICT)),
        "FunctionVersion": PropertyType(True, one_of(IS_STR, IS_DICT)),
        "ProvisionedConcurrencyConfig": PropertyType(False, IS_DICT),
    }

    runtime_attrs = {"arn": lambda self: ref(self.logical_id)}


class LambdaEventSourceMapping(Resource):
    resource_type = "AWS::Lambda::EventSourceMapping"
    property_types = {
        "BatchSize": PropertyType(False, is_type(int)),
        "Enabled": PropertyType(False, is_type(bool)),
        "EventSourceArn": PropertyType(False, IS_STR),
        "FunctionName": PropertyType(True, IS_STR),
        "MaximumBatchingWindowInSeconds": PropertyType(False, is_type(int)),
        "MaximumRetryAttempts": PropertyType(False, is_type(int)),
        "BisectBatchOnFunctionError": PropertyType(False, is_type(bool)),
        "MaximumRecordAgeInSeconds": PropertyType(False, is_type(int)),
        "DestinationConfig": PropertyType(False, IS_DICT),
        "ParallelizationFactor": PropertyType(False, is_type(int)),
        "StartingPosition": PropertyType(False, IS_STR),
        "StartingPositionTimestamp": PassThroughProperty(False),
        "Topics": PropertyType(False, is_type(list)),
        "Queues": PropertyType(False, is_type(list)),
        "SourceAccessConfigurations": PropertyType(False, is_type(list)),
        "TumblingWindowInSeconds": PropertyType(False, is_type(int)),
        "FunctionResponseTypes": PropertyType(False, is_type(list)),
        "SelfManagedEventSource": PropertyType(False, IS_DICT),
        "FilterCriteria": PropertyType(False, IS_DICT),
        "AmazonManagedKafkaEventSourceConfig": PropertyType(False, IS_DICT),
        "SelfManagedKafkaEventSourceConfig": PropertyType(False, IS_DICT),
        "ScalingConfig": PropertyType(False, IS_DICT),
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id)}


class LambdaPermission(Resource):
    resource_type = "AWS::Lambda::Permission"
    property_types = {
        "Action": PropertyType(True, IS_STR),
        "FunctionName": PropertyType(True, IS_STR),
        "Principal": PropertyType(True, IS_STR),
        "SourceAccount": PropertyType(False, IS_STR),
        "SourceArn": PropertyType(False, IS_STR),
        "EventSourceToken": PropertyType(False, IS_STR),
        "FunctionUrlAuthType": PropertyType(False, IS_STR),
    }


class LambdaEventInvokeConfig(Resource):
    resource_type = "AWS::Lambda::EventInvokeConfig"
    property_types = {
        "DestinationConfig": PropertyType(False, IS_DICT),
        "FunctionName": PropertyType(True, IS_STR),
        "MaximumEventAgeInSeconds": PropertyType(False, is_type(int)),
        "MaximumRetryAttempts": PropertyType(False, is_type(int)),
        "Qualifier": PropertyType(True, IS_STR),
    }


class LambdaLayerVersion(Resource):
    """Lambda layer version resource"""

    resource_type = "AWS::Lambda::LayerVersion"
    property_types = {
        "Content": PropertyType(True, IS_DICT),
        "Description": PropertyType(False, IS_STR),
        "LayerName": PropertyType(False, IS_STR),
        "CompatibleArchitectures": PropertyType(False, list_of(one_of(IS_STR, IS_DICT))),
        "CompatibleRuntimes": PropertyType(False, list_of(one_of(IS_STR, IS_DICT))),
        "LicenseInfo": PropertyType(False, IS_STR),
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
        "TargetFunctionArn": PropertyType(True, one_of(IS_STR, IS_DICT)),
        "AuthType": PropertyType(True, IS_STR),
        "Cors": PropertyType(False, IS_DICT),
    }
