from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, one_of, is_str, list_of, any_type
from samtranslator.model.intrinsics import fnGetAtt, ref


class LambdaFunction(Resource):
    resource_type = "AWS::Lambda::Function"
    property_types = {
        "Code": PropertyType(True, is_type(dict)),
        "PackageType": PropertyType(False, is_str()),
        "DeadLetterConfig": PropertyType(False, is_type(dict)),
        "Description": PropertyType(False, is_str()),
        "FunctionName": PropertyType(False, is_str()),
        "Handler": PropertyType(False, is_str()),
        "MemorySize": PropertyType(False, is_type(int)),
        "Role": PropertyType(False, is_str()),
        "Runtime": PropertyType(False, is_str()),
        "Timeout": PropertyType(False, is_type(int)),
        "VpcConfig": PropertyType(False, is_type(dict)),
        "Environment": PropertyType(False, is_type(dict)),
        "Tags": PropertyType(False, list_of(is_type(dict))),
        "TracingConfig": PropertyType(False, is_type(dict)),
        "KmsKeyArn": PropertyType(False, one_of(is_type(dict), is_str())),
        "Layers": PropertyType(False, list_of(one_of(is_str(), is_type(dict)))),
        "ReservedConcurrentExecutions": PropertyType(False, any_type()),
        "FileSystemConfigs": PropertyType(False, list_of(is_type(dict))),
        "CodeSigningConfigArn": PropertyType(False, is_str()),
        "ImageConfig": PropertyType(False, is_type(dict)),
        "Architectures": PropertyType(False, list_of(one_of(is_str(), is_type(dict)))),
        "EphemeralStorage": PropertyType(False, is_type(dict)),
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}


class LambdaVersion(Resource):
    resource_type = "AWS::Lambda::Version"
    property_types = {
        "CodeSha256": PropertyType(False, is_str()),
        "Description": PropertyType(False, is_str()),
        "FunctionName": PropertyType(True, one_of(is_str(), is_type(dict))),
    }

    runtime_attrs = {
        "arn": lambda self: ref(self.logical_id),
        "version": lambda self: fnGetAtt(self.logical_id, "Version"),
    }


class LambdaAlias(Resource):
    resource_type = "AWS::Lambda::Alias"
    property_types = {
        "Description": PropertyType(False, is_str()),
        "Name": PropertyType(False, is_str()),
        "FunctionName": PropertyType(True, one_of(is_str(), is_type(dict))),
        "FunctionVersion": PropertyType(True, one_of(is_str(), is_type(dict))),
        "ProvisionedConcurrencyConfig": PropertyType(False, is_type(dict)),
    }

    runtime_attrs = {"arn": lambda self: ref(self.logical_id)}


class LambdaEventSourceMapping(Resource):
    resource_type = "AWS::Lambda::EventSourceMapping"
    property_types = {
        "BatchSize": PropertyType(False, is_type(int)),
        "Enabled": PropertyType(False, is_type(bool)),
        "EventSourceArn": PropertyType(False, is_str()),
        "FunctionName": PropertyType(True, is_str()),
        "MaximumBatchingWindowInSeconds": PropertyType(False, is_type(int)),
        "MaximumRetryAttempts": PropertyType(False, is_type(int)),
        "BisectBatchOnFunctionError": PropertyType(False, is_type(bool)),
        "MaximumRecordAgeInSeconds": PropertyType(False, is_type(int)),
        "DestinationConfig": PropertyType(False, is_type(dict)),
        "ParallelizationFactor": PropertyType(False, is_type(int)),
        "StartingPosition": PropertyType(False, is_str()),
        "Topics": PropertyType(False, is_type(list)),
        "Queues": PropertyType(False, is_type(list)),
        "SourceAccessConfigurations": PropertyType(False, is_type(list)),
        "TumblingWindowInSeconds": PropertyType(False, is_type(int)),
        "FunctionResponseTypes": PropertyType(False, is_type(list)),
        "SelfManagedEventSource": PropertyType(False, is_type(dict)),
        "FilterCriteria": PropertyType(False, is_type(dict)),
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id)}


class LambdaPermission(Resource):
    resource_type = "AWS::Lambda::Permission"
    property_types = {
        "Action": PropertyType(True, is_str()),
        "FunctionName": PropertyType(True, is_str()),
        "Principal": PropertyType(True, is_str()),
        "SourceAccount": PropertyType(False, is_str()),
        "SourceArn": PropertyType(False, is_str()),
        "EventSourceToken": PropertyType(False, is_str()),
        "FunctionUrlAuthType": PropertyType(False, is_str()),
    }


class LambdaEventInvokeConfig(Resource):
    resource_type = "AWS::Lambda::EventInvokeConfig"
    property_types = {
        "DestinationConfig": PropertyType(False, is_type(dict)),
        "FunctionName": PropertyType(True, is_str()),
        "MaximumEventAgeInSeconds": PropertyType(False, is_type(int)),
        "MaximumRetryAttempts": PropertyType(False, is_type(int)),
        "Qualifier": PropertyType(True, is_str()),
    }


class LambdaLayerVersion(Resource):
    """Lambda layer version resource"""

    resource_type = "AWS::Lambda::LayerVersion"
    property_types = {
        "Content": PropertyType(True, is_type(dict)),
        "Description": PropertyType(False, is_str()),
        "LayerName": PropertyType(False, is_str()),
        "CompatibleArchitectures": PropertyType(False, list_of(one_of(is_str(), is_type(dict)))),
        "CompatibleRuntimes": PropertyType(False, list_of(one_of(is_str(), is_type(dict)))),
        "LicenseInfo": PropertyType(False, is_str()),
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}


class LambdaUrl(Resource):
    resource_type = "AWS::Lambda::Url"
    property_types = {
        "TargetFunctionArn": PropertyType(True, one_of(is_str(), is_type(dict))),
        "AuthType": PropertyType(True, is_str()),
        "Cors": PropertyType(False, is_type(dict)),
    }
