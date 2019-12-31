from unittest import TestCase

from samtranslator.model.tags.resource_tagging import get_tag_list


class TestResourceTagging(TestCase):
    def test_get_tag_list_returns_default_tag_list_values(self):
        tag_list = get_tag_list(None)
        expected_tag_list = []

        self.assertEqual(tag_list, expected_tag_list)

    def test_get_tag_list_with_tag_dictionary_with_key_only(self):
        tag_list = get_tag_list({"key": None})
        expected_tag_list = [{"Key": "key", "Value": ""}]

        self.assertEqual(tag_list, expected_tag_list)

    def test_get_tag_list_with_tag_dictionary(self):
        tag_list = get_tag_list({"AnotherKey": "This time with a value"})
        expected_tag_list = [{"Key": "AnotherKey", "Value": "This time with a value"}]

        self.assertEqual(tag_list, expected_tag_list)
