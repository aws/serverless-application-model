from unittest.mock import patch

import pytest
from samtranslator.policy_template_processor.processor import PolicyTemplatesProcessor


@pytest.fixture(autouse=True, scope="session")
def validate_default_policy_templates_once():
    """
    Every translation validates the default policy templates, which takes about half of the translation time.
    Validate them once per session instead. Other policy templates are still validated on every call.
    """
    default_policy_templates = PolicyTemplatesProcessor.get_default_policy_templates_json()
    is_valid_templates_dict = PolicyTemplatesProcessor._is_valid_templates_dict
    is_valid_templates_dict(default_policy_templates)

    def is_valid_or_default(policy_templates_dict, schema=None):
        if schema is None and policy_templates_dict == default_policy_templates:
            return True
        return is_valid_templates_dict(policy_templates_dict, schema)

    with patch.object(PolicyTemplatesProcessor, "_is_valid_templates_dict", staticmethod(is_valid_or_default)):
        yield
