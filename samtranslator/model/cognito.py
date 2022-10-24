from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, list_of, is_str
from samtranslator.model.intrinsics import fnGetAtt, ref


class CognitoUserPool(Resource):
    resource_type = "AWS::Cognito::UserPool"
    property_types = {
        "AccountRecoverySetting": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "AdminCreateUserConfig": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "AliasAttributes": PropertyType(False, list_of(is_str())),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call]
        "AutoVerifiedAttributes": PropertyType(False, list_of(is_str())),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call]
        "DeviceConfiguration": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "EmailConfiguration": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "EmailVerificationMessage": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "EmailVerificationSubject": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "EnabledMfas": PropertyType(False, list_of(is_str())),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call]
        "LambdaConfig": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "MfaConfiguration": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "Policies": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "Schema": PropertyType(False, list_of(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "SmsAuthenticationMessage": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "SmsConfiguration": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "SmsVerificationMessage": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "UserAttributeUpdateSettings": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "UsernameAttributes": PropertyType(False, list_of(is_str())),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call]
        "UsernameConfiguration": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "UserPoolAddOns": PropertyType(False, list_of(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "UserPoolName": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "UserPoolTags": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "VerificationMessageTemplate": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
    }

    runtime_attrs = {
        "name": lambda self: ref(self.logical_id),  # type: ignore[no-untyped-call]
        "arn": lambda self: fnGetAtt(self.logical_id, "Arn"),  # type: ignore[no-untyped-call]
        "provider_name": lambda self: fnGetAtt(self.logical_id, "ProviderName"),  # type: ignore[no-untyped-call]
        "provider_url": lambda self: fnGetAtt(self.logical_id, "ProviderURL"),  # type: ignore[no-untyped-call]
    }
