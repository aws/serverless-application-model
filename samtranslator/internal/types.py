from typing import Callable, Dict

# Function to retrieve name-to-ARN managed policy map
GetManagedPolicyMap = Callable[[], Dict[str, str]]
