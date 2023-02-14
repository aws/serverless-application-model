from typing import Callable, Dict, Optional

# Function to retrieve name-to-ARN managed policy map
#
# Callers must pass a function that returns Dict[str, str], but internally
# the function can return None as it's more convenient:
# the result of get_managed_policy_map is cached by wrapping with another function,
# and since get_managed_policy_map is optional, it's easier for the function to just
# return None if the wrapped function isn't provided.
InternalGetManagedPolicyMap = Callable[[], Optional[Dict[str, str]]]
