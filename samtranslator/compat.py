try:
    from pydantic import v1 as pydantic

    # Starting Pydantic v1.10.17, pydantic import v1 will success,
    # adding the following line to make Pydantic v1 should fall back to v1 import correctly.
    pydantic.error_wrappers.ValidationError  # noqa
except ImportError:
    # Unfortunately mypy cannot handle this try/expect pattern, and "type: ignore"
    # is the simplest work-around. See: https://github.com/python/mypy/issues/1153
    import pydantic  # type: ignore
except AttributeError:
    # Pydantic v1.10.17+
    import pydantic  # type: ignore

__all__ = ["pydantic"]
