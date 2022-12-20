from typing import Any, Dict, List, Optional

from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import IS_DICT, list_of, IS_STR
from samtranslator.model.intrinsics import fnGetAtt, ref


class StepFunctionsStateMachine(Resource):
    resource_type = "AWS::StepFunctions::StateMachine"
    property_types = {
        "Definition": PropertyType(False, IS_DICT),
        "DefinitionString": PropertyType(False, IS_STR),
        "DefinitionS3Location": PropertyType(False, IS_DICT),
        "LoggingConfiguration": PropertyType(False, IS_DICT),
        "RoleArn": PropertyType(True, IS_STR),
        "StateMachineName": PropertyType(False, IS_STR),
        "StateMachineType": PropertyType(False, IS_STR),
        "Tags": PropertyType(False, list_of(IS_DICT)),
        "DefinitionSubstitutions": PropertyType(False, IS_DICT),
        "TracingConfiguration": PropertyType(False, IS_DICT),
    }

    Definition: Optional[Dict[str, Any]]
    DefinitionString: Optional[str]
    DefinitionS3Location: Optional[Dict[str, Any]]
    LoggingConfiguration: Optional[Dict[str, Any]]
    RoleArn: str
    StateMachineName: Optional[str]
    StateMachineType: Optional[str]
    Tags: Optional[List[Dict[str, Any]]]
    DefinitionSubstitutions: Optional[Dict[str, Any]]
    TracingConfiguration: Optional[Dict[str, Any]]

    runtime_attrs = {
        "arn": lambda self: ref(self.logical_id),
        "name": lambda self: fnGetAtt(self.logical_id, "Name"),
    }
