from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, one_of, is_str, list_of
from samtranslator.model.intrinsics import ref
from samtranslator.model.exceptions import InvalidResourceException


class ApiGatewayV2HttpApi(Resource):
    resource_type = "AWS::ApiGatewayV2::Api"
    property_types = {
        "Body": PropertyType(False, is_type(dict)),
        "BodyS3Location": PropertyType(False, is_type(dict)),
        "Description": PropertyType(False, is_str()),
        "FailOnWarnings": PropertyType(False, is_type(bool)),
        "BasePath": PropertyType(False, is_str()),
        "Tags": PropertyType(False, list_of(is_type(dict))),
        "CorsConfiguration": PropertyType(False, is_type(dict)),
    }

    runtime_attrs = {"http_api_id": lambda self: ref(self.logical_id)}


class ApiGatewayV2Stage(Resource):
    resource_type = "AWS::ApiGatewayV2::Stage"
    property_types = {
        "AccessLogSettings": PropertyType(False, is_type(dict)),
        "DefaultRouteSettings": PropertyType(False, is_type(dict)),
        "ClientCertificateId": PropertyType(False, is_str()),
        "Description": PropertyType(False, is_str()),
        "ApiId": PropertyType(True, is_str()),
        "StageName": PropertyType(False, one_of(is_str(), is_type(dict))),
        "Tags": PropertyType(False, list_of(is_type(dict))),
        "StageVariables": PropertyType(False, is_type(dict)),
        "AutoDeploy": PropertyType(False, is_type(bool)),
    }

    runtime_attrs = {"stage_name": lambda self: ref(self.logical_id)}


class ApiGatewayV2Authorizer(object):
    def __init__(
        self,
        api_logical_id=None,
        name=None,
        open_id_connect_url=None,
        authorization_scopes=[],
        jwt_configuration={},
        id_source=None,
    ):
        """
        Creates an authorizer for use in V2 Http Apis
        """
        # OIDC uses a connect url, oauth2 doesn't
        self.auth_type = "openIdConnect"
        if open_id_connect_url is None:
            self.auth_type = "oauth2"

        self.api_logical_id = api_logical_id
        self.name = name
        self.open_id_connect_url = open_id_connect_url
        self.authorization_scopes = authorization_scopes

        # Validate necessary parameters exist
        if not jwt_configuration:
            raise InvalidResourceException(api_logical_id, name + " Authorizer must define 'JwtConfiguration'")
        self.jwt_configuration = jwt_configuration
        if not id_source:
            raise InvalidResourceException(api_logical_id, name + " Authorizer must define 'IdentitySource'")
        self.id_source = id_source

    def generate_openapi(self):
        """
        Generates OAS for the securitySchemes section
        """
        openapi = {
            "type": self.auth_type,
            "x-amazon-apigateway-authorizer": {
                "jwtConfiguration": self.jwt_configuration,
                "identitySource": self.id_source,
                "type": "jwt",
            },
        }
        if self.open_id_connect_url:
            openapi["x-amazon-apigateway-authorizer"]["openIdConnectUrl"] = self.open_id_connect_url
        return openapi
