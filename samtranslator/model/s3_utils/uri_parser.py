from urlparse import urlparse, parse_qs

from six import string_types


def parse_s3_uri(uri):
    """Parses a S3 Uri into a dictionary of the Bucket, Key, and VersionId

    :return: a BodyS3Location dict or None if not an S3 Uri
    :rtype: dict
    """
    if not isinstance(uri, string_types):
        return None

    url = urlparse(uri)
    query = parse_qs(url.query)

    if url.scheme == 's3' and url.netloc and url.path:
        s3_pointer = {
            'Bucket': url.netloc,
            'Key': url.path.lstrip('/')
        }
        if 'versionId' in query and len(query['versionId']) == 1:
            s3_pointer['Version'] = query['versionId'][0]
        return s3_pointer
    else:
        return None


def to_s3_uri(code_dict):
    """Constructs a S3 URI string from given code dictionary

    :param dict code_dict: Dictionary containing Lambda function Code S3 location of the form
                          {S3Bucket, S3Key, S3ObjectVersion}
    :return: S3 URI of form s3://bucket/key?versionId=version
    :rtype string
    """

    try:
        uri = "s3://{bucket}/{key}".format(bucket=code_dict["S3Bucket"], key=code_dict["S3Key"])
        version = code_dict.get("S3ObjectVersion", None)
    except (TypeError, AttributeError):
        raise TypeError("Code location should be a dictionary")

    if version:
            uri += "?versionId=" + version

    return uri
