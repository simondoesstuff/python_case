"""Snake Shift - Smart codebase refactoring from camelCase to pythonic snake_case."""

__version__ = "1.0.0"

from .core import refactor_source
from .file_operations import collect_file_renames, execute_file_renames

__all__ = ["refactor_source", "collect_file_renames", "execute_file_renames"]