from abc import ABC, abstractmethod
from typing import List, Optional, Sequence, Union


class ExceptionWithMessage(ABC, Exception):
    @property
    @abstractmethod
    def message(self) -> str:
        """Return the exception message."""


class InvalidDocumentException(ExceptionWithMessage):
    """Exception raised when the given document is invalid and cannot be transformed.

    Attributes:
        message -- explanation of the error
        causes -- list of errors which caused this document to be invalid
    """

    def __init__(self, causes: Sequence[ExceptionWithMessage]):
        self._causes = causes

    @property
    def message(self) -> str:
        return "Invalid Serverless Application Specification document. Number of errors found: {}.".format(
            len(self.causes)
        )

    @property
    def causes(self) -> Sequence[ExceptionWithMessage]:
        return self._causes


class DuplicateLogicalIdException(ExceptionWithMessage):
    """Exception raised when a transformation adds a resource with a logical id which already exists.
    Attributes:
        message -- explanation of the error
    """

    def __init__(self, logical_id, duplicate_id, type):  # type: ignore[no-untyped-def]
        self._logical_id = logical_id
        self._duplicate_id = duplicate_id
        self._type = type

    @property
    def message(self):  # type: ignore[no-untyped-def]
        return (
            "Transforming resource with id [{logical_id}] attempts to create a new"
            ' resource with id [{duplicate_id}] and type "{type}". A resource with that id already'
            " exists within this template. Please use a different id for that resource.".format(
                logical_id=self._logical_id, type=self._type, duplicate_id=self._duplicate_id
            )
        )


class InvalidTemplateException(ExceptionWithMessage):
    """Exception raised when the template structure is invalid

    Attributes
        message -- explanation of the error
    """

    def __init__(self, message: str) -> None:
        self._message = message

    @property
    def message(self) -> str:
        return "Structure of the SAM template is invalid. {}".format(self._message)


class InvalidResourceException(ExceptionWithMessage):
    """Exception raised when a resource is invalid.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, logical_id: Union[str, List[str]], message: str) -> None:
        self._logical_id = logical_id
        self._message = message

    def __lt__(self, other):  # type: ignore[no-untyped-def]
        return self._logical_id < other._logical_id

    @property
    def message(self) -> str:
        return "Resource with id [{}] is invalid. {}".format(self._logical_id, self._message)


class InvalidEventException(ExceptionWithMessage):
    """Exception raised when an event is invalid.

    Attributes:
        message -- explanation of the error
    """

    # Note: event_id should not be None, but currently there are too many
    # usage of this class with `event_id` being Optional.
    # TODO: refactor the code to make type correct.
    def __init__(self, event_id: Optional[str], message: str) -> None:
        self._event_id = event_id
        self._message = message

    @property
    def message(self) -> str:
        return "Event with id [{}] is invalid. {}".format(self._event_id, self._message)


def prepend(exception, message, end=": "):  # type: ignore[no-untyped-def]
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
