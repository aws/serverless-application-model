import re


def is_dynamic_reference(input):
    """
    Checks if the given input is a dynamic reference. Dynamic references follow the pattern '{{resolve:service-name:reference-key}}'

    This method does not validate if the dynamic reference is valid or not, only if it follows the valid pattern: {{resolve:service-name:reference-key}}

    :param input: Input value to check if it is a dynamic reference
    :return: True, if yes
    """
    pattern = re.compile("^{{resolve:([a-z-]+):(.+)}}$")
    if input is not None and isinstance(input, str):
        if pattern.match(input):
            return True
    return False
