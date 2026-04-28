"""Unit tests for :mod:`samtranslator.model.s3_utils.uri_parser`."""

from unittest import TestCase

from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.s3_utils.uri_parser import construct_s3_location_object, parse_s3_uri


class TestParseS3Uri(TestCase):
    def test_valid_s3_uri(self):
        self.assertEqual(
            parse_s3_uri("s3://bucket/key"),
            {"Bucket": "bucket", "Key": "key"},
        )

    def test_valid_s3_uri_with_version(self):
        self.assertEqual(
            parse_s3_uri("s3://bucket/key?versionId=abcdef"),
            {"Bucket": "bucket", "Key": "key", "Version": "abcdef"},
        )

    def test_non_s3_scheme_returns_none(self):
        self.assertIsNone(parse_s3_uri("https://example.com/key"))

    def test_non_string_returns_none(self):
        self.assertIsNone(parse_s3_uri({"Bucket": "b", "Key": "k"}))
        self.assertIsNone(parse_s3_uri(None))

    def test_unresolved_cdk_token_returns_none(self):
        """Bracketed host segments that are not valid IPv4/IPv6 raise ValueError
        from urllib (see CVE-2024-11168); parse_s3_uri should treat the input as
        "not a valid S3 URI" and return None so callers can raise a friendly
        InvalidResourceException instead of crashing the transform.
        """
        self.assertIsNone(parse_s3_uri("s3://[TOKEN.25]/my/key"))
        self.assertIsNone(parse_s3_uri("https://[TOKEN.25]/path"))
        self.assertIsNone(parse_s3_uri("s3://bucket-[TOKEN.25]/key"))


class TestConstructS3LocationObjectWithMalformedUri(TestCase):
    """Verify that the top-level helper raises InvalidResourceException with the
    logical id instead of letting the underlying urllib ValueError propagate.
    """

    def test_unresolved_cdk_token_raises_invalid_resource_exception(self):
        with self.assertRaises(InvalidResourceException) as ctx:
            construct_s3_location_object("s3://[TOKEN.25]/my/key", "MyFunction", "CodeUri")
        self.assertIn("MyFunction", str(ctx.exception))
        self.assertIn("'CodeUri' is not a valid S3 Uri", str(ctx.exception))
