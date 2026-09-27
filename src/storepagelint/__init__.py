"""storepagelint: does a game store page say its genre, and where can a reader find it."""

from .core import FOLD, Finding, Page, as_dict, check, find_terms, normalise, rules

__version__ = "0.1.0"
__all__ = [
    "FOLD",
    "Finding",
    "Page",
    "as_dict",
    "check",
    "find_terms",
    "normalise",
    "rules",
    "__version__",
]
