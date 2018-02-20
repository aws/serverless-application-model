#
# Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import re

ARN_FIELD_REGEX = \
    'arn:aws:lambda:([a-z]{2}-[a-z]+-\d{1}):(\d{12}):function:([a-zA-Z0-9-_]+)(?::(\$LATEST|[a-zA-Z0-9-_]+))?'


class FunctionArnFields:
    """
    This class takes in a string representing a Lambda function's ARN (the qualifier is optional), parses that string
    into individual fields for region, account_id, name and qualifier. It also has a static method for creating a
    Function ARN string from those subfields.
    """
    @staticmethod
    def build_arn_string(region, account_id, name, qualifier):
        if qualifier:
            return 'arn:aws:lambda:{region}:{account_id}:function:{name}:{qualifier}'.format(
                region=region, account_id=account_id, name=name, qualifier=qualifier
            )
        else:
            return 'arn:aws:lambda:{region}:{account_id}:function:{name}'.format(
                region=region, account_id=account_id, name=name
            )

    def __init__(self, function_arn_string):
        self.parse_function_arn(function_arn_string)

    def parse_function_arn(self, function_arn_string):
        regex_match = re.match(ARN_FIELD_REGEX, function_arn_string)
        if regex_match:
            region, account_id, name, qualifier = map(
                lambda s: s.replace(':', '') if s else s, regex_match.groups()
            )
        else:
            raise ValueError('Cannot parse given string as a function ARN.')

        self.region = region
        self.account_id = account_id
        self.name = name
        self.qualifier = qualifier

    def to_arn_string(self):
        return FunctionArnFields.build_arn_string(self.region, self.account_id, self.name, self.qualifier)
