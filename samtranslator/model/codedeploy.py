from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import ref


class CodeDeployApplication(Resource):
    resource_type = "AWS::CodeDeploy::Application"
    property_types = {
        "ComputePlatform": GeneratedProperty(),
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id)}


class CodeDeployDeploymentGroup(Resource):
    resource_type = "AWS::CodeDeploy::DeploymentGroup"
    property_types = {
        "AlarmConfiguration": GeneratedProperty(),
        "ApplicationName": GeneratedProperty(),
        "AutoRollbackConfiguration": GeneratedProperty(),
        "DeploymentConfigName": GeneratedProperty(),
        "DeploymentStyle": GeneratedProperty(),
        "ServiceRoleArn": GeneratedProperty(),
        "TriggerConfigurations": GeneratedProperty(),
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id)}
