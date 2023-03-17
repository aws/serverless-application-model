from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt, ref


class CognitoUserPool(Resource):
    resource_type = "AWS::Cognito::UserPool"
    property_types = {
        "AccountRecoverySetting": GeneratedProperty(),
        "AdminCreateUserConfig": GeneratedProperty(),
        "AliasAttributes": GeneratedProperty(),
        "AutoVerifiedAttributes": GeneratedProperty(),
        "DeletionProtection": GeneratedProperty(),
        "DeviceConfiguration": GeneratedProperty(),
        "EmailConfiguration": GeneratedProperty(),
        "EmailVerificationMessage": GeneratedProperty(),
        "EmailVerificationSubject": GeneratedProperty(),
        "EnabledMfas": GeneratedProperty(),
        "LambdaConfig": GeneratedProperty(),
        "MfaConfiguration": GeneratedProperty(),
        "Policies": GeneratedProperty(),
        "Schema": GeneratedProperty(),
        "SmsAuthenticationMessage": GeneratedProperty(),
        "SmsConfiguration": GeneratedProperty(),
        "SmsVerificationMessage": GeneratedProperty(),
        "UserAttributeUpdateSettings": GeneratedProperty(),
        "UsernameAttributes": GeneratedProperty(),
        "UsernameConfiguration": GeneratedProperty(),
        "UserPoolAddOns": GeneratedProperty(),
        "UserPoolName": GeneratedProperty(),
        "UserPoolTags": GeneratedProperty(),
        "VerificationMessageTemplate": GeneratedProperty(),
    }

    runtime_attrs = {
        "name": lambda self: ref(self.logical_id),
        "arn": lambda self: fnGetAtt(self.logical_id, "Arn"),
        "provider_name": lambda self: fnGetAtt(self.logical_id, "ProviderName"),
        "provider_url": lambda self: fnGetAtt(self.logical_id, "ProviderURL"),
    }
