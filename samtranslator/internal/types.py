from typing import Callable, Dict, Optional

# Function to retrieve name-to-ARN managed policy map
GetManagedPolicyMap = Callable[[], Optional[Dict[str, str]]]
