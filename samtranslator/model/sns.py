from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, is_str


class SNSSubscription(Resource):
    resource_type = 'AWS::SNS::Subscription'
    property_types = {
        'Endpoint': PropertyType(True, is_str()),
        'Protocol': PropertyType(True, is_str()),
        'TopicArn': PropertyType(True, is_str()),
        'FilterPolicy': PropertyType(False, is_type(dict))
    }
