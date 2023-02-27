from typing import Any, Dict, Optional

from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt


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

    ScheduleExpression: str
    FlexibleTimeWindow: Dict[str, Any]
    Name: str
    State: Optional[str]
    Description: Optional[str]
    StartDate: Optional[str]
    EndDate: Optional[str]
    ScheduleExpressionTimezone: Optional[str]
    GroupName: Optional[str]
    KmsKeyArn: Optional[str]
    Target: Dict[str, Any]

    runtime_attrs = {"arn": lambda self: fnGetAtt(self.logical_id, "Arn")}
