"""
Compatibility methods to support Python 2.7 style hashing in Python 3.X+

This is designed for compatibility not performance.
"""

import ctypes
import math


def hash27(value):
    """
    Wrapper call to Hash.hash()

    Args:
        value: input value

    Returns:
        Python 2.7 hash
    """

    return Hash.hash(value)


class Hash(object):
    """
    Various hashing methods using Python 2.7's algorithms
    """

    @staticmethod
    def hash(value):
        """
        Returns a Python 2.7 hash for a value.

        Args:
            value: input value

        Returns:
            Python 2.7 hash
        """

        if isinstance(value, tuple):
            return Hash.thash(value)
        if isinstance(value, float):
            return Hash.fhash(value)
        if isinstance(value, int):
            return hash(value)
        if isinstance(value, ("".__class__, bytes)) or type(value).__name__ == "buffer":
            return Hash.shash(value)

        raise TypeError("unhashable type: '%s'" % (type(value).__name__))

    @staticmethod
    def thash(value):
        """
        Returns a Python 2.7 hash for a tuple.

        Logic ported from the 2.7 Python branch: cpython/Objects/tupleobject.c
        Method: static long tuplehash(PyTupleObject *v)

        Args:
            value: input tuple

        Returns:
            Python 2.7 hash
        """

        length = len(value)

        mult = 1000003

        x = 0x345678
        for y in value:
            length -= 1

            y = Hash.hash(y)
            x = (x ^ y) * mult
            mult += 82520 + length + length

        x += 97531

        if x == -1:
            x = -2

        # Convert to C type
        return ctypes.c_long(x).value

    @staticmethod
    def fhash(value):
        """
        Returns a Python 2.7 hash for a float.

        Logic ported from the 2.7 Python branch: cpython/Objects/object.c
        Method: long _Py_HashDouble(double v)

        Args:
            value: input float

        Returns:
            Python 2.7 hash
        """

        fpart = math.modf(value)
        if fpart[0] == 0.0:
            return hash(int(fpart[1]))

        v, e = math.frexp(value)

        # 2**31
        v *= 2147483648.0

        # Top 32 bits
        hipart = int(v)

        # Next 32 bits
        v = (v - float(hipart)) * 2147483648.0

        x = hipart + int(v) + (e << 15)
        if x == -1:
            x = -2

        # Convert to C long type
        return ctypes.c_long(x).value

    @staticmethod
    def shash(value):
        """
        Returns a Python 2.7 hash for a string.

        Logic ported from the 2.7 Python branch: cpython/Objects/stringobject.c
        Method: static long string_hash(PyStringObject *a)

        Args:
            value: input string

        Returns:
            Python 2.7 hash
        """

        length = len(value)

        if length == 0:
            return 0

        x = Hash.ordinal(value[0]) << 7
        for c in value:
            x = (1000003 * x) ^ Hash.ordinal(c)

        x ^= length
        x &= 0xFFFFFFFFFFFFFFFF
        if x == -1:
            x = -2

        # Convert to C long type
        return ctypes.c_long(x).value

    @staticmethod
    def ordinal(value):
        """
        Converts value to an ordinal or returns the input value if it's an int.

        Args:
            value: input

        Returns:
            ordinal for value
        """

        return value if isinstance(value, int) else ord(value)
