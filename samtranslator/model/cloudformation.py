from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, is_str, list_of, one_of
from samtranslator.model.intrinsics import ref


class NestedStack(Resource):
    resource_type = "AWS::CloudFormation::Stack"
    # TODO: support passthrough parameters for stacks (Conditions, etc)
    property_types = {
        "TemplateURL": PropertyType(True, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "Parameters": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "NotificationARNs": PropertyType(False, list_of(one_of(is_str(), is_type(dict)))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call, no-untyped-call, no-untyped-call]
        "Tags": PropertyType(False, list_of(is_type(dict))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call]
        "TimeoutInMinutes": PropertyType(False, is_type(int)),  # type: ignore[no-untyped-call, no-untyped-call]
    }

    runtime_attrs = {"stack_id": lambda self: ref(self.logical_id)}  # type: ignore[no-untyped-call]
