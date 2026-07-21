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


class TestConstructS3LocationObject(TestCase):
    def test_dict_with_bucket_and_key(self):
        result = construct_s3_location_object({"Bucket": "b", "Key": "k"}, "Fn", "CodeUri")
        self.assertEqual(result, {"S3Bucket": "b", "S3Key": "k"})

    def test_dict_with_version(self):
        result = construct_s3_location_object(
            {"Bucket": "b", "Key": "k", "Version": "v1"}, "Fn", "CodeUri"
        )
        self.assertEqual(result, {"S3Bucket": "b", "S3Key": "k", "S3ObjectVersion": "v1"})

    def test_dict_with_storage_mode(self):
        result = construct_s3_location_object(
            {"Bucket": "b", "Key": "k", "StorageMode": "SingleObject"}, "Fn", "CodeUri"
        )
        self.assertEqual(result, {"S3Bucket": "b", "S3Key": "k", "S3ObjectStorageMode": "SingleObject"})

    def test_dict_with_all_optional_fields(self):
        result = construct_s3_location_object(
            {"Bucket": "b", "Key": "k", "Version": "v1", "StorageMode": "SingleObject"}, "Fn", "CodeUri"
        )
        self.assertEqual(
            result, {"S3Bucket": "b", "S3Key": "k", "S3ObjectVersion": "v1", "S3ObjectStorageMode": "SingleObject"}
        )

    def test_s3_uri_string(self):
        result = construct_s3_location_object("s3://bucket/path/key", "Fn", "CodeUri")
        self.assertEqual(result, {"S3Bucket": "bucket", "S3Key": "path/key"})

    def test_dict_missing_bucket_raises(self):
        with self.assertRaises(InvalidResourceException):
            construct_s3_location_object({"Key": "k"}, "Fn", "CodeUri")

    def test_dict_missing_key_raises(self):
        with self.assertRaises(InvalidResourceException):
            construct_s3_location_object({"Bucket": "b"}, "Fn", "CodeUri")

    def test_invalid_type_raises(self):
        with self.assertRaises(InvalidResourceException):
            construct_s3_location_object(42, "Fn", "CodeUri")  # type: ignore[arg-type]


class TestConstructS3LocationObjectWithMalformedUri(TestCase):
    """Verify that the top-level helper raises InvalidResourceException with the
    logical id instead of letting the underlying urllib ValueError propagate.
    """

    def test_unresolved_cdk_token_raises_invalid_resource_exception(self):
        with self.assertRaises(InvalidResourceException) as ctx:
            construct_s3_location_object("s3://[TOKEN.25]/my/key", "MyFunction", "CodeUri")
        self.assertIn("MyFunction", str(ctx.exception))
        self.assertIn("'CodeUri' is not a valid S3 Uri", str(ctx.exception))
