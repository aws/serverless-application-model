import logging
from typing import Dict, Optional, cast

from botocore.client import BaseClient

from samtranslator.metrics.method_decorator import cw_timer

LOG = logging.getLogger(__name__)


class ManagedPolicyLoader:
    def __init__(self, iam_client: BaseClient) -> None:
        self._iam_client = iam_client
        self._policy_map: Optional[Dict[str, str]] = None
        self.max_items = 1000

    @cw_timer(prefix="External", name="IAM")
    def _load_policies_from_iam(self) -> None:
        LOG.info("Loading policies from IAM...")

        paginator = self._iam_client.get_paginator("list_policies")
        # Setting the scope to AWS limits the returned values to only AWS Managed Policies and will
        # not returned policies owned by any specific account.
        # http://docs.aws.amazon.com/IAM/latest/APIReference/API_ListPolicies.html#API_ListPolicies_RequestParameters
        # Note(jfuss): boto3 PaginationConfig MaxItems does not control the number of items returned from the API
        # call. This is actually controlled by PageSize.
        page_iterator = paginator.paginate(Scope="AWS", PaginationConfig={"PageSize": self.max_items})
        name_to_arn_map: Dict[str, str] = {}

        for page in page_iterator:
            name_to_arn_map.update((x["PolicyName"], x["Arn"]) for x in page["Policies"])

        LOG.info("Finished loading policies from IAM.")
        self._policy_map = name_to_arn_map

    def load(self) -> Dict[str, str]:
        if self._policy_map is None:
            self._load_policies_from_iam()
        # mypy doesn't realize that function above assigns non-None value
        return cast(Dict[str, str], self._policy_map)
