from urllib.parse import urlparse, parse_qs
from samtranslator.model.exceptions import InvalidResourceException


def parse_s3_uri(uri):
    """Parses a S3 Uri into a dictionary of the Bucket, Key, and VersionId

    :return: a BodyS3Location dict or None if not an S3 Uri
    :rtype: dict
    """
    if not isinstance(uri, str):
        return None

    url = urlparse(uri)
    query = parse_qs(url.query)

    if url.scheme == "s3" and url.netloc and url.path:
        s3_pointer = {"Bucket": url.netloc, "Key": url.path.lstrip("/")}
        if "versionId" in query and len(query["versionId"]) == 1:
            s3_pointer["Version"] = query["versionId"][0]
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


def construct_image_code_object(image_uri, logical_id, property_name):
    """Constructs a Lambda `Code` or `Content` property, from the SAM `ImageUri` property.
    This follows the current scheme for Lambda Functions.

    :param string image_uri: string
    :param string logical_id: logical_id of the resource calling this function
    :param string property_name: name of the property which is used as an input to this function.
    :returns: a Code dict, containing the ImageUri.
    :rtype: dict
    """
    if not image_uri:
        raise InvalidResourceException(
            logical_id, "'{}' requires that a image hosted at a registry be specified.".format(property_name)
        )

    return {"ImageUri": image_uri}


def construct_s3_location_object(location_uri, logical_id, property_name):
    """Constructs a Lambda `Code` or `Content` property, from the SAM `CodeUri` or `ContentUri` property.
    This follows the current scheme for Lambda Functions and LayerVersions.

    :param dict or string location_uri: s3 location dict or string
    :param string logical_id: logical_id of the resource calling this function
    :param string property_name: name of the property which is used as an input to this function.
    :returns: a Code dict, containing the S3 Bucket, Key, and Version of the Lambda layer code
    :rtype: dict
    """
    if isinstance(location_uri, dict):
        if not location_uri.get("Bucket") or not location_uri.get("Key"):
            # location_uri is a dictionary but does not contain Bucket or Key property
            raise InvalidResourceException(
                logical_id, "'{}' requires Bucket and Key properties to be specified.".format(property_name)
            )

        s3_pointer = location_uri

    else:
        # location_uri is NOT a dictionary. Parse it as a string
        s3_pointer = parse_s3_uri(location_uri)

        if s3_pointer is None:
            raise InvalidResourceException(
                logical_id,
                "'{}' is not a valid S3 Uri of the form "
                "'s3://bucket/key' with optional versionId query "
                "parameter.".format(property_name),
            )

    code = {"S3Bucket": s3_pointer["Bucket"], "S3Key": s3_pointer["Key"]}
    if "Version" in s3_pointer:
        code["S3ObjectVersion"] = s3_pointer["Version"]
    return code
