from mock import MagicMock
from samtranslator.translator.managed_policy_translator import ManagedPolicyLoader


def create_page(policies):
    return {
        'Policies': map(lambda x: {'PolicyName': x[0], 'Arn': x[1]}, policies)
    }


def test_load_local():
    paginator = MagicMock()
    iam = MagicMock()
    iam.get_paginator.return_value = paginator

    actual = ManagedPolicyLoader(iam).load()

    assert not iam.get_paginator.called
    assert isinstance(actual, dict)
    assert actual.get('AmazonMechanicalTurkCrowdFullAccess')

    # NOTE: this is a moving target that must be updated when ManagedPolicyLoader._local_managed_policies_map is updated
    assert len(actual) == 401


def test_load():
    paginator = MagicMock()
    paginator.paginate.return_value = [
        create_page([
            ('Policy-1', 'Arn-1'),
            ('Policy-2', 'Arn-2'),
            ('Policy-3', 'Arn-3'),
            ('Policy-4', 'Arn-4'),
        ]),
        create_page([
            ('Policy-a', 'Arn-a'),
            ('Policy-b', 'Arn-b'),
            ('Policy-c', 'Arn-c'),
            ('Policy-d', 'Arn-d'),
        ]),
        create_page([
            ('Policy-final', 'Arn-final'),
        ]),
    ]

    iam = MagicMock()
    iam.get_paginator.return_value = paginator

    actual = ManagedPolicyLoader(iam).load(use_local_managed_policies=False)
    expected = {
        'Policy-1': 'Arn-1',
        'Policy-2': 'Arn-2',
        'Policy-3': 'Arn-3',
        'Policy-4': 'Arn-4',
        'Policy-a': 'Arn-a',
        'Policy-b': 'Arn-b',
        'Policy-c': 'Arn-c',
        'Policy-d': 'Arn-d',
        'Policy-final': 'Arn-final'
    }
    assert actual == expected

    iam.get_paginator.assert_called_once_with('list_policies')
    paginator.paginate.assert_called_once_with(Scope='AWS')
