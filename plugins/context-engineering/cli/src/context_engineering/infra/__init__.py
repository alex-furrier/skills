"""Thin wrappers around the outside world — git, YAML, filesystem."""

from .filesystem import EXCLUDED_DIRS, read_text_safe
from .git import git_log, git_root
from .yaml_frontmatter import parse_frontmatter

__all__ = [
    "EXCLUDED_DIRS",
    "git_log",
    "git_root",
    "parse_frontmatter",
    "read_text_safe",
]
