from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Union


class ExpectedType(Enum):
    MAP = ("map", dict)
    LIST = ("list", list)
    STRING = ("string", str)
    INTEGER = ("integer", int)
    BOOLEAN = ("boolean", bool)


class ExceptionWithMessage(ABC, Exception):
    @property
    @abstractmethod
    def message(self) -> str:
        """Return the exception message."""

    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        """Return the exception metadata."""


class InvalidDocumentException(ExceptionWithMessage):
    """Exception raised when the given document is invalid and cannot be transformed.

    Attributes:
        message -- explanation of the error
        metadata -- a dictionary of metadata (key, value pair)
        causes -- list of errors which caused this document to be invalid
    """

    def __init__(self, causes: Sequence[ExceptionWithMessage]) -> None:
        self._causes = list(causes)
        # Sometimes, the same error could be raised from different plugins,
        # so here we do a deduplicate based on the message:
        self._causes = list({cause.message: cause for cause in self._causes}.values())

    @property
    def message(self) -> str:
        return f"Invalid Serverless Application Specification document. Number of errors found: {len(self.causes)}."

    @property
    def metadata(self) -> Dict[str, List[Any]]:
        # Merge metadata in each exception to one single metadata dictionary
        metadata_dict = defaultdict(list)
        for cause in self.causes:
            if not cause.metadata:
                continue
            for k, v in cause.metadata.items():
                metadata_dict[k].append(v)
        return metadata_dict

    @property
    def causes(self) -> Sequence[ExceptionWithMessage]:
        return self._causes


class DuplicateLogicalIdException(ExceptionWithMessage):
    """Exception raised when a transformation adds a resource with a logical id which already exists.
    Attributes:
        message -- explanation of the error
    """

    def __init__(self, logical_id: str, duplicate_id: str, resource_type: str) -> None:
        self._logical_id = logical_id
        self._duplicate_id = duplicate_id
        self._type = resource_type

    @property
    def message(self) -> str:
        return (
            f"Transforming resource with id [{self._logical_id}] attempts to create a new"
            f' resource with id [{self._duplicate_id}] and type "{self._type}". A resource with that id already'
            " exists within this template. Please use a different id for that resource."
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
        return f"Structure of the SAM template is invalid. {self._message}"


class InvalidResourceException(ExceptionWithMessage):
    """Exception raised when a resource is invalid.

    Attributes:
        message -- explanation of the error
    """

    def __init__(
        self, logical_id: Union[str, List[str]], message: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        self._logical_id = logical_id
        self._message = message
        self._metadata = metadata

    def __lt__(self, other):  # type: ignore[no-untyped-def]
        return self._logical_id < other._logical_id

    @property
    def message(self) -> str:
        return f"Resource with id [{self._logical_id}] is invalid. {self._message}"

    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        return self._metadata


class InvalidResourcePropertyTypeException(InvalidResourceException):
    def __init__(
        self,
        logical_id: str,
        key_path: str,
        expected_type: Optional[ExpectedType],
        message: Optional[str] = None,
    ) -> None:
        message = message or self._default_message(key_path, expected_type)
        super().__init__(logical_id, message)

        self.key_path = key_path

    @staticmethod
    def _default_message(key_path: str, expected_type: Optional[ExpectedType]) -> str:
        if expected_type:
            type_description, _ = expected_type.value
            return f"Property '{key_path}' should be a {type_description}."
        return f"Type of property '{key_path}' is invalid."


class InvalidResourceAttributeTypeException(InvalidResourceException):
    def __init__(
        self,
        logical_id: str,
        key_path: str,
        expected_type: Optional[ExpectedType],
        message: Optional[str] = None,
    ) -> None:
        message = message or self._default_message(logical_id, key_path, expected_type)
        super().__init__(logical_id, message)

    @staticmethod
    def _default_message(logical_id: str, key_path: str, expected_type: Optional[ExpectedType]) -> str:
        if expected_type:
            type_description, _ = expected_type.value
            return f"Attribute '{key_path}' should be a {type_description}."
        return f"Type of attribute '{key_path}' is invalid."


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
        return f"Event with id [{self._event_id}] is invalid. {self._message}"


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
