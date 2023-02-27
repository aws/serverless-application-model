from typing import Any, Dict, List, Optional

from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt, ref

# Event Rule Targets Id and Logical Id has maximum 64 characters limit
# https://docs.aws.amazon.com/eventbridge/latest/APIReference/API_Target.html
EVENT_RULE_LOGICAL_ID_MAX_LENGTH = 64
EVENT_RULE_LOGICAL_ID_EVENT_SUFFIX = "Event"


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

    def __init__(
        self,
        logical_id: Optional[Any],
        relative_id: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(logical_id, relative_id, depends_on, attributes)

        if len(self.logical_id) > EVENT_RULE_LOGICAL_ID_MAX_LENGTH:
            # Truncate logical id to satisfy the EVENT_RULE_ID_MAX_LENGTH limit
            self.logical_id = _truncate_with_suffix(
                self.logical_id, EVENT_RULE_LOGICAL_ID_MAX_LENGTH, EVENT_RULE_LOGICAL_ID_EVENT_SUFFIX
            )


def generate_valid_target_id(logical_id: str, suffix: str) -> str:
    """Truncate Target Id if it is exceeding EVENT_RULE_ID_MAX_LENGTH limi."""
    if len(logical_id) + len(suffix) <= EVENT_RULE_LOGICAL_ID_MAX_LENGTH:
        return logical_id + suffix

    return _truncate_with_suffix(logical_id, EVENT_RULE_LOGICAL_ID_MAX_LENGTH, suffix)


def _truncate_with_suffix(s: str, length: int, suffix: str) -> str:
    """
    Truncate string if input string + suffix exceeds length requirement
    """
    return s[: length - len(suffix)] + suffix
