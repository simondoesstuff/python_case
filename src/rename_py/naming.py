"""
Naming convention utilities for Python refactoring.
"""

import re


def _is_pascalcase(name: str) -> bool:
    """Check if a name follows PascalCase convention (likely a class/type)."""
    if not name or len(name) < 2:
        return False
    return name[0].isupper() and not name.isupper() and '_' not in name


def to_snake_case(name: str) -> str:
    """Converts a string to snake_case."""
    if not name:
        return ""
    
    if name.startswith('__') and name.endswith('__'):
        return name

    leading_underscores = len(name) - len(name.lstrip('_'))
    
    name = name.lstrip('_')
    # Add an underscore before any uppercase letter, except at the start
    s1 = re.sub(r"([A-Z]+)", r"_\1", name)
    # Handle cases where there's an uppercase letter after a lowercase letter or number
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    
    return "_" * leading_underscores + s2.lower().lstrip('_')


def to_pascal_case(name: str) -> str:
    """Converts a string to PascalCase."""
    snake_case_name = to_snake_case(name)
    return ''.join(word.capitalize() for word in snake_case_name.split('_'))