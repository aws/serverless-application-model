from typing import Any

from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt
from samtranslator.model.types import PassThrough


class SchedulerSchedule(Resource):
    resource_type = "AWS::Scheduler::Schedule"
    property_types = {
        "ScheduleExpression": GeneratedProperty(),
        "FlexibleTimeWindow": GeneratedProperty(),
        "Name": GeneratedProperty(),
        "State": GeneratedProperty(),
        "Description": GeneratedProperty(),
        "StartDate": GeneratedProperty(),
        "EndDate": GeneratedProperty(),
        "ScheduleExpressionTimezone": GeneratedProperty(),
        "GroupName": GeneratedProperty(),
        "KmsKeyArn": GeneratedProperty(),
        "Target": GeneratedProperty(),
    }

    ScheduleExpression: PassThrough
    FlexibleTimeWindow: PassThrough
    Name: PassThrough | None
    State: PassThrough | None
    Description: PassThrough | None
    StartDate: PassThrough | None
    EndDate: PassThrough | None
    ScheduleExpressionTimezone: PassThrough | None
    GroupName: PassThrough | None
    KmsKeyArn: PassThrough | None
    Target: dict[str, Any]

    runtime_attrs = {"arn": lambda self: fnGetAtt(self.logical_id, "Arn")}
