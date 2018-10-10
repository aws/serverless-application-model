from samtranslator.model import PropertyType, Resource
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.types import is_type, one_of, is_str
from samtranslator.model.intrinsics import ref, fnSub
from samtranslator.translator import logical_id_generator
from samtranslator.translator.arn_generator import ArnGenerator


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


class ApiGatewayAuthorizer(object):
    _VALID_FUNCTION_PAYLOAD_TYPES = [None, 'TOKEN', 'REQUEST']

    def __init__(self, api_logical_id=None, name=None, user_pool_arn=None, function_arn=None, identity=None,
                 function_payload_type=None, function_invoke_role=None):
        if function_payload_type not in ApiGatewayAuthorizer._VALID_FUNCTION_PAYLOAD_TYPES:
            raise InvalidResourceException(api_logical_id, name + " Authorizer has invalid "
                                           "'FunctionPayloadType': " + function_payload_type)

        if function_payload_type == 'REQUEST' and self._is_missing_identity_source(identity):
            raise InvalidResourceException(api_logical_id, name + " Authorizer must specify Identity with at least one "
                                           "of Headers, QueryStrings, StageVariables, or Context.")

        self.api_logical_id = api_logical_id
        self.name = name
        self.user_pool_arn = user_pool_arn
        self.function_arn = function_arn
        self.identity = identity
        self.function_payload_type = function_payload_type
        self.function_invoke_role = function_invoke_role

    def _is_missing_identity_source(self, identity):
        if not identity:
            return True

        headers = identity.get('Headers')
        query_strings = identity.get('QueryStrings')
        stage_variables = identity.get('StageVariables')
        context = identity.get('Context')

        if not headers and not query_strings and not stage_variables and not context:
            return True

        return False

    def generate_swagger(self):
        authorizer_type = self._get_type()
        APIGATEWAY_AUTHORIZER_KEY = 'x-amazon-apigateway-authorizer'
        swagger = {
            "type": "apiKey",
            "name": self._get_swagger_header_name(),
            "in": "header",
            "x-amazon-apigateway-authtype": self._get_swagger_authtype(),
            "x-amazon-apigateway-authorizer": {
                "type": self._get_swagger_authorizer_type()
            }
        }

        if authorizer_type == 'COGNITO_USER_POOLS':
            swagger[APIGATEWAY_AUTHORIZER_KEY]['providerARNs'] = self._get_user_pool_arn_array()

        elif authorizer_type == 'LAMBDA':
            partition = ArnGenerator.get_partition_name()
            resource = 'lambda:path/2015-03-31/functions/${__FunctionArn__}/invocations'
            authorizer_uri = fnSub(ArnGenerator.generate_arn(partition=partition, service='apigateway',
                                   resource=resource, include_account_id=False),
                                   {'__FunctionArn__': self.function_arn})

            swagger[APIGATEWAY_AUTHORIZER_KEY]['authorizerUri'] = authorizer_uri
            reauthorize_every = self._get_reauthorize_every()
            function_invoke_role = self._get_function_invoke_role()

            if reauthorize_every is not None:
                swagger[APIGATEWAY_AUTHORIZER_KEY]['authorizerResultTtlInSeconds'] = reauthorize_every

            if function_invoke_role:
                swagger[APIGATEWAY_AUTHORIZER_KEY]['authorizerCredentials'] = function_invoke_role

            if self._get_function_payload_type() == 'REQUEST':
                swagger[APIGATEWAY_AUTHORIZER_KEY]['identitySource'] = self._get_identity_source()

        # Authorizer Validation Expression is only allowed on COGNITO_USER_POOLS and LAMBDA_TOKEN
        is_lambda_token_authorizer = authorizer_type == 'LAMBDA' and self._get_function_payload_type() == 'TOKEN'

        if authorizer_type == 'COGNITO_USER_POOLS' or is_lambda_token_authorizer:
            identity_validation_expression = self._get_identity_validation_expression()

            if identity_validation_expression:
                swagger[APIGATEWAY_AUTHORIZER_KEY]['identityValidationExpression'] = identity_validation_expression

        return swagger

    def _get_identity_validation_expression(self):
        return self.identity and self.identity.get('ValidationExpression')

    def _get_identity_source(self):
        identity_source_headers = []
        identity_source_query_strings = []
        identity_source_stage_variables = []
        identity_source_context = []

        if self.identity.get('Headers'):
            identity_source_headers = list(map(lambda h: 'method.request.header.' + h, self.identity.get('Headers')))

        if self.identity.get('QueryStrings'):
            identity_source_query_strings = list(map(lambda qs: 'method.request.querystring.' + qs, self.identity.get('QueryStrings')))

        if self.identity.get('StageVariables'):
            identity_source_stage_variables = list(map(lambda sv: 'stageVariables.' + sv, self.identity.get('StageVariables')))

        if self.identity.get('Context'):
            identity_source_context = list(map(lambda c: 'context.' + c, self.identity.get('Context')))

        identity_source_array = identity_source_headers + identity_source_query_strings + identity_source_stage_variables + identity_source_context
        identity_source = ', '.join(identity_source_array)

        return identity_source

    def _get_user_pool_arn_array(self):
        return self.user_pool_arn if isinstance(self.user_pool_arn, list) else [self.user_pool_arn]

    def _get_swagger_header_name(self):
        authorizer_type = self._get_type()
        payload_type = self._get_function_payload_type()

        if authorizer_type == 'LAMBDA' and payload_type == 'REQUEST':
            return 'Unused'

        return self._get_identity_header()

    def _get_type(self):
        if self.user_pool_arn:
            return 'COGNITO_USER_POOLS'

        return 'LAMBDA'

    def _get_identity_header(self):
        if not self.identity or not self.identity.get('Header'):
            return 'Authorization'

        return self.identity.get('Header')

    def _get_reauthorize_every(self):
        if not self.identity:
            return None

        return self.identity.get('ReauthorizeEvery')

    def _get_function_invoke_role(self):
        if not self.function_invoke_role or self.function_invoke_role == 'NONE':
            return None

        return self.function_invoke_role

    def _get_swagger_authtype(self):
        authorizer_type = self._get_type()

        return 'cognito_user_pools' if authorizer_type == 'COGNITO_USER_POOLS' else 'custom'

    def _get_function_payload_type(self):
        return 'TOKEN' if not self.function_payload_type else self.function_payload_type

    def _get_swagger_authorizer_type(self):
        authorizer_type = self._get_type()

        if authorizer_type == 'COGNITO_USER_POOLS':
            return 'cognito_user_pools'

        payload_type = self._get_function_payload_type()

        if payload_type == 'REQUEST':
            return 'request'

        if payload_type == 'TOKEN':
            return 'token'
