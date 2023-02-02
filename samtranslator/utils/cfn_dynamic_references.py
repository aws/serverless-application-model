import re
from typing import Any


def is_dynamic_reference(_input: Any) -> bool:
    """
    Checks if the given input is a dynamic reference. Dynamic references follow the pattern '{{resolve:service-name:reference-key}}'

    This method does not validate if the dynamic reference is valid or not, only if it follows the valid pattern: {{resolve:service-name:reference-key}}

    :param _input: Input value to check if it is a dynamic reference
    :return: True, if yes
    """
    pattern = re.compile("^{{resolve:([a-z-]+):(.+)}}$")
    if _input is not None and isinstance(_input, str) and pattern.match(_input):
        return True
    return False
