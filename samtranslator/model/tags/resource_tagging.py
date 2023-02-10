# Constants for Tagging
from typing import Any, Dict, List, Optional

_KEY = "Key"
_VALUE = "Value"


def get_tag_list(resource_tag_dict: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transforms the SAM defined Tags into the form CloudFormation is expecting.

    SAM Example:
        ```
        ...
        Tags:
          TagKey: TagValue
        ```


    CloudFormation equivalent:
          - Key: TagKey
            Value: TagValue
        ```

    :param resource_tag_dict: Customer defined dictionary (SAM Example from above)
    :return: List of Tag Dictionaries (CloudFormation Equivalent from above)
    """
    tag_list = []  # type: ignore[var-annotated]
    if resource_tag_dict is None:
        return tag_list

    for tag_key, tag_value in resource_tag_dict.items():
        tag = {_KEY: tag_key, _VALUE: tag_value if tag_value else ""}
        tag_list.append(tag)

    return tag_list
