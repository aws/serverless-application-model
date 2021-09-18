"""
"""

import ctypes
import copy
import json
import sys
import logging

from samtranslator.third_party.py27hash.hash import Hash
from six import string_types


LOG = logging.getLogger(__name__)
# Constants based on Python2.7 dictionary
# See: https://github.com/python/cpython/blob/v2.7.18/Objects/dictobject.c
MINSIZE = 8
PERTURB_SHIFT = 5

unicode_string_type = str if sys.version_info.major >= 3 else unicode


class Py27UniStr(unicode_string_type):
    """
    A string subclass to allow string be recognized as Python2 unicode string
    To preserve the instance type in string operations, we need to override certain methods
    """
    def __add__(self, other):
        return Py27UniStr(super(Py27UniStr, self).__add__(other))

    def __repr__(self):
        if sys.version_info.major >= 3:
            return "u" + super(Py27UniStr, self).__repr__()
        return super(Py27UniStr, self).__repr__()

    def upper(self):
        return Py27UniStr(super(Py27UniStr, self).upper())

    def lower(self):
        return Py27UniStr(super(Py27UniStr, self).lower())

    def replace(self, __old, __new, __count=None):
        if __count:
            return Py27UniStr(super(Py27UniStr, self).replace(__old, __new, __count))
        return Py27UniStr(super(Py27UniStr, self).replace(__old, __new))

    def split(self, sep=None, maxsplit=-1):
        return [Py27UniStr(s) for s in super(Py27UniStr, self).split(sep, maxsplit)]
