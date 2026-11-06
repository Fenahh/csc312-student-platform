"""Input normalization helpers for Commons search/discovery.

Kept independent of Flask so they can be tested without a running server.
"""
import re

MAX_SEARCH_LENGTH = 100
MAX_MODULE_LENGTH = 16
MODULE_CODE_PATTERN = re.compile(r"^[A-Z]{2,8}\d{3,4}$")


def normalized_search(value: str | None) -> str:
    """Trim accidental whitespace and cap excessively long search strings."""
    return (value or "").strip()[:MAX_SEARCH_LENGTH]


def escaped_like_contains(value: str) -> str:
    """Build a literal contains pattern for SQL LIKE with escape='\\'.

    SQLAlchemy still parameterizes this value when passed to .ilike().
    """
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def normalized_module(value: str | None) -> str:
    """Canonicalize a supplied module code; return blank when unspecified."""
    return (value or "").strip().upper()[:MAX_MODULE_LENGTH]


def valid_new_module(code: str) -> bool:
    """Disallow invalid module labels on newly created resources."""
    return bool(MODULE_CODE_PATTERN.fullmatch(code))
