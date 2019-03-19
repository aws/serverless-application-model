from re import match

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
            "BinaryMediaTypes": PropertyType(False, is_type(list)),
            "MinimumCompressionSize": PropertyType(False, is_type(int))
    }

    runtime_attrs = {
        "rest_api_id": lambda self: ref(self.logical_id),
    }


class ApiGatewayStage(Resource):
    resource_type = 'AWS::ApiGateway::Stage'
    property_types = {
            'AccessLogSetting': PropertyType(False, is_type(dict)),
            'CacheClusterEnabled': PropertyType(False, is_type(bool)),
            'CacheClusterSize': PropertyType(False, is_str()),
            'CanarySetting': PropertyType(False, is_type(dict)),
            'ClientCertificateId': PropertyType(False, is_str()),
            'DeploymentId': PropertyType(True, is_str()),
            'Description': PropertyType(False, is_str()),
            'RestApiId': PropertyType(True, is_str()),
            'StageName': PropertyType(True, one_of(is_str(), is_type(dict))),
            'TracingEnabled': PropertyType(False, is_type(bool)),
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


class ApiGatewayResponse(object):
    ResponseParameterProperties = ["Headers", "Paths", "QueryStrings"]

    def __init__(self, api_logical_id=None, response_parameters=None, response_templates=None, status_code=None):
        if response_parameters:
            for response_parameter_key in response_parameters.keys():
                if response_parameter_key not in ApiGatewayResponse.ResponseParameterProperties:
                    raise InvalidResourceException(
                        api_logical_id,
                        "Invalid gateway response parameter '{}'".format(response_parameter_key))

        status_code_str = self._status_code_string(status_code)
        # status_code must look like a status code, if present. Let's not be judgmental; just check 0-999.
        if status_code and not match(r'^[0-9]{1,3}$', status_code_str):
            raise InvalidResourceException(api_logical_id, "Property 'StatusCode' must be numeric")

        self.api_logical_id = api_logical_id
        self.response_parameters = response_parameters or {}
        self.response_templates = response_templates or {}
        self.status_code = status_code_str

    def generate_swagger(self):
        swagger = {
            "responseParameters": self._add_prefixes(self.response_parameters),
            "responseTemplates": self.response_templates
        }

        # Prevent "null" being written.
        if self.status_code:
            swagger["statusCode"] = self.status_code

        return swagger

    def _add_prefixes(self, response_parameters):
        GATEWAY_RESPONSE_PREFIX = 'gatewayresponse.'
        prefixed_parameters = {}
        for key, value in response_parameters.get('Headers', {}).items():
            prefixed_parameters[GATEWAY_RESPONSE_PREFIX + 'header.' + key] = value
        for key, value in response_parameters.get('Paths', {}).items():
            prefixed_parameters[GATEWAY_RESPONSE_PREFIX + 'path.' + key] = value
        for key, value in response_parameters.get('QueryStrings', {}).items():
            prefixed_parameters[GATEWAY_RESPONSE_PREFIX + 'querystring.' + key] = value

        return prefixed_parameters

    def _status_code_string(self, status_code):
        return None if status_code is None else str(status_code)


class ApiGatewayAuthorizer(object):
    _VALID_FUNCTION_PAYLOAD_TYPES = [None, 'TOKEN', 'REQUEST']

    def __init__(self, api_logical_id=None, name=None, user_pool_arn=None, function_arn=None, identity=None,
                 function_payload_type=None, function_invoke_role=None, is_aws_iam_authorizer=False):
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
        self.is_aws_iam_authorizer = is_aws_iam_authorizer

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
            "x-amazon-apigateway-authtype": self._get_swagger_authtype()
        }

        if authorizer_type == 'COGNITO_USER_POOLS':
            swagger[APIGATEWAY_AUTHORIZER_KEY] = {
                'type': self._get_swagger_authorizer_type(),
                'providerARNs': self._get_user_pool_arn_array()
            }

        elif authorizer_type == 'LAMBDA':
            swagger[APIGATEWAY_AUTHORIZER_KEY] = {
                'type': self._get_swagger_authorizer_type()
            }
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
            identity_source_query_strings = list(map(lambda qs: 'method.request.querystring.' + qs,
                                                     self.identity.get('QueryStrings')))

        if self.identity.get('StageVariables'):
            identity_source_stage_variables = list(map(lambda sv: 'stageVariables.' + sv,
                                                       self.identity.get('StageVariables')))

        if self.identity.get('Context'):
            identity_source_context = list(map(lambda c: 'context.' + c, self.identity.get('Context')))

        identity_source_array = (identity_source_headers + identity_source_query_strings +
                                 identity_source_stage_variables + identity_source_context)
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
        if self.is_aws_iam_authorizer:
            return 'AWS_IAM'

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
        if authorizer_type == 'AWS_IAM':
            return 'awsSigv4'

        if authorizer_type == 'COGNITO_USER_POOLS':
            return 'cognito_user_pools'

        return 'custom'

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
