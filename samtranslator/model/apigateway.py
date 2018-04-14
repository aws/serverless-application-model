from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, one_of, is_str
from samtranslator.model.intrinsics import ref
from samtranslator.translator import logical_id_generator


class ApiGatewayRestApi(Resource):
    resource_type = 'AWS::ApiGateway::RestApi'
    property_types = {
            'Body': PropertyType(False, is_type(dict)),
            'BodyS3Location': PropertyType(False, is_type(dict)),
            'CloneFrom': PropertyType(False, is_str()),
            'Description': PropertyType(False, is_str()),
            'FailOnWarnings': PropertyType(False, is_type(bool)),
            'Name': PropertyType(False, is_str()),
            'Parameters': PropertyType(False, is_type(dict)),
            'EndpointConfiguration': PropertyType(False, is_type(dict)),
            "BinaryMediaTypes": PropertyType(False, is_type(list))
    }

    runtime_attrs = {
        "rest_api_id": lambda self: ref(self.logical_id),
    }


class ApiGatewayStage(Resource):
    resource_type = 'AWS::ApiGateway::Stage'
    property_types = {
            'CacheClusterEnabled': PropertyType(False, is_type(bool)),
            'CacheClusterSize': PropertyType(False, is_str()),
            'ClientCertificateId': PropertyType(False, is_str()),
            'DeploymentId': PropertyType(True, is_str()),
            'Description': PropertyType(False, is_str()),
            'RestApiId': PropertyType(True, is_str()),
            'StageName': PropertyType(True, one_of(is_str(), is_type(dict))),
            'Variables': PropertyType(False, is_type(dict)),
            "MethodSettings": PropertyType(False, is_type(list))
    }

    runtime_attrs = {
        "stage_name": lambda self: ref(self.logical_id),
    }

    def update_deployment_ref(self, deployment_logical_id):
        self.DeploymentId = ref(deployment_logical_id)


class ApiGatewayAccount(Resource):
    resource_type = 'AWS::ApiGateway::Account'
    property_types = {
        'CloudWatchRoleArn': PropertyType(False, one_of(is_str(), is_type(dict)))
    }


class ApiGatewayDeployment(Resource):
    resource_type = 'AWS::ApiGateway::Deployment'
    property_types = {
            'Description': PropertyType(False, is_str()),
            'RestApiId': PropertyType(True, is_str()),
            'StageDescription': PropertyType(False, is_type(dict)),
            'StageName': PropertyType(True, is_str())
    }

    runtime_attrs = {
        "deployment_id": lambda self: ref(self.logical_id),
    }

    def make_auto_deployable(self, stage, swagger=None):
        """
        Sets up the resource such that it will triggers a re-deployment when Swagger changes

        :param swagger: Dictionary containing the Swagger definition of the API
        """
        if not swagger:
            return

        # CloudFormation does NOT redeploy the API unless it has a new deployment resource
        # that points to latest RestApi resource. Append a hash of Swagger Body location to
        # redeploy only when the API data changes. First 10 characters of hash is good enough
        # to prevent redeployment when API has not changed

        # NOTE: `str(swagger)` is for backwards compatibility. Changing it to a JSON or something will break compat
        generator = logical_id_generator.LogicalIdGenerator(self.logical_id, str(swagger))
        self.logical_id = generator.gen()
        hash = generator.get_hash(length=40)  # Get the full hash
        self.Description = "RestApi deployment id: {}".format(hash)
        stage.update_deployment_ref(self.logical_id)
