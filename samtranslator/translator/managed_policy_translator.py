class ManagedPolicyLoader(object):

    def __init__(self, iam_client):
        self._iam_client = iam_client
        self._policy_map = None

    def load(self):
        if self._policy_map is None:
            paginator = self._iam_client.get_paginator('list_policies')
            # Setting the scope to AWS limits the returned values to only AWS Managed Policies and will
            # not returned policies owned by any specific account.
            # http://docs.aws.amazon.com/IAM/latest/APIReference/API_ListPolicies.html#API_ListPolicies_RequestParameters
            page_iterator = paginator.paginate(Scope='AWS')
            name_to_arn_map = {}

            for page in page_iterator:
                name_to_arn_map.update(map(lambda x: (x['PolicyName'], x['Arn']), page['Policies']))

            self._policy_map = name_to_arn_map
        return self._policy_map
