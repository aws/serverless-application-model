try:
    from pydantic import v1 as pydantic
except ImportError:
    # Unfortunately mypy cannot handle this try/expect pattern, and "type: ignore"
    # is the simplest work-around. See: https://github.com/python/mypy/issues/1153
    import pydantic  # type: ignore

__all__ = ["pydantic"]
