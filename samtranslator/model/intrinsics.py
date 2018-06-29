def fnGetAtt(logical_name, attribute_name):
    return {'Fn::GetAtt': [logical_name, attribute_name]}


def ref(logical_name):
    return {'Ref': logical_name}


def fnJoin(delimiter, values):
    return {'Fn::Join': [delimiter, values]}


def fnSub(string, variables=None):
    if variables:
        return {'Fn::Sub': [string, variables]}
    return {'Fn::Sub': string}


def make_shorthand(intrinsic_dict):
    """
    Converts a given intrinsics dictionary into a short-hand notation that Fn::Sub can use. Only Ref and Fn::GetAtt
    support shorthands.
    Ex:
     {"Ref": "foo"} => ${foo}
     {"Fn::GetAtt": ["bar", "Arn"]} => ${bar.Arn}

    This method assumes that the input is a valid intrinsic function dictionary. It does no validity on the input.

    :param dict intrinsic_dict: Input dictionary which is assumed to be a valid intrinsic function dictionary
    :returns string: String representing the shorthand notation
    :raises NotImplementedError: For intrinsic functions that don't support shorthands.
    """
    if "Ref" in intrinsic_dict:
        return "${%s}" % intrinsic_dict['Ref']
    elif "Fn::GetAtt" in intrinsic_dict:
        return "${%s}" % ".".join(intrinsic_dict["Fn::GetAtt"])
    else:
        raise NotImplementedError("Shorthanding is only supported for Ref and Fn::GetAtt")


def is_instrinsic(input):
    """
    Checks if the given input is an intrinsic function dictionary. Intrinsic function is a dictionary with single
    key that is the name of the intrinsics.

    :param input: Input value to check if it is an intrinsic
    :return: True, if yes
    """

    if input is not None \
        and isinstance(input, dict) \
        and len(input) == 1:

        key = list(input.keys())[0]
        return key == "Ref" or key == "Condition" or key.startswith("Fn::")

    return False
