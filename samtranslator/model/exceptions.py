class InvalidDocumentException(Exception):
    """Exception raised when the given document is invalid and cannot be transformed.

    Attributes:
        message -- explanation of the error
        causes -- list of errors which caused this document to be invalid
    """

    def __init__(self, causes):
        self._causes = causes

    @property
    def message(self):
        return "Invalid Serverless Application Specification document. Number of errors found: {}.".format(
            len(self.causes)
        )

    @property
    def causes(self):
        return self._causes


class DuplicateLogicalIdException(Exception):
    """Exception raised when a transformation adds a resource with a logical id which already exists.
    Attributes:
        message -- explanation of the error
    """

    def __init__(self, logical_id, duplicate_id, type):
        self._logical_id = logical_id
        self._duplicate_id = duplicate_id
        self._type = type

    @property
    def message(self):
        return (
            "Transforming resource with id [{logical_id}] attempts to create a new"
            ' resource with id [{duplicate_id}] and type "{type}". A resource with that id already'
            " exists within this template. Please use a different id for that resource.".format(
                logical_id=self._logical_id, type=self._type, duplicate_id=self._duplicate_id
            )
        )


class InvalidTemplateException(Exception):
    """Exception raised when the template structure is invalid

    Attributes
        message -- explanation of the error
    """

    def __init__(self, message):
        self._message = message

    @property
    def message(self):
        return "Structure of the SAM template is invalid. {}".format(self._message)


class InvalidResourceException(Exception):
    """Exception raised when a resource is invalid.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, logical_id, message):
        self._logical_id = logical_id
        self._message = message

    def __lt__(self, other):
        return self._logical_id < other._logical_id

    @property
    def message(self):
        return "Resource with id [{}] is invalid. {}".format(self._logical_id, self._message)


class InvalidEventException(Exception):
    """Exception raised when an event is invalid.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, event_id, message):
        self._event_id = event_id
        self._message = message

    @property
    def message(self):
        return "Event with id [{}] is invalid. {}".format(self._event_id, self._message)


def prepend(exception, message, end=": "):
    """Prepends the first argument (i.e., the exception message) of the a BaseException with the provided message.
    Useful for reraising exceptions with additional information.

    :param BaseException exception: the exception to prepend
    :param str message: the message to prepend
    :param str end: the separator to add to the end of the provided message
    :returns: the exception
    """
    exception.args = exception.args or ("",)
    exception.args = (message + end + exception.args[0],) + exception.args[1:]
    return exception
