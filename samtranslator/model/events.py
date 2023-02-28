from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt, ref

# Event Rule Targets Id and Logical Id has maximum 64 characters limit
# https://docs.aws.amazon.com/eventbridge/latest/APIReference/API_Target.html
_EVENT_RULE_TARGET_ID_MAX_LENGTH = 64


class EventsRule(Resource):
    resource_type = "AWS::Events::Rule"
    property_types = {
        "Description": GeneratedProperty(),
        "EventBusName": GeneratedProperty(),
        "EventPattern": GeneratedProperty(),
        "Name": GeneratedProperty(),
        "RoleArn": GeneratedProperty(),
        "ScheduleExpression": GeneratedProperty(),
        "State": GeneratedProperty(),
        "Targets": GeneratedProperty(),
    }

    runtime_attrs = {"rule_id": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}


def generate_valid_target_id(logical_id: str, suffix: str) -> str:
    """Truncate Target Id if it is exceeding _EVENT_RULE_TARGET_ID_MAX_LENGTH limit."""
    if len(logical_id) + len(suffix) <= _EVENT_RULE_TARGET_ID_MAX_LENGTH:
        return logical_id + suffix

    return _truncate_with_suffix(logical_id, _EVENT_RULE_TARGET_ID_MAX_LENGTH, suffix)


def _truncate_with_suffix(s: str, length: int, suffix: str) -> str:
    """
    Truncate string if input string + suffix exceeds length requirement
    """
    return s[: length - len(suffix)] + suffix
