from collections.abc import Callable

# Function to retrieve name-to-ARN managed policy map
GetManagedPolicyMap = Callable[[], dict[str, str]]
