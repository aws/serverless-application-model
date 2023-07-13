from unittest import TestCase

import pytest
from samtranslator.internal.deprecation_control import deprecated


def replacement_function(x, y):
    return x + y


@deprecated(replacement="replacement_function")
def deprecated_function(x, y):
    return x + y


class TestDeprecationControl(TestCase):
    def test_deprecated_decorator(self):
        with pytest.warns(DeprecationWarning):
            deprecated_function(1, 1)
