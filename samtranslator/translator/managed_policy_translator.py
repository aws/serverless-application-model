from samtranslator.policy_template_processor.processor import PolicyTemplatesProcessor


class ManagedPolicyLoader(object):
    _local_managed_policies_map = PolicyTemplatesProcessor.get_managed_policies_json()

    def __init__(self, iam_client):
        self._iam_client = iam_client
        self._policy_map = None

    def load(self, use_local_managed_policies=True):
        if use_local_managed_policies:
            return ManagedPolicyLoader._local_managed_policies_map

        paginator = self._iam_client.get_paginator('list_policies')
        # Setting the scope to AWS limits the returned values to only AWS Managed Policies and will
        # not returned policies owned by any specific account.
        # http://docs.aws.amazon.com/IAM/latest/APIReference/API_ListPolicies.html#API_ListPolicies_RequestParameters
        page_iterator = paginator.paginate(Scope='AWS')
        name_to_arn_map = {}

        for page in page_iterator:
            name_to_arn_map.update(map(lambda x: (x['PolicyName'], x['Arn']), page['Policies']))

        self._policy_map = name_to_arn_map

        # NOTE: Uncomment the line below and set use_local_managed_policies=False to easily
        # get the latest list of managed policies in order to update the local list above.
        # print(name_to_arn_map, len(name_to_arn_map))

        return self._policy_map
