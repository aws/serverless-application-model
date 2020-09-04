from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, dict_of, list_of, is_str, one_of
from samtranslator.model.intrinsics import fnGetAtt, ref


class StepFunctionsStateMachine(Resource):
    resource_type = "AWS::StepFunctions::StateMachine"
    property_types = {
        "Definition": PropertyType(False, is_type(dict)),
        "DefinitionString": PropertyType(False, is_str()),
        "DefinitionS3Location": PropertyType(False, is_type(dict)),
        "LoggingConfiguration": PropertyType(False, is_type(dict)),
        "RoleArn": PropertyType(True, is_str()),
        "StateMachineName": PropertyType(False, is_str()),
        "StateMachineType": PropertyType(False, is_str()),
        "Tags": PropertyType(False, list_of(is_type(dict))),
        "DefinitionSubstitutions": PropertyType(False, is_type(dict)),
        "TracingConfiguration": PropertyType(False, is_type(dict)),
    }

    runtime_attrs = {
        "arn": lambda self: ref(self.logical_id),
        "name": lambda self: fnGetAtt(self.logical_id, "Name"),
    }
