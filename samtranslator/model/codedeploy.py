from samtranslator.model import PropertyType, Resource
from samtranslator.model.intrinsics import ref
from samtranslator.model.types import is_type, one_of, is_str


class CodeDeployApplication(Resource):
    resource_type = 'AWS::CodeDeploy::Application'
    property_types = {
        'ComputePlatform': PropertyType(False, one_of(is_str(), is_type(dict))),
    }

    runtime_attrs = {
        "name": lambda self: ref(self.logical_id),
    }


class CodeDeployDeploymentGroup(Resource):
    resource_type = 'AWS::CodeDeploy::DeploymentGroup'
    property_types = {
        'AlarmConfiguration': PropertyType(False, is_type(dict)),
        'ApplicationName': PropertyType(True, one_of(is_str(), is_type(dict))),
        'AutoRollbackConfiguration': PropertyType(False, is_type(dict)),
        'DeploymentConfigName': PropertyType(False, one_of(is_str(), is_type(dict))),
        'DeploymentStyle': PropertyType(False, is_type(dict)),
        'ServiceRoleArn': PropertyType(True, one_of(is_str(), is_type(dict))),
    }

    runtime_attrs = {
        "name": lambda self: ref(self.logical_id),
    }
