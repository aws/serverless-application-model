import warnings
from unittest import TestCase

from samtranslator.internal.deprecation_control import deprecated


def replacement_function(x, y):
    return x + y


@deprecated(replacement="replacement_function")
def deprecated_function(x, y):
    return x + y


class TestDeprecationControl(TestCase):
    def test_deprecated_decorator(self):
        with warnings.catch_warnings(record=True) as w:
            deprecated_function(1, 1)
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertIn(
                "deprecated_function is deprecated and will be removed in a future release, "
                "please use replacement_function",
                str(w[-1].message),
            )
