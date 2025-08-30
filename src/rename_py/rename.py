"""
Python refactoring tool - backward compatibility imports.

This module re-exports the main functionality for backward compatibility
while the actual implementation has been modularized for better maintainability.
"""

# Import and re-export main functionality for backward compatibility
from .core import refactor_source, refactor_directory
from .naming import to_snake_case, to_pascal_case, _is_pascalcase
from .file_operations import (
    should_rename_file, 
    get_new_file_path, 
    collect_file_renames, 
    execute_file_renames
)
from .module_detection import ImportAnalyzer
from .transformer import RenameTransformer

# Make all functions available at module level for backward compatibility
__all__ = [
    'refactor_source',
    'refactor_directory', 
    'to_snake_case',
    'to_pascal_case',
    'should_rename_file',
    'get_new_file_path',
    'collect_file_renames',
    'execute_file_renames',
    'ImportAnalyzer',
    'RenameTransformer',
]