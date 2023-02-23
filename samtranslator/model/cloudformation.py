from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import ref


class NestedStack(Resource):
    resource_type = "AWS::CloudFormation::Stack"
    # TODO: support passthrough parameters for stacks (Conditions, etc)
    property_types = {
        "TemplateURL": GeneratedProperty(),
        "Parameters": GeneratedProperty(),
        "NotificationARNs": GeneratedProperty(),
        "Tags": GeneratedProperty(),
        "TimeoutInMinutes": GeneratedProperty(),
    }

    runtime_attrs = {"stack_id": lambda self: ref(self.logical_id)}
