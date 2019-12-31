from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, is_str, list_of, one_of
from samtranslator.model.intrinsics import ref


class NestedStack(Resource):
    resource_type = "AWS::CloudFormation::Stack"
    # TODO: support passthrough parameters for stacks (Conditions, etc)
    property_types = {
        "TemplateURL": PropertyType(True, is_str()),
        "Parameters": PropertyType(False, is_type(dict)),
        "NotificationARNs": PropertyType(False, list_of(one_of(is_str(), is_type(dict)))),
        "Tags": PropertyType(False, list_of(is_type(dict))),
        "TimeoutInMinutes": PropertyType(False, is_type(int)),
    }

    runtime_attrs = {"stack_id": lambda self: ref(self.logical_id)}
