"""Cross-cutting analysis — pair mode + discover mode over 3 signals."""

from .discover import discover
from .pair import pair

__all__ = ["discover", "pair"]
