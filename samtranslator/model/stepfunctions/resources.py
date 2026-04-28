from typing import Any

from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt, ref


class StepFunctionsStateMachine(Resource):
    resource_type = "AWS::StepFunctions::StateMachine"
    property_types = {
        "Definition": GeneratedProperty(),
        "DefinitionString": GeneratedProperty(),
        "DefinitionS3Location": GeneratedProperty(),
        "LoggingConfiguration": GeneratedProperty(),
        "RoleArn": GeneratedProperty(),
        "StateMachineName": GeneratedProperty(),
        "StateMachineType": GeneratedProperty(),
        "Tags": GeneratedProperty(),
        "DefinitionSubstitutions": GeneratedProperty(),
        "TracingConfiguration": GeneratedProperty(),
    }

    Definition: dict[str, Any] | None
    DefinitionString: str | None
    DefinitionS3Location: dict[str, Any] | None
    LoggingConfiguration: dict[str, Any] | None
    RoleArn: str
    StateMachineName: str | None
    StateMachineType: str | None
    Tags: list[dict[str, Any]] | None
    DefinitionSubstitutions: dict[str, Any] | None
    TracingConfiguration: dict[str, Any] | None

    runtime_attrs = {
        "arn": lambda self: ref(self.logical_id),
        "name": lambda self: fnGetAtt(self.logical_id, "Name"),
        "state_machine_revision_id": lambda self: fnGetAtt(self.logical_id, "StateMachineRevisionId"),
    }


class StepFunctionsStateMachineVersion(Resource):
    resource_type = "AWS::StepFunctions::StateMachineVersion"

    property_types = {"StateMachineArn": GeneratedProperty(), "StateMachineRevisionId": GeneratedProperty()}

    runtime_attrs = {"arn": lambda self: ref(self.logical_id)}


class StepFunctionsStateMachineAlias(Resource):
    resource_type = "AWS::StepFunctions::StateMachineAlias"
    property_types = {"Name": GeneratedProperty(), "DeploymentPreference": GeneratedProperty()}

    runtime_attrs = {"arn": lambda self: ref(self.logical_id)}
