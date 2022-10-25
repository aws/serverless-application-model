import yaml
from yaml import ScalarNode, SequenceNode

# This helper copied almost entirely from
# https://github.com/aws/aws-cli/blob/develop/awscli/customizations/cloudformation/yamlhelper.py


def yaml_parse(yamlstr):  # type: ignore[no-untyped-def]
    """Parse a yaml string"""
    yaml.SafeLoader.add_multi_constructor("!", intrinsics_multi_constructor)  # type: ignore[no-untyped-call]
    return yaml.safe_load(yamlstr)


def intrinsics_multi_constructor(loader, tag_prefix, node):  # type: ignore[no-untyped-def]
    """
    YAML constructor to parse CloudFormation intrinsics.
    This will return a dictionary with key being the instrinsic name
    """

    # Get the actual tag name excluding the first exclamation
    tag = node.tag[1:]

    # Some intrinsic functions doesn't support prefix "Fn::"
    prefix = "Fn::"
    if tag in ["Ref", "Condition"]:
        prefix = ""

    cfntag = prefix + tag

    if tag == "GetAtt" and isinstance(node.value, str):
        # ShortHand notation for !GetAtt accepts Resource.Attribute format
        # while the standard notation is to use an array
        # [Resource, Attribute]. Convert shorthand to standard format
        value = node.value.split(".", 1)

    elif isinstance(node, ScalarNode):
        # Value of this node is scalar
        value = loader.construct_scalar(node)

    elif isinstance(node, SequenceNode):
        # Value of this node is an array (Ex: [1,2])
        value = loader.construct_sequence(node)

    else:
        # Value of this node is an mapping (ex: {foo: bar})
        value = loader.construct_mapping(node)

    return {cfntag: value}
