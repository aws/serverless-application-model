from samtranslator.model import PropertyType, Resource
from samtranslator.model.intrinsics import ref
from samtranslator.model.types import IS_DICT, is_type, one_of, IS_STR


class CodeDeployApplication(Resource):
    resource_type = "AWS::CodeDeploy::Application"
    property_types = {"ComputePlatform": PropertyType(False, one_of(IS_STR, IS_DICT))}

    runtime_attrs = {"name": lambda self: ref(self.logical_id)}


class CodeDeployDeploymentGroup(Resource):
    resource_type = "AWS::CodeDeploy::DeploymentGroup"
    property_types = {
        "AlarmConfiguration": PropertyType(False, IS_DICT),
        "ApplicationName": PropertyType(True, one_of(IS_STR, IS_DICT)),
        "AutoRollbackConfiguration": PropertyType(False, IS_DICT),
        "DeploymentConfigName": PropertyType(False, one_of(IS_STR, IS_DICT)),
        "DeploymentStyle": PropertyType(False, IS_DICT),
        "ServiceRoleArn": PropertyType(True, one_of(IS_STR, IS_DICT)),
        "TriggerConfigurations": PropertyType(False, is_type(list)),
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id)}
