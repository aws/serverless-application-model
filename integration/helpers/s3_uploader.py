"""
Client for uploading files to s3
"""

import logging
from typing import Any

from botocore.exceptions import ClientError

LOG = logging.getLogger(__name__)


class S3Uploader:
    """
    Class to upload objects to S3 bucket.
    """

    def __init__(
        self,
        s3_client: Any,
        bucket_name: str,
    ):
        self.s3_client = s3_client
        self.bucket_name = bucket_name

    def upload_file(self, file_name, file_path):
        """
        Uploads given file to S3
        :param file_name:  the file name as s3 bucket key
        :param file_path: Path to the file that will be uploaded
        """
        try:
            LOG.debug("Uploading file %s to bucket %s", file_name, self.bucket_name)
            self.s3_client.upload_file(Filename=file_path, Bucket=self.bucket_name, Key=file_name)
            LOG.debug("File %s uploaded successfully to bucket %s", file_name, self.bucket_name)
        except ClientError as error:
            LOG.error("Upload of file %s to bucket %s failed", file_name, self.bucket_name, exc_info=error)
            raise error

    def get_s3_uri(self, file_name):
        """
        This link describes the format of Path Style URLs
        http://docs.aws.amazon.com/AmazonS3/latest/dev/UsingBucket.html#access-bucket-intro
        """
        base = self.s3_client.meta.endpoint_url
        result = f"{base}/{self.bucket_name}/{file_name}"
        return result
