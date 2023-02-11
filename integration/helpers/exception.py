from py.error import Error


class StatusCodeError(Error):
    """raise when the return status code is not match the expected one"""
