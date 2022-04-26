# Utils for requests
import logging

import requests

from integration.config.logger_configurations import CustomLoggers


REQUEST_LOGGER = logging.getLogger(__name__)
CustomLoggers.configure_request_logger(REQUEST_LOGGER)

# Relevant headers that should be captured for debugging
AMAZON_HEADERS = [
    "x-amzn-requestid",
    "x-amz-apigw-id",
    "x-amz-cf-id",
    "x-amzn-errortype",
    "apigw-requestid",
]


class RequestUtils:

    def __init__(self):
        self.response = None
        self.headers = None

    def _get_amazon_headers(self):
        """
        Get a list of relevant amazon headers that could be useful for debugging
        """
        amazon_headers = {}
        for header, header_val in self.headers.items():
            if header in AMAZON_HEADERS:
                amazon_headers[header] = header_val
        return amazon_headers

    def _normalize_response_headers(self):
        """
        API gateway can return headers with letters in different cases i.e. x-amzn-requestid or x-amzn-requestId
        We make them all lowercase here to more easily match them up
        """
        if self.response is None or not self.response.headers:
            # Need to check for response is None here since the __bool__ method checks 200 <= status < 400
            return {}

        return dict((k.lower(), v) for k, v in self.response.headers.items())

    def do_get_request_with_logging(self, url):
        REQUEST_LOGGER.info("Making request to " + url)
        self.response = requests.get(url)
        self.headers = self._normalize_response_headers()
        status = self.response.status_code
        amazon_headers = self._get_amazon_headers()
        REQUEST_LOGGER.info("Calling API Gateway", extra={"status": status, "headers": amazon_headers})
        return self.response
