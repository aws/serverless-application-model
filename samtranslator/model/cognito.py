from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import IS_DICT, list_of, IS_STR
from samtranslator.model.intrinsics import fnGetAtt, ref


class CognitoUserPool(Resource):
    resource_type = "AWS::Cognito::UserPool"
    property_types = {
        "AccountRecoverySetting": PropertyType(False, IS_DICT),
        "AdminCreateUserConfig": PropertyType(False, IS_DICT),
        "AliasAttributes": PropertyType(False, list_of(IS_STR)),
        "AutoVerifiedAttributes": PropertyType(False, list_of(IS_STR)),
        "DeviceConfiguration": PropertyType(False, IS_DICT),
        "EmailConfiguration": PropertyType(False, IS_DICT),
        "EmailVerificationMessage": PropertyType(False, IS_STR),
        "EmailVerificationSubject": PropertyType(False, IS_STR),
        "EnabledMfas": PropertyType(False, list_of(IS_STR)),
        "LambdaConfig": PropertyType(False, IS_DICT),
        "MfaConfiguration": PropertyType(False, IS_STR),
        "Policies": PropertyType(False, IS_DICT),
        "Schema": PropertyType(False, list_of(dict)),
        "SmsAuthenticationMessage": PropertyType(False, IS_STR),
        "SmsConfiguration": PropertyType(False, IS_DICT),
        "SmsVerificationMessage": PropertyType(False, IS_STR),
        "UserAttributeUpdateSettings": PropertyType(False, IS_DICT),
        "UsernameAttributes": PropertyType(False, list_of(IS_STR)),
        "UsernameConfiguration": PropertyType(False, IS_DICT),
        "UserPoolAddOns": PropertyType(False, list_of(dict)),
        "UserPoolName": PropertyType(False, IS_STR),
        "UserPoolTags": PropertyType(False, IS_DICT),
        "VerificationMessageTemplate": PropertyType(False, IS_DICT),
    }

    runtime_attrs = {
        "name": lambda self: ref(self.logical_id),
        "arn": lambda self: fnGetAtt(self.logical_id, "Arn"),
        "provider_name": lambda self: fnGetAtt(self.logical_id, "ProviderName"),
        "provider_url": lambda self: fnGetAtt(self.logical_id, "ProviderURL"),
    }
