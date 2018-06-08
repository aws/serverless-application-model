from unittest import TestCase

from mock import MagicMock

from samtranslator.translator.managed_policy_translator import ManagedPolicyLoader


class TestManagedPoliciesTranslator(TestCase):
    def create_page(self, policies):
        return {
            'Policies': map(lambda x: {'PolicyName': x[0], 'Arn': x[1]}, policies)
        }

    def test_load(self):
        paginator = MagicMock()
        paginator.paginate.return_value = [
            self.create_page([
                ('Policy-1', 'Arn-1'),
                ('Policy-2', 'Arn-2'),
                ('Policy-3', 'Arn-3'),
                ('Policy-4', 'Arn-4'),
            ]),
            self.create_page([
                ('Policy-a', 'Arn-a'),
                ('Policy-b', 'Arn-b'),
                ('Policy-c', 'Arn-c'),
                ('Policy-d', 'Arn-d'),
            ]),
            self.create_page([
                ('Policy-final', 'Arn-final'),
            ]),
        ]

        iam = MagicMock()
        iam.get_paginator.return_value = paginator

        actual = ManagedPolicyLoader(iam).load()
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
        self.assertEquals(actual, expected)

        iam.get_paginator.assert_called_once_with('list_policies')
        paginator.paginate.assert_called_once_with(Scope='AWS')
