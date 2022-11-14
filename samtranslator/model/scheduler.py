from typing import Any, Dict, Optional

from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, is_str
from samtranslator.model.intrinsics import fnGetAtt


class SchedulerSchedule(Resource):
    resource_type = "AWS::Scheduler::Schedule"
    property_types = {
        "ScheduleExpression": PropertyType(True, is_str()),
        "FlexibleTimeWindow": PropertyType(True, is_type(dict)),
        "Name": PropertyType(True, is_str()),
        "State": PropertyType(False, is_str()),
        "Description": PropertyType(False, is_str()),
        "StartDate": PropertyType(False, is_str()),
        "EndDate": PropertyType(False, is_str()),
        "ScheduleExpressionTimezone": PropertyType(False, is_str()),
        "GroupName": PropertyType(False, is_str()),
        "KmsKeyArn": PropertyType(False, is_str()),
        "Target": PropertyType(True, is_type(dict)),
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
