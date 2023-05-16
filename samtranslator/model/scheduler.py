from typing import Any, Dict, Optional

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
    Name: Optional[PassThrough]
    State: Optional[PassThrough]
    Description: Optional[PassThrough]
    StartDate: Optional[PassThrough]
    EndDate: Optional[PassThrough]
    ScheduleExpressionTimezone: Optional[PassThrough]
    GroupName: Optional[PassThrough]
    KmsKeyArn: Optional[PassThrough]
    Target: Dict[str, Any]

    runtime_attrs = {"arn": lambda self: fnGetAtt(self.logical_id, "Arn")}
