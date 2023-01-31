from samtranslator.model import PropertyType, Resource
from samtranslator.model.intrinsics import ref
from samtranslator.model.types import IS_DICT, IS_STR, is_type, list_of, one_of


class NestedStack(Resource):
    resource_type = "AWS::CloudFormation::Stack"
    # TODO: support passthrough parameters for stacks (Conditions, etc)
    property_types = {
        "TemplateURL": PropertyType(True, IS_STR),
        "Parameters": PropertyType(False, IS_DICT),
        "NotificationARNs": PropertyType(False, list_of(one_of(IS_STR, IS_DICT))),
        "Tags": PropertyType(False, list_of(IS_DICT)),
        "TimeoutInMinutes": PropertyType(False, is_type(int)),
    }

    runtime_attrs = {"stack_id": lambda self: ref(self.logical_id)}
