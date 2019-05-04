from samtranslator.model import PropertyType, Resource
from samtranslator.model.intrinsics import ref
from samtranslator.model.types import is_type, one_of, is_str


class AppSyncApi(Resource):
    resource_type = 'AWS::AppSync::GraphQLApi'
    property_types = {
        'AuthenticationType': PropertyType(True, is_str()),
        'LogConfig': PropertyType(False, is_type(dict)),
        'Name': PropertyType(True, is_str()),
        'OpenIDConnectConfig': PropertyType(False, is_type(dict)),
        'UserPoolConfig': PropertyType(False, is_type(dict)),
    }

    runtime_attrs = {
        "name": lambda self: ref(self.logical_id),
    }

class AppSyncApiSchema(Resource):
    resource_type = 'AWS::AppSync::GraphQLSchema'
    property_types = {
        'ApiId': PropertyType(True, is_str()),
        'Definition': PropertyType(False, is_str()),
        'DefinitionS3Location': PropertyType(False, is_str())
    }

    runtime_attrs = {
        "name": lambda self: ref(self.logical_id),
    }

class AppSyncApiKey(Resource):
    resource_type = 'AWS::AppSync::ApiKey'
    property_types = {
        'ApiId': PropertyType(True, is_str()),
        'Description': PropertyType(False, is_str()),
        'Expires': PropertyType(False, is_type(float))
    }

    runtime_attrs = {
        "name": lambda self: ref(self.logical_id),
    }