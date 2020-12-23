"""
Logic for uploading to S3 per Cloudformation Specific Resource
This was ported over from the sam-cli repo
"""
# pylint: disable=no-member

# Copyright 2012-2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import os
import tempfile
import contextlib
from contextlib import contextmanager

try:
    from urllib.parse import urlparse, parse_qs
except ImportError:  # py2
    from urlparse import urlparse, parse_qs
import uuid


def parse_s3_url(url, bucket_name_property="Bucket", object_key_property="Key", version_property=None):

    if isinstance(url, str) and url.startswith("s3://"):

        parsed = urlparse(url)
        query = parse_qs(parsed.query)

        if parsed.netloc and parsed.path:
            result = dict()
            result[bucket_name_property] = parsed.netloc
            result[object_key_property] = parsed.path.lstrip("/")

            # If there is a query string that has a single versionId field,
            # set the object version and return
            if version_property is not None and "versionId" in query and len(query["versionId"]) == 1:
                result[version_property] = query["versionId"][0]

            return result

    raise ValueError("URL given to the parse method is not a valid S3 url " "{0}".format(url))


@contextmanager
def mktempfile():
    directory = tempfile.gettempdir()
    filename = os.path.join(directory, uuid.uuid4().hex)

    try:
        with open(filename, "w+") as handle:
            yield handle
    finally:
        if os.path.exists(filename):
            os.remove(filename)
