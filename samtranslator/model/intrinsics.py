def fnGetAtt(logical_name, attribute_name):
    return {"Fn::GetAtt": [logical_name, attribute_name]}


def ref(logical_name):
    return {"Ref": logical_name}


def fnJoin(delimiter, values):
    return {"Fn::Join": [delimiter, values]}


def fnSub(string, variables=None):
    if variables:
        return {"Fn::Sub": [string, variables]}
    return {"Fn::Sub": string}


def fnOr(argument_list):
    return {"Fn::Or": argument_list}


def fnAnd(argument_list):
    return {"Fn::And": argument_list}


def make_conditional(condition, true_data, false_data=None):
    if false_data is None:
        false_data = {"Ref": "AWS::NoValue"}
    return {"Fn::If": [condition, true_data, false_data]}


def make_not_conditional(condition):
    return {"Fn::Not": [{"Condition": condition}]}


def make_condition_or_list(conditions_list):
    condition_or_list = []
    for condition in conditions_list:
        c = {"Condition": condition}
        condition_or_list.append(c)
    return condition_or_list


def make_or_condition(conditions_list):
    or_list = make_condition_or_list(conditions_list)
    condition = fnOr(or_list)
    return condition


def make_and_condition(conditions_list):
    and_list = make_condition_or_list(conditions_list)
    condition = fnAnd(and_list)
    return condition


def calculate_number_of_conditions(conditions_length, max_conditions):
    """
    Every condition can hold up to max_conditions, which (as of writing this) is 10.
    Every time a condition is created, (max_conditions) are used and 1 new one is added to the conditions list.
    This means that there is a net decrease of up to (max_conditions-1) with each iteration.

    This formula calculates the number of conditions needed.
    x items in groups of y, where every group adds another number to x
    Math: either math.ceil((x-1)/(y-1))
            or  math.floor((x+(y-1)-2)/(y-1)) == 1 + (x-2)//(y-1)

    :param int conditions_length: total # of conditions to handle
    :param int max_conditions: maximum number of conditions that can be put in an Fn::Or statement
    :return: the number (int) of necessary additional conditions.
    """
    num_conditions = 1 + (conditions_length - 2) // (max_conditions - 1)
    return num_conditions


def make_combined_condition(conditions_list, condition_name):
    """
    Makes a combined condition using Fn::Or. Since Fn::Or only accepts up to 10 conditions,
    this method optionally creates multiple conditions. These conditions are named based on
    the condition_name parameter that is passed into the method.

    :param list conditions_list: list of conditions
    :param string condition_name: base name desired for new condition
    :return: dictionary of condition_name: condition_value
    """
    if len(conditions_list) < 2:
        # Can't make a condition if <2 conditions provided.
        return None

    # Total number of conditions allows in an Fn::Or statement. See docs:
    # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-conditions.html#intrinsic-function-reference-conditions-or
    max_conditions = 10

    conditions = {}
    conditions_length = len(conditions_list)
    # Get number of conditions needed, then minus one to use them as 0-based indices
    zero_based_num_conditions = calculate_number_of_conditions(conditions_length, max_conditions) - 1

    while len(conditions_list) > 1:
        new_condition_name = condition_name
        # If more than 1 new condition is needed, add a number to the end of the name
        if zero_based_num_conditions > 0:
            new_condition_name = "{}{}".format(condition_name, zero_based_num_conditions)
            zero_based_num_conditions -= 1
        new_condition_content = make_or_condition(conditions_list[:max_conditions])
        conditions_list = conditions_list[max_conditions:]
        conditions_list.append(new_condition_name)
        conditions[new_condition_name] = new_condition_content
    return conditions


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
        return "${%s}" % intrinsic_dict["Ref"]
    elif "Fn::GetAtt" in intrinsic_dict:
        return "${%s}" % ".".join(intrinsic_dict["Fn::GetAtt"])
    else:
        raise NotImplementedError("Shorthanding is only supported for Ref and Fn::GetAtt")


def is_intrinsic(input):
    """
    Checks if the given input is an intrinsic function dictionary. Intrinsic function is a dictionary with single
    key that is the name of the intrinsics.

    :param input: Input value to check if it is an intrinsic
    :return: True, if yes
    """

    if input is not None and isinstance(input, dict) and len(input) == 1:

        key = list(input.keys())[0]
        return key == "Ref" or key == "Condition" or key.startswith("Fn::")

    return False


def is_intrinsic_if(input):
    """
    Is the given input an intrinsic if? Intrinsic function 'if' is a dictionary with single
    key - if

    :param input: Input value to check if it is an intrinsic if
    :return: True, if yes
    """

    if not is_intrinsic(input):
        return False

    key = list(input.keys())[0]
    return key == "Fn::If"


def validate_intrinsic_if_items(items):
    """
    Validates Fn::If items

    Parameters
    ----------
    items : list
        Fn::If items

    Raises
    ------
    ValueError
        If the items are invalid
    """
    if not isinstance(items, list) or len(items) != 3:
        raise ValueError("Fn::If requires 3 arguments")


def is_intrinsic_no_value(input):
    """
    Is the given input an intrinsic Ref: AWS::NoValue? Intrinsic function is a dictionary with single
    key - Ref and value - AWS::NoValue

    :param input: Input value to check if it is an intrinsic if
    :return: True, if yes
    """

    if not is_intrinsic(input):
        return False

    key = list(input.keys())[0]
    return key == "Ref" and input["Ref"] == "AWS::NoValue"
