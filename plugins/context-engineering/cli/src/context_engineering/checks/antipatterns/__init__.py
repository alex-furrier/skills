"""Antipattern checkers — each a pure function yielding Findings."""

from .runner import lint

__all__ = ["lint"]
