from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, is_str, list_of, one_of
from samtranslator.model.intrinsics import ref, fnGetAtt


# https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-synthetics-canary.html
class SyntheticsCanary(Resource):
    resource_type = "AWS::Synthetics::Canary"

    property_types = {
        "ArtifactS3Location": PropertyType(True, is_str()),
        "Code": PropertyType(True, is_type(dict)),
        "ExecutionRoleArn": PropertyType(True, is_str()),
        "FailureRetentionPeriod": PropertyType(False, is_type(int)),
        "Name": PropertyType(True, is_str()),
        "RunConfig": PropertyType(False, is_type(dict)),
        "RuntimeVersion": PropertyType(True, is_str()),
        "Schedule": PropertyType(True, is_type(dict)),
        "StartCanaryAfterCreation": PropertyType(True, is_type(bool)),
        "SuccessRetentionPeriod": PropertyType(False, is_type(int)),
        "Tags": PropertyType(False, list_of(is_type(dict))),
        "VPCConfig": PropertyType(False, is_type(dict)),
    }


class CloudWatchAlarm(Resource):
    resource_type = "AWS::CloudWatch::Alarm"

    property_types = {
        "ActionsEnabled": PropertyType(False, is_type(bool)),
        "AlarmActions": PropertyType(False, list_of(is_str())),
        "AlarmDescription": PropertyType(False, is_str()),
        "AlarmName": PropertyType(False, is_str()),
        "ComparisonOperator": PropertyType(True, is_str()),
        "DatapointsToAlarm": PropertyType(False, is_type(int)),
        "Dimensions": PropertyType(False, list_of(is_type(dict))),
        "EvaluateLowSampleCountPercentile": PropertyType(False, is_str()),
        "EvaluationPeriods": PropertyType(True, is_type(int)),
        "ExtendedStatistic": PropertyType(False, is_str()),
        "InsufficientDataActions": PropertyType(False, list_of(is_str())),
        "MetricName": PropertyType(False, is_str()),
        "Metrics": PropertyType(False, is_type(dict)),
        "Namespace": PropertyType(False, is_str()),
        "OKActions": PropertyType(False, list_of(is_str())),
        "Period": PropertyType(False, is_type(int)),
        "Statistic": PropertyType(False, is_str()),
        "Threshold": PropertyType(False, is_type(float)),
        "ThresholdMetricId": PropertyType(False, is_str()),
        "TreatMissingData": PropertyType(False, is_str()),
        "Unit": PropertyType(False, is_str()),
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}
