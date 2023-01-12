from typing import Any, Dict, Optional

from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import IS_DICT, IS_STR
from samtranslator.model.intrinsics import fnGetAtt


class SchedulerSchedule(Resource):
    resource_type = "AWS::Scheduler::Schedule"
    property_types = {
        "ScheduleExpression": PropertyType(True, IS_STR),
        "FlexibleTimeWindow": PropertyType(True, IS_DICT),
        "Name": PropertyType(True, IS_STR),
        "State": PropertyType(False, IS_STR),
        "Description": PropertyType(False, IS_STR),
        "StartDate": PropertyType(False, IS_STR),
        "EndDate": PropertyType(False, IS_STR),
        "ScheduleExpressionTimezone": PropertyType(False, IS_STR),
        "GroupName": PropertyType(False, IS_STR),
        "KmsKeyArn": PropertyType(False, IS_STR),
        "Target": PropertyType(True, IS_DICT),
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
