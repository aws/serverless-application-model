from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, list_of, is_str
from samtranslator.model.intrinsics import fnGetAtt, ref


class StepFunctionsStateMachine(Resource):
    resource_type = "AWS::StepFunctions::StateMachine"
    property_types = {
        "Definition": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "DefinitionString": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "DefinitionS3Location": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "LoggingConfiguration": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "RoleArn": PropertyType(True, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "StateMachineName": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "StateMachineType": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "Tags": PropertyType(False, list_of(is_type(dict))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call]
        "DefinitionSubstitutions": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "TracingConfiguration": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
    }

    runtime_attrs = {
        "arn": lambda self: ref(self.logical_id),  # type: ignore[no-untyped-call]
        "name": lambda self: fnGetAtt(self.logical_id, "Name"),  # type: ignore[no-untyped-call]
    }
