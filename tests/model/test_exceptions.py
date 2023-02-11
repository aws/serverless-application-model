from unittest import TestCase

from samtranslator.model.exceptions import (
    DuplicateLogicalIdException,
    InvalidDocumentException,
    InvalidEventException,
    InvalidResourceException,
    InvalidTemplateException,
)


class TestExceptions(TestCase):
    def setUp(self) -> None:
        self.invalid_template = InvalidTemplateException("foo")
        self.duplicate_id = DuplicateLogicalIdException("foo", "bar", "type")
        self.invalid_resource = InvalidResourceException("foo", "bar")
        self.invalid_event = InvalidEventException("foo", "bar")
        self.invalid_resource_with_metadata = InvalidResourceException("foo-bar", "foo", {"hello": "world"})

    def test_invalid_template(self):
        self.assertEqual(self.invalid_template.metadata, None)
        self.assertIn("Structure of the SAM template is invalid", self.invalid_template.message)

    def test_duplicate_id(self):
        self.assertEqual(self.duplicate_id.metadata, None)
        self.assertIn("Transforming resource with id", self.duplicate_id.message)

    def test_invalid_resource_without_metadata(self):
        self.assertEqual(self.invalid_resource.metadata, None)
        self.assertIn("Resource with id [foo] is invalid", self.invalid_resource.message)

    def test_invalid_resource_with_metadata(self):
        self.assertEqual(self.invalid_resource_with_metadata.metadata, {"hello": "world"})
        self.assertIn("Resource with id [foo-bar] is invalid", self.invalid_resource_with_metadata.message)

    def test_invalid_event(self):
        self.assertEqual(self.invalid_event.metadata, None)
        self.assertIn("Event with id [foo] is invalid.", self.invalid_event.message)

    def test_invalid_document_exceptions(self):
        unsupported_connector_profile = InvalidResourceException("hello", "world", {"KEY": {"C": "D"}})
        unsupported_connector_profile2 = InvalidResourceException("foobar", "bar", {"KEY": {"A": "B"}})
        self.assertEqual(unsupported_connector_profile.metadata, {"KEY": {"C": "D"}})
        self.assertEqual(unsupported_connector_profile2.metadata, {"KEY": {"A": "B"}})

        invalid_document_exception = InvalidDocumentException(
            [
                self.invalid_template,
                self.duplicate_id,
                self.invalid_resource,
                self.invalid_event,
                self.invalid_resource_with_metadata,
                unsupported_connector_profile,
                unsupported_connector_profile2,
            ]
        )
        self.assertEqual(
            "Invalid Serverless Application Specification document. Number of errors found: 7.",
            invalid_document_exception.message,
        )
        self.assertEqual(
            invalid_document_exception.metadata,
            {"hello": ["world"], "KEY": [{"C": "D"}, {"A": "B"}]},
        )
