from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, one_of, is_str, list_of, any_type
from samtranslator.model.intrinsics import fnGetAtt, ref


class LambdaFunction(Resource):
    resource_type = "AWS::Lambda::Function"
    property_types = {
        "Code": PropertyType(True, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "PackageType": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "DeadLetterConfig": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "Description": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "FunctionName": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "Handler": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "MemorySize": PropertyType(False, is_type(int)),  # type: ignore[no-untyped-call, no-untyped-call]
        "Role": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "Runtime": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "Timeout": PropertyType(False, is_type(int)),  # type: ignore[no-untyped-call, no-untyped-call]
        "VpcConfig": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "Environment": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "Tags": PropertyType(False, list_of(is_type(dict))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call]
        "TracingConfig": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "KmsKeyArn": PropertyType(False, one_of(is_type(dict), is_str())),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call, no-untyped-call]
        "Layers": PropertyType(False, list_of(one_of(is_str(), is_type(dict)))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call, no-untyped-call, no-untyped-call]
        "ReservedConcurrentExecutions": PropertyType(False, any_type()),  # type: ignore[no-untyped-call, no-untyped-call]
        "FileSystemConfigs": PropertyType(False, list_of(is_type(dict))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call]
        "CodeSigningConfigArn": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "ImageConfig": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "Architectures": PropertyType(False, list_of(one_of(is_str(), is_type(dict)))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call, no-untyped-call, no-untyped-call]
        "EphemeralStorage": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}  # type: ignore[no-untyped-call, no-untyped-call]


class LambdaVersion(Resource):
    resource_type = "AWS::Lambda::Version"
    property_types = {
        "CodeSha256": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "Description": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "FunctionName": PropertyType(True, one_of(is_str(), is_type(dict))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call, no-untyped-call]
    }

    runtime_attrs = {
        "arn": lambda self: ref(self.logical_id),  # type: ignore[no-untyped-call]
        "version": lambda self: fnGetAtt(self.logical_id, "Version"),  # type: ignore[no-untyped-call]
    }


class LambdaAlias(Resource):
    resource_type = "AWS::Lambda::Alias"
    property_types = {
        "Description": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "Name": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "FunctionName": PropertyType(True, one_of(is_str(), is_type(dict))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call, no-untyped-call]
        "FunctionVersion": PropertyType(True, one_of(is_str(), is_type(dict))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call, no-untyped-call]
        "ProvisionedConcurrencyConfig": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
    }

    runtime_attrs = {"arn": lambda self: ref(self.logical_id)}  # type: ignore[no-untyped-call]


class LambdaEventSourceMapping(Resource):
    resource_type = "AWS::Lambda::EventSourceMapping"
    property_types = {
        "BatchSize": PropertyType(False, is_type(int)),  # type: ignore[no-untyped-call, no-untyped-call]
        "Enabled": PropertyType(False, is_type(bool)),  # type: ignore[no-untyped-call, no-untyped-call]
        "EventSourceArn": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "FunctionName": PropertyType(True, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "MaximumBatchingWindowInSeconds": PropertyType(False, is_type(int)),  # type: ignore[no-untyped-call, no-untyped-call]
        "MaximumRetryAttempts": PropertyType(False, is_type(int)),  # type: ignore[no-untyped-call, no-untyped-call]
        "BisectBatchOnFunctionError": PropertyType(False, is_type(bool)),  # type: ignore[no-untyped-call, no-untyped-call]
        "MaximumRecordAgeInSeconds": PropertyType(False, is_type(int)),  # type: ignore[no-untyped-call, no-untyped-call]
        "DestinationConfig": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "ParallelizationFactor": PropertyType(False, is_type(int)),  # type: ignore[no-untyped-call, no-untyped-call]
        "StartingPosition": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "Topics": PropertyType(False, is_type(list)),  # type: ignore[no-untyped-call, no-untyped-call]
        "Queues": PropertyType(False, is_type(list)),  # type: ignore[no-untyped-call, no-untyped-call]
        "SourceAccessConfigurations": PropertyType(False, is_type(list)),  # type: ignore[no-untyped-call, no-untyped-call]
        "TumblingWindowInSeconds": PropertyType(False, is_type(int)),  # type: ignore[no-untyped-call, no-untyped-call]
        "FunctionResponseTypes": PropertyType(False, is_type(list)),  # type: ignore[no-untyped-call, no-untyped-call]
        "SelfManagedEventSource": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "FilterCriteria": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "AmazonManagedKafkaEventSourceConfig": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "SelfManagedKafkaEventSourceConfig": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id)}  # type: ignore[no-untyped-call]


class LambdaPermission(Resource):
    resource_type = "AWS::Lambda::Permission"
    property_types = {
        "Action": PropertyType(True, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "FunctionName": PropertyType(True, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "Principal": PropertyType(True, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "SourceAccount": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "SourceArn": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "EventSourceToken": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "FunctionUrlAuthType": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
    }


class LambdaEventInvokeConfig(Resource):
    resource_type = "AWS::Lambda::EventInvokeConfig"
    property_types = {
        "DestinationConfig": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "FunctionName": PropertyType(True, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "MaximumEventAgeInSeconds": PropertyType(False, is_type(int)),  # type: ignore[no-untyped-call, no-untyped-call]
        "MaximumRetryAttempts": PropertyType(False, is_type(int)),  # type: ignore[no-untyped-call, no-untyped-call]
        "Qualifier": PropertyType(True, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
    }


class LambdaLayerVersion(Resource):
    """Lambda layer version resource"""

    resource_type = "AWS::Lambda::LayerVersion"
    property_types = {
        "Content": PropertyType(True, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "Description": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "LayerName": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "CompatibleArchitectures": PropertyType(False, list_of(one_of(is_str(), is_type(dict)))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call, no-untyped-call, no-untyped-call]
        "CompatibleRuntimes": PropertyType(False, list_of(one_of(is_str(), is_type(dict)))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call, no-untyped-call, no-untyped-call]
        "LicenseInfo": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}  # type: ignore[no-untyped-call, no-untyped-call]


class LambdaUrl(Resource):
    resource_type = "AWS::Lambda::Url"
    property_types = {
        "TargetFunctionArn": PropertyType(True, one_of(is_str(), is_type(dict))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call, no-untyped-call]
        "AuthType": PropertyType(True, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "Cors": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
    }
