from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import IS_DICT, is_type, IS_STR, list_of, one_of
from samtranslator.model.intrinsics import ref


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
