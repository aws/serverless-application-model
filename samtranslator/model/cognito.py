from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, list_of, is_str
from samtranslator.model.intrinsics import fnGetAtt, ref


class CognitoUserPool(Resource):
    resource_type = "AWS::Cognito::UserPool"
    property_types = {
        "AccountRecoverySetting": PropertyType(False, is_type(dict)),
        "AdminCreateUserConfig": PropertyType(False, is_type(dict)),
        "AliasAttributes": PropertyType(False, list_of(is_str())),
        "AutoVerifiedAttributes": PropertyType(False, list_of(is_str())),
        "DeviceConfiguration": PropertyType(False, is_type(dict)),
        "EmailConfiguration": PropertyType(False, is_type(dict)),
        "EmailVerificationMessage": PropertyType(False, is_str()),
        "EmailVerificationSubject": PropertyType(False, is_str()),
        "EnabledMfas": PropertyType(False, list_of(is_str())),
        "LambdaConfig": PropertyType(False, is_type(dict)),
        "MfaConfiguration": PropertyType(False, is_str()),
        "Policies": PropertyType(False, is_type(dict)),
        "Schema": PropertyType(False, list_of(dict)),
        "SmsAuthenticationMessage": PropertyType(False, is_str()),
        "SmsConfiguration": PropertyType(False, is_type(dict)),
        "SmsVerificationMessage": PropertyType(False, is_str()),
        "UsernameAttributes": PropertyType(False, list_of(is_str())),
        "UsernameConfiguration": PropertyType(False, is_type(dict)),
        "UserPoolAddOns": PropertyType(False, list_of(dict)),
        "UserPoolName": PropertyType(False, is_str()),
        "UserPoolTags": PropertyType(False, is_type(dict)),
        "VerificationMessageTemplate": PropertyType(False, is_type(dict)),
    }

    runtime_attrs = {
        "name": lambda self: ref(self.logical_id),
        "arn": lambda self: fnGetAtt(self.logical_id, "Arn"),
        "provider_name": lambda self: fnGetAtt(self.logical_id, "ProviderName"),
        "provider_url": lambda self: fnGetAtt(self.logical_id, "ProviderURL"),
    }
